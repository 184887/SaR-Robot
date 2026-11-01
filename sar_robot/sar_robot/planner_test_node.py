import rclpy
from rclpy.node import Node
from rclpy.time import Time
from geometry_msgs.msg import PointStamped, PoseStamped
from nav_msgs.msg import OccupancyGrid, Path
from tf2_ros import Buffer, TransformListener, TransformException

from sar_robot.map_grid import MapGrid
from sar_robot.map_node import MAP_QOS
from sar_robot.planner import Planner


class PlannerTestNode(Node):
    def __init__(self):
        super().__init__('planner_test_node')

        self.declare_parameter('robot', 'tb3_0')
        self.declare_parameter('cell_factor', 5)  # 5 x 1 cm = 5 cm-ruter
        self.robot = self.get_parameter('robot').value
        self.factor = self.get_parameter('cell_factor').value
        self.planner = None

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.create_subscription(OccupancyGrid, '/inflated_map', self.clbk_map, MAP_QOS)
        self.create_subscription(PointStamped, '/clicked_point', self.clbk_point, 10)
        self.pub = self.create_publisher(Path, '/planned_path', 10)

    def clbk_map(self, msg):
        self.planner = Planner(MapGrid.from_msg(msg).downsample(self.factor))
        self.get_logger().info('Kart mottatt, klikk et punkt i RViz')

    def clbk_point(self, msg):
        if self.planner is None:
            self.get_logger().warn('Har ikke fått /inflated_map ennå')
            return
        try:
            t = self.tf_buffer.lookup_transform('map', f'{self.robot}/base_footprint', Time())
        except TransformException as e:
            self.get_logger().warn(f'Fant ikke posisjonen til {self.robot}: {e}')
            return

        start = (t.transform.translation.x, t.transform.translation.y)
        points = self.planner.plan(start, (msg.point.x, msg.point.y))
        if not points:
            self.get_logger().warn('Fant ingen rute dit')
            return

        path = Path()
        path.header.frame_id = 'map'
        for x, y in points:
            pose = PoseStamped()
            pose.header.frame_id = 'map'
            pose.pose.position.x = x
            pose.pose.position.y = y
            pose.pose.orientation.w = 1.0
            path.poses.append(pose)
        self.pub.publish(path)
        self.get_logger().info(f'Rute med {len(points)} punkter publisert')


def main(args=None):
    rclpy.init(args=args)
    node = PlannerTestNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()