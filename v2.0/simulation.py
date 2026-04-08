import numpy as np
from typing import List
from emissions import EmissionSource
from sinks import CarbonSink

class CityGrid:
    """
    Manages the state of the city.
    Can hold multiple layers: CO2, SO2, NOx, etc.
    """
    def __init__(self, size=100):
        self.size = size
        self.layers = {
            "CO2": np.zeros((size, size), dtype=float),
            # "SO2": np.zeros((size, size), dtype=float),  # optional
        }

    def add_emissions(self, sources: List[EmissionSource]):
        """
        Loop through sources. Route emission to the correct pollutant layer.
        """
        for src in sources:
            layer_name = src.pollutant_type
            if layer_name not in self.layers:
                # Auto-create new layer if needed
                self.layers[layer_name] = np.zeros((self.size, self.size), dtype=float)
            grid = self.layers[layer_name]
            src.emit(grid)

    def apply_sinks(self, sinks: List[CarbonSink]):
        """
        Apply sinks to CO2 (for now).
        Later you can extend CarbonSink to specify pollutant types.
        """
        co2 = self.layers.get("CO2")
        if co2 is None:
            return
        for sink in sinks:
            sink.capture(co2)

    # ---------- Physics Core ---------- #
    @staticmethod
    def _apply_diffusion(field: np.ndarray, D: float) -> np.ndarray:
        up = np.roll(field, -1, axis=0)
        down = np.roll(field, 1, axis=0)
        left = np.roll(field, -1, axis=1)
        right = np.roll(field, 1, axis=1)
        lap = -4 * field + up + down + left + right
        return field + D * lap

    @staticmethod
    def _apply_advection(field: np.ndarray, ux: float, uy: float) -> np.ndarray:
        # Upwind in X
        if ux > 0:
            dCdx = field - np.roll(field, 1, axis=1)      # current - left
        else:
            dCdx = np.roll(field, -1, axis=1) - field     # right - current

        # Upwind in Y
        if uy > 0:
            dCdy = field - np.roll(field, 1, axis=0)      # current - down
        else:
            dCdy = np.roll(field, -1, axis=0) - field     # up - current

        return field - (ux * dCdx + uy * dCdy)

    def update_physics(self, wind_x: float, wind_y: float, diffusion_rate: float):
        """
        Apply advection + diffusion to ALL pollutant layers.
        """
        for key, field in self.layers.items():
            advected = self._apply_advection(field, wind_x, wind_y)
            diffused = self._apply_diffusion(advected, diffusion_rate)

            # Open boundaries: let pollutant leave the map
            diffused[:, 0] = 0
            diffused[:, -1] = 0
            diffused[0, :] = 0
            diffused[-1, :] = 0

            self.layers[key] = diffused
