import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time

from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import OccupancyGrid, Path
from sensor_msgs.msg import LaserScan
from std_srvs.srv import SetBool
from sar_robot_interface.msg import RobotState
from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener

from sar_robot.map_grid import MapGrid
from sar_robot.map_node import MAP_QOS
from sar_robot.path_follower import PathFollower
from sar_robot.planner import Planner
from sar_robot.wall_follower import WallFollower


class RobotController(Node):
    """
    Én per robot. Kjører mellom dekningspunktene fra coverage_node (FOLLOW_PATH),
    med A* mellom hvert punkt. Følger veggen hvis ruta er blokkert, eller når den er ferdig.
    """

    def __init__(self):
        super().__init__('robot_controller')

        self.declare_parameter('follow_left', False)  # velg side: False = høyre vegg, True = venstre
        self.declare_parameter('sving_mot_timeout', 7.0)
        self.declare_parameter('cell_factor', 5)      # 5 x 1 cm = 5 cm-ruter, som coverage_node
        self.declare_parameter('blocked_dist', 0.3)   # noe nærmere enn dette foran = ruta er blokkert
        self.declare_parameter('blocked_time', 3.0)   # så lenge vi følger veggen før vi prøver ruta igjen
        self.declare_parameter('max_blocked', 2)      # ganger et punkt kan blokkere før vi hopper over det
        self.declare_parameter('goal_tolerance', 1.0)  # så nær målet vi stopper (scoring krever 2 m)
        self.follower = WallFollower(self.get_parameter('follow_left').value,
                                     self.get_parameter('sving_mot_timeout').value)
        self.factor = self.get_parameter('cell_factor').value
        self.blocked_dist = self.get_parameter('blocked_dist').value
        self.blocked_time = self.get_parameter('blocked_time').value
        self.max_blocked = self.get_parameter('max_blocked').value
        self.goal_tolerance = self.get_parameter('goal_tolerance').value

        self.path = PathFollower()
        self.planner = None
        self.targets = []        # dekningspunkter vi ikke har vært ved ennå
        self.target = None       # punktet vi kjører mot nå
        self.blocked_count = 0
        self.blocked_until = 0.0
        self.mode = None
        self.goal = None         # mål fra coordinatoren (x, y), går foran dekningsruta

        self.robot_id = self.get_namespace().strip('/')   # 'tb3_0' eller 'tb3_1'
        self.map_frame = 'map'
        self.robot_frame = self.robot_id + '/base_footprint'
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.create_subscription(LaserScan, 'scan', self.clbk_lidar, qos_profile_sensor_data)
        self.create_subscription(OccupancyGrid, '/inflated_map', self.clbk_map, MAP_QOS)
        # uten / foran, så tb3_0 får /tb3_0/coverage_path
        self.create_subscription(Path, 'coverage_path', self.clbk_path, MAP_QOS)
        self.create_subscription(PoseStamped, 'goal', self.clbk_goal, 10)   # /tb3_X/goal
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.create_service(SetBool, 'wallfollower_switch', self.clbk_switch)
        # '/robot_states' med / foran, så begge robotene publiserer på samme globale topic
        self.pub_state = self.create_publisher(RobotState, '/robot_states', 10)

        self.active = True
        self.create_timer(0.1, self.timer_callback)

        side = 'venstre' if self.follower.follow_left else 'høyre'
        self.get_logger().info(f'robot_controller startet, følger {side} vegg til ruta kommer')

    def clbk_switch(self, request, response):
        self.active = request.data

        if self.active:
            self.follower.reset()
            if self.goal is not None:   # på igjen etter målet: fortsett dekningsruta
                self.targets = [t for t in self.targets if t != self.goal]
                if self.target == self.goal:   # stoppet før vi var helt framme
                    self.target = None
                    self.path.set_path([])
                self.goal = None
        else:
            self.pub.publish(Twist())

        response.success = True
        return response

    def clbk_lidar(self, msg):
        self.follower.set_scan(msg.ranges, msg.range_min, msg.range_max)

    def clbk_map(self, msg):
        self.planner = Planner(MapGrid.from_msg(msg).downsample(self.factor))

    def clbk_path(self, msg):
        self.targets = [(p.pose.position.x, p.pose.position.y) for p in msg.poses]
        self.target = None
        self.path.set_path([])
        self.get_logger().info(f'Fikk {len(self.targets)} dekningspunkter')

    def clbk_goal(self, msg):
        """Mål fra coordinatoren. Kjøres før resten av dekningsruta, som fortsetter etterpå"""
        self.goal = (msg.pose.position.x, msg.pose.position.y)
        if self.target is not None:
            self.targets.insert(0, self.target)   # punktet vi var på vei til, tas etter målet
        self.targets.insert(0, self.goal)
        self.target = None
        self.path.set_path([])
        self.blocked_count = 0
        self.blocked_until = 0.0
        self.get_logger().info(f'Fikk mål ({self.goal[0]:.2f}, {self.goal[1]:.2f})')

    def robot_pose(self):
        """(x, y, theta) i map, eller None hvis transformen ikke finnes ennå"""
        try:
            t = self.tf_buffer.lookup_transform(self.map_frame, self.robot_frame, Time())
        except TransformException as e:
            self.get_logger().debug(f'Ingen transform ennå: {e}')
            return None

        q = t.transform.rotation
        theta = math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                           1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        return t.transform.translation.x, t.transform.translation.y, theta

    def publish_robot_state(self, pose):
        msg = RobotState()
        msg.robot_id = self.robot_id
        msg.x, msg.y, msg.theta = pose
        msg.state = self.mode or self.follower.state.name
        self.pub_state.publish(msg)

    def next_target(self, pose):
        """Planlegger til neste dekningspunkt. False hvis det ikke er flere"""
        while self.targets:
            self.target = self.targets.pop(0)
            self.blocked_count = 0
            points = self.planner.plan(pose[:2], self.target)
            if points:
                self.path.set_path(points)
                return True
            self.get_logger().warn(f'Fant ingen rute til {self.target}, hopper over')
        self.target = None
        return False

    def use_path(self, pose, naa):
        """True hvis vi skal følge ruta nå, False gir veggfølging"""
        if pose is None or self.planner is None or naa < self.blocked_until:
            return False

        if not self.path.done() and self.follower.regions['front'] < self.blocked_dist:
            self.blocked_count += 1
            self.blocked_until = naa + self.blocked_time
            self.path.set_path([])
            if self.blocked_count < self.max_blocked or self.target == self.goal:
                self.targets.insert(0, self.target)   # prøv samme punkt igjen etterpå
                self.get_logger().warn('Ruta er blokkert, følger veggen en stund')
            else:
                self.get_logger().warn(f'{self.target} er blokkert for ofte, hopper over')
            return False

        if self.path.done() and not self.next_target(pose):
            return False
        return True

    def timer_callback(self):
        pose = self.robot_pose()
        if pose is not None:
            self.publish_robot_state(pose)   # også når roboten er av, så coordinatoren vet hvor den er
        if not self.active:
            return

        naa = self.get_clock().now().nanoseconds / 1e9
        forrige = self.mode or self.follower.state.name
        if self.goal is not None and pose is not None and \
                math.hypot(pose[0] - self.goal[0], pose[1] - self.goal[1]) < self.goal_tolerance:
            self.mode = 'AT_GOAL'           # står og venter til coordinatoren skrur oss på igjen
            self.path.set_path([])
            v, w = 0.0, 0.0
        elif self.use_path(pose, naa):
            self.mode = 'FOLLOW_PATH'
            v, w = self.path.step(*pose)
        else:
            self.mode = None
            v, w = self.follower.step(naa)
        naa_state = self.mode or self.follower.state.name
        if naa_state != forrige:
            self.get_logger().info(f'Tilstand: {naa_state}')

        cmd = Twist()
        cmd.linear.x = v
        cmd.angular.z = w
        self.pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = RobotController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
