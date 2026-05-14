# Urban CO₂ Digital Twin: Gaussian Plume Simulator

## Overview
The Urban CO₂ Digital Twin is a high-fidelity, decoupled spatial simulation tool designed to model the dispersion of carbon dioxide and other atmospheric pollutants in urban environments. 

Moving beyond basic finite-difference diffusion, this engine utilizes the EPA-standard **Gaussian Plume Model** to calculate steady-state pollutant concentrations downwind from continuous point sources (e.g., industrial stacks). The platform features a decoupled architecture, utilizing a high-speed Python/FastAPI backend for matrix calculations and a custom JavaScript/Canvas Heads-Up Display (HUD) for precision coordinate targeting and spatial visualization.

## Architecture
The system is strictly decoupled into two layers to ensure computational efficiency and UI flexibility:
1. **Simulation Engine (Backend):** Built with Python, NumPy, and FastAPI. It processes meteorological parameters (wind vectors, Pasquill-Gifford stability classes) and physical stack parameters (emission rate, effective stack height) to output precise dispersion matrices.
2. **Tactical HUD (Frontend):** A raw HTML/CSS/JS interface bypassing standard dashboard frameworks. It features a full-bleed interactive map canvas, allowing users to execute click-to-place point sources and receive real-time heatmap overlays.

## The Science: Gaussian Plume Implementation
The core physics engine evaluates the following analytical solution to the advection-diffusion equation:

$$C(x,y,z) = \frac{Q}{2\pi u \sigma_y \sigma_z} \exp\left(-\frac{y^2}{2\sigma_y^2}\right) \left[ \exp\left(-\frac{(z-H)^2}{2\sigma_z^2}\right) + \exp\left(-\frac{(z+H)^2}{2\sigma_z^2}\right) \right]$$

Where:
* `C` = Pollutant concentration
* `Q` = Emission rate
* `u` = Wind speed
* `H` = Effective stack height
* `σy, σz` = Dispersion coefficients based on atmospheric stability

## Installation & Execution

### 1. Boot the Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. Boot the Frontend (HUD)

Since the frontend is vanilla JS/HTML, you can serve it using a simple Python HTTP server:

```bash
cd frontend
python -m http.server 3000
```

Navigate to `http://localhost:3000` in your browser to access the HUD.

## Future Roadmap

* Integration of Line Sources (Traffic grids) using finite difference integration alongside the Gaussian model.
* Dynamic receptor placement for live time-series tracking of Parts Per Million (PPM) at specific spatial coordinates.
* Automated integration of live weather APIs for real-time wind and stability class calibration.
