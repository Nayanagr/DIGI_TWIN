# app.py
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from simulation import CityGrid
from emissions import PointSource, LineSource, AreaSource
from sinks import NaturalSink, ArtificialSink

# ----------------- STREAMLIT CONFIG ----------------- #
st.set_page_config(layout="wide", page_title="Urban CO₂ Digital Twin")
st.title("🏙️ CO₂ Simulation Tool")
st.markdown("Interactive prototype of your **Urban CO₂ Digital Twin** stack.")


# ----------------- SESSION STATE INIT ----------------- #
if "sources" not in st.session_state:
    st.session_state.sources = []   # list of EmissionSource (Point/Line/Area)
if "sinks" not in st.session_state:
    st.session_state.sinks = []     # list of CarbonSink
if "last_grid" not in st.session_state:
    st.session_state.last_grid = None


# ----------------- SIDEBAR CONFIG ----------------- #
st.sidebar.header("1️⃣ City Board")
grid_size = st.sidebar.slider("Map Size", 50, 200, 100)

st.sidebar.header("2️⃣ Atmosphere")
wind_x = st.sidebar.slider("Wind X", -1.0, 1.0, 0.2)
wind_y = st.sidebar.slider("Wind Y", -1.0, 1.0, 0.0)
diffusion = st.sidebar.slider("Diffusion Rate D", 0.0, 0.25, 0.1, help="Must be ≤ 0.25 for explicit stability.")
steps = st.sidebar.number_input("Simulation Steps", min_value=50, max_value=5000, value=500, step=50)


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
        src = PointSource(
            x=ind_x,
            y=ind_y,
            emission_rate=ind_emit,
            stack_height=ind_stack,
            name=ind_name,
        )
        st.session_state.sources.append(src)
        st.success(f"Added Industry: {ind_name} at ({ind_x}, {ind_y})")


# ---- Add Road (LineSource) ---- #
with st.sidebar.expander("➕ Add Road / Highway (Line Source)"):
    road_name = st.text_input("Road Name", "Road 1", key="road_name")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        r_start_x = st.number_input("Start X", 0, grid_size - 1, 10, key="r_start_x")
        r_start_y = st.number_input("Start Y", 0, grid_size - 1, 20, key="r_start_y")
    with col_r2:
        r_end_x = st.number_input("End X", 0, grid_size - 1, 80, key="r_end_x")
        r_end_y = st.number_input("End Y", 0, grid_size - 1, 20, key="r_end_y")

    traffic_count = st.number_input("Traffic Count (veh / step)", 0.0, 1e6, 200.0, key="traffic_count")
    emission_factor = st.number_input("Emission per Vehicle (unit / veh / step)", 0.0, 1e3, 0.5, key="em_factor")

    if st.button("Add Road", key="btn_add_road"):
        src = LineSource(
            start_x=r_start_x,
            start_y=r_start_y,
            end_x=r_end_x,
            end_y=r_end_y,
            traffic_count=traffic_count,
            emission_factor=emission_factor,
            name=road_name,
        )
        st.session_state.sources.append(src)
        st.success(f"Added Road: {road_name} from ({r_start_x}, {r_start_y}) to ({r_end_x}, {r_end_y})")


