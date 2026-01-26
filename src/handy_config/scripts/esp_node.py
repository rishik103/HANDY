#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from control_msgs.msg import JointTrajectoryControllerState
import serial
import math

class ESP32Bridge(Node):
    def __init__(self):
        super().__init__('esp32_bridge')
        self.declare_parameter("serial_port", "/dev/ttyUSB0")
        self.declare_parameter("baud_rate", 115200) 
        self.port_ = self.get_parameter("serial_port").value
        self.baud_rate_ = self.get_parameter("baud_rate").value
        
        self.sub = self.create_subscription(
            JointTrajectoryControllerState,
            '/arm_controller/controller_state',
            self.cb,
            10)
        self.esp_port = serial.Serial(port=self.port_, baudrate=self.baud_rate_, timeout=0.1)
        self.get_logger().info(f"Connected to ESP32 on {self.port_} at {self.baud_rate_} baud.", throttle_duration_sec=1.0)
    
    def cb(self, msg):
        cmd = msg.output.positions
        cmd_deg = [max(0.0, min(180.0, math.degrees(x))) for x in cmd   ]
        line = ",".join(f"{x:.4f}" for x in cmd_deg) + "\n"
        self.get_logger().info(f"Sending to ESP32: {line.strip()}")
        try:
            self.esp_port.write(line.encode())     
        except serial.SerialException as e:
            self.get_logger().error(f"Failed to write to ESP32: {e}")

    def destroy_node(self):
        if self.esp_port.is_open:
            self.esp_port.close()
        super().destroy_node()   



def main():
    rclpy.init()
    node = ESP32Bridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
