import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import phy_eng as phys

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Urban CO2 Twin", layout="wide")

st.title("CO₂ Digital Twin")
st.markdown("### Interactive Simulation Dashboard")

# --- SIDEBAR: CONTROLS ---
with st.sidebar:
    st.header("Simulation Parameters")

    # 1. Atmospheric Conditions
    st.subheader("Atmosphere")
    col1, col2 = st.columns(2)
    with col1:
        wind_x = st.slider("Wind X (East/West)", -1.0, 1.0, 0.2, step=0.05)
    with col2:
        wind_y = st.slider("Wind Y (North/South)", -1.0, 1.0, 0.05, step=0.05)

    D = st.slider("Diffusion Rate", 0.0, 0.25, 0.1, help="Higher = Faster spread. Max 0.25.")
    steps = st.number_input("Simulation Steps", min_value=100, max_value=5000, value=500)

    # 2. City Infrastructure Builder (Simple Toggles for now)
    st.subheader("City Layout")
    show_industries = st.checkbox("Active Industries", value=True)
    show_roads = st.checkbox("Active Roads", value=True)
    show_captures = st.checkbox("Active Capture Units", value=False)

# --- MAIN LOGIC ---

if st.button("🚀 Run Simulation", type="primary"):

    # 1. Safety Check (Using your physics engine)
    if not phys.check_cfl_condition(D, wind_x, wind_y):
        st.error("⚠️ **Stability Warning:** The parameters provided violate the CFL condition. "
                 "Please reduce Wind Speed or Diffusion Rate.")
    else:
        # 2. Build the Scenario (The "Model")
        industries = []
        roads = []
        captures = []

        if show_industries:
            industries.append(phys.Industry(20, 50, emission_rate=50.0,
                                            name="Power Plant", stack_height=0))
            industries.append(phys.Industry(40, 30, emission_rate=35.0,
                                            name="Factory", stack_height=3))

        if show_roads:
            roads.append(phys.Road(10, 20, 80, 20, emission_rate=50.0, name="Highway A"))
            roads.append(phys.Road(15, 10, 15, 70, emission_rate=30.0, name="Ave B"))

        if show_captures:
            captures.append(phys.CarbonCapture(60, 40, efficiency=1.0, name="Central Park"))
            captures.append(phys.CarbonCapture(70, 60, efficiency=1.5, name="Green Belt"))

        # 3. Execution (The "Controller")
        with st.spinner(f"Simulating {steps} time steps..."):
            final_grid = phys.run_simulation(
                industries=industries,
                steps=steps,
                D=D,
                wind_x=wind_x,
                wind_y=wind_y,
                roads=roads,
                captures=captures,
            )

        # 4. Visualization (The "View")
        st.success("Simulation Complete!")

        # Metrics Row
        total_co2 = np.sum(final_grid)
        max_conc = np.max(final_grid)

        m1, m2, m3 = st.columns(3)
        m1.metric("Total CO₂", f"{total_co2:.0f}")
        m2.metric("Max Concentration", f"{max_conc:.2f}")
        m3.metric("Sources Active", f"{len(industries) + len(roads)}")

        # Plotting
        fig, ax = plt.subplots(figsize=(10, 6))

        # Heatmap
        im = ax.imshow(final_grid, origin='lower', cmap='jet', vmin=0, vmax=20)
        fig.colorbar(im, ax=ax, label='CO₂ Concentration')

        # Overlay: Industries
        for s in industries:
            ax.plot(s.x, s.y, 'w*', markersize=12, markeredgecolor='black')
            ax.text(s.x, s.y + 2, s.name, color='white',
                    ha='center', fontsize=8, fontweight='bold')

        # Overlay: Roads
        for r in roads:
            xs = [p[0] for p in r.pixels]
            ys = [p[1] for p in r.pixels]
            ax.scatter(xs, ys, s=2, c='white', alpha=0.3)

        # Overlay: Captures
        for c in captures:
            ax.plot(c.x, c.y, 'gs', markersize=8, markeredgecolor='black')
            ax.text(c.x, c.y + 2, c.name, color='white',
                    ha='center', fontsize=7)

        ax.set_title(f"CO₂ Dispersion Map (Steps: {steps})")

        st.pyplot(fig)
