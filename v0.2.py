import matplotlib.pyplot as plt
import numpy as np

# --------------PARAMS-------------------#
GRID_SIZE = 100  # Larger size of grid
D = 0.09         # Diffusion rate
W_X = 0.09       # Wind in right direction
W_Y = 0.30       # Wind in upward direction
STEPS = 1000

# ---------- Industry ------------------#
class Industry:
    def __init__(self, x, y, emission_rate, name="Factory"):
        self.x = x
        self.y = y
        self.rate = emission_rate
        self.name = name  # so we can label on plot later

    def emit(self, grid):
        # Add CO2 to the grid at industry location
        # grid[row, col] => grid[y, x]
        grid[self.y, self.x] += self.rate

# ---------- Physics -------------------#
def diffuser(C, D):
    # Spread CO2 isotropically
    up = np.roll(C, -1, axis=0)
    down = np.roll(C, 1, axis=0)
    left = np.roll(C, -1, axis=1)
    right = np.roll(C, 1, axis=1)

    lap = -4 * C + up + down + left + right
    return C + D * lap

def apply_advection_current(C, ux, uy):
    """Moves CO2 based on wind speed (ux, uy) using a simple upwind scheme."""

    # Gradient in X
    if ux > 0:
        dCdx = C - np.roll(C, 1, axis=1)      # Current - Left
    else:
        dCdx = np.roll(C, -1, axis=1) - C     # Right - Current

    # Gradient in Y
    if uy > 0:
        dCdy = C - np.roll(C, 1, axis=0)      # Current - Down
    else:
        dCdy = np.roll(C, -1, axis=0) - C     # Up - Current

    C_new = C - (ux * dCdx + uy * dCdy)
    return C_new

def sim_run(industries, steps):
    C = np.zeros((GRID_SIZE, GRID_SIZE), dtype=float)

    for t in range(steps):
        # 1. Emission
        for source in industries:
            source.emit(C)

        # 2. Advection (wind)
        C = apply_advection_current(C, W_X, W_Y)

        # 3. Diffusion (spreading)
        C = diffuser(C, D)

        # 4. Open boundaries: wipe edges so pollution doesn't wrap
        C[:, 0] = 0; C[:, -1] = 0; C[0, :] = 0; C[-1, :] = 0

    return C

# ------ Execution -----------------------#
if __name__ == "__main__":
    sources = [
        Industry(x=40, y=50, emission_rate=20.0, name="Mini Power Plant"),
        Industry(x=30, y=10, emission_rate=90.0, name="Small Factory")
    ]

    print(f"Simulating {STEPS} with WIND = ({W_X}, {W_Y})....")
    final_grid = sim_run(sources, STEPS)

    plt.figure(figsize=(10, 8))
    plt.imshow(final_grid, origin="lower", cmap='jet', vmin=0, vmax=20)
    plt.colorbar(label='CO2 Concentration')

    # Mark sources
    for s in sources:
        plt.plot(s.x, s.y, 'w*', markersize=10, markeredgecolor='black')
        plt.text(s.x, s.y + 2, s.name, color='white', ha='center', fontweight='bold')

    plt.title(
        f"Simulation v0.2: Continuous Plumes with Wind\n"
        f"Advection ({W_X}, {W_Y}) | Diffusion ({D})"
    )
    plt.show()
