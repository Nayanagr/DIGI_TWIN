# Case Study: Building the Urban CO₂ Digital Twin
## A Journey from Physics Scripts to Interactive Urban Simulation

### Introduction: Why Model CO₂?
This project, nicknamed **TWIN**, wasn't just about writing code; it was about understanding the invisible. How does a factory plume actually move through a city? If we plant a forest on the north side, does it help the south? 

What follows is the "lab notebook" of this project—a documented history of every version, every experiment, and the lessons learned along the way.

---

### Phase 1: The "Lab Bench" Experiments (v0.1 – v0.4)
Before there was a dashboard, there was just raw math. I spent these first few versions making sure the physics felt "real."

#### Experiment 1: The "Drop of Ink" (v0.1)
*   **The Goal**: Can I simulate basic diffusion on a 2D grid?
*   **The Method**: I placed a single high-concentration point of CO₂ in the center of a static grid and applied a Laplacian filter.
*   **The Result**: It worked! The CO₂ spread out in a perfect circle, much like a drop of ink in water.
*   **Visual Evidence**:
    ![Fig 1: Initial Point Source Diffusion](assets/image1.png)
    *Caption: The early stages of the model showing a concentrated source gradually bleeding into the surrounding environment.*

#### Experiment 2: Adding the Wind (v0.2)
*   **The Goal**: Real cities have wind. I needed to move that "ink drop."
*   **The Method**: Introduced an **Advection** scheme. Instead of just spreading out, the CO₂ now had a velocity vector.
*   **The Lesson**: My first attempt caused some weird "oscillations" at the edges. I had to implement an **Upwind Scheme** to keep the smoke moving smoothly in one direction.
*   **Visual Evidence**:
    ![Fig 2: Advection and Wind Drift](assets/image4.png)
    *Caption: Notice how the plume now stretches and "leans" in the direction of the wind—much more realistic.*

#### Experiment 3: The Chimney Problem (v0.3 & v0.4)
*   **The Goal**: Factories don't emit CO₂ at ground level. They have tall stacks.
*   **The Method**: I added "Stack Height" logic. If a source is "tall," its CO₂ is immediately distributed over a wider area (simulating the plume touching down further away).
*   **The Result**: This made the heatmap much more complex. I also added a **CFL Stability Check** because if I turned the wind up too high, the whole simulation would crash!
*   **Visual Evidence**:
    ![Fig 3: Stack Height and Dispersion](assets/image5.png)
    *Caption: Comparing how a ground-level source stays concentrated vs. how a tall stack spreads the load.*

---

### Phase 2: Building the Interface (v1.0)
Once the math was solid, it was time to let other people play with it. I moved the project into **Streamlit**.

*   **The Big Change**: I separated the "Brain" (physics) from the "Body" (UI).
*   **The Feature**: Live sliders. For the first time, I could grab a slider for "Wind X" and watch the plume move in real-time. It changed from a script to a *tool*.

---

### Phase 3: The Modular City (v2.0 – v3.0)
This is the current state of TWIN. I realized that a city isn't just one factory—it’s a network of roads, parks, and buildings.

#### The "City Builder" Inventory
I refactored the code so that everything is a "Module." You can now "paint" your city with:
1.  **Line Sources**: These represent roads. I used a rasterization algorithm to turn a road line into a series of emitting pixels. 
    ![Fig 4: Road/Line Source Modeling](assets/image2.png)
2.  **Carbon Sinks**: This was the most rewarding part. I added "Natural Sinks" (forests) that actually *subtract* CO₂ from the grid.

---

### Phase 4: Applied Research — The Damoh Case Study (v3.1)
In version 3.1, I moved from theoretical grids to a real-world application: **Damoh, India**. This experiment was designed to model the emissions from major industrial clusters and the urban core, testing various mitigation strategies.

#### The Parameters
| Parameter | Value |
| :--- | :--- |
| **Wind X** | 0.22 (Eastward) |
| **Wind Y** | -0.08 (Southward) |
| **Diffusion** | 0.11 |
| **Simulation Steps** | 1000 |

#### The Emission Inventory
*   **Mycem NW "Main"**: Industrial point source (Rate: 120, Stack: 7).
*   **Heidelberg Cement**: Major industrial source (Rate: 180, Stack: 9).
*   **Urban Damoh**: Modeled as an area source (Radius: 12, Intensity: 1.8 units/step).
*   **NH34 (Main Road)**: A heavy-traffic corridor (Traffic: 28,000, Emission Factor: 0.045).

#### Experiment 4: The Baseline (No Mitigation)
Before adding capture tech, I ran the simulation to see the "business as usual" scenario. The industrial plumes from Mycem and Heidelberg merged with the urban core emissions, creating a significant pollution corridor.
![Fig 5: Damoh Baseline Emissions](assets/image6.png)
*Caption: The full emission profile of Damoh without any intervention.*

#### Experiment 5: Mitigation via Natural Sinks & Technology
I then introduced targeted "Sinks" to see if we could "scrub" the air:
1.  **Rajnagar Wetland Sink**: A natural area (12x10) with a capture density of 0.35 unit/step.
2.  **Industrial Green Belt**: A strategic forest buffer (18x10) with 0.42 unit/step capture.
3.  **DAC Deployment**: I placed Direct Air Capture (DAC) units at coordinates (50,50), (51,51), (52,52), and (52,53) with a massive 14 unit/step capture intensity.

![Fig 6: Impact of Sinks and DAC](./assets/image8.png)
*Caption: The air quality significantly improves near the DAC deployment zones and the Green Belt.*

---

### Technical Specification (The "Boring" But Important Stuff)
If you're looking to replicate these experiments, here is the technical stack:

*   **The Grid**: A 2D NumPy array.
*   **The Physics**: 
    *   **Diffusion**: $\Delta C = D \nabla^2 C \Delta t$
    *   **Advection**: $C_{new} = C - (u_x \frac{\Delta C}{\Delta x} + u_y \frac{\Delta C}{\Delta y})$
*   **The Boundaries**: I implemented "Open Boundaries" in v3.0. This means when CO₂ hits the edge of your screen, it "blows away" instead of piling up like snow against a wall.

---

### Conclusion: What's Next?
This project started as a simple curiosity about how things spread. Today, it’s a framework that can model anything from a small neighborhood forest to a major industrial zone like Damoh. 

**Want to run your own experiment?**
Check out `v3.0/app.py`, upload a map of your hometown, and see what happens when you add a forest next to the highway.

---
*Documented by the TWIN Development Team.*
*Part of the 100-Days-of-Programming Initiative.*
