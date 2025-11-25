from inspect import CORO_CREATED

import matplotlib.pyplot as plt
import numpy as np, matplotlib.pyplot as mpl
from scipy.sparse.csgraph import laplacian

#PARAMS
GRID_SIZE = 50
D = 0.1
STEPS = 500

#GRID

C = np.zeros((GRID_SIZE, GRID_SIZE), dtype=float)
center = GRID_SIZE//2
C[center,center] = 100.0 # CO2 arbitary value

##dC/dt = D * (d²C/dx² + d²C/dy²)
def diffusion(C,D):
    up = np.roll(C,-1,axis=0)
    down = np.roll(C,1,axis=0)
    left = np.roll(C, -1,axis=1)
    right = np.roll(C,1,axis=1)

    laplacian = -4 * C + up + down + left + right
    C_N = C + D * laplacian
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
    fig, axes = mpl.subplots(1,2,figsize=(10,4))
    im = axes[0].imshow(C_ini, origin='lower')
    axes[0].set_title("Initial CO2 Field")
    plt.colorbar(im,ax=axes[0])

    im1 = axes[1].imshow(C_final, origin='lower')
    axes[1].set_title("CO₂ Field After {TIME_STEPS} Steps")
    plt.colorbar(im1, ax=axes[1])

    plt.tight_layout()
    plt.show()
