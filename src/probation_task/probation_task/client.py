#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from mavros_msgs.srv import SetMode

class ClientAsync(Node):

    def __init__(self):
        super().__init__("client_async")
        self.cli = self.create_client(SetMode, '/mavros/set_mode') # Create a client for the SetMode service

        # Wait until the service is available
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = SetMode.Request()

    def send_request(self):
        self.req.custom_mode = 'GUIDED'
        return self.cli.call_async(self.req)

def main(args=None):
    rclpy.init(args=args)

    node = ClientAsync()
    node.get_logger().info("Client Async Node has been started.")
    future = node.send_request()
    rclpy.spin_until_future_complete(node, future)
    response = future.result()
    if response.mode_sent:
        node.get_logger().info('Service call successful')
    else:
        node.get_logger().info('Service call failed')

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()