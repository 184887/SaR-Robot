import numpy as np

from sar_robot.map_grid import MapGrid
from sar_robot.planner import Planner


def make_map(gap=True):
    """
    Testkart: 2 x 1 m, ruter på 0.1 m, origin i (0, 0).

    Vegg på kolonne 10 (x = 1.0 til 1.1), med en åpning i rad 7-8 (y = 0.7 til 0.9).
    """
    grid = np.zeros((10, 20), dtype=np.int8)
    grid[:, 10] = 100
    if gap:
        grid[7:9, 10] = 0
    return MapGrid(grid, 0.1, 0.0, 0.0)


def test_path_through_gap():
    m = make_map()
    path = Planner(m).plan((0.15, 0.15), (1.85, 0.15))
    assert path
    assert all(m.is_free(x, y) for x, y in path)
    assert any(y > 0.7 for x, y in path)  # må gå gjennom åpningen


def test_no_path():
    assert Planner(make_map(gap=False)).plan((0.15, 0.15), (1.85, 0.15)) == []


def test_start_in_wall():
    m = make_map()
    path = Planner(m).plan((1.05, 0.15), (1.85, 0.15))  # start inni veggen
    assert path and m.is_free(*path[0])


def test_downsample():
    small = make_map().downsample(2)
    assert small.grid.shape == (5, 10)
    assert abs(small.resolution - 0.2) < 1e-9
    assert small.grid[0, 5] == 100  # veggen havner i ny kolonne 5
    assert small.grid[0, 4] == 0