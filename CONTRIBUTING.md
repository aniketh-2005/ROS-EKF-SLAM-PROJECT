# Contributing to ROS-EKF-SLAM Project

Thank you for your interest in contributing to the ROS-EKF-SLAM Project!

## Development Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Code Style

- Follow PEP 8 guidelines for Python code
- Use meaningful variable names
- Add docstrings to functions and classes
- Keep functions focused and modular

## Testing

Before submitting changes:
```bash
python test_multi_robot.py
python test_viz.py
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Project Structure

- `main.py` - Entry point
- `ekf_slam.py` - Core EKF-SLAM implementation
- `models.py` - Motion and measurement models
- `simulator.py` - World simulation
- `viz.py` - Visualization engine
- `utils.py` - Utility functions
- `config.py` - Configuration parameters
