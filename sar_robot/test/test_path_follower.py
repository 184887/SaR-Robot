import math

from sar_robot.path_follower import PathFollower


def test_tom_rute_er_ferdig():
    pf = PathFollower()
    assert pf.done()
    assert pf.step(0.0, 0.0, 0.0) == (0.0, 0.0)


def test_kjorer_rett_fram_mot_punkt():
    pf = PathFollower()
    pf.set_path([(1.0, 0.0)])
    v, w = pf.step(0.0, 0.0, 0.0)
    assert v > 0 and w == 0.0


def test_snur_paa_stedet_naar_punktet_er_bak():
    pf = PathFollower()
    pf.set_path([(-1.0, 0.0)])
    v, w = pf.step(0.0, 0.0, 0.0)
    assert v == 0.0 and w != 0.0


def test_svinger_mot_venstre():
    pf = PathFollower()
    pf.set_path([(0.0, 1.0)])
    _, w = pf.step(0.0, 0.0, 0.0)
    assert w > 0


def test_hopper_over_naadde_punkter():
    pf = PathFollower(tolerance=0.2)
    pf.set_path([(0.1, 0.0), (2.0, 0.0)])
    pf.step(0.0, 0.0, 0.0)
    assert pf.points == [(2.0, 0.0)]
    pf.step(1.95, 0.0, 0.0)
    assert pf.done()


def test_vinkel_rundt_pi():
    """Peker nesten bakover, men like over pi: skal svinge den korte veien"""
    pf = PathFollower()
    pf.set_path([(-1.0, -0.01)])
    _, w = pf.step(0.0, 0.0, math.pi - 0.1)
    assert w > 0
