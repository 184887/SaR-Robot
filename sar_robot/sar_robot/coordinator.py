import rclpy
from rclpy.node import Node

from sar_robot_interface.msg import KnownMarkers, MarkerFound, RobotState


class Coordinator(Node):
    """Global node: holder oversikt over godkjente markører og robotenes status."""

    def __init__(self):
        """Setter opp abonnementer, publisher og en timer som sender /known_markers hvert sekund."""
        super().__init__('coordinator')
        self.known = set()   # ID-er som scoring har godkjent

        self.create_subscription(MarkerFound, '/markers_found', self.clbk_marker_found, 10)
        self.create_subscription(RobotState, '/robot_states', self.clbk_robot_state, 10)
        self.known_pub = self.create_publisher(KnownMarkers, '/known_markers', 10)
        self.create_timer(1.0, self.publish_known)

        self.get_logger().info('coordinator startet')

    def clbk_marker_found(self, msg):
        """Logger en rapport fra en robot og lagrer markøren hvis scoring godkjente den."""
        self.get_logger().info(
            f'{msg.robot_id} rapporterte markør {msg.marker_id}, godkjent: {msg.accepted}')
        if msg.accepted:
            self.known.add(msg.marker_id)

    def clbk_robot_state(self, msg):
        """Logger hvor roboten er og hva den gjør."""
        self.get_logger().info(
            f'{msg.robot_id}: {msg.state} ({msg.x:.2f}, {msg.y:.2f})')

    def publish_known(self):
        """Sender listen over godkjente markører til alle robotene."""
        msg = KnownMarkers()
        msg.marker_ids = sorted(self.known)
        self.known_pub.publish(msg)


def main(args=None):
    """Starter coordinator-noden."""
    rclpy.init(args=args)
    node = Coordinator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()