"""
main.py — Urban CO₂ Digital Twin: FastAPI Simulation Engine (V4.2)
==================================================================
Supports multiple source geometries, sinks, and advanced global params.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List
import uvicorn

from physics import calculate_dispersion_grid

app = FastAPI(
    title="Urban CO₂ Physics Engine",
    version="4.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

class SimulationRequest(BaseModel):
    grid_size: int = Field(100, ge=50, le=500)
    wind_speed: float = Field(5.0, ge=0.1)
    wind_direction_deg: float = Field(270.0, ge=0, lt=360)
    stability_class: str = Field("D")
    receptor_height: float = Field(0.0, ge=0.0)
    metres_per_pixel: float = Field(10.0, ge=1.0)
    entities: List[dict] = []
    
    @validator("stability_class")
    def validate_stability(cls, v):
        allowed = {"A", "B", "C", "D", "E", "F"}
        if v.upper() not in allowed:
            raise ValueError(f"stability_class must be one of {allowed}")
        return v.upper()

class SimulationResponse(BaseModel):
    grid: list
    meta: dict

@app.post("/simulate", response_model=SimulationResponse)
async def run_simulation(data: SimulationRequest):
    try:
        grid = calculate_dispersion_grid(
            grid_size=data.grid_size,
            entities=data.entities,
            wind_speed=data.wind_speed,
            wind_dir_deg=data.wind_direction_deg,
            stability_class=data.stability_class,
            receptor_height=data.receptor_height,
            metres_per_pixel=data.metres_per_pixel
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Physics engine error: {str(exc)}")

    meta = {
        "grid_size": data.grid_size,
        "entity_count": len(data.entities),
        "wind_speed": data.wind_speed,
        "wind_dir_deg": data.wind_direction_deg,
        "stability_class": data.stability_class,
        "receptor_height": data.receptor_height,
        "metres_per_pixel": data.metres_per_pixel
    }

    return SimulationResponse(grid=grid, meta=meta)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
