# TEST VERSION: README (do not treat as final)

## Handy robotic arm — project overview

This repository contains a ROS2-compatible robotic arm project (Handy). It includes simulation, robot description, and MoveIt configuration to experiment with planning and controllers.

Key features
- URDF/XACRO robot description and meshes located in `src/handy_description/`.
- MoveIt configuration and planning parameters under `src/arm_config/config/`.
- Launch files for simulation, RViz, MoveIt, and controller startup in `src/arm_config/launch/` and `src/handy_description/launch/`.
- Gazebo (Ignition) world and SDF file in `src/arm_config/worlds/` for running a simulated robot.
- Controller configuration for ros2_control and MoveIt integration.
- Example initial positions, joint limits, and kinematics configurations for testing planning pipelines.

Quick start (development machine)
1. Install ROS 2 (compatible distro) and colcon. Follow official ROS 2 install instructions for your distro.
2. From the workspace root (/home/rishik/handy):

   - Build the workspace:
     colcon build --symlink-install

   - Source the workspace:
     source install/setup.bash

   - Launch a simulation or RViz using the provided launch files, for example:
     ros2 launch arm_config demo.launch.py

Notes and caveats
- This README is a placeholder test version. Update it with more detailed build/run instructions, dependency lists (ROS packages), and contribution guidelines.
- Large binary files (meshes) are present in `src/handy_description/meshes/` — consider using Git LFS if pushing to a remote that requires it.

License and attribution
- Check `src/handy_description/LICENSE` for licensing information.

Contact / next steps
- If you want, I can add CI, more detailed developer/setup steps, or push this repository to a remote for you — provide the remote URL and branch preference.