# ---- Add Area Source (Wildfire / Farm Burn) ---- #
with st.sidebar.expander("➕ Add Area Source (Fire / Burn)"):
    area_name = st.text_input("Area Source Name", "Wildfire Zone", key="area_name")
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        a_x = st.number_input("Center X", 0, grid_size - 1, 50, key="a_x")
        a_radius = st.number_input("Radius", 1, grid_size // 2, 10, key="a_radius")
    with col_a2:
        a_y = st.number_input("Center Y", 0, grid_size - 1, 50, key="a_y")
        a_intensity = st.number_input("Intensity per Cell (unit/step)", 0.0, 1e3, 5.0, key="a_intensity")

    if st.button("Add Area Source", key="btn_add_area"):
        src = AreaSource(
            center_x=a_x,
            center_y=a_y,
            radius=a_radius,
            intensity=a_intensity,
            name=area_name,
        )
        st.session_state.sources.append(src)
        st.success(f"Added Area Source: {area_name} at ({a_x}, {a_y}), r={a_radius}")


# ----------------- BUILDER: SINKS ----------------- #
st.sidebar.header("4️⃣ Place Sinks (Capture Units)")

# ---- Add Natural Sink (Forest / Park) ---- #
with st.sidebar.expander("🌳 Add Natural Sink (Forest / Park)"):
    forest_name = st.text_input("Forest Name", "Forest A", key="forest_name")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        f_x = st.number_input("Top-left X", 0, grid_size - 1, 60, key="f_x")
        f_w = st.number_input("Width", 1, grid_size, 10, key="f_w")
    with col_f2:
        f_y = st.number_input("Top-left Y", 0, grid_size - 1, 40, key="f_y")
        f_h = st.number_input("Height", 1, grid_size, 10, key="f_h")

    density = st.number_input("Capture Density (unit / cell / step)", 0.0, 1e3, 0.5, key="forest_density")

    if st.button("Add Natural Sink", key="btn_add_forest"):
        sink = NaturalSink(
            x=f_x,
            y=f_y,
            width=f_w,
            height=f_h,
            density=density,
            name=forest_name,
        )
        st.session_state.sinks.append(sink)
        st.success(f"Added Natural Sink: {forest_name} at ({f_x}, {f_y}), {f_w}×{f_h}")


# ---- Add Artificial Sink (DAC / Filter) ---- #
with st.sidebar.expander("⚙️ Add Artificial Sink (DAC Unit / Filter)"):
    dac_name = st.text_input("Unit Name", "DAC 1", key="dac_name")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        d_x = st.number_input("X", 0, grid_size - 1, 70, key="d_x")
    with col_d2:
        d_y = st.number_input("Y", 0, grid_size - 1, 60, key="d_y")

    capacity = st.number_input("Capture Capacity (unit / step)", 0.0, 1e5, 10.0, key="dac_capacity")

    if st.button("Add Artificial Sink", key="btn_add_dac"):
        sink = ArtificialSink(
            x=d_x,
            y=d_y,
            capacity=capacity,
            name=dac_name,
        )
        st.session_state.sinks.append(sink)
        st.success(f"Added Artificial Sink: {dac_name} at ({d_x}, {d_y})")


# ----------------- MAIN: RUN SIMULATION ----------------- #
col_run, col_clear = st.columns([2, 1])
with col_run:
    run_clicked = st.button("🚀 Run Simulation", type="primary")
with col_clear:
    if st.button("🧹 Clear All Objects"):
        st.session_state.sources = []
        st.session_state.sinks = []
        st.session_state.last_grid = None
        st.success("Cleared all sources and sinks.")

if run_clicked:
    if not st.session_state.sources:
        st.warning("No emission sources placed yet. Add at least one industry, road, or area source.")
    else:
        city = CityGrid(size=grid_size)

        with st.spinner(f"Simulating {steps} steps on {grid_size}×{grid_size} grid..."):
            for t in range(int(steps)):
                city.add_emissions(st.session_state.sources)
                city.apply_sinks(st.session_state.sinks)
                city.update_physics(wind_x=wind_x, wind_y=wind_y, diffusion_rate=diffusion)

            co2_grid = city.layers["CO2"]
            st.session_state.last_grid = co2_grid.copy()

        st.success("Simulation complete!")


# ----------------- VISUALIZATION ----------------- #
st.subheader("🛰️ CO₂ Field")

if st.session_state.last_grid is not None:
    co2_grid = st.session_state.last_grid
    total_co2 = float(np.sum(co2_grid))
    max_conc = float(np.max(co2_grid))

    m1, m2, m3 = st.columns(3)
    m1.metric("Total CO₂ (arb. units)", f"{total_co2:.1f}")
    m2.metric("Max Cell Concentration", f"{max_conc:.2f}")
    m3.metric("Objects", f"{len(st.session_state.sources)} sources, {len(st.session_state.sinks)} sinks")

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(co2_grid, origin="lower", cmap="jet")
    fig.colorbar(im, ax=ax, label="CO₂ Concentration (arb. units)")

    # Overlays: sources and sinks
    for src in st.session_state.sources:
        if isinstance(src, PointSource):
            ax.plot(src.x, src.y, 'w*', markersize=10, markeredgecolor='black')
            ax.text(src.x, src.y + 1, src.name, color="white", fontsize=7, ha="center")
        elif isinstance(src, LineSource):
            xs = [p[0] for p in src.pixels]
            ys = [p[1] for p in src.pixels]
            ax.scatter(xs, ys, s=3, c='white', alpha=0.4)
        elif isinstance(src, AreaSource):
            circ = plt.Circle((src.cx, src.cy), src.radius, color='white', fill=False, alpha=0.4, linewidth=1)
            ax.add_patch(circ)

    for sink in st.session_state.sinks:
        if isinstance(sink, NaturalSink):
            x0, y0 = sink.x, sink.y
            rect = plt.Rectangle((x0, y0), sink.width, sink.height,
                                 linewidth=1, edgecolor='lime', facecolor='none', alpha=0.7)
            ax.add_patch(rect)
        elif isinstance(sink, ArtificialSink):
            ax.plot(sink.x, sink.y, 'gs', markersize=7, markeredgecolor='black')

    ax.set_xlim(0, grid_size - 1)
    ax.set_ylim(0, grid_size - 1)
    ax.set_title(f"CO₂ Field (Steps={steps}, Wind=({wind_x}, {wind_y}), D={diffusion})")
    st.pyplot(fig)
else:
    st.info("Run a simulation to see the CO₂ field.")
