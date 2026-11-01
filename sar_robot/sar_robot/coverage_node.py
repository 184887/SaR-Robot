import rclpy
from rclpy.node import Node
from rclpy.time import Time
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import OccupancyGrid, Path
from tf2_ros import Buffer, TransformListener, TransformException

from sar_robot.coverage import coverage_points, split_route
from sar_robot.map_grid import MapGrid
from sar_robot.map_node import MAP_QOS

ROBOTS = ['tb3_0', 'tb3_1']


class CoverageNode(Node):
    """Venter på /inflated_map og posisjonen til robotene. Kaller så over funksjonene og publiserer rutene"""
    
    def __init__(self):
        super().__init__('coverage_node')

        self.declare_parameter('spacing', 1.5)     # meter mellom punktene
        self.declare_parameter('cell_factor', 5)   # 5 x 1 cm = 5 cm-ruter
        self.spacing = self.get_parameter('spacing').value
        self.factor = self.get_parameter('cell_factor').value
        self.map = None

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.create_subscription(OccupancyGrid, '/inflated_map', self.clbk_map, MAP_QOS)
        # transient local: en node som starter senere får likevel rutene
        self.pubs = {r: self.create_publisher(Path, f'/{r}/coverage_path', MAP_QOS) for r in ROBOTS}
        self.timer = self.create_timer(1.0, self.try_plan)

    def clbk_map(self, msg):
        self.map = MapGrid.from_msg(msg).downsample(self.factor)

    def robot_position(self, robot):
        t = self.tf_buffer.lookup_transform('map', f'{robot}/base_footprint', Time())
        return t.transform.translation.x, t.transform.translation.y

    def try_plan(self):
        """Venter til kart og robotposisjoner finnes, regner ut rutene én gang"""
        if self.map is None:
            return
        try:
            starts = [self.robot_position(r) for r in ROBOTS]
        except TransformException:
            return

        points = coverage_points(self.map, starts[0], self.spacing)
        routes = split_route(self.map, points, starts)
        for robot, route in zip(ROBOTS, routes):
            self.pubs[robot].publish(self.to_path(route))
            self.get_logger().info(f'{robot}: {len(route)} dekningspunkter')
        self.timer.cancel()

    @staticmethod
    def to_path(points):
        path = Path()
        path.header.frame_id = 'map'
        for x, y in points:
            pose = PoseStamped()
            pose.header.frame_id = 'map'
            pose.pose.position.x = float(x)
            pose.pose.position.y = float(y)
            pose.pose.orientation.w = 1.0
            path.poses.append(pose)
        return path


def main(args=None):
    rclpy.init(args=args)
    node = CoverageNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()