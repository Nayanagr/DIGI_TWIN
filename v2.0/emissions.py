import numpy as np

class EmissionSource:
    """Base class for all pollution sources."""
    def __init__(self, name, pollutant_type="CO2"):
        self.name = name
        self.pollutant_type = pollutant_type  # e.g. "CO2", "NOx", etc.

    @property
    def total_rate(self) -> float:
        """
        Total emission rate per timestep (in whatever units you decide, e.g. g/s).
        Subclasses should override or set this.
        """
        return 0.0

    def emit(self, grid: np.ndarray):
        """Virtual method to be overridden by subclasses."""
        raise NotImplementedError


class PointSource(EmissionSource):
    """
    Represents Industries, Small Factories, or Chimneys.
    Corresponds to: 'Industry -> Plumes'.

    - per_unit_rate: emission per timestep at the core location
    - total_rate: total emission per timestep (for now, equal to per_unit_rate)
    """
    def __init__(
        self,
        x,
        y,
        emission_rate,
        stack_height=0,
        name="Factory",
        pollutant_type="CO2",
    ):
        super().__init__(name, pollutant_type)
        self.x = int(x)
        self.y = int(y)
        self.per_unit_rate = float(emission_rate)   # core cell emission
        self.stack_height = stack_height           # controls kernel spread

    @property
    def total_rate(self) -> float:
        # For a simple point source, total = per-unit (all emitted from one “unit”).
        return self.per_unit_rate

    def emit(self, grid: np.ndarray):
        """
        If stack_height == 0: all mass goes into a single cell.
        If stack_height > 0: mass is spread over a 3x3 kernel (simple plume landing).
        """
        h, w = grid.shape
        y = self.y
        x = self.x

        if not (0 <= x < w and 0 <= y < h):
            return  # out of bounds, ignore

        if self.stack_height == 0:
            grid[y, x] += self.per_unit_rate
        else:
            # Simple 3x3 spread around (x, y)
            y_min = max(y - 1, 0)
            y_max = min(y + 2, h)
            x_min = max(x - 1, 0)
            x_max = min(x + 2, w)

            area = (y_max - y_min) * (x_max - x_min)
            if area > 0:
                grid[y_min:y_max, x_min:x_max] += self.per_unit_rate / area
class LineSource(EmissionSource):
    """
    Represents Roads, Highways, Traffic.
    - traffic_count: vehicles per timestep
    - emission_factor: emission per vehicle per timestep (per_unit_rate)
    - total_rate = traffic_count * emission_factor
    """
    def __init__(
        self,
        start_x,
        start_y,
        end_x,
        end_y,
        traffic_count,
        emission_factor,
        name="Road",
        pollutant_type="CO2",
    ):
        super().__init__(name, pollutant_type)
        self.start = (float(start_x), float(start_y))
        self.end = (float(end_x), float(end_y))

        self.traffic_count = float(traffic_count)
        self.per_unit_rate = float(emission_factor)  # per vehicle
        self._total_rate = self.traffic_count * self.per_unit_rate

        self.pixels = self._rasterize_line()

    @property
    def total_rate(self) -> float:
        return self._total_rate

    def _rasterize_line(self):
        """
        Returns a list of (x, y) integer pixels approximating the road.
        Uses np.linspace between start and end.
        """
        x0, y0 = self.start
        x1, y1 = self.end

        length = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        if length <= 1:
            xs = np.array([x0], dtype=int)
            ys = np.array([y0], dtype=int)
        else:
            xs = np.linspace(x0, x1, length)
            ys = np.linspace(y0, y1, length)
            xs = np.round(xs).astype(int)
            ys = np.round(ys).astype(int)

        pixels = list(dict.fromkeys(zip(xs, ys)))  # remove duplicates, preserve order
        return pixels

    def emit(self, grid: np.ndarray):
        """
        Distribute total_rate evenly across all road pixels.
        Each pixel is like a 'road unit' emitting per_unit_cell_rate.
        """
        if not self.pixels:
            return

        h, w = grid.shape
        n = len(self.pixels)
        per_pixel = self.total_rate / n  # emission per pixel (unit)

        for x, y in self.pixels:
            if 0 <= x < w and 0 <= y < h:
                grid[y, x] += per_pixel
class AreaSource(EmissionSource):
    """
    Represents Wildfires, Forest Fires, Farm Fires.
    - per_unit_rate: emission per cell inside the area
    - total_rate: per_unit_rate * number_of_cells_in_radius
    """
    def __init__(
        self,
        center_x,
        center_y,
        radius,
        intensity,
        name="Wildfire",
        pollutant_type="CO2",
    ):
        super().__init__(name, pollutant_type)
        self.cx = float(center_x)
        self.cy = float(center_y)
        self.radius = float(radius)
        self.per_unit_rate = float(intensity)  # emission per cell per timestep

    def _mask_inside_radius(self, grid_shape):
        """Return boolean mask for cells within radius of center."""
        h, w = grid_shape
        yy, xx = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")
        dist2 = (xx - self.cx) ** 2 + (yy - self.cy) ** 2
        return dist2 <= self.radius ** 2

    @property
    def total_rate(self) -> float:
        # You can approximate area as πr² * per_unit_rate,
        # but we’ll keep it exact per grid layer when emitting.
        # Here we just return a continuous approximation:
        from math import pi
        return pi * (self.radius ** 2) * self.per_unit_rate

    def emit(self, grid: np.ndarray):
        """
        Add per_unit_rate to all pixels within radius.
        """
        mask = self._mask_inside_radius(grid.shape)
        grid[mask] += self.per_unit_rate
