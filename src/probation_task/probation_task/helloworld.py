#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

# node allows the class to have ROS2 functionality
class HelloWorldNode(Node):

    # To initialize the node, we need to call the parent class constructor
    def __init__(self):
        super().__init__("helloworld")
        self.counter_ = 0
        self.create_timer(1.0, self.timer_callback)

    def timer_callback(self):
        self.get_logger().info("Hello World." + str(self.counter_))
        self.counter_ += 1

def main(args=None):
    rclpy.init(args=args)

    node = HelloWorldNode()
    node.get_logger().info("Hello World Node has been started.")
    rclpy.spin(node)        # Keep the node alive until interrupted
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()