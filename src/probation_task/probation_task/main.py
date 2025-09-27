#!/usr/bin/env python3
import math

import rclpy
from rclpy.node import Node
from vision_msgs.msg import BoundingBoxArray
from std_msgs.msg import Float64
from geometry_msgs.msg import Twist
from mavros_msgs.srv import SetMode

class MovePublisher(Node):

    # To initialize the node, we need to call the parent class constructor
    def __init__(self):
        super().__init__("move_publisher")

        # Create a client for the SetMode (Service)
        self.cli = self.create_client(SetMode, '/mavros/set_mode')

        # Wait until the service is available
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = SetMode.Request()

        # Sensors (Subscribers)
        self.box_subscriber_ = self.create_subscription(BoundingBoxArray, '/main_camera/detection/bounding_boxes', self.box_callback, 10)
        self.compass_subscriber_ = self.create_subscription(Float64, '/mavros/global_position/compass_hdg', self.compass_callback, 10)
        self.position_subscriber_ = self.create_subscription(Float64, '/mavros/global_position/rel_alt', self.position_callback, 10)

        # Movement (Publisher)
        self.cmd_movement_ = self.create_publisher(Twist, '/mavros/setpoint_velocity/cmd_vel_unstamped', 10)

        # Parameters for Box Detection
        self.last_boxes = []
        self.target_label_name = self.declare_parameter('target_label_name', 'gate').value
        self.target_label_id = int(self.declare_parameter('target_label_id', 3).value)      # wtf is gate id 3??? Wasted 2 hours finding out gate id is 3 not 4
        self.det_conf_threshold = self.declare_parameter('det_conf_threshold', 0.70).value
        self.target_box = None

        self.kp_linear_y = self.declare_parameter('linear_y_kp', 2.5).value
        self.kd_linear_y = self.declare_parameter('linear_y_kd', 0.3).value
        self.prev_error_y = 0.0
        self.max_y_vel = self.declare_parameter('max_y_vel', 2.0).value

        # Parameters for Heading Control
        self.kp_heading = self.declare_parameter('yaw_kp', 0.8).value
        self.kd_heading = self.declare_parameter('yaw_kd', 0.12).value
        self.prev_error_deg = 0.0
        self.max_yaw_rate = self.declare_parameter('max_yaw_rate', 2.0).value
        self.target_heading = self.declare_parameter('target_heading', 180.0).value
        self.current_heading = None

        # Parameters for Depth Control
        self.kp_depth = self.declare_parameter('depth_kp', 2.0).value
        self.max_z_vel = self.declare_parameter('max_z_vel', 1.0).value
        self.depth_positive_down = self.declare_parameter('depth_positive_down', True).value
        self.invert_z_cmd = self.declare_parameter('invert_z_cmd', False).value
        self.target_depth = self.declare_parameter('target_depth', -1.5).value
        self.current_depth = None

        # Control Loop Timer
        self.dt = 0.01  # Control loop interval in seconds
        self.timer = self.create_timer(self.dt, self.control_movement)  # Control loop at 100 Hz

    def send_request(self):
        self.req.custom_mode = 'GUIDED'
        return self.cli.call_async(self.req)

    def box_callback(self, msg: BoundingBoxArray):
        boxes = []
        for box in msg.bounding_boxes:
            boxes.append({
                'x': float(box.x),  # center x (relative)
                'y': float(box.y),  # center y (relative)
                'w': float(box.w),  # width (relative)
                'h': float(box.h),  # height (relative)
                'conf': float(getattr(box, 'conf', 0.0)),
                'label_id': int(box.label_id),
                'label_name': str(box.label_name),
            })
        self.last_boxes = boxes
        # self.get_logger().info(f'{len(self.last_boxes)} boxes: {self.last_boxes}')

        candidates = [box for box in boxes if self._is_target_box(box)]
        best = self._select_best(candidates)

        # Get target box information
        if best is None:
            self.target_box = None
            # self.get_logger().info(f'No target box detected. (boxes={len(boxes)})')
            return

        self.target_box = best
        self.dx = best['x'] - 0.5  # Horizontal offset from center (negative is left, positive is right)
        self.dy = best['y'] - 0.5  # Vertical offset from center (negative is up, positive is down)
        # self.get_logger().info(f'Target box detected: name={best["label_name"]}_{best["label_id"]} conf={best["conf"]:.2f} center=({best["x"]:.2f},{best["y"]:.2f}) size=({best["w"]:.2f},{best["h"]:.2f}) offset=({dx:.2f},{dy:.2f})')

    # Check if the detected box matches the confidence threshold (Filtering)
    def _is_target_box(self, boxes: dict):
        if boxes['conf'] < self.det_conf_threshold:
            return False
        if self.target_label_id >= 0:
            return boxes['label_id'] == self.target_label_id
        return boxes['label_name'] == self.target_label_name

    # Select the best candidate box based on highest confidence (Ranking)
    def _select_best(self, candidates: list[dict]) -> dict | None:
        if not candidates:
            return None
        return max(candidates, key=lambda boxes: boxes['conf'])

    def compass_callback(self, msg: Float64):
        self.current_heading = float(msg.data)

    def position_callback(self, msg: Float64):
        self.current_depth = float(msg.data)

    def angle_error(self, target, current):
        target = math.radians(target)
        current = math.radians(current)
        return math.atan2(math.sin(target - current), math.cos(target - current))

    def control_movement(self):
        cmd = Twist()

        # PD Control for Lateral Movement (Y-axis)
        if self.target_box is not None:
            error_y = self.target_box['x'] - 0.5  # Horizontal offset from center (negative is left, positive is right)
            error_rate_y = (error_y - self.prev_error_y) / self.dt

            max_derivative = 1.0  # Limit derivative to avoid spikes
            error_rate_y = max(-max_derivative, min(max_derivative, error_rate_y))  # Clamp derivative

            y_vel = (self.kp_linear_y * error_y) + (self.kd_linear_y * error_rate_y)
            y_vel = max(-self.max_y_vel, min(self.max_y_vel, -y_vel))  # Clamp to max y velocity
            self.prev_error_y = error_y

            cmd.linear.y = y_vel 
            # self.get_logger().info(f'Target: {self.target_box["label_name"]}_{self.target_box["label_id"]}, center: ({self.dx:.2f}, {self.dy:.2f}), Error: "{error_y:.2f}", Y Velocity: "{cmd.linear.y:.2f}"')

        # PD Control for Heading
        if self.current_heading is not None:
            error_deg = self.angle_error(self.target_heading, self.current_heading)
            error_rate_deg = (error_deg - self.prev_error_deg) / self.dt

            max_derivative = math.radians(90)
            error_rate_deg = max(-max_derivative, min(max_derivative, error_rate_deg))  # Clamp derivative to avoid spikes

            yaw_rate = (self.kp_heading * error_deg) + (self.kd_heading * error_rate_deg)
            yaw_rate = max(-self.max_yaw_rate, min(self.max_yaw_rate, -yaw_rate))  # Clamp to max yaw rate
            self.prev_error_deg = error_deg

            cmd.angular.z = yaw_rate
            # self.get_logger().info(f'Current: "{self.current_heading:.2f}", Target: "{self.target_heading:.2f}", Yaw Rate: "{cmd.angular.z:.2f}", Error: "{error:.2f}"')

        # P Control for Depth
        if self.current_depth is not None:

            depth_error = self.target_depth - self.current_depth
            z_vel = self.kp_depth * depth_error
            z_vel = max(-self.max_z_vel, min(self.max_z_vel, z_vel))  # Clamp to max z velocity

            cmd.linear.z = z_vel
            # self.get_logger().info(f'Current Depth: "{self.current_depth:.2f}", Target Depth: "{self.target_depth:.2f}", Z Velocity: "{cmd.linear.z:.2f}"')

        # Only publish if at least one control value is set (No need Box detection)
        if self.current_heading is not None and self.current_depth is not None:
            now = self.get_clock().now()
            if self.movement_started is None:
                self.movement_started = now
            elapsed = (now - self.movement_started).nanoseconds / 1e9

            cmd.linear.x = 0.3 if elapsed >= 10.0 else 0.0

            self.cmd_movement_.publish(cmd)
            self.get_logger().info(f'LinearXYZ=({cmd.linear.x:.2f}, {cmd.linear.y:.2f}, {cmd.linear.z:.2f}), AngularXYZ=({cmd.angular.x:.2f}, {cmd.angular.y:.2f}, {cmd.angular.z:.2f})')
        else:
            self.movement_started = None

def main(args=None):
    rclpy.init(args=args)

    node = MovePublisher()
    node.get_logger().info("Node has been started.")
    future = node.send_request()

    def _on_set_mode_done(fut):
        try:
            response = fut.result()
            if response.mode_sent:
                node.get_logger().info('SetMode: success')
            else:
                node.get_logger().warn('SetMode: failed')
        except Exception as e:
            node.get_logger().error(f'SetMode call error: {e}')

    future.add_done_callback(_on_set_mode_done)

    try:
        rclpy.spin(node)  # keep running timers/subscribers/publishers
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down...')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()