import math

import numpy as np
from scipy import ndimage

class MapGrid:
    """Kartet som tabell: grid[rad, kolonne], rad følger y, kolonne følger x"""
    def __init__(self, grid, resolution, origin_x, origin_y):
        self.grid = np.asarray(grid, dtype=np.int8)
        self.resolution = resolution
        self.origin_x = origin_x
        self.origin_y = origin_y

    @classmethod
    def from_msg(cls, msg):
        """Lag MapGrid fra en /map-melding"""
        info = msg.info
        grid = np.asarray(msg.data, dtype=np.int8).reshape(info.height, info.width)

        return cls(grid, info.resolution, info.origin.position.x, info.origin.position.y)
        
    def world_to_grid(self, x, y):
        """Meter til (rad, kolonne)"""
        col = math.floor((x - self.origin_x) / self.resolution)
        row = math.floor ((y - self.origin_y) / self.resolution)
            
        return row, col
        
    def grid_to_world(self, row, col):
        """(rad, kolonne) til meter"""
        x = self.origin_x + (col + 0.5) * self.resolution
        y = self.origin_y + (row + 0.5) * self.resolution

        return x, y
        
    def is_free(self, x, y):
        """True hvis punktet er inne i kartet og ruta er fri"""
        row, col = self.world_to_grid(x, y)
        height, width = self.grid.shape
        inside = 0 <= row < height and 0 <= col < width

        return inside and self.grid[row, col] == 0
        
    def inflate(self, radius_m):
        """Nytt kart der veggene er radius_m tykkere. Ukjent regnes som vegg"""
        n = math.ceil(radius_m / self.resolution - 1e-6)
        yy, xx = np.ogrid[-n:n + 1, -n:n + 1]
        circle = xx * xx + yy * yy <= n * n
        blocked = ndimage.binary_dilation(self.grid != 0, structure=circle)
        grid = np.where(blocked, 100, 0).astype(np.int8)
            
        return MapGrid(grid, self.resolution, self.origin_x, self.origin_y)