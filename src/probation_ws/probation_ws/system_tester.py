#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import time

from mavros_msgs.srv import SetMode
from geometry_msgs.msg import Twist
from vision_msgs.msg import BoundingBoxArray

from .subscriber import BoundingBoxSubscriber


class SystemTester(Node):
    """Test individual components of the AUV system"""
    
    def __init__(self):
        super().__init__('system_tester')
        
        # Initialize components
        self.vision_subscriber = BoundingBoxSubscriber()
        
        # Service client
        self.mode_client = self.create_client(SetMode, '/mavros/set_mode')
        
        # Publisher
        self.cmd_vel_publisher = self.create_publisher(Twist, '/mavros/setpoint_velocity/cmd_vel_unstamped', 10)
        
        self.get_logger().info("System Tester initialized")
    
    def test_mode_service(self):
        """Test setting flight mode"""
        self.get_logger().info("Testing mode service...")
        
        if not self.mode_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error("MAVROS service not available")
            return False
        
        request = SetMode.Request()
        request.custom_mode = 'GUIDED'
        
        try:
            future = self.mode_client.call_async(request)
            rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
            
            if future.result():
                response = future.result()
                if response.mode_sent:
                    self.get_logger().info("✓ Mode service working correctly")
                    return True
                else:
                    self.get_logger().warning("✗ Mode not accepted by vehicle")
                    return False
            else:
                self.get_logger().error("✗ Service call timeout")
                return False
                
        except Exception as e:
            self.get_logger().error(f"✗ Service call failed: {e}")
            return False
    
    def test_velocity_publisher(self):
        """Test velocity publishing"""
        self.get_logger().info("Testing velocity publisher...")
        
        try:
            # Send a small test command
            cmd_vel = Twist()
            cmd_vel.linear.x = 0.1
            
            for i in range(5):
                self.cmd_vel_publisher.publish(cmd_vel)
                time.sleep(0.1)
            
            # Stop
            cmd_vel = Twist()
            self.cmd_vel_publisher.publish(cmd_vel)
            
            self.get_logger().info("✓ Velocity publisher working correctly")
            return True
            
        except Exception as e:
            self.get_logger().error(f"✗ Velocity publisher failed: {e}")
            return False
    
    def test_vision_subscriber(self, duration=10.0):
        """Test vision system"""
        self.get_logger().info(f"Testing vision subscriber for {duration} seconds...")
        
        detection_count = 0
        start_time = time.time()
        
        while (time.time() - start_time) < duration:
            rclpy.spin_once(self.vision_subscriber, timeout_sec=0.1)
            
            if self.vision_subscriber.is_gate_detected():
                detection_count += 1
                gate_info = self.vision_subscriber.get_gate_info()
                self.get_logger().info(
                    f"Detection #{detection_count}: confidence={gate_info['confidence']:.2f}, "
                    f"center=({gate_info['center_x']:.3f}, {gate_info['center_y']:.3f})"
                )
            
            time.sleep(0.1)
        
        if detection_count > 0:
            self.get_logger().info(f"✓ Vision system working - {detection_count} detections")
            return True
        else:
            self.get_logger().warning("✗ No gate detections (may be normal if no gate visible)")
            return False
    
    def run_all_tests(self):
        """Run all system tests"""
        self.get_logger().info("Starting system tests...")
        
        results = {
            'mode_service': self.test_mode_service(),
            'velocity_publisher': self.test_velocity_publisher(),
            'vision_subscriber': self.test_vision_subscriber()
        }
        
        # Summary
        passed = sum(results.values())
        total = len(results)
        
        self.get_logger().info(f"\n=== Test Results ===")
        for test, result in results.items():
            status = "PASS" if result else "FAIL" 
            self.get_logger().info(f"{test}: {status}")
        
        self.get_logger().info(f"Overall: {passed}/{total} tests passed")
        
        return passed == total


def main(args=None):
    rclpy.init(args=args)
    
    tester = SystemTester()
    
    try:
        success = tester.run_all_tests()
        if success:
            tester.get_logger().info("All tests passed! System ready for autonomous operation.")
        else:
            tester.get_logger().warning("Some tests failed. Check system configuration.")
            
    except KeyboardInterrupt:
        tester.get_logger().info("Tests interrupted by user")
    finally:
        tester.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()