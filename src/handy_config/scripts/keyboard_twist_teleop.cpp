#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist_stamped.hpp>
#include <moveit_msgs/srv/servo_command_type.hpp>
#include <termios.h>
#include <unistd.h>
#include <fcntl.h>
#include <thread>
#include <atomic>
#include <mutex>
#include <chrono>

class KeyboardTwistTeleop : public rclcpp::Node
{
public:
  KeyboardTwistTeleop() : Node("keyboard_twist_teleop")
  {
    // ---------------- Parameters ----------------
    declare_parameter("planning_frame", "Link6");
    declare_parameter("linear_vel", 0.02);   // m/s
    declare_parameter("angular_vel", 0.1);   // rad/s
    declare_parameter("deadman_timeout_ms", 150);  // ms before deadman expires

    frame_id_ = get_parameter("planning_frame").as_string();
    lin_vel_  = get_parameter("linear_vel").as_double();
    ang_vel_  = get_parameter("angular_vel").as_double();
    deadman_timeout_ = std::chrono::milliseconds(
      get_parameter("deadman_timeout_ms").as_int());

    // ---------------- Publisher ----------------
    pub_ = create_publisher<geometry_msgs::msg::TwistStamped>(
      "/moveit_servo/delta_twist_cmds",
      rclcpp::QoS(10).reliable());

    // ---------------- Service Client ----------------
    switch_cmd_client_ = create_client<moveit_msgs::srv::ServoCommandType>(
      "/moveit_servo/switch_command_type");
    
    // Switch to TWIST mode on startup
    enableTwistMode();

    // ---------------- Timer ----------------
    timer_ = create_wall_timer(
      std::chrono::milliseconds(100),   // 100 Hz
      std::bind(&KeyboardTwistTeleop::publishTwist, this));

    // ---------------- Keyboard ----------------
    if (!openKeyboardInput()) {
      RCLCPP_ERROR(get_logger(), "Failed to open keyboard input. Run in a terminal with keyboard access.");
      RCLCPP_ERROR(get_logger(), "Try: ros2 run handy_config keyboard_twist_teleop");
    } else {
      startKeyboardThread();
      RCLCPP_INFO(get_logger(), "Keyboard Twist Teleop started");
      RCLCPP_INFO(get_logger(), "Controls: WASD=XY, R/F=Z up/down, Q/E=rotate");
      RCLCPP_INFO(get_logger(), "Hold SPACE as deadman switch while pressing motion keys");
    }
  }

  ~KeyboardTwistTeleop()
  {
    // Stop keyboard thread
    running_ = false;
    if (keyboard_thread_.joinable())
      keyboard_thread_.join();

    // Send explicit zero command once
    geometry_msgs::msg::TwistStamped stop;
    stop.header.stamp = now();
    stop.header.frame_id = frame_id_;
    stop.twist = geometry_msgs::msg::Twist();
    pub_->publish(stop);

    restoreTerminal();
  }

private:
  // ---------------- Keyboard Handling ----------------

  bool openKeyboardInput()
  {
    // Check if stdin is a terminal
    if (!isatty(STDIN_FILENO)) {
      RCLCPP_WARN(get_logger(), "stdin is not a terminal");
      return false;
    }
    return true;
  }

  void startKeyboardThread()
  {
    setTerminalRaw();

    keyboard_thread_ = std::thread([this]()
    {
      char c;
      while (running_)
      {
        // Use select() for non-blocking read with timeout
        fd_set fds;
        FD_ZERO(&fds);
        FD_SET(STDIN_FILENO, &fds);
        
        struct timeval tv;
        tv.tv_sec = 0;
        tv.tv_usec = 50000;  // 50ms timeout
        
        int ret = select(STDIN_FILENO + 1, &fds, nullptr, nullptr, &tv);
        if (ret > 0 && FD_ISSET(STDIN_FILENO, &fds)) {
          if (read(STDIN_FILENO, &c, 1) > 0) {
            handleKey(c);
          }
        }
      }
    });
  }

