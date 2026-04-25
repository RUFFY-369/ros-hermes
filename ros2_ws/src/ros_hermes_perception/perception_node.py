import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CompressedImage
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import json
from ultralytics import YOLO

class PerceptionEngine(Node):
    """
    Observation Normalizer (O)
    Consumes camera data and publishes structured YOLOv8 object detections.
    """
    def __init__(self):
        super().__init__('ros_hermes_perception')
        self.bridge = CvBridge()
        
        # Initialize YOLOv8 (nano for speed)
        self.get_logger().info("Loading YOLOv8n model...")
        self.model = YOLO('yolov8n.pt')
        
        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10)
            
        self.publisher = self.create_publisher(String, '/ros_hermes/observations', 10)
        self.image_pub = self.create_publisher(Image, '/ros_hermes/annotated_image', 10)
        self.get_logger().info("Perception Engine Initialized")

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            results = self.model(cv_image, verbose=False)
            
            observations = {
                "timestamp": self.get_clock().now().to_msg().sec,
                "objects": []
            }
            
            img_h, img_w, _ = cv_image.shape
            
            for result in results:
                # Annotate image for the dashboard
                annotated_frame = result.plot()
                
                for box in result.boxes:
                    x_raw = float(box.xywh[0][0])
                    y_raw = float(box.xywh[0][1])
                    
                    obs = {
                        "label": self.model.names[int(box.cls[0])],
                        "confidence": float(box.conf[0]),
                        "x": (x_raw - (img_w / 2)) / (img_w / 2),
                        "y": (y_raw - (img_h / 2)) / (img_h / 2),
                        "size": float(box.xywh[0][2] * box.xywh[0][3]) / (img_w * img_h)
                    }
                    observations["objects"].append(obs)
            
            # Publish Observations
            self.publisher.publish(String(data=json.dumps(observations)))
            
            # Publish Annotated Image
            ros_image = self.bridge.cv2_to_imgmsg(annotated_frame, "bgr8")
            self.image_pub.publish(ros_image)
            
        except Exception as e:
            self.get_logger().error(f"Perception Error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = PerceptionEngine()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
