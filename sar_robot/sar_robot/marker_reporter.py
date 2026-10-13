import rclpy
from rclpy.node import Node
from rclpy.time import Time

from geometry_msgs.msg import PointStamped
from ros2_aruco_interfaces.msg import ArucoMarkers
from sar_robot_interface.msg import KnownMarkers, MarkerFound
from scoring_interfaces.srv import SetMarkerPosition
from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
import tf2_geometry_msgs


class MarkerReporter(Node):

    def __init__(self):
        super().__init__('marker_reporter')
        self.robot_id = self.get_namespace().strip('/')   # 'tb3_0' eller 'tb3_1'
        self.camera_frame = self.robot_id + '/camera_rgb_optical_frame'

        self.known = set()     # godkjent av noen (fra coordinator)
        self.pending = set()   # venter på svar fra scoring
        self.accepted = 0
        self.rejected = 0

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # 'aruco_markers' uten / foran, så namespace legges på automatisk
        self.create_subscription(ArucoMarkers, 'aruco_markers', self.clbk_markers, 10)
        self.create_subscription(KnownMarkers, '/known_markers', self.clbk_known, 10)
        self.found_pub = self.create_publisher(MarkerFound, '/markers_found', 10)
        self.client = self.create_client(SetMarkerPosition, '/set_marker_position')

        self.get_logger().info(f'marker_reporter startet for {self.robot_id}')

    def clbk_known(self, msg):
        self.known = set(msg.marker_ids)

    def clbk_markers(self, msg):
        # Kalles hver gang kameraet ser markører. Posisjonen regnes om HER,
        # ikke i en timer, så vi sender aldri en gammel posisjon.
        for marker_id, pose in zip(msg.marker_ids, msg.poses):
            marker_id = int(marker_id)
            if marker_id in self.known or marker_id in self.pending:
                continue

            try:
                tf = self.tf_buffer.lookup_transform('map', self.camera_frame, Time())
            except TransformException:
                return

            p = PointStamped()
            p.point = pose.position
            p_map = tf2_geometry_msgs.do_transform_point(p, tf).point
            self.report(marker_id, p_map)

    def report(self, marker_id, position):
        if not self.client.service_is_ready():
            self.get_logger().warn('Scoring svarer ikke. Kjører scoring?')
            return

        request = SetMarkerPosition.Request()
        request.marker_id = marker_id
        request.marker_position = position

        self.pending.add(marker_id)
        future = self.client.call_async(request)
        future.add_done_callback(lambda f: self.on_response(f, marker_id, position))

    def on_response(self, future, marker_id, position):
        self.pending.discard(marker_id)
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
    rclpy.init(args=args)
    node = MarkerReporter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()