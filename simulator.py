import numpy as np
from dataclasses import dataclass
from utils import wrap_angle
import config as C

@dataclass
class RobotTruth:
    x: float
    y: float
    th: float

@dataclass
class Landmark:
    x: float
    y: float

class World:
    def __init__(self, num_landmarks, multi_robot=False):
        rng = np.random.default_rng(3)
        # spread landmarks in a square
        Ls = []
        for _ in range(num_landmarks):
            Ls.append(Landmark(float(rng.uniform(-C.WORLD_SIZE, C.WORLD_SIZE)),
                               float(rng.uniform(-C.WORLD_SIZE, C.WORLD_SIZE))))
        self.landmarks = Ls

        self.robot = RobotTruth(0.0, 0.0, 0.0)
        self.multi_robot = multi_robot
        
        # Second robot starts at different position
        if self.multi_robot:
            self.robot2 = RobotTruth(-5.0, -5.0, np.pi/4)
        else:
            self.robot2 = None
            
        self.t = 0.0
        self.rng = rng

    def _apply_collision_avoidance(self, robot, other_robot, v_cmd, w_cmd):
        """Apply repulsive force if robots are too close"""
        dx = robot.x - other_robot.x
        dy = robot.y - other_robot.y
        dist = np.hypot(dx, dy)
        
        if dist < C.COLLISION_RADIUS and dist > 0.01:
            # Repulsive force proportional to proximity
            repulsion = C.COLLISION_AVOIDANCE_GAIN * (C.COLLISION_RADIUS - dist) / dist
            
            # Modify velocity to move away
            angle_to_other = np.arctan2(dy, dx)
            angle_diff = wrap_angle(angle_to_other - robot.th)
            
            # Reduce forward velocity and add turning away
            v_cmd = v_cmd * 0.5
            w_cmd = w_cmd + np.sign(angle_diff) * repulsion * 0.5
            
        return v_cmd, w_cmd

    def step(self):
        # commanded
        v_cmd = C.BASE_V
        w_cmd = C.BASE_W * np.sin(0.1*self.t)

        # Apply collision avoidance if multi-robot mode
        if self.multi_robot and self.robot2 is not None:
            v_cmd, w_cmd = self._apply_collision_avoidance(self.robot, self.robot2, v_cmd, w_cmd)

        # add control noise
        v_noisy = v_cmd + self.rng.normal(0, C.PROC_NOISE_V)
        w_noisy = w_cmd + self.rng.normal(0, C.PROC_NOISE_W)

        # integrate kinematics
        self.robot.x += v_noisy*C.DT*np.cos(self.robot.th) + self.rng.normal(0, C.PROC_NOISE_XY)
        self.robot.y += v_noisy*C.DT*np.sin(self.robot.th) + self.rng.normal(0, C.PROC_NOISE_XY)
        self.robot.th = wrap_angle(self.robot.th + w_noisy*C.DT + self.rng.normal(0, C.PROC_NOISE_TH))

        # Update robot 2 if in multi-robot mode
        if self.multi_robot and self.robot2 is not None:
            v_cmd2 = C.BASE_V * 0.8  # Slightly different speed
            w_cmd2 = C.BASE_W * np.cos(0.12*self.t)  # Different motion pattern
            
            # Apply collision avoidance for robot 2
            v_cmd2, w_cmd2 = self._apply_collision_avoidance(self.robot2, self.robot, v_cmd2, w_cmd2)
            
            v_noisy2 = v_cmd2 + self.rng.normal(0, C.PROC_NOISE_V)
            w_noisy2 = w_cmd2 + self.rng.normal(0, C.PROC_NOISE_W)
            
            self.robot2.x += v_noisy2*C.DT*np.cos(self.robot2.th) + self.rng.normal(0, C.PROC_NOISE_XY)
            self.robot2.y += v_noisy2*C.DT*np.sin(self.robot2.th) + self.rng.normal(0, C.PROC_NOISE_XY)
            self.robot2.th = wrap_angle(self.robot2.th + w_noisy2*C.DT + self.rng.normal(0, C.PROC_NOISE_TH))

        self.t += C.DT

        return np.array([v_noisy, w_noisy]), np.array([self.robot.x, self.robot.y, self.robot.th])

    def sense(self):
        """Produce observations to visible landmarks.
        Returns list of tuples: (lm_id, z, R)
        - If range-bearing: z=[r,b], R=diag([sig_r^2, sig_b^2])
        - If bearing-only:  z=[b],   R=[sig_b^2]
        """
        obs = []
        xr, yr, th = self.robot.x, self.robot.y, self.robot.th

        for i, lm in enumerate(self.landmarks):
            dx, dy = lm.x - xr, lm.y - yr
            r = np.hypot(dx, dy)
            ang = np.arctan2(dy, dx) - th
            ang = wrap_angle(ang)

            # visibility by FOV and range (range check only for range-bearing mode)
            if abs(ang) <= C.FOV/2 and (not C.USE_BEARING_ONLY and r <= C.MAX_RANGE or C.USE_BEARING_ONLY):
                if C.USE_BEARING_ONLY:
                    b = ang + self.rng.normal(0, C.MEAS_NOISE_B)
                    z = np.array([wrap_angle(b)])
                    R = np.array([[C.MEAS_NOISE_B**2]])
                else:
                    rr = r + self.rng.normal(0, C.MEAS_NOISE_R)
                    bb = ang + self.rng.normal(0, C.MEAS_NOISE_B)
                    z = np.array([max(0.01, rr), wrap_angle(bb)])
                    R = np.diag([C.MEAS_NOISE_R**2, C.MEAS_NOISE_B**2])
                obs.append((i, z, R))
        return obs
    
    def sense_robot2(self):
        """Observations for robot 2"""
        if not self.multi_robot or self.robot2 is None:
            return []
        
        obs = []
        xr, yr, th = self.robot2.x, self.robot2.y, self.robot2.th

        for i, lm in enumerate(self.landmarks):
            dx, dy = lm.x - xr, lm.y - yr
            r = np.hypot(dx, dy)
            ang = np.arctan2(dy, dx) - th
            ang = wrap_angle(ang)

            if abs(ang) <= C.FOV/2 and (not C.USE_BEARING_ONLY and r <= C.MAX_RANGE or C.USE_BEARING_ONLY):
                if C.USE_BEARING_ONLY:
                    b = ang + self.rng.normal(0, C.MEAS_NOISE_B)
                    z = np.array([wrap_angle(b)])
                    R = np.array([[C.MEAS_NOISE_B**2]])
                else:
                    rr = r + self.rng.normal(0, C.MEAS_NOISE_R)
                    bb = ang + self.rng.normal(0, C.MEAS_NOISE_B)
                    z = np.array([max(0.01, rr), wrap_angle(bb)])
                    R = np.diag([C.MEAS_NOISE_R**2, C.MEAS_NOISE_B**2])
                obs.append((i, z, R))
        return obs
