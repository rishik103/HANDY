from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    keyboard_node = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='keyboard_twist',
        prefix='xterm -e',
        output='screen',
        parameters=[{
            "stamped": True,
            "speed": 0.5,
            "frame_id": "base_link",
            "cmd_vel": "/servo_node/delta_twist_cmds"
        }]
    )
    return LaunchDescription([
        keyboard_node
])