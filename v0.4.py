import numpy as np
import matplotlib.pyplot as plt

# --- PARAMS ---
GRID_SIZE = 100
D = 0.24        # Diffusion Rate (Must be <= 0.25 for stability with dt=dx=dy=1)
WIND_X = 0.2    # Wind X (|ux| <= 1.0 for stability)
WIND_Y = 0.05   # Wind Y (|uy| <= 1.0 for stability)
STEPS = 500


# ---------- CFL / Stability Check ----------
def check_cfl_condition(D, ux, uy):
    """
    Simple CFL-like condition for explicit 2D advection-diffusion with dx = dy = dt = 1:
      - Diffusion: D <= 0.25
      - Advection: |ux| <= 1, |uy| <= 1
    Returns True if parameters are in a "safe" range.
    """
    stable_diff = D <= 0.25
    stable_adv = (abs(ux) <= 1.0) and (abs(uy) <= 1.0)

    if not stable_diff:
        print(f"[Warning] Diffusion may be unstable: D = {D} > 0.25")
    if not stable_adv:
        print(f"[Warning] Advection may be unstable: |ux|={abs(ux)}, |uy|={abs(uy)} should be <= 1.0")

    return stable_diff and stable_adv


# ---------- Sources ----------
class Industry:
    def __init__(self, x, y, emission_rate, stack_height=0, name="Factory"):
        self.x = x
        self.y = y
        self.rate = emission_rate
        self.name = name
        self.stack_height = stack_height

    def emit(self, grid):
        """
        Adds CO2.
        If stack_height > 0, we disperse the emission over a wider area
        to simulate a plume landing more spread out.
        """
        # Safety: make sure indices are inside the grid
        y = int(self.y)
        x = int(self.x)

        if self.stack_height == 0:
            if 0 <= y < GRID_SIZE and 0 <= x < GRID_SIZE:
                grid[y, x] += self.rate
        else:
            # Simple 3x3 kernel for a taller stack
            y_min = max(y - 1, 0)
            y_max = min(y + 2, GRID_SIZE)
            x_min = max(x - 1, 0)
            x_max = min(x + 2, GRID_SIZE)

            area = (y_max - y_min) * (x_max - x_min)
            if area > 0:
                grid[y_min:y_max, x_min:x_max] += self.rate / float(area)


class Road:
    def __init__(self, start_x, start_y, end_x, end_y, emission_rate, name="Road"):
        self.start = (start_x, start_y)
        self.end = (end_x, end_y)
        self.rate = emission_rate
        self.name = name

        # Precompute the pixels along this road once
        self.pixels = self.get_line_pixels()

    def get_line_pixels(self):
        """
        Returns a list of (x, y) integer pixel coordinates approximating the road line.
        Uses a simple linspace-based rasterization.
        """
        x0, y0 = self.start
        x1, y1 = self.end

        # Number of sample points along the line
        length = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        if length <= 1:
            xs = np.array([x0], dtype=int)
            ys = np.array([y0], dtype=int)
        else:
            xs = np.linspace(x0, x1, length)
            ys = np.linspace(y0, y1, length)
            xs = np.round(xs).astype(int)
            ys = np.round(ys).astype(int)

        # Keep only valid pixels within the grid
        pixels = []
        for x, y in zip(xs, ys):
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                pixels.append((x, y))

        # Remove duplicates
        pixels = list(dict.fromkeys(pixels))
        return pixels

    def emit(self, grid):
        """
        Add emissions along the road pixels.
        Distribute the rate evenly over all pixels to keep units reasonable.
        """
        if not self.pixels:
            return

        per_pixel = self.rate / len(self.pixels)
        for x, y in self.pixels:
            grid[y, x] += per_pixel


# ---------- Sinks ----------
class CarbonCapture:
    def __init__(self, x, y, efficiency, name="Tree"):
        self.x = x
        self.y = y
        self.rate = efficiency  # Amount of CO2 removed per tick
        self.name = name

    def activate(self, grid):
        """
        Removes CO2 from the grid at (x, y).
        Ensure grid value doesn't go below 0.
        """
        y = int(self.y)
        x = int(self.x)
        if 0 <= y < GRID_SIZE and 0 <= x < GRID_SIZE:
            grid[y, x] = max(0.0, grid[y, x] - self.rate)


