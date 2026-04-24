# EKF-SLAM (Camera-Based) — CS3112 PL CIE-3 Project

This repository implements a **camera-based Extended Kalman Filter SLAM** for a differential drive robot
with a 2D simulator and **Pygame** visualization. It follows the requirements from the provided brief:
- Differential-drive motion model
- Simulated 2D world with fixed **3–4 landmarks**
- Noisy **camera observations** (range+bearing or bearing-only)
- Full **EKF-SLAM** (prediction + update) with a joint robot+landmark state vector
- **Pygame** display of true/estimated robot poses, true/estimated landmarks, and **uncertainty ellipses**
- Saved plots of **true vs estimated trajectories** and **landmarks**

## 🆕 Multi-Robot Mode with Collision Avoidance

**NEW FEATURE**: Choose between single-robot mode (original) or multi-robot mode with collision avoidance!
- Interactive menu at startup
- Two robots with independent EKF-SLAM
- Real-time collision avoidance using repulsive forces
- Different motion patterns for each robot
- See [MULTI_ROBOT_GUIDE.md](MULTI_ROBOT_GUIDE.md) for details

## 1) Quick Start

```bash
# 1) (Optional) create a virtualenv
python3 -m venv .venv && source .venv/bin/activate

# 2) Install deps
pip install -r requirements.txt

# 3) Run the simulation
python main.py
```

**You'll see a menu** - choose your mode:
- **Single Robot Mode**: Original EKF-SLAM (unchanged)
- **Multi-Robot Mode**: Two robots with collision avoidance (new!)

The app opens a Pygame window with advanced visualization and runs the simulation for a fixed number of steps.
It also saves plots to `outputs/`.

### Quick Demo

```bash
# Run automated demo showing both modes
python demo_multi_robot.py

# Test multi-robot functionality
python test_multi_robot.py
```

### Additional Scripts

```bash
# Run comprehensive demo of all features
python demo_all.py

# Test the visualization independently
python test_viz.py

# Generate a demo screenshot
python generate_demo_screenshot.py

# Create an animated GIF of the simulation
python save_animation.py

# Compare Range-Bearing vs Bearing-Only modes
python compare_modes.py
```

## 2) Controls & Config

### Keyboard Controls
- **SPACE**: Pause/Resume simulation
- **ESC**: Exit simulation

### Configuration (`config.py`)
- `USE_BEARING_ONLY = False`: If `True`, use bearing-only camera (needs reobservations from different poses).
- `NUM_LANDMARKS = 4`: Count of landmarks in the world.
- `SIM_STEPS = 600`: Number of time-steps to simulate.
- Process & measurement noise levels.
- Field-of-view, max range, dt, etc.

### Visualization Features
- **Real-time Info Panel**: Displays simulation stats, robot state (true & estimated), errors, and uncertainty metrics
- **Grid Background**: Realistic coordinate grid with major/minor lines
- **Field of View (FOV)**: Semi-transparent cone showing camera's visible area
- **Trajectory Trails**: Gradient paths showing robot movement history
- **Observation Lines**: Yellow dashed lines from robot to observed landmarks
- **Uncertainty Ellipses**: Multi-level confidence ellipses (1σ, 2σ, 3σ) for robot and landmarks
- **Enhanced Robot Graphics**: Detailed robot with body, wheels, and directional arrow
- **Landmark Markers**: True landmarks (circles) vs estimated landmarks (squares) with IDs
- **Legend**: Color-coded legend for all visual elements

### During the Run
- The robot follows a velocity profile and steers with sinusoidal angular velocity to create excitation.
- Observations are only generated for landmarks inside the **FOV** and **max_range** (for range-bearing mode).
- The info panel updates in real-time showing position errors and covariance values.

## 3) Project Structure

```
ekf_slam_project/
├── main.py                 # Entry point
├── ekf_slam.py             # EKF-SLAM class
├── models.py               # Motion & measurement models + Jacobians
├── simulator.py            # World, robot truth, noise models, observation generation
├── viz.py                  # Pygame rendering + uncertainty ellipses
├── utils.py                # Math helpers
├── config.py               # Central config switches & constants
├── requirements.txt
├── README.md
└── report_template.md      # Fill-in report template for submission
```

## 4) Outputs

All outputs are saved to the `outputs/` directory:

### Automatic Outputs (from main.py)
- `trajectory.png` — True vs estimated robot path with landmarks
- `landmarks.png` — True vs estimated landmark positions with covariance ellipses
- `final_state.json` — Final metrics (RMSE, number of initialized landmarks, mode)

### Optional Outputs
- `demo_screenshot.png` — Single frame showing all visualization features (run `generate_demo_screenshot.py`)
- `ekf_slam_demo.gif` — Animated GIF of the entire simulation (run `save_animation.py`)
- `mode_comparison.png` — Side-by-side comparison of Range-Bearing vs Bearing-Only modes (run `compare_modes.py`)

## 5) Notes

- **Bearing-only** initialization is handled by delaying the addition of a landmark until multiple bearings from different poses are fused to triangulate (simple linear triangulation with a sliding buffer). Set `USE_BEARING_ONLY=True` to enable it.
- For standard grading and smooth demo, we default to **range+bearing** mode.
- Numerical stability: small epsilons are added when inverting matrices; angles normalized to [-pi, pi].

## 6) Advanced Features

This implementation includes several advanced features beyond the basic requirements:

### Professional Visualization
- **Realistic robot model** with body, wheels, and directional arrow
- **3D-styled landmarks** with shadows and unique IDs
- **Multi-level uncertainty ellipses** (1σ, 2σ, 3σ) for robot and landmarks
- **Field of View cone** showing camera's visible area
- **Trajectory trails** with gradient coloring
- **Observation indicators** (dashed lines to observed landmarks)
- **Professional grid system** with coordinate axes

### Real-Time Information Panel
- Simulation progress (step, time, mode)
- Robot state (true and estimated positions/heading)
- Position and heading errors
- Landmark initialization status
- Uncertainty metrics (covariance values)
- FPS counter
- Color-coded legend

### Interactive Controls
- **SPACE**: Pause/Resume simulation
- **ESC**: Exit simulation
- Real-time pause indicator

### Multiple Output Formats
- High-resolution plots (trajectory, landmarks)
- JSON metrics file
- Demo screenshots
- Animated GIF export
- Mode comparison analysis

### Dual Sensor Modes
- **Range-Bearing**: Direct landmark initialization
- **Bearing-Only**: Triangulation-based initialization with baseline checking

For detailed documentation, see:
- `VISUALIZATION_ENHANCEMENTS.md` - Complete feature documentation
- `FEATURES.md` - Full feature list
- `ENHANCEMENTS_SUMMARY.md` - Before/after comparison

## 7) License

For coursework use. Modify as needed.
