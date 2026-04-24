import math

# --- Simulation toggles ---
USE_BEARING_ONLY = False   # If True: bearing-only "camera" and delayed landmark init via triangulation
NUM_LANDMARKS = 4
WORLD_SIZE = 20.0          # meters (world spans roughly [-W, +W] square)
SIM_STEPS = 600
DT = 0.1                   # seconds per step

# --- Multi-robot settings ---
MULTI_ROBOT_MODE = False   # Set at runtime via menu
COLLISION_RADIUS = 1.5     # meters - minimum distance between robots
COLLISION_AVOIDANCE_GAIN = 2.0  # repulsion strength

# Motion (control) profile
BASE_V = 0.4               # m/s
BASE_W = 0.3               # rad/s

# Noise std devs
PROC_NOISE_V = 0.05        # m/s (velocity noise)
PROC_NOISE_W = 0.03        # rad/s (angular vel noise)
PROC_NOISE_XY = 0.02       # m (additive perturb)
PROC_NOISE_TH = 0.01       # rad

MEAS_NOISE_R = 0.08        # meters (range noise)  - used if USE_BEARING_ONLY=False
MEAS_NOISE_B = 0.03        # rad (bearing noise)

# Sensor limits
MAX_RANGE = 12.0           # m
FOV = math.radians(180)    # +/- 90 deg FOV about heading

# Visualization
WINDOW_SCALE = 30          # pixels per meter
WINDOW_SIZE = (1400, 900)  # Width x Height (includes info panel)

# EKF parameters
ROBOT_INIT_COV = 0.1
LM_INIT_RANGE_GUESS = 4.0  # used if poor observability at init (range-bearing)
LM_INIT_COV = 3.0          # landmark init covariance (diag)

# Bearing-only init params
BO_MIN_BASELINE = 0.8      # need baseline for triangulation
BO_BUFFER = 10             # keep last N bearing obs per landmark id for triangulation

SAVE_OUTPUTS = True
