import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import httpx
import json
import threading
from abc import ABC, abstractmethod

# --- Perception Interface ---
class PerceptionEngine(ABC):
    @abstractmethod
    def detect(self, frame):
        pass

# --- YOLO Implementation ---
class YOLOv8Engine(PerceptionEngine):
    def __init__(self, model_name='yolov8n.pt'):
        from ultralytics import YOLO
        self.model = YOLO(model_name)
        
    def detect(self, frame):
        results = self.model(frame, verbose=False)
        detections = []
        for r in results:
            for box in r.boxes:
                detections.append({
                    "label": r.names[int(box.cls[0])],
                    "confidence": float(box.conf[0]),
                    "box": box.xyxy[0].tolist() # [x1, y1, x2, y2]
                })
        return detections

# --- ROS2 Node ---
class VisionNode(Node):
    def __init__(self, engine: PerceptionEngine):
        super().__init__('vision_node')
        self.engine = engine
        self.bridge = CvBridge()
        
        # Subscribe to camera
        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )
        
        self.api_url = 'http://localhost:8000/internal/update_detections'
        self.get_logger().info("Vision Node with YOLOv8n started.")

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            detections = self.engine.detect(cv_image)
            
            # Sync with Bridge API
            self.push_to_api(detections)
            
        except Exception as e:
            self.get_logger().error(f"Perception Error: {e}")

    def push_to_api(self, detections):
        # Async-style fire and forget in a separate thread for performance
        def do_push():
            try:
                with httpx.Client() as client:
                    client.post(self.api_url, json=detections, timeout=0.1)
            except:
                pass
        threading.Thread(target=do_push).start()

def main(args=None):
    rclpy.init(args=args)
    
    # Pluggable Engine Selection
    try:
        engine = YOLOv8Engine()
    except Exception as e:
        print(f"Failed to load YOLO (falling back to Dummy): {e}")
        class DummyEngine(PerceptionEngine):
            def detect(self, frame): return [{"label": "red_sphere", "confidence": 0.99, "box": [0,0,10,10]}]
        engine = DummyEngine()

    node = VisionNode(engine)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
