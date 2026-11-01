import math

import numpy as np
from scipy import ndimage
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

from sar_robot.planner import Planner


def coverage_points(map_grid, start_xy, spacing):
    """
    Kartet deles i ruter på spacing x spacing meter. I hver rute velges punktet
    lengst unna vegger. Punkter nærmere enn spacing / 2 et annet punkt hoppes over.
    """
    labels, _ = ndimage.label(map_grid.grid == 0)
    row, col = Planner(map_grid).nearest_free(map_grid.world_to_grid(*start_xy))
    reachable = labels == labels[row, col]
    dist = ndimage.distance_transform_edt(reachable)

    step = max(1, round(spacing / map_grid.resolution))
    height, width = reachable.shape
    points = []
    for r0 in range(0, height, step):
        for c0 in range(0, width, step):
            block = dist[r0:r0 + step, c0:c0 + step]
            if block.max() == 0:
                continue
            r, c = np.unravel_index(block.argmax(), block.shape)
            p = map_grid.grid_to_world(r0 + r, c0 + c)
            if all(math.dist(p, q) >= spacing / 2 for q in points):
                points.append(p)
    return points


def path_distances(map_grid, points):
    """Måler lengde mellom punkter når man kjører langs gangene og ikke gjennom vegger. Bruker Djikstra"""
    free = map_grid.grid == 0
    height, width = free.shape
    index = np.arange(height * width).reshape(height, width)

    # kant mellom alle frie naboruter (høyre og ned holder, grafen er urettet)
    right = free[:, :-1] & free[:, 1:]
    down = free[:-1, :] & free[1:, :]
    a = np.concatenate([index[:, :-1][right], index[:-1, :][down]])
    b = np.concatenate([index[:, 1:][right], index[1:, :][down]])
    graph = csr_matrix((np.ones(len(a)), (a, b)), shape=(height * width, height * width))

    planner = Planner(map_grid)  # for nearest_free, i tilfelle en robot står i bufferen
    cells = [index[planner.nearest_free(map_grid.world_to_grid(x, y))] for x, y in points]
    dist = dijkstra(graph, directed=False, indices=cells)
    return dist[:, cells] * map_grid.resolution


def split_route(map_grid, points, starts):
    """Lag én rute gjennom alle punktene og del den i to, én halvdel per robot"""
    D = path_distances(map_grid, list(starts) + points)
    n = len(starts)

    # nærmeste nabo fra robot 0 sin start, målt langs gangene
    order = []
    current = 0
    left = set(range(n, len(D)))
    while left:
        current = min(left, key=lambda j: D[current][j])
        left.remove(current)
        order.append(current)

    half = len(order) // 2
    first, second = order[:half], order[half:]
    if D[1][second[-1]] < D[1][second[0]]:  # robot 1 starter i den enden som er nærmest
        second.reverse()
    return [[points[i - n] for i in first], [points[i - n] for i in second]]