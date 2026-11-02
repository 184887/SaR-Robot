from sar_robot.wall_follower import State, WallFollower


def scan(front=5.0, right=5.0, left=5.0):
    """360 avstander, med valgt avstand foran, til høyre og til venstre"""
    r = [5.0] * 360
    for i in list(range(330, 360)) + list(range(0, 31)):
        r[i] = front
    for i in range(70, 110):
        r[i] = left
    for i in range(250, 291):
        r[i] = right
    return r


def test_vegg_foran_gir_sving_bort():
    wf = WallFollower()
    wf.set_scan(scan(front=0.3), 0.1, 10.0)
    v, w = wf.step(0.0)
    assert wf.state == State.SVING_BORT
    assert v == 0.0 and w > 0


def test_folger_hoyre_vegg():
    wf = WallFollower(follow_left=False)
    wf.set_scan(scan(right=0.4), 0.1, 10.0)
    wf.step(0.0)
    assert wf.state == State.FOLLOW_WALL


def test_venstre_snur_fortegnet():
    hoyre = WallFollower(follow_left=False)
    venstre = WallFollower(follow_left=True)
    hoyre.set_scan(scan(front=0.3), 0.1, 10.0)
    venstre.set_scan(scan(front=0.3), 0.1, 10.0)
    assert hoyre.step(0.0)[1] == -venstre.step(0.0)[1]


def test_sving_mot_timeout():
    wf = WallFollower(sving_mot_timeout=7.0)
    wf.set_scan(scan(right=0.4), 0.1, 10.0)
    wf.step(0.0)
    wf.set_scan(scan(), 0.1, 10.0)   # veggen forsvinner
    wf.step(1.0)
    assert wf.state == State.SVING_MOT
    wf.step(5.0)
    assert wf.state == State.SVING_MOT
    wf.step(9.0)
    assert wf.state == State.FINN_VEGG


def test_ugyldige_verdier_ignoreres():
    wf = WallFollower()
    wf.set_scan([float('inf')] * 360, 0.1, 10.0)
    assert wf.regions['front'] == float('inf')
