import math

import numpy as np

from sar_robot.coverage import coverage_points, path_distances, route_length, split_route
from sar_robot.map_grid import MapGrid

STARTS = [(0.5, 0.5), (0.5, 1.5)]


def make_map():
    """Testkart: 4 x 2 m, ruter på 0.1 m, origin i (0, 0).

    Yttervegg rundt alt. Midtvegg på kolonne 20 (x = 2.0) med åpning i rad 8-11.
    Lukket boks i øvre høyre hjørne (x = 3.0-3.8, y = 1.2-1.8) som ikke kan nås.
    """
    grid = np.zeros((20, 40), dtype=np.int8)
    grid[0, :] = grid[-1, :] = grid[:, 0] = grid[:, -1] = 100
    grid[:, 20] = 100
    grid[8:12, 20] = 0
    grid[12, 30:39] = grid[18, 30:39] = 100
    grid[12:19, 30] = grid[12:19, 38] = 100
    return MapGrid(grid, 0.1, 0.0, 0.0)


def test_points_free_and_reachable():
    m = make_map()
    points = coverage_points(m, STARTS[0], 0.5)
    assert all(m.is_free(x, y) for x, y in points)
    assert not any(3.0 < x < 3.8 and 1.2 < y < 1.8 for x, y in points)  # ikke i boksen


def test_points_cover_both_rooms():
    points = coverage_points(make_map(), STARTS[0], 0.5)
    assert any(x < 2.0 for x, y in points)
    assert any(x > 2.1 for x, y in points)


def test_path_distance_goes_around_wall():
    a, b = (1.5, 0.5), (2.5, 0.5)  # hver sin side av midtveggen
    D = path_distances(make_map(), [a, b])
    assert D[0][1] > math.dist(a, b) + 0.5  # må via åpningen


def test_split_route():
    m = make_map()
    points = coverage_points(m, STARTS[0], 0.5)
    routes = split_route(m, points, STARTS)
    assert sorted(routes[0] + routes[1]) == sorted(points)   # alle punktene er med, ingen dobbelt

    D = path_distances(m, list(STARTS) + routes[0] + routes[1])
    n0 = len(routes[0])
    a = route_length(D, 0, range(2, 2 + n0))
    b = route_length(D, 1, range(2 + n0, len(D)))
    assert abs(a - b) <= 0.3 * max(a, b)   # omtrent like lange


def test_start_in_wall():
    m = make_map()
    points = coverage_points(m, (2.05, 0.5), 0.5)  # start inni midtveggen
    assert len(points) > 5