  void handleKey(char c)
  {
    auto now_time = std::chrono::steady_clock::now();
    
    // Debug: print the key being pressed
    RCLCPP_INFO(get_logger(), "Key pressed: '%c' (ASCII: %d)", c, static_cast<int>(c));
    
    std::lock_guard<std::mutex> lock(twist_mutex_);
    
    // Reset twist each keypress, then set the active direction
    twist_ = geometry_msgs::msg::Twist();
    last_key_time_ = now_time;
    key_active_ = true;

    // Set velocity based on key
    switch (c)
    {
      case 'w': case 'W': twist_.linear.x  =  lin_vel_; break;
      case 's': case 'S': twist_.linear.x  = -lin_vel_; break;
      case 'a': case 'A': twist_.linear.y  =  lin_vel_; break;
      case 'd': case 'D': twist_.linear.y  = -lin_vel_; break;
      case 'r': case 'R': twist_.linear.z  =  lin_vel_; break;
      case 'f': case 'F': twist_.linear.z  = -lin_vel_; break;

      case 'q': case 'Q': twist_.angular.z =  ang_vel_; break;
      case 'e': case 'E': twist_.angular.z = -ang_vel_; break;
      
      case ' ':  // SPACE = immediate stop
        twist_ = geometry_msgs::msg::Twist();
        key_active_ = false;
        RCLCPP_INFO(get_logger(), "STOP");
        break;
      
      // ESC or Ctrl+C to stop
      case 27: case 3:
        running_ = false;
        break;
      default: 
        key_active_ = false;
        break;
    }
  }

  // ---------------- Publishing ----------------

  void publishTwist()
  {
    geometry_msgs::msg::TwistStamped msg;
    msg.header.stamp = now();
    msg.header.frame_id = frame_id_;

    {
      std::lock_guard<std::mutex> lock(twist_mutex_);
      
      auto now_time = std::chrono::steady_clock::now();
      bool key_valid = key_active_ && 
                       (now_time - last_key_time_) <= deadman_timeout_;
      
      if (key_valid) {
        msg.twist = twist_;
        RCLCPP_INFO(get_logger(), "Publishing twist: x=%.3f y=%.3f z=%.3f", 
                    twist_.linear.x, twist_.linear.y, twist_.linear.z);
      } else {
        msg.twist = geometry_msgs::msg::Twist();
        twist_ = geometry_msgs::msg::Twist();  // Reset stored twist
        key_active_ = false;
      }
    }

    pub_->publish(msg);
  }

  // ---------------- Enable Servo TWIST Mode ----------------

  void enableTwistMode()
  {
    RCLCPP_INFO(get_logger(), "Waiting for servo switch_command_type service...");
    
    if (!switch_cmd_client_->wait_for_service(std::chrono::seconds(5))) {
      RCLCPP_ERROR(get_logger(), "Service not available! Is servo node running?");
      return;
    }

    auto request = std::make_shared<moveit_msgs::srv::ServoCommandType::Request>();
    request->command_type = 1;  // TWIST mode

    auto future = switch_cmd_client_->async_send_request(request,
      [this](rclcpp::Client<moveit_msgs::srv::ServoCommandType>::SharedFuture response) {
        if (response.get()->success) {
          RCLCPP_INFO(get_logger(), "Servo switched to TWIST mode successfully");
        } else {
          RCLCPP_ERROR(get_logger(), "Failed to switch servo to TWIST mode");
        }
      });
  }

  // ---------------- Terminal Control ----------------

  void setTerminalRaw()
  {
    tcgetattr(STDIN_FILENO, &orig_term_);
    termios raw = orig_term_;
    raw.c_lflag &= ~(ICANON | ECHO);
    raw.c_cc[VMIN] = 0;   // Non-blocking
    raw.c_cc[VTIME] = 0;
    tcsetattr(STDIN_FILENO, TCSANOW, &raw);
  }

  void restoreTerminal()
  {
    tcsetattr(STDIN_FILENO, TCSANOW, &orig_term_);
  }

  // ---------------- Members ----------------

  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr pub_;
  rclcpp::Client<moveit_msgs::srv::ServoCommandType>::SharedPtr switch_cmd_client_;
  rclcpp::TimerBase::SharedPtr timer_;
  std::thread keyboard_thread_;

  std::atomic<bool> running_{true};
  bool key_active_{false};
  std::chrono::steady_clock::time_point last_key_time_;
  std::chrono::milliseconds deadman_timeout_;

  geometry_msgs::msg::Twist twist_;
  std::mutex twist_mutex_;

  std::string frame_id_;
  double lin_vel_{0.0};
  double ang_vel_{0.0};

  termios orig_term_;
};

// ---------------- main ----------------

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<KeyboardTwistTeleop>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
