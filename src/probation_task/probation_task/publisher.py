#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from geometry_msgs.msg import Twist
from mavros_msgs.srv import SetMode

class MovePublisher(Node):

    def __init__(self):
        super().__init__("move_publisher")

        self.cmd_vel_pub_x_ = self.create_publisher(Float32, '/mavros/setpoint_velocity/cmd_vel_unstamped/x', 10)
        self.cmd_vel_pub_y_ = self.create_publisher(Float32, '/mavros/setpoint_velocity/cmd_vel_unstamped/y', 10)
        self.cmd_vel_pub_z_ = self.create_publisher(Float32, '/mavros/setpoint_velocity/cmd_vel_unstamped/z', 10)
        # self.timer_ = self.create_timer(0.5, self.send_velocity_command)

        self.cmd_movement_ = self.create_publisher(Twist, '/mavros/setpoint_velocity/cmd_vel_unstamped', 10)
        # self.timer_ = self.create_timer(0.5, self.send_geometry_command)

    def send_velocity_command(self):
        msg_x = Float32()
        msg_x.data = 0.0
        msg_y = Float32()
        msg_y.data = 0.0
        msg_z = Float32()
        msg_z.data = 0.0

        self.cmd_vel_pub_x_.publish(msg_x)
        self.cmd_vel_pub_y_.publish(msg_y)
        self.cmd_vel_pub_z_.publish(msg_z)

        self.get_logger().info(f'X: "{msg_x.data:.2f}" Y: "{msg_y.data:.2f}" Z: "{msg_z.data:.2f}"')

    def send_geometry_command(self):
        twist_msg = Twist()
        twist_msg.linear.x = 0.0    # Forward velocity
        twist_msg.linear.y = 0.0    # lateral movement
        twist_msg.linear.z = 0.0    # vertical movement
        twist_msg.angular.x = 0.0   # Roll (Not used)
        twist_msg.angular.y = 0.0   # Pitch (Not used)
        twist_msg.angular.z = 0.5   # Yaw rate

        self.cmd_movement_.publish(twist_msg)

        self.get_logger().info(f'X: "{twist_msg.linear.x:.2f}" Y: "{twist_msg.linear.y:.2f}" Z: "{twist_msg.linear.z:.2f}", Angular Z: "{twist_msg.angular.z:.2f}"')

def main(args=None):
    rclpy.init(args=args)

    node = MovePublisher()
    node.get_logger().info("Move Publisher Node has been started.")
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()