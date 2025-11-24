from launch_ros.parameter_descriptions import ParameterValue
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Joint State Publisher GUI
    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen'
    )
    urdf_file = os.path.join(
        get_package_share_directory('handy_description'),
        'urdf',
        'handy_arm.urdf'
    )

    # Robot State Publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
    parameters=[{'robot_description': ParameterValue(open(urdf_file).read(), value_type=str)}]
    )

    # RViz
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
    )

    # gazebo_node removed

    # Gazebo Fortress (using ros_gz_sim)
    # gazebo_node = ExecuteProcess(
    #     cmd=['ros_gz', 'sim', '-v', '4'],
    #     output='screen'
    # )

    # # Spawn robot in Gazebo Fortress using ros_gz service call
    # spawn_entity = ExecuteProcess(
    #     cmd=[
    #         'ros2', 'service', 'call', '/world/default/create', 'ros_gz_interfaces/srv/EntityFactory',
    #         '{sdf_filename: "' + urdf_file + '", name: "robot"}'
    #     ],
    #     output='screen'
    # )

    return LaunchDescription([
        joint_state_publisher_gui_node,
        robot_state_publisher_node,
        rviz_node,
    ])
    