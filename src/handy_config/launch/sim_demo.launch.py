from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.conditions import IfCondition
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument(
            "world",
            default_value="empty.sdf",
            description="Gazebo world file",
        ),
        DeclareLaunchArgument(
            "use_sim",
            default_value="true",
            description="Use Gazebo-backed ros2_control",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Use simulation time",
        ),
        DeclareLaunchArgument(
            "rviz_tutorial",
            default_value="false",
            description="Launch RViz in tutorial mode",
        ),
        DeclareLaunchArgument(
            "db",
            default_value="false",
            description="Start MongoDB warehouse",
        ),
        DeclareLaunchArgument(
            "start_keyboard_teleop",
            default_value="false",
            description="Start keyboard twist teleop node",
        ),
    ]

    gz_sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("handy_config"), "launch", "gz_sim.launch.py"]
            )
        ),
        launch_arguments={
            "world": LaunchConfiguration("world"),
            "use_sim": LaunchConfiguration("use_sim"),
            "use_sim_time": LaunchConfiguration("use_sim_time"),
        }.items(),
    )

    moveit_demo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("handy_config"), "launch", "demo.launch.py"]
            )
        ),
        launch_arguments={
            "use_sim": LaunchConfiguration("use_sim"),
            "use_sim_time": LaunchConfiguration("use_sim_time"),
            "rviz_tutorial": LaunchConfiguration("rviz_tutorial"),
            "db": LaunchConfiguration("db"),
            # gz_sim.launch.py already starts robot_state_publisher.
            "start_robot_state_publisher": "false",
        }.items(),
    )

    keyboard_twist_teleop = Node(
        package="handy_config",
        executable="keyboard_twist_teleop",
        name="keyboard_twist_teleop",
        output="screen",
        emulate_tty=True,
        condition=IfCondition(LaunchConfiguration("start_keyboard_teleop")),
    )

    return LaunchDescription(
        declared_arguments + [gz_sim_launch, moveit_demo_launch, keyboard_twist_teleop]
    )
