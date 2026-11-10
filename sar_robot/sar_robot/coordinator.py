import math

import rclpy
from rclpy.node import Node

from nav_msgs.msg import Path
from std_srvs.srv import SetBool
from sar_robot_interface.msg import KnownMarkers, MarkerFound, RobotState

from sar_robot.coverage_node import CoverageNode
from sar_robot.map_node import MAP_QOS

ROBOTS = ['tb3_0', 'tb3_1']


class Coordinator(Node):
    """Holder oversikt over godkjente markører og samler robotene ved storbrannen."""

    def __init__(self):
        """Setter opp abonnementer, publishere, klienter og en timer for /known_markers."""
        super().__init__('coordinator')
        self.known = set()      # ID-er som scoring har godkjent
        self.positions = {}     # robot -> siste posisjon (x, y)
        self.fire = None        # posisjonen til storbrannen (x, y) når den er funnet
        self.fire_done = False  # True når begge robotene har vært der
        self.waiting = set()    # roboter som står og venter ved storbrannen

        self.create_subscription(MarkerFound, '/markers_found', self.clbk_marker_found, 10)
        self.create_subscription(RobotState, '/robot_states', self.clbk_robot_state, 10)
        self.known_pub = self.create_publisher(KnownMarkers, '/known_markers', 10)
        self.create_timer(1.0, self.publish_known)

        # robot_controller kjører dit coverage_path sier, og kan skrus av og på
        self.path_pubs = {}
        self.switches = {}
        for robot in ROBOTS:
            self.path_pubs[robot] = self.create_publisher(Path, f'/{robot}/coverage_path', MAP_QOS)
            self.switches[robot] = self.create_client(SetBool, f'/{robot}/wallfollower_switch')

        self.get_logger().info('coordinator startet')

    def clbk_marker_found(self, msg):
        """Logger en rapport, lagrer godkjente markører og sender robotene til storbrannen (markør 4)."""
        self.get_logger().info(
            f'{msg.robot_id} rapporterte markør {msg.marker_id}, godkjent: {msg.accepted}')
        if not msg.accepted:
            return
        self.known.add(msg.marker_id)

        if msg.marker_id == 4 and self.fire is None:
            self.fire = (msg.position.x, msg.position.y)
            self.get_logger().info('STORBRANN funnet, sender begge robotene dit')
            # robot_controller tar bare imot en rute (Path), så vi lager en med ett punkt
            path = CoverageNode.to_path([self.fire])
            for robot in ROBOTS:
                self.path_pubs[robot].publish(path)

    def clbk_robot_state(self, msg):
        """Lagrer posisjonen. Stopper roboten ved storbrannen til begge er der."""
        self.get_logger().info(
            f'{msg.robot_id}: {msg.state} ({msg.x:.2f}, {msg.y:.2f})', throttle_duration_sec=5.0)
        self.positions[msg.robot_id] = (msg.x, msg.y)

        if self.fire is None or self.fire_done:
            return

        # Framme? Stopp og vent på den andre.
        if msg.robot_id not in self.waiting and self.dist_to_fire(msg.robot_id) < 1.5:
            self.get_logger().info(f'{msg.robot_id} venter ved storbrannen')
            self.waiting.add(msg.robot_id)
            self.set_active(msg.robot_id, False)

        # Begge innenfor 2 m gir +300 hos scoring. Da kan de kjøre videre.
        if all(r in self.positions and self.dist_to_fire(r) < 2.0 for r in ROBOTS):
            self.get_logger().info('Begge robotene er ved storbrannen, fortsetter søket')
            self.fire_done = True
            for robot in self.waiting:
                self.set_active(robot, True)

    def publish_known(self):
        """Sender listen over godkjente markører til alle robotene."""
        msg = KnownMarkers()
        msg.marker_ids = sorted(self.known)
        self.known_pub.publish(msg)

    def dist_to_fire(self, robot):
        """Avstand i meter fra roboten til storbrannen."""
        x, y = self.positions[robot]
        return math.hypot(x - self.fire[0], y - self.fire[1])

    def set_active(self, robot, active):
        """Skrur robot_controller av eller på med tjenesten wallfollower_switch."""
        request = SetBool.Request()
        request.data = active
        self.switches[robot].call_async(request)


def main(args=None):
    """Starter coordinator-noden."""
    rclpy.init(args=args)
    node = Coordinator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
