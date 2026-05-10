# app.py
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
from PIL import Image

from simulation import CityGrid
from emissions import PointSource, LineSource, AreaSource
from sinks import NaturalSink, ArtificialSink

# ----------------- STREAMLIT CONFIG ----------------- #
st.set_page_config(layout="wide", page_title="Urban CO₂ Digital Twin V3.1")
st.title("🏭 Urban CO₂ Digital Twin (v3.1)")
st.markdown("GIS-Enabled Simulation Tool: Upload a map, place high-precision sources/sinks, and simulate dispersion.")

# ----------------- SESSION STATE INIT ----------------- #
if "sources" not in st.session_state:
    st.session_state.sources = []   
if "sinks" not in st.session_state:
    st.session_state.sinks = []     
if "last_grid" not in st.session_state:
    st.session_state.last_grid = None
if "city_map" not in st.session_state:
    st.session_state.city_map = None

# ----------------- SIDEBAR: MAP & ATMOSPHERE ----------------- #
st.sidebar.header("1️⃣ City Board & Map")

uploaded_map = st.sidebar.file_uploader("Upload City Map (Image)", type=['png', 'jpg', 'jpeg'])
if uploaded_map:
    st.session_state.city_map = np.array(Image.open(uploaded_map))

grid_size = st.sidebar.slider("Grid Resolution (Map Size)", 50, 200, 100)

st.sidebar.header("2️⃣ Atmosphere")
col_w1, col_w2 = st.sidebar.columns(2)
with col_w1:
    wind_x = st.slider("Wind X", -1.0, 1.0, 0.2)
with col_w2:
    wind_y = st.slider("Wind Y", -1.0, 1.0, 0.0)

diffusion = st.sidebar.slider("Diffusion Rate D", 0.0, 0.25, 0.1, help="Must be ≤ 0.25 for explicit stability.")
steps = st.sidebar.number_input("Simulation Steps", min_value=50, max_value=5000, value=500, step=50)

# ----------------- SIDEBAR: INVENTORY ----------------- #
st.sidebar.header("📋 Active Inventory")
if st.sidebar.checkbox("Show Objects", value=True):
    if st.session_state.sources:
        st.sidebar.markdown("**Sources:**")
        for i, src in enumerate(st.session_state.sources):
            c1, c2 = st.sidebar.columns([4, 1])
            c1.caption(f"{src.name}")
            if c2.button("❌", key=f"del_src_{i}"):
                st.session_state.sources.pop(i)
                st.rerun()
    if st.session_state.sinks:
        st.sidebar.markdown("**Sinks:**")
        for i, sink in enumerate(st.session_state.sinks):
            c1, c2 = st.sidebar.columns([4, 1])
            c1.caption(f"{sink.name}")
            if c2.button("❌", key=f"del_snk_{i}"):
                st.session_state.sinks.pop(i)
                st.rerun()

# ----------------- BUILDER: EMISSION SOURCES ----------------- #
st.sidebar.header("3️⃣ Place Emission Sources")

# ---- Add Industry (PointSource) ---- #
with st.sidebar.expander("➕ Add Industry / Chimney (Point Source)"):
    ind_name = st.text_input("Industry Name", "Factory A", key="ind_name")
    col_ind1, col_ind2 = st.columns(2)
    with col_ind1:
        ind_x = st.number_input("X", 0, grid_size - 1, 20, key="ind_x")
    with col_ind2:
        ind_y = st.number_input("Y", 0, grid_size - 1, 20, key="ind_y")

    ind_emit = st.number_input("Emission Rate (unit / step)", 0.0, 1e6, 50.0, key="ind_emit")
    ind_stack = st.number_input("Stack Height (0 = ground)", 0, 10, 0, key="ind_stack")

    if st.button("Add Industry", key="btn_add_industry"):
        src = PointSource(x=ind_x, y=ind_y, emission_rate=ind_emit, stack_height=ind_stack, name=ind_name)
        st.session_state.sources.append(src)
        st.success(f"Added {ind_name}")

