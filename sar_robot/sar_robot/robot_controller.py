import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time

from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from std_srvs.srv import SetBool
from sar_robot_interface.msg import RobotState
from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener

from sar_robot.wall_follower import WallFollower


class RobotController(Node):
    """Én per robot: kobler WallFollower til scan, cmd_vel og /robot_states"""

    def __init__(self):
        super().__init__('robot_controller')

        self.declare_parameter('follow_left', False)  # velg side: False = høyre vegg, True = venstre
        self.declare_parameter('sving_mot_timeout', 7.0)
        self.follower = WallFollower(self.get_parameter('follow_left').value,
                                     self.get_parameter('sving_mot_timeout').value)

        self.robot_id = self.get_namespace().strip('/')   # 'tb3_0' eller 'tb3_1'
        self.map_frame = 'map'
        self.robot_frame = self.robot_id + '/base_footprint'
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.create_subscription(LaserScan, 'scan', self.clbk_lidar, qos_profile_sensor_data)
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.create_service(SetBool, 'wallfollower_switch', self.clbk_switch)
        # '/robot_states' med / foran, så begge robotene publiserer på samme globale topic
        self.pub_state = self.create_publisher(RobotState, '/robot_states', 10)

        self.active = True
        self.create_timer(0.1, self.timer_callback)

        side = 'venstre' if self.follower.follow_left else 'høyre'
        self.get_logger().info(f'robot_controller startet, følger {side} vegg')

    def clbk_switch(self, request, response):
        self.active = request.data

        if self.active:
            self.follower.reset()
        else:
            self.pub.publish(Twist())

        response.success = True
        return response

    def clbk_lidar(self, msg):
        self.follower.set_scan(msg.ranges, msg.range_min, msg.range_max)

    def publish_robot_state(self):
        try:
            t = self.tf_buffer.lookup_transform(self.map_frame, self.robot_frame, Time())
        except TransformException as e:
            self.get_logger().debug(f'Ingen transform ennå: {e}')
            return

        q = t.transform.rotation
        theta = math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                           1.0 - 2.0 * (q.y * q.y + q.z * q.z))

        msg = RobotState()
        msg.robot_id = self.robot_id
        msg.x = t.transform.translation.x
        msg.y = t.transform.translation.y
        msg.theta = theta
        msg.state = self.follower.state.name
        self.pub_state.publish(msg)

    def timer_callback(self):
        self.publish_robot_state()   # også når roboten er av, så coordinatoren vet hvor den er
        if not self.active:
            return

        forrige = self.follower.state
        naa = self.get_clock().now().nanoseconds / 1e9
        v, w = self.follower.step(naa)
        if self.follower.state != forrige:
            self.get_logger().info(f'Tilstand: {self.follower.state.name}')

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
