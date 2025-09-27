#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, Float64
from vision_msgs.msg import BoundingBoxArray

class SensorSubscriber(Node):

    def __init__(self):
        super().__init__("sensor_subscriber")
        # self.box_subscriber_ = self.create_subscription(BoundingBoxArray, '/main_camera/detection/bounding_boxes', self.box_callback, 10)
        # self.compass_subscriber_ = self.create_subscription(Float64, '/mavros/global_position/compass_hdg', self.compass_callback, 10)
        self.position_subscriber_ = self.create_subscription(Float64, '/mavros/global_position/rel_alt', self.position_callback, 10)

    def box_callback(self, msg: BoundingBoxArray):
        self.get_logger().info(str(msg))

    def compass_callback(self, msg: Float64):
        self.get_logger().info(f'Heading: "{msg.data:.2f}"')

    def position_callback(self, msg: Float64):
        self.get_logger().info(f'Position - Altitude: "{msg.data:.2f}"')

def main(args=None):
    rclpy.init(args=args)

    node = SensorSubscriber()
    node.get_logger().info("Sensor Subscriber Node has been started.")
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()