import math
import time

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Pose
from std_msgs.msg import Int64
from sar_robot_interface.msg import KnownMarkers, MarkerFound
from scoring_interfaces.srv import SetMarkerPosition


class MarkerReporter(Node):
    """Én per robot: rapporterer nye markører til scoring, fra marker_pose sine topics."""

    def __init__(self):
        """Setter opp abonnementer, publisher og klienten til scoring."""
        super().__init__('marker_reporter')
        self.robot_id = self.get_namespace().strip('/')   # 'tb3_0' eller 'tb3_1'

        self.known = set()     # godkjent av noen (fra coordinator)
        self.pending = set()   # venter på svar fra scoring
        self.accepted = 0
        self.rejected = 0
        self.last_try = {}     # marker_id -> når vi sist sendte den

        self.last_pose = None  # siste posisjon fra marker_map_pose
        self.start_id = None
        self.start_pos = None
        self.count = 0

        # marker_pose  publiserer disse i kart-koordinater
        self.create_subscription(Pose, 'marker_map_pose', self.clbk_pose, 10)
        self.create_subscription(Int64, 'marker_id', self.clbk_id, 10)
        self.create_subscription(KnownMarkers, '/known_markers', self.clbk_known, 10)
        self.found_pub = self.create_publisher(MarkerFound, '/markers_found', 10)
        self.client = self.create_client(SetMarkerPosition, '/set_marker_position')

        self.get_logger().info(f'marker_reporter startet for {self.robot_id}')

    def clbk_known(self, msg):
        """Legger til markører som coordinatoren sier er godkjent ."""
        self.known |= set(msg.marker_ids)

    def clbk_pose(self, msg):
        """Husker siste posisjon. marker_pose sender posisjonen rett før ID-en."""
        self.last_pose = msg.position

    def clbk_id(self, msg):
        """Rapporterer markøren hvis den har stått stille i kartet i 1 sekund."""
        marker_id = int(msg.data)
        p = self.last_pose
        if p is None:
            return

        # Ny markør, eller har den flyttet seg over 5 cm? Da starter vi tellingen på nytt.
        if marker_id != self.start_id or math.hypot(p.x - self.start_pos.x, p.y - self.start_pos.y) > 0.05:
            self.start_id = marker_id
            self.start_pos = p
            self.count = 0
            return

        self.count += 1
        if self.count < 10:   # 10 meldinger = 1 sekund
            return

        if marker_id in self.known or marker_id in self.pending:
            return
        if time.time() - self.last_try.get(marker_id, 0) < 5.0:
            return
        self.report(marker_id, p)

    def report(self, marker_id, position):
        """Sender markøren og posisjonen til scoring-tjenesten."""
        if not self.client.service_is_ready():
            self.get_logger().warn('Scoring svarer ikke. Kjører scoring?')
            return

        request = SetMarkerPosition.Request()
        request.marker_id = marker_id
        request.marker_position = position

        self.last_try[marker_id] = time.time()
        self.pending.add(marker_id)
        future = self.client.call_async(request)
        future.add_done_callback(lambda f: self.on_response(f, marker_id, position))

    def on_response(self, future, marker_id, position):
        """Tar imot svaret fra scoring, teller opp og publiserer MarkerFound."""
        self.pending.discard(marker_id)
        if future.result() is None:
            self.get_logger().warn(f'Scoring svarte ikke for markør {marker_id}')
            return
        accepted = future.result().accepted

        if accepted:
            self.accepted += 1
            self.known.add(marker_id)
        else:
            self.rejected += 1
        self.get_logger().info(
            f'Markør {marker_id} på ({position.x:.2f}, {position.y:.2f}) '
            f'godkjent: {accepted}. Totalt godkjent {self.accepted}, avvist {self.rejected}')

        msg = MarkerFound()
        msg.robot_id = self.robot_id
        msg.marker_id = marker_id
        msg.position = position
        msg.accepted = accepted
        self.found_pub.publish(msg)


def main(args=None):
    """Starter marker_reporter-noden."""
    rclpy.init(args=args)
    node = MarkerReporter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
