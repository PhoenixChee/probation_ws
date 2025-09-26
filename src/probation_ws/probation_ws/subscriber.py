import rclpy
from rclpy.node import Node
import math

from vision_msgs.msg import BoundingBoxArray, BoundingBox


class BoundingBoxSubscriber(Node):

    def __init__(self):
        super().__init__('bounding_box_subscriber')
        self.subscription = self.create_subscription(
            BoundingBoxArray,
            '/main_camera/detection/bounding_boxes',
            self.listener_callback,
            10)
        self.subscription
        
        # Gate detection variables
        self.gate_detected = False
        self.gate_center_x = 0.5  # Center of image frame
        self.gate_center_y = 0.5
        self.gate_width = 0.0
        self.gate_height = 0.0
        self.detection_confidence = 0.0
        
        # Detection thresholds
        self.min_confidence = 0.5
        self.center_tolerance = 0.1  # How close to center is considered "centered"
        
    def listener_callback(self, msg):
        self.gate_detected = False
        best_confidence = 0.0
        best_gate = None
        
        # Find the gate with highest confidence
        for bbox in msg.bounding_boxes:
            # Assuming gate class_id is known (you may need to adjust this)
            # For now, we'll take the highest confidence detection
            if bbox.probability > best_confidence and bbox.probability > self.min_confidence:
                best_confidence = bbox.probability
                best_gate = bbox
        
        if best_gate:
            self.gate_detected = True
            self.gate_center_x = best_gate.x + best_gate.width / 2.0
            self.gate_center_y = best_gate.y + best_gate.height / 2.0
            self.gate_width = best_gate.width
            self.gate_height = best_gate.height
            self.detection_confidence = best_gate.probability
            
            self.get_logger().info(
                f"Gate detected - Confidence: {self.detection_confidence:.2f}, "
                f"Center: ({self.gate_center_x:.3f}, {self.gate_center_y:.3f}), "
                f"Size: {self.gate_width:.3f}x{self.gate_height:.3f}"
            )
        else:
            self.get_logger().debug("No gate detected")
    
    def is_gate_detected(self):
        return self.gate_detected
    
    def get_gate_info(self):
        return {
            'detected': self.gate_detected,
            'center_x': self.gate_center_x,
            'center_y': self.gate_center_y,
            'width': self.gate_width,
            'height': self.gate_height,
            'confidence': self.detection_confidence
        }
    
    def is_gate_centered(self):
        if not self.gate_detected:
            return False
        
        x_centered = abs(self.gate_center_x - 0.5) < self.center_tolerance
        y_centered = abs(self.gate_center_y - 0.5) < self.center_tolerance
        return x_centered and y_centered
    
    def get_centering_error(self):
        """Returns x, y error from center (negative means go left/up, positive means go right/down)"""
        if not self.gate_detected:
            return 0.0, 0.0
        
        x_error = self.gate_center_x - 0.5
        y_error = self.gate_center_y - 0.5
        return x_error, y_error


def main(args=None):
    rclpy.init(args=args)
    subscriber = BoundingBoxSubscriber()
    rclpy.spin(subscriber)
    subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()