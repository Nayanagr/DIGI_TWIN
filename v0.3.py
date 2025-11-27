import matplotlib.pyplot as plt
import numpy as np

# --- PARAMS ---
GRID_SIZE = 100
D = 0.05  # Diffusion Rate (Must be <= 0.25 for stability)
WIND_X = 0.2  # Wind X (Must be <= 1.0)
WIND_Y = 0.05  # Wind Y (Must be <= 1.0)
STEPS = 500


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
        to simulate the plume touching down further away or wider.
        """
        if self.stack_height == 0:
            grid[self.y, self.x] += self.rate
        else:
            # SIMULATION OF HEIGHT:
            # A tall stack spreads pollution to neighbors immediately
            # so it's less concentrated at the exact center point.
            radius = 1
            # Simple 3x3 kernel addition for "tall" stacks
            grid[self.y - 1:self.y + 2, self.x - 1:self.x + 2] += (self.rate / 9.0)


# --- PHYSICS ENGINE & STABILITY ---

def check_cfl_condition(D, ux, uy):
    """
    Checks if the simulation parameters will cause a crash (Numerical Instability).
    Based on the Courant-Friedrichs-Lewy (CFL) condition.
    """
    # 1. Check Diffusion Stability
    # In 2D explicit method, D must be <= 0.25
    if D > 0.25:
        print(f"⚠️  WARNING: Diffusion rate {D} is UNSTABLE! (Must be <= 0.25)")
        print("   -> The simulation will likely explode or oscillate.")
        return False

    # 2. Check Advection Stability (Courant Number)
    # Wind speed cannot move particles more than 1 cell per step
    max_wind = max(abs(ux), abs(uy))
    if max_wind > 1.0:
        print(f"⚠️  WARNING: Wind speed {max_wind} is too fast! (Must be <= 1.0)")
        print("   -> Pollution will 'skip' over cells.")
        return False

    print("✅ Simulation Parameters are STABLE.")
    return True


def apply_diffusion(C, D):
    up = np.roll(C, -1, axis=0)
    down = np.roll(C, 1, axis=0)
    left = np.roll(C, -1, axis=1)
    right = np.roll(C, 1, axis=1)
    lap = -4 * C + up + down + left + right
    return C + D * lap


def apply_advection(C, ux, uy):
    # Gradient X
    if ux > 0:
        dCdx = C - np.roll(C, 1, axis=1)
    else:
        dCdx = np.roll(C, -1, axis=1) - C

    # Gradient Y
    if uy > 0:
        dCdy = C - np.roll(C, 1, axis=0)
    else:
        dCdy = np.roll(C, -1, axis=0) - C

    return C - (ux * dCdx + uy * dCdy)


def run_simulation(industries, steps):
    C = np.zeros((GRID_SIZE, GRID_SIZE), dtype=float)

    for t in range(steps):
        for source in industries:
            source.emit(C)
        C = apply_advection(C, WIND_X, WIND_Y)
        C = apply_diffusion(C, D)

        # Open Boundaries (Pollution leaves the map)
        C[:, 0] = 0;
        C[:, -1] = 0;
        C[0, :] = 0;
        C[-1, :] = 0

    return C


# --- EXECUTION ---
if __name__ == '__main__':
    # 1. Check Math Stability BEFORE running
    is_safe = check_cfl_condition(D, WIND_X, WIND_Y)

    if is_safe:
        # 2. Define City
        sources = [
            Industry(20, 50, emission_rate=5.0, name="Ground Source", stack_height=0),
            Industry(40, 30, emission_rate=5.0, name="Tall Stack", stack_height=1)
        ]

        # 3. Run
        print(f"Simulating {STEPS} steps...")
        final_grid = run_simulation(sources, STEPS)

        # 4. Viz
        plt.figure(figsize=(10, 8))
        plt.imshow(final_grid, origin='lower', cmap='jet', vmin=0, vmax=10)
        plt.colorbar(label='CO2 Concentration')

        for s in sources:
            label = f"{s.name}\n(H={s.stack_height})"
            plt.plot(s.x, s.y, 'w*', markersize=10, markeredgecolor='black')
            plt.text(s.x, s.y + 2, label, color='white', ha='center', fontsize=8, fontweight='bold')

        plt.title(f"Simulation v0.3: Stability Checked\nD={D}, Wind=({WIND_X}, {WIND_Y})")
        plt.show()
    else:
        print("❌ Simulation Aborted due to instability risk.")