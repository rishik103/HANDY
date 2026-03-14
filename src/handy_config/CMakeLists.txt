cmake_minimum_required(VERSION 3.22)
project(handy_config)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(moveit_msgs REQUIRED)

add_executable(keyboard_twist_teleop src/keyboard_twist_teleop.cpp)
ament_target_dependencies(keyboard_twist_teleop rclcpp geometry_msgs moveit_msgs)

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/launch")
  install(
    DIRECTORY launch 
    DESTINATION share/${PROJECT_NAME}
    PATTERN "setup_assistant.launch" EXCLUDE)
endif()

install(DIRECTORY config DESTINATION share/${PROJECT_NAME})
install(FILES .setup_assistant DESTINATION share/${PROJECT_NAME})
install(TARGETS keyboard_twist_teleop DESTINATION lib/${PROJECT_NAME})

ament_package()
