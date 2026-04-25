#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from gazebo_msgs.srv import SpawnEntity
import sys

# Define a simple red sphere SDF
RED_SPHERE_SDF = """
<?xml version='1.0'?>
<sdf version='1.6'>
  <model name='red_sphere'>
    <pose>2 0 0.5 0 0 0</pose>
    <link name='link'>
      <visual name='visual'>
        <geometry>
          <sphere><radius>0.2</radius></sphere>
        </geometry>
        <material>
          <ambient>1 0 0 1</ambient>
          <diffuse>1 0 0 1</diffuse>
        </material>
      </visual>
      <collision name='collision'>
        <geometry>
          <sphere><radius>0.2</radius></sphere>
        </geometry>
      </collision>
    </link>
  </model>
</sdf>
"""

class Spawner(Node):
    def __init__(self, x=2.0, y=0.0):
        super().__init__('sphere_spawner')
        self.client = self.create_client(SpawnEntity, '/spawn_entity')
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for /spawn_entity service...')
        
        request = SpawnEntity.Request()
        request.name = 'red_sphere'
        request.xml = RED_SPHERE_SDF.replace('<pose>2 0', f'<pose>{x} {y}')
        request.initial_pose.position.x = float(x)
        request.initial_pose.position.y = float(y)
        request.initial_pose.position.z = 0.5
        
        self.get_logger().info(f'Spawning red sphere at ({x}, {y})...')
        self.client.call_async(request)

def main():
    rclpy.init()
    x = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
    y = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    node = Spawner(x, y)
    rclpy.spin_once(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
