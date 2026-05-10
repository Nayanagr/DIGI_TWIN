import numpy as np
from typing import List
from emissions import EmissionSource
from sinks import CarbonSink

class CityGrid:
    """Manages grid state and physics calculations."""
    def __init__(self, size=100):
        self.size = size
        self.layers = {"CO2": np.zeros((size, size), dtype=float)}

    def add_emissions(self, sources: List[EmissionSource]):
        for src in sources:
            if src.pollutant_type not in self.layers:
                self.layers[src.pollutant_type] = np.zeros((self.size, self.size))
            src.emit(self.layers[src.pollutant_type])

    def apply_sinks(self, sinks: List[CarbonSink]):
        if "CO2" in self.layers:
            for sink in sinks: 
                sink.capture(self.layers["CO2"])

    def update_physics(self, wind_x, wind_y, diffusion_rate):
        for key, field in self.layers.items():
            # 1. Advection (Upwind Scheme)
            if wind_x > 0: 
                dCdx = field - np.roll(field, 1, axis=1)
            else: 
                dCdx = np.roll(field, -1, axis=1) - field
            
            if wind_y > 0: 
                dCdy = field - np.roll(field, 1, axis=0)
            else: 
                dCdy = np.roll(field, -1, axis=0) - field
            
            advected = field - (wind_x * dCdx + wind_y * dCdy)

            # 2. Diffusion (Finite Difference Laplacian)
            lap = -4 * advected + np.roll(advected,-1,0) + np.roll(advected,1,0) + \
                  np.roll(advected,-1,1) + np.roll(advected,1,1)
            diffused = advected + diffusion_rate * lap

            # 3. Open Boundaries
            diffused[:, [0, -1]] = 0 
            diffused[[0, -1], :] = 0
            
            self.layers[key] = diffused
