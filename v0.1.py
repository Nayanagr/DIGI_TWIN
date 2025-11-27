from inspect import CORO_CREATED

import matplotlib.pyplot as plt
import numpy as np, matplotlib.pyplot as mpl
from scipy.sparse.csgraph import laplacian
#PARAMS
GRID_SIZE = 50
D = 0.1
STEPS = 1000

#GRID

C = np.zeros((GRID_SIZE, GRID_SIZE), dtype=float)
center = GRID_SIZE//2
C[center,center] = 50.0 # CO2 arbitary value

##dC/dt = D * (d²C/dx² + d²C/dy²)
def diffusion(C, D):
    up = np.roll(C,-1,axis=0)
    down = np.roll(C,1,axis=0)
    left = np.roll(C, -1,axis=1)
    right = np.roll(C,1,axis=1)

    lap = -4 * C + up + down + left + right
    C_N = C + D * lap

    return C_N


def run_simulations(C,D,time_steps):
    C_current = C.copy()
    for t in range(time_steps):
        C_current = diffusion(C_current,D)
    return C_current

if __name__ == '__main__':
    C_ini = C.copy()
    C_final = run_simulations(C_ini,D,STEPS)

    #PLOTTING
    fig = plt.figure(figsize=(10, 4))

    # Narrower side pane using smaller width ratio
    gs = fig.add_gridspec(1, 3, width_ratios=[1.4, 1.4, 0.4])

    # Plot 1
    ax0 = fig.add_subplot(gs[0, 0])
    im = ax0.imshow(C_ini, origin='lower')
    ax0.set_title("Initial CO₂ Field")
    plt.colorbar(im, ax=ax0, fraction=0.045, pad=0.02)

    # Plot 2
    ax1 = fig.add_subplot(gs[0, 1])
    im1 = ax1.imshow(C_final, origin='lower')
    ax1.set_title(f"CO₂ After {STEPS} Steps")
    plt.colorbar(im1, ax=ax1, fraction=0.045, pad=0.02)

    # Small side info box
    ax_info = fig.add_subplot(gs[0, 2])
    ax_info.axis("off")

    info = (
        "Params\n"
        "-----------\n"
        f"D: {D}\n"
        f"Steps: {STEPS}\n"
        f"Grid: {GRID_SIZE}×{GRID_SIZE}"
    )

    ax_info.text(
        0.05, 0.95,
        info,
        fontsize=9,
        va="top",
        ha="left",
        family="monospace",
    )

    plt.tight_layout()
    plt.show()

