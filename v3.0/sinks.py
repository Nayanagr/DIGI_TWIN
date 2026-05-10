import numpy as np

class CarbonSink:
    def __init__(self, name, efficiency):
        self.name = name
        self.efficiency = float(efficiency)

    def capture(self, grid: np.ndarray):
        raise NotImplementedError

class NaturalSink(CarbonSink):
    """Forests. Rectangular area capture."""
    def __init__(self, x, y, width, height, density, name="Forest"):
        super().__init__(name, efficiency=density)
        self.x, self.y = int(x), int(y)
        self.width, self.height = int(width), int(height)

    def capture(self, grid: np.ndarray):
        h, w = grid.shape
        x0, y0 = max(self.x, 0), max(self.y, 0)
        x1, y1 = min(self.x + self.width, w), min(self.y + self.height, h)
        if x0 >= x1 or y0 >= y1: return
        
        region = grid[y0:y1, x0:x1]
        grid[y0:y1, x0:x1] = np.maximum(region - self.efficiency, 0.0)

class ArtificialSink(CarbonSink):
    """DAC Units. Point capture."""
    def __init__(self, x, y, capacity, name="DAC Unit"):
        super().__init__(name, efficiency=capacity)
        self.x, self.y = int(x), int(y)

    def capture(self, grid: np.ndarray):
        h, w = grid.shape
        if 0 <= self.x < w and 0 <= self.y < h:
            grid[self.y, self.x] = max(0.0, grid[self.y, self.x] - self.efficiency)
