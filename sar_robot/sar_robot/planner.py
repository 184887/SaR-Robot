import heapq
import math

# (drow, dcol, kostnad) for de 8 naborutene
NEIGHBORS = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
             (-1, -1, math.sqrt(2)), (-1, 1, math.sqrt(2)),
             (1, -1, math.sqrt(2)), (1, 1, math.sqrt(2))]


class Planner:
    """A* på et MapGrid der 0 er fritt og alt annet er vegg"""

    def __init__(self, map_grid):
        self.map = map_grid

    def free_cell(self, row, col):
        """Sjekker om en rute er inn i kartert og fri"""
        height, width = self.map.grid.shape
        return 0 <= row < height and 0 <= col < width and self.map.grid[row, col] == 0

    def nearest_free(self, cell, max_dist=20):
        """Nærmeste frie rute, i tilfelle roboten står i bufferen"""
        row, col = cell
        for d in range(max_dist + 1):
            for dr in range(-d, d + 1):
                for dc in range(-d, d + 1):
                    if max(abs(dr), abs(dc)) == d and self.free_cell(row + dr, col + dc):
                        return row + dr, col + dc
        return None

    def heuristic(self, a, b):
        """Anslag på hvor langt det er til målet hvis det ikke var vegger"""
        dr, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
        return max(dr, dc) + (math.sqrt(2) - 1) * min(dr, dc)

    def plan(self, start_xy, goal_xy):
        """Liste med (x, y) fra start til mål, eller [] hvis det ikke finnes noen vei"""
        start = self.nearest_free(self.map.world_to_grid(*start_xy))
        goal = self.nearest_free(self.map.world_to_grid(*goal_xy))
        if start is None or goal is None:
            return []

        open_list = [(self.heuristic(start, goal), start)]
        came_from = {start: None}
        cost = {start: 0.0}

        while open_list:
            _, current = heapq.heappop(open_list)
            if current == goal:
                break
            for dr, dc, step in NEIGHBORS:
                nxt = (current[0] + dr, current[1] + dc)
                if not self.free_cell(*nxt):
                    continue
                # ikke kutt hjørner: begge rutene vi går diagonalt forbi må være frie
                if dr and dc and not (self.free_cell(current[0] + dr, current[1])
                                      and self.free_cell(current[0], current[1] + dc)):
                    continue
                new_cost = cost[current] + step
                if new_cost < cost.get(nxt, math.inf):
                    cost[nxt] = new_cost
                    came_from[nxt] = current
                    heapq.heappush(open_list, (new_cost + self.heuristic(nxt, goal), nxt))

        if goal not in came_from:
            return []

        cells = []
        cell = goal
        while cell is not None:
            cells.append(cell)
            cell = came_from[cell]
        cells.reverse()
        return [self.map.grid_to_world(row, col) for row, col in self.simplify(cells)]

    @staticmethod
    def simplify(cells):
        """Fjern ruter midt på rette strekk, behold bare der retningen endres"""
        if len(cells) < 3:
            return cells
        kept = [cells[0]]
        for prev, cur, nxt in zip(cells, cells[1:], cells[2:]):
            if (cur[0] - prev[0], cur[1] - prev[1]) != (nxt[0] - cur[0], nxt[1] - cur[1]):
                kept.append(cur)
        kept.append(cells[-1])
        return kept