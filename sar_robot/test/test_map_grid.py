import numpy as np

from sar_robot.map_grid import MapGrid


def make_map():
    """Testkart: 1 x 1 m, ruter på 0.1 m, origin i (-0.5, -0.5).

    Vegg langs hele kanten, og en vegg på kolonne 5 (x = 0.0 til 0.1).
    """
    grid = np.zeros((10, 10), dtype=np.int8)
    grid[0, :] = grid[-1, :] = grid[:, 0] = grid[:, -1] = 100
    grid[:, 5] = 100
    return MapGrid(grid, 0.1, -0.5, -0.5)


def test_world_to_grid():
    m = make_map()
    assert m.world_to_grid(-0.5, -0.5) == (0, 0)
    assert m.world_to_grid(0.05, -0.25) == (2, 5)  # x gir kolonne, y gir rad


def test_round_trip():
    m = make_map()
    x, y = m.grid_to_world(*m.world_to_grid(0.23, -0.31))
    assert abs(x - 0.23) <= 0.05 and abs(y - (-0.31)) <= 0.05


def test_is_free():
    m = make_map()
    assert m.is_free(-0.25, 0.0)       # midt i venstre rom
    assert not m.is_free(0.05, 0.0)    # midtveggen
    assert not m.is_free(-0.45, 0.0)   # ytterveggen
    assert not m.is_free(5.0, 5.0)     # utenfor kartet


def test_inflate():
    m = make_map()
    big = m.inflate(0.1)
    assert (big.grid == 100).sum() > (m.grid == 100).sum()
    assert m.is_free(-0.05, 0.0)        # fri før ...
    assert not big.is_free(-0.05, 0.0)  # ... men nær vegg etter
    assert (m.grid[1:-1, 6] == 0).all()  # originalen er uendret