# ---------- Physics ----------
def apply_diffusion(C, D):
    up = np.roll(C, -1, axis=0)
    down = np.roll(C, 1, axis=0)
    left = np.roll(C, -1, axis=1)
    right = np.roll(C, 1, axis=1)
    lap = -4 * C + up + down + left + right
    return C + D * lap


def apply_advection(C, ux, uy):
    # Gradient X (upwind)
    if ux > 0:
        dCdx = C - np.roll(C, 1, axis=1)      # Current - Left
    else:
        dCdx = np.roll(C, -1, axis=1) - C     # Right - Current

    # Gradient Y (upwind)
    if uy > 0:
        dCdy = C - np.roll(C, 1, axis=0)      # Current - Down
    else:
        dCdy = np.roll(C, -1, axis=0) - C     # Up - Current

    return C - (ux * dCdx + uy * dCdy)


# ---------- Simulation Loop ----------
def run_simulation(industries, steps, roads=None, captures=None):
    if roads is None:
        roads = []
    if captures is None:
        captures = []

    C = np.zeros((GRID_SIZE, GRID_SIZE), dtype=float)

    for t in range(steps):
        # A. Emissions: Industries + Roads
        for src in industries:
            src.emit(C)
        for road in roads:
            road.emit(C)

        # B. Transport: Advection + Diffusion
        C = apply_advection(C, WIND_X, WIND_Y)
        C = apply_diffusion(C, D)

        # C. Carbon Capture sinks
        for sink in captures:
            sink.activate(C)

        # D. Open Boundaries (pollution leaves domain)
        C[:, 0] = 0
        C[:, -1] = 0
        C[0, :] = 0
        C[-1, :] = 0

    return C


# ---------- Main ----------
if __name__ == '__main__':
    # 1. Check stability before running
    is_safe = check_cfl_condition(D, WIND_X, WIND_Y)

    if is_safe:
        # 2. Define City
        industries = [
            Industry(20, 50, emission_rate=50.0, name="Ground Source", stack_height=0),
            Industry(40, 30, emission_rate=35.0, name="Tall Stack", stack_height=3),
        ]

        roads = [
            Road(10, 20, 80, 20, emission_rate=50.0, name="Main Road"),
            Road(15, 10, 15, 70, emission_rate=30.0, name="Vertical Road"),
        ]

        captures = [
            CarbonCapture(60, 40, efficiency=1.0, name="Park A"),
            CarbonCapture(70, 60, efficiency=1.5, name="Park B"),
        ]

        # 3. Run simulation
        print(f"Simulating {STEPS} steps...")
        final_grid = run_simulation(industries, STEPS, roads=roads, captures=captures)

        # 4. Visualization
        plt.figure(figsize=(10, 8))
        plt.imshow(final_grid, origin='lower', cmap='jet', vmin=0, vmax=10)
        plt.colorbar(label='CO2 Concentration')

        # Mark industries
        for s in industries:
            label = f"{s.name}\n(H={s.stack_height})"
            plt.plot(s.x, s.y, 'w*', markersize=10, markeredgecolor='black')
            plt.text(s.x, s.y + 2, label, color='white', ha='center', fontsize=8, fontweight='bold')

        # Mark roads (optional: small dots)
        for r in roads:
            xs = [p[0] for p in r.pixels]
            ys = [p[1] for p in r.pixels]
            plt.scatter(xs, ys, s=2, c='white', alpha=0.4)

        # Mark capture locations
        for c in captures:
            plt.plot(c.x, c.y, 'gs', markersize=6, markeredgecolor='black')  # green square
            plt.text(c.x, c.y + 2, c.name, color='white', ha='center', fontsize=7)

        plt.title(f"Simulation v0.3: Stability Checked\nD={D}, Wind=({WIND_X}, {WIND_Y})")
        plt.tight_layout()
        plt.show()
    else:
        print("❌ Simulation aborted due to instability risk. Tune D and WIND values.")
