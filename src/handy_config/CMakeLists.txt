cmake_minimum_required(VERSION 3.22)
project(handy_config)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(moveit_ros_move_group REQUIRED)
find_package(moveit_kinematics REQUIRED)
find_package(moveit_planners REQUIRED)
find_package(moveit_servo REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(moveit_core REQUIRED)

# add_executable(Twist_command scripts/Twist_command.cpp)
# ament_target_dependencies(rclcpp 
#   std_msgs 
#   sensor_msgs 
#   geometry_msgs 
#   moveit_ros_move_group 
#   moveit_kinematics 
#   moveit_planners 
#   moveit_servo
#   tf2_ros
#   tf2_geometry_msgs
#   moveit_core
# )

add_executable(keyboard_twist_teleop scripts/keyboard_twist_teleop.cpp)
ament_target_dependencies(keyboard_twist_teleop 
  rclcpp 
  std_msgs 
  sensor_msgs 
  geometry_msgs 
  moveit_ros_move_group 
  moveit_kinematics 
  moveit_planners 
  moveit_servo
  tf2_ros
  tf2_geometry_msgs
  moveit_core
)

install(TARGETS
  keyboard_twist_teleop
  DESTINATION lib/${PROJECT_NAME}
)

# Install esp_node.py as an executable Python node
install(PROGRAMS scripts/esp_node.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()


install(
  DIRECTORY launch 
  DESTINATION share/${PROJECT_NAME}
)


install(
  DIRECTORY scripts
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY config DESTINATION share/${PROJECT_NAME})
install(FILES .setup_assistant DESTINATION share/${PROJECT_NAME})



