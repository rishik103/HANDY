cmake_minimum_required(VERSION 3.22)
project(handy_description)

find_package(ament_cmake REQUIRED)


# Install URDF files
install(
  DIRECTORY urdf
  DESTINATION share/${PROJECT_NAME}
)

# Install mesh files
install(
  DIRECTORY meshes
  DESTINATION share/${PROJECT_NAME}
)


ament_package()