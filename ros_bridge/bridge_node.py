import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import httpx
import asyncio
import threading
import math

class HermesRosBridgeNode(Node):
    def __init__(self):
        super().__init__('hermes_bridge_node')
        
        # --- Parameters (Hard Safety) ---
        self.declare_parameter('max_linear_speed', 0.5)
        self.declare_parameter('max_angular_speed', 1.0)
        self.declare_parameter('geofence_box', 10.0)  # ±10m
        self.declare_parameter('bridge_api_url', 'http://localhost:8000')

        # --- Publishers & Subscribers ---
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        
        # --- Internal State ---
        self.current_pose = {"x": 0.0, "y": 0.0, "theta": 0.0}
        self.api_url = self.get_parameter('bridge_api_url').get_parameter_value().string_value
        
        # Start the background sync thread
        self.sync_thread = threading.Thread(target=self.sync_loop, daemon=True)
        self.sync_thread.start()
        
        self.get_logger().info("Hermes-ROS Bridge Node Started.")

    def odom_callback(self, msg):
        """Update local pose from Odometry."""
        pos = msg.pose.pose.position
        ori = msg.pose.pose.orientation
        
        # Simplistic Quaternion to Euler (Yaw only for 2D TB3)
        siny_cosp = 2 * (ori.w * ori.z + ori.x * ori.y)
        cosy_cosp = 1 - 2 * (ori.y * ori.y + ori.z * ori.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        
        self.current_pose = {
            "x": pos.x,
            "y": pos.y,
            "theta": yaw
        }
        
    def sync_loop(self):
        """Periodically push Pose to the Execution Bridge."""
        client = httpx.Client()
        while rclpy.ok():
            try:
                client.post(f"{self.api_url}/internal/update_pose", json=self.current_pose, timeout=0.1)
            except Exception:
                pass
            time.sleep(0.1)

    def publish_safe_cmd(self, linear_x, angular_z):
        """Enforce Hard Safety Clamping before publishing."""
        max_v = self.get_parameter('max_linear_speed').value
        max_w = self.get_parameter('max_angular_speed').value
        bounds = self.get_parameter('geofence_box').value
        
        # 1. Velocity Clamping
        safe_v = max(-max_v, min(max_v, linear_x))
        safe_w = max(-max_w, min(max_w, angular_z))
        
        # 2. Hard Geofence check
        if abs(self.current_pose["x"]) > bounds or abs(self.current_pose["y"]) > bounds:
            self.get_logger().error("GEOFENCE BREACH! Hard Stop Engaged.")
            safe_v = 0.0
            safe_w = 0.0
            
        msg = Twist()
        msg.linear.x = safe_v
        msg.angular.z = safe_w
        self.cmd_vel_pub.publish(msg)

def main(args=None):
    import time
    rclpy.init(args=args)
    node = HermesRosBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
