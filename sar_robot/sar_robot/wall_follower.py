from enum import Enum, auto


class State(Enum):
    FINN_VEGG = auto()
    SVING_BORT = auto()
    FOLLOW_WALL = auto()
    SVING_MOT = auto()


class WallFollower:
    """Veggfølger uten ROS: tar inn laseravstander og tid, gir ut fart (v, w)"""

    def __init__(self, follow_left=False, sving_mot_timeout=7.0):
        self.follow_left = follow_left  # velg side: False = høyre vegg, True = venstre
        self.sign = -1 if follow_left else 1
        self.sving_mot_timeout = sving_mot_timeout
        self.sving_mot_start = None

        self.regions = {'front': 100.0, 'front_left': 100.0, 'left': 100.0,
                        'back': 100.0, 'right': 100.0, 'front_right': 100.0,
                        'side': 100.0}
        self.state = State.FINN_VEGG

    def reset(self):
        """Start på nytt med å lete etter en vegg"""
        self.state = State.FINN_VEGG

    def set_scan(self, ranges, range_min, range_max):
        """Deler 360 laseravstander inn i soner og tar minste gyldige verdi i hver"""
        r = list(ranges)

        def sone_min(verdier):
            gyldige = [v for v in verdier if range_min < v < range_max]
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

    def update_state(self, naa):
        """Bytter tilstand ut fra sonene. naa er tiden i sekunder"""
        if self.regions['front'] < 0.5:
            self.state = State.SVING_BORT
        elif self.regions['side'] < 0.7:
            self.state = State.FOLLOW_WALL
        elif self.state == State.FOLLOW_WALL:
            self.state = State.SVING_MOT
            self.sving_mot_start = naa
        elif self.state == State.SVING_MOT:
            if naa - self.sving_mot_start > self.sving_mot_timeout:
                self.state = State.FINN_VEGG
        else:
            self.state = State.FINN_VEGG

    def gi_comando(self):
        """Fart for tilstanden vi er i: (lineær, vinkel)"""
        side = self.regions['side']
        d_ref = 0.4
        Kp = 0.5
        v = 0.0
        w = 0.0
        if self.state == State.FINN_VEGG:
            v = 0.15
        elif self.state == State.SVING_BORT:
            w = 0.5
        elif self.state == State.SVING_MOT:
            v = 0.15
            w = -0.5
        elif self.state == State.FOLLOW_WALL:
            v = 0.15
            w = max(-0.5, min(0.5, (d_ref - side) * Kp))

        return v, self.sign * w

    def step(self, naa):
        """Oppdater tilstand og gi fart. Brukes hver timer-runde"""
        self.update_state(naa)
        return self.gi_comando()
