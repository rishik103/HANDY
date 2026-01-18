from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, RegisterEventHandler
from launch.event_handlers import OnProcessExit, OnProcessStart
from launch.substitutions import LaunchConfiguration, Command
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder
from launch_ros.parameter_descriptions import ParameterValue
import os, pprint

def generate_launch_description():
    tutorial_arg = DeclareLaunchArgument("rviz_tutorial", default_value="False")
    ros2_control_hardware_type = DeclareLaunchArgument(
        "ros2_control_hardware_type", default_value="mock_components"
    )
    db_arg = DeclareLaunchArgument("db", default_value="False")

    moveit_config = (
        MoveItConfigsBuilder('handy', package_name='handy_config')
        .robot_description(
            file_path="config/handy_description.urdf.xacro",
            mappings={"ros2_control_hardware_type": LaunchConfiguration("ros2_control_hardware_type")}
        )
        .robot_description_semantic(
            file_path="config/handy_description.srdf"
        )
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .planning_pipelines(pipelines=["ompl"])
        .to_moveit_configs()
    )


    robot_description = ParameterValue(
        Command(["xacro ", os.path.join(get_package_share_directory('handy_config'), "config", "handy_description.urdf.xacro")]),
        value_type=str
    )

    rviz_base = os.path.join(get_package_share_directory("handy_config"), "launch")
    rviz_full_config = os.path.join(rviz_base, "moveit.rviz")
    rviz_empty_config = os.path.join(rviz_base, "moveit_empty.rviz")
    tutorial_mode = LaunchConfiguration("rviz_tutorial")

    
    
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_full_config],
        # Use the full MoveIt config dict to avoid accidentally passing
        # tuple-like attributes (which can raise ParameterValue type errors).
        parameters=[moveit_config.to_dict()],
        condition=UnlessCondition(tutorial_mode),
    )

    static_tf_node = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_transform_publisher",
        output="log",
        arguments=["0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "world", "base_link"],
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="both",
        parameters=[moveit_config.to_dict()],
    )

    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            {"robot_description": robot_description},
            os.path.join(get_package_share_directory("handy_config"), "config", "ros2_controllers.yaml"),
        ],
    )

     # Controller spawners - load joint_state_broadcaster first, then arm_controller
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arm_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_config.to_dict()],
        arguments=["--ros-args", "--log-level", "info"],
    )

    mongodb_server_node = Node(
        package="warehouse_ros_mongo",
        executable="mongo_wrapper_ros.py",
        parameters=[
            {"warehouse_port": 33829},
            {"warehouse_host": "localhost"},
            {"warehouse_plugin": "warehouse_ros_mongo::MongoDatabaseConnection"},
        ],
        output="screen",
        condition=IfCondition(LaunchConfiguration("db")),
    )


    servo_yaml = os.path.join(
    get_package_share_directory("handy_config"),
    "config",
    "servo.yaml"
)

    servo_node = Node(
        package="moveit_servo",
        executable="servo_node",
        name="servo_node",
        output="screen",
        parameters=[servo_yaml,
                    moveit_config.robot_description,
                    moveit_config.robot_description_semantic,
                    moveit_config.robot_description_kinematics
        ],
        arguments=["--ros-args", "--log-level", "info"],
    )



    return LaunchDescription(
        [
            tutorial_arg,
            db_arg,
            ros2_control_hardware_type,
            static_tf_node,
            robot_state_publisher,
            ros2_control_node,
            joint_state_broadcaster_spawner,
            arm_controller_spawner,
            move_group_node,
            rviz_node,
            mongodb_server_node,
            # servo_node
        ]
    )