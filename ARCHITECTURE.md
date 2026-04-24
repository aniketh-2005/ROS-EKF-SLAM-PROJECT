# ROS-EKF-SLAM Project Architecture

## Overview

This project implements Extended Kalman Filter SLAM (Simultaneous Localization and Mapping) for differential drive robots with camera-based observations.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Main Entry                          │
│                        (main.py)                            │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌─────────┐   ┌──────────┐   ┌──────────┐
    │ Config  │   │Simulator │   │   Viz    │
    │         │   │          │   │          │
    └─────────┘   └────┬─────┘   └────┬─────┘
                       │              │
                       ▼              │
                  ┌─────────┐         │
                  │EKF-SLAM │         │
                  │         │         │
                  └────┬────┘         │
                       │              │
                       ▼              │
                  ┌─────────┐         │
                  │ Models  │         │
                  │         │         │
                  └─────────┘         │
                       │              │
                       ▼              ▼
                  ┌──────────────────────┐
                  │      Utils           │
                  └──────────────────────┘
```

## Core Components

### 1. EKF-SLAM (`ekf_slam.py`)
- **State Vector**: [x, y, θ, lm₁_x, lm₁_y, ..., lmₙ_x, lmₙ_y]
- **Prediction Step**: Uses motion model with process noise
- **Update Step**: Incorporates landmark observations
- **Data Association**: Matches observations to known landmarks
- **Landmark Initialization**: Adds new landmarks to state vector

### 2. Simulator (`simulator.py`)
- **World Model**: Fixed landmarks in 2D space
- **Robot Dynamics**: Differential drive kinematics
- **Sensor Model**: Camera with FOV and range limits
- **Noise Generation**: Process and measurement noise

### 3. Models (`models.py`)
- **Motion Model**: Differential drive kinematics
- **Measurement Model**: Range-bearing or bearing-only
- **Jacobians**: Analytical derivatives for EKF
- **Noise Models**: Gaussian process and measurement noise

### 4. Visualization (`viz.py`)
- **Real-time Rendering**: Pygame-based display
- **Uncertainty Visualization**: Covariance ellipses
- **Info Panel**: Live statistics and metrics
- **Trajectory Trails**: Historical path visualization

### 5. Configuration (`config.py`)
- **Simulation Parameters**: Time step, duration, world size
- **Noise Parameters**: Process and measurement noise levels
- **Sensor Parameters**: FOV, max range
- **Visualization Settings**: Window size, scaling

## Data Flow

1. **Initialization**
   - Load configuration
   - Initialize world with landmarks
   - Create robot at starting pose
   - Initialize EKF with robot state

2. **Simulation Loop**
   ```
   For each time step:
     1. Generate control input (v, ω)
     2. Update true robot pose (with noise)
     3. EKF Prediction step
     4. Generate observations (if landmarks in FOV)
     5. EKF Update step
     6. Render visualization
     7. Log metrics
   ```

3. **Output Generation**
   - Save trajectory plots
   - Save landmark comparison plots
   - Export final metrics to JSON

## Key Algorithms

### EKF Prediction
```
x̂⁻ = f(x̂, u)           # State prediction
P⁻ = F·P·Fᵀ + Q        # Covariance prediction
```

### EKF Update
```
ŷ = h(x̂⁻)              # Predicted measurement
S = H·P⁻·Hᵀ + R        # Innovation covariance
K = P⁻·Hᵀ·S⁻¹          # Kalman gain
x̂ = x̂⁻ + K·(z - ŷ)     # State update
P = (I - K·H)·P⁻       # Covariance update
```

## Multi-Robot Extension

### Collision Avoidance
- Repulsive force field between robots
- Minimum separation distance: `COLLISION_RADIUS`
- Force magnitude: `COLLISION_AVOIDANCE_GAIN`

### Independent EKF
- Each robot maintains its own state estimate
- Separate landmark maps (can be merged in future)
- No communication between robots (decentralized)

## Sensor Modes

### Range-Bearing Mode
- Measures distance and angle to landmarks
- Direct landmark initialization
- More accurate, faster convergence

### Bearing-Only Mode
- Measures only angle to landmarks
- Requires triangulation from multiple poses
- More challenging, realistic for cameras

## Performance Considerations

- **Computational Complexity**: O(n²) where n = number of landmarks
- **Memory Usage**: State vector grows with landmarks
- **Real-time Capability**: ~60 FPS with 4 landmarks
- **Scalability**: Tested up to 10 landmarks

## Future Enhancements

1. **Loop Closure Detection**: Recognize revisited areas
2. **Map Merging**: Combine maps from multiple robots
3. **Active SLAM**: Optimal path planning for exploration
4. **3D Extension**: Extend to 3D environments
5. **ROS Integration**: Connect to actual ROS ecosystem
