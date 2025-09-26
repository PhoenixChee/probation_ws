#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
import time
import math
import threading

from mavros_msgs.srv import SetMode
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32
from vision_msgs.msg import BoundingBoxArray

from .subscriber import BoundingBoxSubscriber


class AUVController(Node):
    
    def __init__(self):
        super().__init__('auv_controller')
        
        # Callback group for handling multiple operations
        self.callback_group = ReentrantCallbackGroup()
        
        # Initialize vision subscriber
        self.vision_subscriber = BoundingBoxSubscriber()
        
        # Service client for changing flight mode
        self.mode_client = self.create_client(
            SetMode, 
            '/mavros/set_mode',
            callback_group=self.callback_group
        )
        
        # Publishers for movement control
        self.cmd_vel_publisher = self.create_publisher(
            Twist, 
            '/mavros/setpoint_velocity/cmd_vel_unstamped', 
            10,
            callback_group=self.callback_group
        )
        
        # Individual axis publishers (if needed for specific control)
        self.vel_x_publisher = self.create_publisher(
            Float32, 
            '/mavros/setpoint_velocity/cmd_vel_unstamped/x', 
            10,
            callback_group=self.callback_group
        )
        self.vel_y_publisher = self.create_publisher(
            Float32, 
            '/mavros/setpoint_velocity/cmd_vel_unstamped/y', 
            10,
            callback_group=self.callback_group
        )
        self.vel_z_publisher = self.create_publisher(
            Float32, 
            '/mavros/setpoint_velocity/cmd_vel_unstamped/z', 
            10,
            callback_group=self.callback_group
        )
        
        # Control parameters
        self.max_linear_speed = 1.0
        self.max_angular_speed = 0.5
        self.target_depth_speed = 0.3
        self.approach_speed = 0.5
        self.search_speed = 0.3
        self.centering_gain = 2.0
        
        # State machine
        self.state = 'INITIALIZING'
        self.states = [
            'INITIALIZING',
            'SETTING_GUIDED_MODE', 
            'DESCENDING',
            'SEARCHING',
            'CENTERING',
            'APPROACHING',
            'PASSING_THROUGH',
            'COMPLETED'
        ]
        
        # Mission parameters
        self.target_depth_time = 10.0  # seconds to descend
        self.search_pattern_time = 5.0  # seconds per search direction
        self.approach_threshold = 0.6  # gate width threshold to start approach
        self.pass_through_time = 5.0   # seconds to pass through gate
        
        # Timing variables
        self.state_start_time = time.time()
        self.search_direction = 1  # 1 for right, -1 for left
        
        # Main control timer
        self.control_timer = self.create_timer(
            0.1,  # 10 Hz control loop
            self.control_loop,
            callback_group=self.callback_group
        )
        
        self.get_logger().info("AUV Controller initialized")
    
    def control_loop(self):
        """Main control loop state machine"""
        current_time = time.time()
        time_in_state = current_time - self.state_start_time
        
        if self.state == 'INITIALIZING':
            self.handle_initializing()
            
        elif self.state == 'SETTING_GUIDED_MODE':
            self.handle_setting_guided_mode()
            
        elif self.state == 'DESCENDING':
            self.handle_descending(time_in_state)
            
        elif self.state == 'SEARCHING':
            self.handle_searching(time_in_state)
            
        elif self.state == 'CENTERING':
            self.handle_centering()
            
        elif self.state == 'APPROACHING':
            self.handle_approaching()
            
        elif self.state == 'PASSING_THROUGH':
            self.handle_passing_through(time_in_state)
            
        elif self.state == 'COMPLETED':
            self.handle_completed()
    
    def change_state(self, new_state):
        """Change state and reset timer"""
        self.get_logger().info(f"State change: {self.state} -> {new_state}")
        self.state = new_state
        self.state_start_time = time.time()
    
    def handle_initializing(self):
        """Wait for services to be available"""
        if self.mode_client.wait_for_service(timeout_sec=1.0):
            self.change_state('SETTING_GUIDED_MODE')
        else:
            self.get_logger().info('Waiting for mavros services...')
    
    def handle_setting_guided_mode(self):
        """Set vehicle to GUIDED mode"""
        request = SetMode.Request()
        request.custom_mode = 'GUIDED'
        
        future = self.mode_client.call_async(request)
        
        def mode_response_callback(future):
            try:
                response = future.result()
                if response.mode_sent:
                    self.get_logger().info('Successfully set to GUIDED mode')
                    self.change_state('DESCENDING')
                else:
                    self.get_logger().warning('Failed to set GUIDED mode, retrying...')
                    time.sleep(1.0)
            except Exception as e:
                self.get_logger().error(f'Service call failed: {e}')
        
        future.add_done_callback(mode_response_callback)
    
    def handle_descending(self, time_in_state):
        """Descend to target depth"""
        if time_in_state < self.target_depth_time:
            # Move down
            cmd_vel = Twist()
            cmd_vel.linear.z = -self.target_depth_speed  # Negative Z is down
            self.cmd_vel_publisher.publish(cmd_vel)
            
            if time_in_state % 2.0 < 0.1:  # Log every 2 seconds
                self.get_logger().info(f'Descending... {time_in_state:.1f}s')
        else:
            # Stop and start searching
            self.stop_movement()
            self.change_state('SEARCHING')
    
    def handle_searching(self, time_in_state):
        """Search for the gate in a pattern"""
        gate_info = self.vision_subscriber.get_gate_info()
        
        if gate_info['detected']:
            self.get_logger().info('Gate detected! Moving to centering phase')
            self.stop_movement()
            self.change_state('CENTERING')
            return
        
        # Execute search pattern (horizontal sweep)
        if time_in_state < self.search_pattern_time:
            cmd_vel = Twist()
            cmd_vel.linear.y = self.search_direction * self.search_speed
            self.cmd_vel_publisher.publish(cmd_vel)
        else:
            # Change direction and continue searching
            self.search_direction *= -1
            self.state_start_time = time.time()
            self.get_logger().info(f'Changing search direction: {"right" if self.search_direction > 0 else "left"}')
    
    def handle_centering(self):
        """Center the gate in the camera view"""
        gate_info = self.vision_subscriber.get_gate_info()
        
        if not gate_info['detected']:
            self.get_logger().warning('Lost gate during centering, returning to search')
            self.change_state('SEARCHING')
            return
        
        if self.vision_subscriber.is_gate_centered():
            self.get_logger().info('Gate centered! Starting approach')
            self.stop_movement()
            self.change_state('APPROACHING')
            return
        
        # Calculate centering corrections
        x_error, y_error = self.vision_subscriber.get_centering_error()
        
        cmd_vel = Twist()
        # X error controls yaw (rotation around Z axis)
        cmd_vel.angular.z = -x_error * self.centering_gain
        # Y error controls vertical movement
        cmd_vel.linear.z = y_error * self.centering_gain
        
        # Limit velocities
        cmd_vel.angular.z = max(min(cmd_vel.angular.z, self.max_angular_speed), -self.max_angular_speed)
        cmd_vel.linear.z = max(min(cmd_vel.linear.z, self.max_linear_speed), -self.max_linear_speed)
        
        self.cmd_vel_publisher.publish(cmd_vel)
        
        self.get_logger().debug(f'Centering - X error: {x_error:.3f}, Y error: {y_error:.3f}')
    
    def handle_approaching(self):
        """Approach the gate"""
        gate_info = self.vision_subscriber.get_gate_info()
        
        if not gate_info['detected']:
            self.get_logger().warning('Lost gate during approach, returning to search')
            self.change_state('SEARCHING')
            return
        
        # Check if gate is large enough (close enough) to pass through
        if gate_info['width'] > self.approach_threshold:
            self.get_logger().info('Gate close enough! Starting pass through')
            self.change_state('PASSING_THROUGH')
            return
        
        # Continue moving forward while maintaining centering
        x_error, y_error = self.vision_subscriber.get_centering_error()
        
        cmd_vel = Twist()
        cmd_vel.linear.x = self.approach_speed  # Move forward
        
        # Minor corrections to stay centered
        if abs(x_error) > 0.05:  # Only correct if error is significant
            cmd_vel.angular.z = -x_error * self.centering_gain * 0.5  # Reduced gain
        if abs(y_error) > 0.05:
            cmd_vel.linear.z = y_error * self.centering_gain * 0.5
        
        # Limit velocities
        cmd_vel.angular.z = max(min(cmd_vel.angular.z, self.max_angular_speed * 0.5), -self.max_angular_speed * 0.5)
        cmd_vel.linear.z = max(min(cmd_vel.linear.z, self.max_linear_speed * 0.5), -self.max_linear_speed * 0.5)
        
        self.cmd_vel_publisher.publish(cmd_vel)
        
        self.get_logger().debug(f'Approaching - Gate width: {gate_info["width"]:.3f}')
    
    def handle_passing_through(self, time_in_state):
        """Pass through the gate"""
        if time_in_state < self.pass_through_time:
            # Continue moving forward
            cmd_vel = Twist()
            cmd_vel.linear.x = self.approach_speed
            self.cmd_vel_publisher.publish(cmd_vel)
            
            self.get_logger().info(f'Passing through gate... {time_in_state:.1f}s')
        else:
            # Mission completed
            self.stop_movement()
            self.change_state('COMPLETED')
    
    def handle_completed(self):
        """Mission completed - hover in place or return to ALT_HOLD"""
        self.stop_movement()
        self.get_logger().info('Mission completed! Gate successfully traversed.')
        
        # Optionally switch back to ALT_HOLD mode
        # self.set_mode('ALT_HOLD')
    
    def stop_movement(self):
        """Stop all movement"""
        cmd_vel = Twist()
        self.cmd_vel_publisher.publish(cmd_vel)
    
    def set_mode(self, mode):
        """Set flight mode"""
        request = SetMode.Request()
        request.custom_mode = mode
        
        future = self.mode_client.call_async(request)
        
        def mode_callback(future):
            try:
                response = future.result()
                if response.mode_sent:
                    self.get_logger().info(f'Successfully set to {mode} mode')
                else:
                    self.get_logger().warning(f'Failed to set {mode} mode')
            except Exception as e:
                self.get_logger().error(f'Mode change service call failed: {e}')
        
        future.add_done_callback(mode_callback)


def main(args=None):
    rclpy.init(args=args)
    
    try:
        # Create executor for handling multiple nodes
        executor = MultiThreadedExecutor()
        
        # Create controller
        controller = AUVController()
        
        # Add nodes to executor
        executor.add_node(controller)
        executor.add_node(controller.vision_subscriber)
        
        controller.get_logger().info('Starting AUV autonomous navigation...')
        
        # Spin the executor
        executor.spin()
        
    except KeyboardInterrupt:
        pass
    finally:
        # Clean shutdown
        controller.get_logger().info('Shutting down AUV controller...')
        controller.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()