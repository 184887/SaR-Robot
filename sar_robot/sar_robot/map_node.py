import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from nav_msgs.msg import OccupancyGrid

from sar_robot.map_grid import MapGrid

# Samme QoS som map_server: sene abonnenter får likevel siste kart
MAP_QOS = QoSProfile(
    history=HistoryPolicy.KEEP_LAST,
    depth=5,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)


class MapNode(Node):
    """Tar inn /map, gjør vegger tykkere, publiserer på /inflated_map"""
    def __init__(self):
        super().__init__('map_node')
        """Leser bufferradius, lager publisher på /inflated_map og abonnerer på /map"""

        self.declare_parameter('inflation_radius', 0.25)  # robotradius ca. 0.24 m
        self.radius = self.get_parameter('inflation_radius').value

        self.pub = self.create_publisher(OccupancyGrid, '/inflated_map', MAP_QOS)
        self.create_subscription(OccupancyGrid, '/map', self.clbk_map, MAP_QOS)
        self.get_logger().info(f'map_node startet, buffer {self.radius} m')

    def clbk_map(self, msg):
        """Gjør msg om til 2D, gjør veggene 25cm tykkere, gjør tilbake til melding og publiserer"""
        start = time.time()
        inflated = MapGrid.from_msg(msg).inflate(self.radius)
        self.pub.publish(inflated.to_msg(msg.header))
        self.get_logger().info(f'/inflated_map publisert ({time.time() - start:.1f} s)')


def main(args=None):
    rclpy.init(args=args)
    node = MapNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()