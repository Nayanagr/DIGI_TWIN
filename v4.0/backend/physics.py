"""
physics.py — Urban CO₂ Digital Twin: Multi-Geometry Engine (V4.2)
==================================================================
Includes advanced receptor and scaling parameters.
"""

import numpy as np
from typing import List, Dict, Any

PG_COEFFICIENTS: Dict[str, Dict[str, float]] = {
    "A": {"sy_a": 0.22, "sy_b": 0.89, "sz_c": 0.20, "sz_d": 0.89, "sz_e": -0.0},
    "B": {"sy_a": 0.16, "sy_b": 0.87, "sz_c": 0.12, "sz_d": 0.95, "sz_e":  0.0},
    "C": {"sy_a": 0.11, "sy_b": 0.86, "sz_c": 0.08, "sz_d": 0.90, "sz_e":  0.0},
    "D": {"sy_a": 0.08, "sy_b": 0.86, "sz_c": 0.06, "sz_d": 0.76, "sz_e":  0.0},
    "E": {"sy_a": 0.06, "sy_b": 0.86, "sz_c": 0.03, "sz_d": 0.71, "sz_e":  0.0},
    "F": {"sy_a": 0.04, "sy_b": 0.86, "sz_c": 0.016,"sz_d": 0.67, "sz_e":  0.0},
}

def sigma_y(x_pos, stability):
    coef = PG_COEFFICIENTS[stability.upper()]
    x_safe = np.maximum(x_pos, 1e-3)
    return coef["sy_a"] * np.power(x_safe, coef["sy_b"])

def sigma_z(x_pos, stability):
    coef = PG_COEFFICIENTS[stability.upper()]
    x_safe = np.maximum(x_pos, 1e-3)
    sz = coef["sz_c"] * np.power(x_safe, coef["sz_d"]) + coef["sz_e"]
    return np.maximum(sz, 1.0)

def rotate_to_wind_frame(X, Y, src_x, src_y, wind_rad):
    dx = X - src_x
    dy = Y - src_y
    cos_w = np.cos(wind_rad)
    sin_w = np.sin(wind_rad)
    x_wind =  dx * cos_w + dy * sin_w
    y_wind = -dx * sin_w + dy * cos_w
    return x_wind, y_wind

def gaussian_plume(X, Y, src_x, src_y, Q, u, H, stability, wind_rad, receptor_height, metres_per_pixel):
    u_safe = max(u, 0.1)
    x_w, y_w = rotate_to_wind_frame(X, Y, src_x, src_y, wind_rad)
    x_m = x_w * metres_per_pixel
    y_m = y_w * metres_per_pixel

    downwind_mask = x_m > 0.0
    C = np.zeros_like(X, dtype=np.float64)
    if not np.any(downwind_mask): return C

    x_dw = np.where(downwind_mask, x_m, np.nan)
    sy = sigma_y(x_dw, stability)
    sz = sigma_z(x_dw, stability)

    z = receptor_height
    denom = (2.0 * np.pi * u_safe * sy * sz)
    prefactor = np.where(downwind_mask, Q / np.maximum(denom, 1e-30), 0.0)
    lateral = np.exp(-0.5 * (y_m / np.maximum(sy, 1e-6))**2)
    vert_direct    = np.exp(-0.5 * ((z - H) / np.maximum(sz, 1e-6))**2)
    vert_reflected = np.exp(-0.5 * ((z + H) / np.maximum(sz, 1e-6))**2)

    C = prefactor * lateral * (vert_direct + vert_reflected)
    return np.nan_to_num(C)

def calculate_dispersion_grid(grid_size, entities, wind_speed, wind_dir_deg, stability_class, receptor_height, metres_per_pixel):
    x_coords = np.arange(grid_size)
    y_coords = np.arange(grid_size)
    X, Y = np.meshgrid(x_coords, y_coords)
    Y_inv = (grid_size - 1) - Y
    
    wind_math_deg = (270.0 - wind_dir_deg) % 360.0
    wind_rad = np.deg2rad(wind_math_deg)
    
    total_concentration = np.zeros((grid_size, grid_size), dtype=np.float64)

    for ent in entities:
        etype = ent.get("type")
        if etype == "point":
            total_concentration += gaussian_plume(X, Y_inv, ent['x'], ent['y'], ent['rate'], wind_speed, ent['stack_height'], stability_class, wind_rad, receptor_height, metres_per_pixel)
        elif etype == "line":
            x1, y1, x2, y2 = ent['x1'], ent['y1'], ent['x2'], ent['y2']
            total_q = ent['traffic_count'] * ent['emission_factor']
            steps = 10
            for i in range(steps + 1):
                px = x1 + (x2 - x1) * (i / steps)
                py = y1 + (y2 - y1) * (i / steps)
                total_concentration += gaussian_plume(X, Y_inv, px, py, total_q / (steps + 1), wind_speed, 2.0, stability_class, wind_rad, receptor_height, metres_per_pixel)
        elif etype == "area":
            dist_sq = (X - ent['x'])**2 + (Y_inv - ent['y'])**2
            mask = dist_sq <= ent['radius']**2
            total_concentration[mask] += ent['intensity']
        elif etype == "natural_sink":
            x, y, w, h = ent['x'], ent['y'], ent['width'], ent['height']
            mask = (X >= x) & (X <= x + w) & (Y_inv <= y) & (Y_inv >= y - h)
            total_concentration -= np.where(mask, ent['capture_density'], 0.0)
        elif etype == "artificial_sink":
            dist_sq = (X - ent['x'])**2 + (Y_inv - ent['y'])**2
            total_concentration -= np.where(dist_sq < 2.0, ent['capture_capacity'], 0.0)

    total_concentration = np.maximum(total_concentration, 0.0)
    max_c = np.max(total_concentration)
    if max_c > 0.0:
        return ((total_concentration / max_c) * 255.0).tolist()
    return total_concentration.tolist()
