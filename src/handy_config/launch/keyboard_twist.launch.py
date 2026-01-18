from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package="handy_config",
            executable="keyboard_twist_teleop",
            name="keyboard_twist_teleop",
            output="screen",
             parameters=[{
        "planning_frame": "base_link",
        "linear_vel": 0.02,
        "angular_vel": 0.1,
                         }],
            ),
])