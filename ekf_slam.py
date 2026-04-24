import numpy as np
from utils import wrap_angle, block_diag
from models import (motion_f, motion_Fx, motion_Fu,
                    meas_h_range_bearing, meas_H_range_bearing,
                    meas_h_bearing_only, meas_H_bearing_only)
import config as C

class EKFSLAM:
    def __init__(self, n_landmarks):
        self.nL = n_landmarks
        self.x = np.zeros(3 + 2*self.nL)  # [rx,ry,th, l1x,l1y, l2x,l2y, ...]
        self.P = np.eye(3 + 2*self.nL) * 1e6  # start with high uncertainty
        self.P[0:3,0:3] = np.eye(3)*C.ROBOT_INIT_COV
        self.lm_inited = np.zeros(self.nL, dtype=bool)

        # For bearing-only init: store recent (pose, bearing) per lm
        self.bo_buffers = {i: [] for i in range(self.nL)}

    def robot_state(self):
        return self.x[0:3]

    def lm_state(self, i):
        idx = 3 + 2*i
        return self.x[idx:idx+2]

    def predict(self, u):
        xr = self.robot_state().copy()
        xr_pred = motion_f(xr, u, C.DT)
        Fx = motion_Fx(xr, u, C.DT)

        # inject into full state
        self.x[0:3] = xr_pred

        # process noise for robot state
        Qr = np.diag([C.PROC_NOISE_XY**2, C.PROC_NOISE_XY**2, C.PROC_NOISE_TH**2])
        # Lift Fx
        F = np.eye(self.P.shape[0])
        F[0:3, 0:3] = Fx
        self.P = F @ self.P @ F.T
        self.P[0:3, 0:3] += Qr

        self.x[2] = wrap_angle(self.x[2])

    def _init_landmark_range_bearing(self, i, z):
        r, b = z
        rx, ry, th = self.robot_state()
        lx = rx + r*np.cos(th + b)
        ly = ry + r*np.sin(th + b)

        idx = 3 + 2*i
        self.x[idx:idx+2] = [lx, ly]
        self.lm_inited[i] = True

        # initialize covariance for that landmark
        self.P[idx:idx+2, idx:idx+2] = np.eye(2)*C.LM_INIT_COV

    def _try_init_bearing_only(self, i, z):
        """Store (pose, bearing); triangulate when baseline is big enough."""
        rx, ry, th = self.robot_state()
        self.bo_buffers[i].append((np.array([rx, ry, th]), float(z[0])))
        if len(self.bo_buffers[i]) < 2:
            return

        (p1, b1), (p2, b2) = self.bo_buffers[i][-2], self.bo_buffers[i][-1]
        r1 = np.array([np.cos(p1[2]+b1), np.sin(p1[2]+b1)])
        r2 = np.array([np.cos(p2[2]+b2), np.sin(p2[2]+b2)])
        # lines: L1: p1 + t*r1, L2: p2 + s*r2
        A = np.array([r1, -r2]).T
        bvec = p2[:2] - p1[:2]
        if np.linalg.cond(A) < 1e8:
            ts = np.linalg.lstsq(A, bvec, rcond=None)[0]
            t = ts[0]
            if np.linalg.norm(p2[:2]-p1[:2]) > C.BO_MIN_BASELINE:
                lm = p1[:2] + t*r1
                idx = 3 + 2*i
                self.x[idx:idx+2] = lm
                self.lm_inited[i] = True
                self.P[idx:idx+2, idx:idx+2] = np.eye(2)*C.LM_INIT_COV

    def update(self, obs_list):
        for (i, z, R) in obs_list:
            if C.USE_BEARING_ONLY:
                if not self.lm_inited[i]:
                    self._try_init_bearing_only(i, z)
                    if not self.lm_inited[i]:
                        continue
                h = meas_h_bearing_only(self.robot_state(), self.lm_state(i))
                H = meas_H_bearing_only(self.robot_state(), self.lm_state(i), i, self.nL)
            else:
                if not self.lm_inited[i]:
                    self._init_landmark_range_bearing(i, z)
                h = meas_h_range_bearing(self.robot_state(), self.lm_state(i))
                H = meas_H_range_bearing(self.robot_state(), self.lm_state(i), i, self.nL)

            y = z - h
            # angle wrap for bearing component
            if y.shape[0] == 2:
                y[1] = wrap_angle(y[1])
            else:
                y[0] = wrap_angle(y[0])

            S = H @ self.P @ H.T + R
            K = self.P @ H.T @ np.linalg.inv(S + 1e-9*np.eye(S.shape[0]))
            self.x = self.x + K @ y
            self.x[2] = wrap_angle(self.x[2])
            self.P = (np.eye(self.P.shape[0]) - K @ H) @ self.P
