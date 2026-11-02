import math

class PathFollower:
    """Følger en liste med punkter (x, y) i map. Uten ROS: tar inn posisjon, gir ut fart (v, w)"""

    def __init__(self, tolerance=0.2, v_max=0.15, Kp=1.0):
        self.tolerance = tolerance   # hvor nær et punkt vi må være for å regne det som nådd
        self.v_max = v_max
        self.Kp = Kp
        self.points = []

    def set_path(self, points):
        self.points = list(points)

    def done(self):
        return not self.points

    def step(self, x, y, theta):
        """Fart mot neste punkt. Hopper over punkter vi allerede er ved"""
        while self.points and math.hypot(self.points[0][0] - x, self.points[0][1] - y) < self.tolerance:
            self.points.pop(0)
        if not self.points:
            return 0.0, 0.0

        gx, gy = self.points[0]
        err = math.atan2(gy - y, gx - x) - theta
        err = math.atan2(math.sin(err), math.cos(err))   # hold vinkelen mellom -pi og pi

        w = max(-0.5, min(0.5, self.Kp * err))
        v = 0.0 if abs(err) > 0.5 else self.v_max   # snu på stedet hvis vi peker feil vei
        return v, w