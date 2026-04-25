import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json

class AffordanceDiscovery(Node):
    """
    Affordance Engine (A)
    Instrospects the ROS 2 graph to generate a Capability Manifest for the Hermes Agent.
    """
    def __init__(self):
        super().__init__('ros_hermes_discovery')
        self.declare_parameter('scan_interval', 5.0)
        
        self.publisher = self.create_publisher(String, '/ros_hermes/affordance_manifest', 10)
        self.timer = self.create_timer(self.get_parameter('scan_interval').value, self.scan_graph)
        
        self.get_logger().info("Affordance Discovery Node Initialized")

    def scan_graph(self):
        manifest = {
            "topics": [],
            "services": [],
            "actions": []
        }
        
        # Discover Topics
        for name, types in self.get_topic_names_and_types():
            if not name.startswith(('/rosout', '/parameter_events')):
                manifest["topics"].append({"path": name, "type": types[0]})
        
        # Discover Services
        for name, types in self.get_service_names_and_types():
            if not name.startswith(('/ros_hermes/', '/rosout')):
                manifest["services"].append({"path": name, "type": types[0]})

        # Heuristic for Actions
        # In ROS2, actions create several topics like /name/_action/feedback
        for name, types in self.get_topic_names_and_types():
            if name.endswith('/_action/feedback'):
                action_base = name.replace('/_action/feedback', '')
                manifest["actions"].append({"path": action_base, "type": types[0].replace('_FeedbackMessage', '')})

        self.publisher.publish(String(data=json.dumps(manifest)))
        self.get_logger().info(f"Published manifest: {len(manifest['topics'])} topics found")

def main(args=None):
    rclpy.init(args=args)
    node = AffordanceDiscovery()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
