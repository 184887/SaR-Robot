import rclpy
from rclpy.node import Node

from sar_robot_interface.msg import KnownMarkers, MarkerFound, RobotState


class Coordinator(Node):

    def __init__(self):
        super().__init__('coordinator')
        self.known = set()   # ID-er som scoring har godkjent

        self.create_subscription(MarkerFound, '/markers_found', self.clbk_marker_found, 10)
        self.create_subscription(RobotState, '/robot_states', self.clbk_robot_state, 10)
        self.known_pub = self.create_publisher(KnownMarkers, '/known_markers', 10)
        self.create_timer(1.0, self.publish_known)

        self.get_logger().info('coordinator startet')

    def clbk_marker_found(self, msg):
        self.get_logger().info(
            f'{msg.robot_id} rapporterte markør {msg.marker_id}, godkjent: {msg.accepted}')
        if msg.accepted:
            self.known.add(msg.marker_id)

    def clbk_robot_state(self, msg):
        self.get_logger().info(
            f'{msg.robot_id}: {msg.state} ({msg.x:.2f}, {msg.y:.2f})')

    def publish_known(self):
        msg = KnownMarkers()
        msg.marker_ids = sorted(self.known)
        self.known_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = Coordinator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()