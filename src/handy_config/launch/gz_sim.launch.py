from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    # ---------------- Launch arguments ----------------
    declared_arguments = [
        DeclareLaunchArgument(
            "world",
            default_value="empty.sdf",
            description="Gazebo world file",
        ),
        DeclareLaunchArgument(
            "use_sim",
            default_value="true",
            description="Use Gazebo simulation",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Use simulation time",
        ),
    ]

    handy_description_path = get_package_share_directory("handy_description")
    handy_config_path = get_package_share_directory("handy_config")
    gazebo_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=os.path.join(get_package_share_directory("handy_description"), "meshes")  
    )
    gz_resource_path = gazebo_resource_path

    robot_description_content = Command(
        [
            FindExecutable(name="xacro"),
            " ",
            os.path.join(handy_config_path, "config", "handy_description.urdf.xacro"),
            " ",
            "use_sim:=", LaunchConfiguration("use_sim"),
        ]
    )

    robot_description = {
        "robot_description": robot_description_content,
        "use_sim_time": LaunchConfiguration("use_sim_time"),
    }

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description],
    )

    world_file = PathJoinSubstitution(
        [handy_description_path, "worlds", LaunchConfiguration("world")]
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"]
            )
        ),
        launch_arguments={
            "gz_args": ["-r -v 4 ", world_file],
            "on_exit_shutdown": "true",
        }.items(),
    )

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name", "handy",
            "-topic", "robot_description",
            "-x", "0.0",
            "-y", "0.0",
            "-z", "0.1",
        ],
        output="screen",
    )

    gz_clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
        ],
        output="screen",
    )

    return LaunchDescription(
        declared_arguments
        + [
            gz_resource_path,
            gazebo,
            gz_clock_bridge,
            robot_state_publisher_node,
            spawn_entity,
        ]
    )
