import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from std_srvs.srv import SetBool
from enum import Enum, auto


class State(Enum):
    FINN_VEGG = auto()
    SVING_BORT = auto()
    FOLLOW_WALL = auto()
    SVING_MOT = auto()


class WallFollower(Node):
    def __init__(self):
        super().__init__('wall_follower')

        self.declare_parameter('follow_left', False)# velg side: False = høyre vegg, True = venstre
        self.follow_left = self.get_parameter('follow_left').value
        self.sign = -1 if self.follow_left else 1

        self.create_subscription(LaserScan, 'scan', self.clbk_lidar, qos_profile_sensor_data)
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.create_service(SetBool, 'wallfollower_switch', self.clbk_switch)

        self.regions = {'front': 100.0, 'front_left': 100.0, 'left': 100.0,
                        'back': 100.0, 'right': 100.0, 'front_right': 100.0,
                        'side': 100.0}
        self.active = True
        self.state = State.FINN_VEGG
        self.create_timer(0.1, self.timer_callback)

        side = 'venstre' if self.follow_left else 'høyre'
        self.get_logger().info(f'wall_follower startet, følger {side} vegg')
        self.declare_parameter('sving_mot_timeout', 7.0)
        self.sving_mot_timeout = self.get_parameter('sving_mot_timeout').value
        self.sving_mot_start = None

    def clbk_switch(self, request, response):
        self.active = request.data

        if self.active:
            self.state = State.FINN_VEGG
        else:
            self.pub.publish(Twist())

        response.success = True
        return response

    def clbk_lidar(self, msg):
        r = list(msg.ranges)

        def sone_min(verdier):
            gyldige = [v for v in verdier if msg.range_min < v < msg.range_max]
            return min(gyldige) if gyldige else float('inf')

        self.regions = {
            'front':       sone_min(r[330:360] + r[0:31]),
            'front_left':  sone_min(r[31:61]),
            'left':        sone_min(r[70:110]),
            'back':        sone_min(r[160:200]),
            'right':       sone_min(r[250:291]),
            'front_right': sone_min(r[300:330]),
        }
        self.regions['side'] = self.regions['left'] if self.follow_left else self.regions['right']

    def update_state(self):
        forrige = self.state
        naa = self.get_clock().now()

        if self.regions['front'] < 0.5:
            self.state = State.SVING_BORT
        elif self.regions['side'] < 0.7:
            self.state = State.FOLLOW_WALL
        elif self.state == State.FOLLOW_WALL:
            self.state = State.SVING_MOT
            self.sving_mot_start = naa
        elif self.state == State.SVING_MOT:
            tid = (naa - self.sving_mot_start).nanoseconds / 1e9
            if tid > self.sving_mot_timeout:
                self.state = State.FINN_VEGG
        else:
            self.state = State.FINN_VEGG

        if self.state != forrige:
            self.get_logger().info(f'Tilstand: {self.state.name}')

    def gi_comando(self, side):
        cmd = Twist()
        d_ref = 0.4
        Kp = 0.5
        w = 0.0
        if self.state == State.FINN_VEGG:
            cmd.linear.x = 0.15
        elif self.state == State.SVING_BORT:
            w = 0.5
        elif self.state == State.SVING_MOT:
            cmd.linear.x = 0.15
            w = -0.5
        elif self.state == State.FOLLOW_WALL:
            cmd.linear.x = 0.15
            w = max(-0.5, min(0.5, (d_ref - side) * Kp))

        cmd.angular.z = self.sign * w
        return cmd

    def timer_callback(self):
        if not self.active:
            return
        self.update_state()
        cmd = self.gi_comando(self.regions['side'])
        self.pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = WallFollower()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()