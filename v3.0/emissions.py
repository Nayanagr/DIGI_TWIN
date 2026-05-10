import numpy as np

class EmissionSource:
    """Base class for all pollution sources."""
    def __init__(self, name, pollutant_type="CO2"):
        self.name = name
        self.pollutant_type = pollutant_type

    def emit(self, grid: np.ndarray):
        raise NotImplementedError

class PointSource(EmissionSource):
    """Factories, Chimneys. Spreads over a 3x3 kernel if stack height > 0."""
    def __init__(self, x, y, emission_rate, stack_height=0, name="Factory", pollutant_type="CO2"):
        super().__init__(name, pollutant_type)
        self.x = int(x)
        self.y = int(y)
        self.rate = float(emission_rate)
        self.stack_height = stack_height

    def emit(self, grid: np.ndarray):
        h, w = grid.shape
        if not (0 <= self.x < w and 0 <= self.y < h): return

        if self.stack_height == 0:
            grid[self.y, self.x] += self.rate
        else:
            # 3x3 kernel spread
            y_min, y_max = max(self.y - 1, 0), min(self.y + 2, h)
            x_min, x_max = max(self.x - 1, 0), min(self.x + 2, w)
            area = (y_max - y_min) * (x_max - x_min)
            if area > 0: grid[y_min:y_max, x_min:x_max] += self.rate / area

class LineSource(EmissionSource):
    """Roads. Rasterized line using linear interpolation."""
    def __init__(self, start_x, start_y, end_x, end_y, traffic_count, emission_factor, name="Road", pollutant_type="CO2"):
        super().__init__(name, pollutant_type)
        self.start = (float(start_x), float(start_y))
        self.end = (float(end_x), float(end_y))
        self.total_rate = float(traffic_count) * float(emission_factor)
        self.pixels = self._rasterize()

    def _rasterize(self):
        x0, y0 = self.start
        x1, y1 = self.end
        length = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        if length <= 1:
            return [(int(x0), int(y0))]
        xs = np.linspace(x0, x1, length)
        ys = np.linspace(y0, y1, length)
        return list(dict.fromkeys(zip(np.round(xs).astype(int), np.round(ys).astype(int))))

    def emit(self, grid: np.ndarray):
        if not self.pixels: return
        h, w = grid.shape
        per_pixel = self.total_rate / len(self.pixels)
        for x, y in self.pixels:
            if 0 <= x < w and 0 <= y < h: grid[y, x] += per_pixel

class AreaSource(EmissionSource):
    """Wildfires. Circular area emission."""
    def __init__(self, center_x, center_y, radius, intensity, name="Wildfire", pollutant_type="CO2"):
        super().__init__(name, pollutant_type)
        self.cx, self.cy = float(center_x), float(center_y)
        self.radius = float(radius)
        self.intensity = float(intensity)

    def emit(self, grid: np.ndarray):
        h, w = grid.shape
        yy, xx = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")
        mask = (xx - self.cx)**2 + (yy - self.cy)**2 <= self.radius**2
        grid[mask] += self.intensity
