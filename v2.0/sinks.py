import numpy as np

class CarbonSink:
    """Base class for all capture methods."""
    def __init__(self, name, efficiency):
        self.name = name
        self.efficiency = float(efficiency)  # per timestep

    def capture(self, grid: np.ndarray):
        raise NotImplementedError
class NaturalSink(CarbonSink):
    """
    Forests, Parks, Farms.
    Low efficiency per pixel, but covers a large area.
    Rectangular region.
    """
    def __init__(self, x, y, width, height, density, name="Forest"):
        super().__init__(name, efficiency=density)
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)

    def capture(self, grid: np.ndarray):
        h, w = grid.shape
        x0 = max(self.x, 0)
        y0 = max(self.y, 0)
        x1 = min(self.x + self.width, w)
        y1 = min(self.y + self.height, h)

        if x0 >= x1 or y0 >= y1:
            return

        # Subtract efficiency from the region but keep >= 0
        sub = grid[y0:y1, x0:x1] - self.efficiency
        sub = np.maximum(sub, 0.0)
        grid[y0:y1, x0:x1] = sub
class ArtificialSink(CarbonSink):
    """
    Biofilters, Adsorbers, Direct Air Capture units.
    High efficiency at a single point.
    """
    def __init__(self, x, y, capacity, name="DAC Unit"):
        super().__init__(name, efficiency=capacity)
        self.x = int(x)
        self.y = int(y)

    def capture(self, grid: np.ndarray):
        h, w = grid.shape
        if 0 <= self.x < w and 0 <= self.y < h:
            grid[self.y, self.x] = max(0.0, grid[self.y, self.x] - self.efficiency)