# ---- Add Road (LineSource) ---- #
with st.sidebar.expander("➕ Add Road / Highway (Line Source)"):
    road_name = st.text_input("Road Name", "Main Highway", key="road_name")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        r_start_x = st.number_input("Start X", 0, grid_size - 1, 10, key="r_start_x")
        r_start_y = st.number_input("Start Y", 0, grid_size - 1, 20, key="r_start_y")
    with col_r2:
        r_end_x = st.number_input("End X", 0, grid_size - 1, 80, key="r_end_x")
        r_end_y = st.number_input("End Y", 0, grid_size - 1, 20, key="r_end_y")

    traffic_count = st.number_input("Traffic Count (veh / step)", 0.0, 1e6, 200.0, key="traffic_count")
    emission_factor = st.number_input("Emission per Vehicle", 0.0, 1e3, 0.5, key="em_factor")

    if st.button("Add Road", key="btn_add_road"):
        src = LineSource(r_start_x, r_start_y, r_end_x, r_end_y, traffic_count, emission_factor, name=road_name)
        st.session_state.sources.append(src)
        st.success(f"Added {road_name}")

# ---- Add Area Source (Wildfire / Farm Burn) ---- #
with st.sidebar.expander("➕ Add Area Source (Fire / Burn)"):
    area_name = st.text_input("Area Source Name", "Wildfire Zone", key="area_name")
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        a_x = st.number_input("Center X", 0, grid_size - 1, 50, key="a_x")
        a_radius = st.number_input("Radius", 1, grid_size // 2, 10, key="a_radius")
    with col_a2:
        a_y = st.number_input("Center Y", 0, grid_size - 1, 50, key="a_y")
        a_intensity = st.number_input("Intensity per Cell", 0.0, 1e3, 5.0, key="a_intensity")

    if st.button("Add Area Source", key="btn_add_area"):
        src = AreaSource(a_x, a_y, a_radius, a_intensity, name=area_name)
        st.session_state.sources.append(src)
        st.success(f"Added {area_name}")

# ----------------- BUILDER: SINKS ----------------- #
st.sidebar.header("4️⃣ Place Sinks (Capture Units)")

# ---- Add Natural Sink (Forest / Park) ---- #
with st.sidebar.expander("🌳 Add Natural Sink (Forest / Park)"):
    forest_name = st.text_input("Forest Name", "City Park", key="forest_name")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        f_x = st.number_input("Top-left X", 0, grid_size - 1, 60, key="f_x")
        f_w = st.number_input("Width", 1, grid_size, 10, key="f_w")
    with col_f2:
        f_y = st.number_input("Top-left Y", 0, grid_size - 1, 40, key="f_y")
        f_h = st.number_input("Height", 1, grid_size, 10, key="f_h")

    density = st.number_input("Capture Density", 0.0, 1e3, 0.5, key="forest_density")

    if st.button("Add Natural Sink", key="btn_add_forest"):
        sink = NaturalSink(f_x, f_y, f_w, f_h, density, name=forest_name)
        st.session_state.sinks.append(sink)
        st.success(f"Added {forest_name}")

# ---- Add Artificial Sink (DAC / Filter) ---- #
with st.sidebar.expander("⚙️ Add Artificial Sink (DAC Unit)"):
    dac_name = st.text_input("Unit Name", "DAC 1", key="dac_name")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        d_x = st.number_input("X Loc", 0, grid_size - 1, 70, key="d_x")
    with col_d2:
        d_y = st.number_input("Y Loc", 0, grid_size - 1, 60, key="d_y")

    capacity = st.number_input("Capture Capacity", 0.0, 1e5, 10.0, key="dac_capacity")

    if st.button("Add Artificial Sink", key="btn_add_dac"):
        sink = ArtificialSink(d_x, d_y, capacity, name=dac_name)
        st.session_state.sinks.append(sink)
        st.success(f"Added {dac_name}")

# ----------------- MAIN: RUN SIMULATION ----------------- #
col_run, col_clear = st.columns([2, 1])
with col_run:
    run_clicked = st.button("🚀 Run Simulation", type="primary")
with col_clear:
    if st.button("🧹 Clear All Objects"):
        st.session_state.sources = []
        st.session_state.sinks = []
        st.session_state.last_grid = None
        st.rerun()

if run_clicked:
    city = CityGrid(size=grid_size)
    with st.spinner(f"Simulating {steps} steps on {grid_size}×{grid_size} grid..."):
        for t in range(int(steps)):
            city.add_emissions(st.session_state.sources)
            city.apply_sinks(st.session_state.sinks)
            city.update_physics(wind_x=wind_x, wind_y=wind_y, diffusion_rate=diffusion)

        st.session_state.last_grid = city.layers["CO2"].copy()

# ----------------- GIS VISUALIZATION ----------------- #
st.subheader("🗺️ Digital Twin Map")

fig, ax = plt.subplots(figsize=(10, 8))

# 1. Background Layer (City Map)
if st.session_state.city_map is not None:
    ax.imshow(st.session_state.city_map, extent=[0, grid_size, 0, grid_size], alpha=0.7)
else:
    ax.imshow(np.zeros((grid_size, grid_size)), extent=[0, grid_size, 0, grid_size], cmap="Greys", vmin=0, vmax=1, alpha=0.1)

# 2. Data Layer (CO2 Heatmap)
if st.session_state.last_grid is not None:
    im = ax.imshow(st.session_state.last_grid, origin="lower", extent=[0, grid_size, 0, grid_size], cmap="jet", alpha=0.6)
    fig.colorbar(im, ax=ax, label="CO₂ Concentration")

# 3. Vector Layer (Sources and Sinks)
pe = [PathEffects.withStroke(linewidth=2, foreground="black")]

for src in st.session_state.sources:
    if isinstance(src, PointSource):
        ax.plot(src.x, src.y, 'w*', markersize=12, markeredgecolor='black')
        ax.text(src.x, src.y + 2, src.name, color="white", fontsize=8, ha="center", path_effects=pe)
    elif isinstance(src, LineSource):
        ax.plot([src.start[0], src.end[0]], [src.start[1], src.end[1]], 'w--', linewidth=2, path_effects=pe)
    elif isinstance(src, AreaSource):
        circ = plt.Circle((src.cx, src.cy), src.radius, color='red', fill=False, linewidth=2, alpha=0.8)
        ax.add_patch(circ)

for sink in st.session_state.sinks:
    if isinstance(sink, NaturalSink):
        rect = plt.Rectangle((sink.x, sink.y), sink.width, sink.height, linewidth=2, edgecolor='lime', facecolor='green', alpha=0.3)
        ax.add_patch(rect)
        ax.text(sink.x, sink.y + sink.height + 1, sink.name, color="lime", fontsize=8, path_effects=pe)
    elif isinstance(sink, ArtificialSink):
        ax.plot(sink.x, sink.y, 's', color='lime', markersize=8, markeredgecolor='black')

ax.set_xlim(0, grid_size)
ax.set_ylim(0, grid_size)
ax.axis('off')

st.pyplot(fig)

# Metrics Output
if st.session_state.last_grid is not None:
    total_co2 = float(np.sum(st.session_state.last_grid))
    max_conc = float(np.max(st.session_state.last_grid))
    m1, m2, m3 = st.columns(3)
    m1.metric("Total CO₂ (Accumulated)", f"{total_co2:.1f}")
    m2.metric("Max Hotspot Concentration", f"{max_conc:.2f}")
    m3.metric("Active Elements", f"{len(st.session_state.sources)} Sources | {len(st.session_state.sinks)} Sinks")