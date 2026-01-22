#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from control_msgs.msg import JointTrajectoryControllerState
# import serial

class ESP32Bridge(Node):
    def __init__(self):
        super().__init__('esp32_bridge')
        self.sub = self.create_subscription(
            JointTrajectoryControllerState,
            '/arm_controller/controller_state',
            self.cb,
            10)
        # self.ser = serial.Serial('/dev/ttyUSB0', 115200)

    def cb(self, msg):
        cmd = msg.output.positions
        line = ",".join(f"{x:.4f}" for x in cmd) + "\n"
        self.get_logger().info(f"Sending to ESP32: {line.strip()}")
        # self.ser.write(line.encode())

def main():
    rclpy.init()
    node = ESP32Bridge()
    rclpy.spin(node)

if __name__ == '__main__':
    main()
