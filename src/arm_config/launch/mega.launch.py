import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler, TimerAction, SetEnvironmentVariable, ExecuteProcess
from launch.event_handlers import OnProcessExit, OnProcessStart
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution, EnvironmentVariable
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
from launch_ros.parameter_descriptions import ParameterValue
from launch.conditions import IfCondition, UnlessCondition
from moveit_configs_utils import MoveItConfigsBuilder
from launch.substitutions import PathJoinSubstitution
    
def generate_launch_description():
    # Get package directories
    pkg_arm_config = get_package_share_directory("arm_config")
    pkg_handy_description = get_package_share_directory("handy_description")
    pkg_ros_gz_sim = get_package_share_directory("ros_gz_sim")

    # Set Gazebo model path
    gazebo_models_path, _ = os.path.split(pkg_arm_config)
    set_gazebo_model_path = SetEnvironmentVariable(
        name="GAZEBO_MODEL_PATH",
        value=gazebo_models_path
    )

    # Declare arguments
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "gui",
            default_value="true",
            description="Start Gazebo GUI",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Use simulation time",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "world",
            default_value="world_gz.sdf",
            description="Gazebo world to load",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "rviz_tutorial", default_value="False", description="Tutorial flag")
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "db", default_value="False", description="Database flag")
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "ros2_control_hardware_type",
            default_value="mock_components",
            description="ROS2 control hardware interface type to use for the launch file -- possible values: [mock_components, isaac]",
        )
    )

    # Initialize Arguments
    gui = LaunchConfiguration("gui")
    use_sim_time = LaunchConfiguration("use_sim_time")
    world = LaunchConfiguration("world")
    tutorial_mode = LaunchConfiguration("rviz_tutorial")
    db_config = LaunchConfiguration("db")
    ros2_control_hardware_type = LaunchConfiguration("ros2_control_hardware_type")

    # MoveIt config
    moveit_config = (
        MoveItConfigsBuilder("handy", package_name="arm_config")
        .robot_description(
            file_path="config/handy.urdf.xacro",
            mappings={
                "ros2_control_hardware_type": ros2_control_hardware_type
            },
        )
        .robot_description_semantic(file_path="config/handy.srdf")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .planning_pipelines(
            pipelines=["ompl", "chomp", "pilz_industrial_motion_planner"]
        )
        .to_moveit_configs()
    )

    # RViz configs
    rviz_base = os.path.join(pkg_arm_config, "launch")
    rviz_full_config = os.path.join(rviz_base, "moveit.rviz")
    rviz_empty_config = os.path.join(rviz_base, "moveit_empty.rviz")
    rviz_node_tutorial = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_empty_config],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.planning_pipelines,
            moveit_config.robot_description_kinematics,
        ],
        condition=IfCondition(tutorial_mode),
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_full_config],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.planning_pipelines,
            moveit_config.robot_description_kinematics,
        ],
        condition=UnlessCondition(tutorial_mode),
    )

    # Static TF
    static_tf_node = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_transform_publisher",
        output="log",
        arguments=["0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "world", "base_link"],
    )

    # ...removed duplicate robot_state_publisher node...

    # Robot description for ros2_control_node
    robot_description = ParameterValue(
        Command(
            [
                "xacro ",
                os.path.join(pkg_arm_config, "config", "handy.urdf.xacro")
            ]
        ),
        value_type=str,
    )

    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            {'robot_description': robot_description},
            os.path.join(
                pkg_arm_config,
                'config',
                'ros2_controllers.yaml'
            )
        ]
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
           'joint_state_broadcaster',
           '--controller-manager',
           '/controller_manager'
        ],
        output='screen',
    )

    # Synchronize arm_controller spawn after joint_state_broadcaster activation
    arm_controller_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[
                Node(
                    package='controller_manager',
                    executable='spawner',
                    arguments=['arm_controller', '--controller-manager', '/controller_manager'],
                    output='screen',
                )
            ],
        )
    )

    # Move group node
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_config.to_dict()],
        arguments=["--ros-args", "--log-level", "info"],
    )

    # Warehouse mongodb server
    mongodb_server_node = Node(
        package="warehouse_ros_mongo",
        executable="mongo_wrapper_ros.py",
        parameters=[
            {"warehouse_port": 33829},
            {"warehouse_host": "localhost"},
            {"warehouse_plugin": "warehouse_ros_mongo::MongoDatabaseConnection"},
        ],
        output="screen",
        condition=IfCondition(db_config),
    )

    # Get URDF via xacro for robot_state_publisher (from handy_gz.launch.py)
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([pkg_arm_config, "config", "handy.urdf.xacro"]),
            " ",
            "ros2_control_hardware_type:=gz_ros2_control",
        ]
    )
    robot_description_gz = {"robot_description": robot_description_content}

    robot_state_publisher_node_gz = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description_gz, {"use_sim_time": use_sim_time}],
    )

    # Gazebo
    # Use the world file from arm_config/worlds/world.sdf by default, allow override
    world_file = PathJoinSubstitution([pkg_arm_config, "worlds", LaunchConfiguration("world")])
    # gazebo = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource(
    #         os.path.join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")
    #     ),
    #     launch_arguments={
    #         "world": world_file
    #     }.items(),
    # )
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": "-r empty.sdf"}.items(),
    )

    # Spawn robot
    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "robot_description",
            "-name", "handy",
            "-z", "0.1",
        ],
        output="screen",
    )

    # ...removed redundant joint_state_broadcaster_spawner_gz and arm_controller_spawner_gz...

    # Bridge for joint states and commands
    gz_ros_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
        ],
        output="screen",
    )

    nodes = [
        set_gazebo_model_path,
        gazebo,
        robot_state_publisher_node_gz,
        spawn_entity,
        gz_ros_bridge,
        rviz_node,
        rviz_node_tutorial,
        static_tf_node,
        move_group_node,
        ros2_control_node,
        joint_state_broadcaster_spawner,
        arm_controller_spawner,
        mongodb_server_node,
    ]

    return LaunchDescription(declared_arguments + nodes)