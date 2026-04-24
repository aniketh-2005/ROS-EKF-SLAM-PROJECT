import numpy as np
from utils import wrap_angle

def motion_f(x, u, dt):
    """
    Nonlinear motion model for differential drive with v, w:
    x = [px, py, th]^T
    u = [v,  w]^T
    """
    px, py, th = x
    v, w = u
    px_n = px + v*dt*np.cos(th)
    py_n = py + v*dt*np.sin(th)
    th_n = wrap_angle(th + w*dt)
    return np.array([px_n, py_n, th_n])

def motion_Fx(x, u, dt):
    px, py, th = x
    v, w = u
    Fx = np.eye(3)
    Fx[0,2] = -v*dt*np.sin(th)
    Fx[1,2] =  v*dt*np.cos(th)
    return Fx

def motion_Fu(x, u, dt):
    th = x[2]
    Fu = np.zeros((3,2))
    Fu[0,0] = dt*np.cos(th)
    Fu[1,0] = dt*np.sin(th)
    Fu[2,1] = dt
    return Fu

def meas_h_range_bearing(x_robot, x_lm):
    """ Range-bearing measurement model: z = [r, b]^T """
    dx = x_lm[0] - x_robot[0]
    dy = x_lm[1] - x_robot[1]
    r = np.hypot(dx, dy)
    b = np.arctan2(dy, dx) - x_robot[2]
    b = wrap_angle(b)
    return np.array([r, b])

def meas_H_range_bearing(x_robot, x_lm, lm_index_in_state, n_landmarks):
    """ Jacobian H wrt full state [robot(3), lms(2*n)] """
    xr, yr, th = x_robot
    lx, ly = x_lm
    dx, dy = lx - xr, ly - yr
    q = dx**2 + dy**2
    r = np.sqrt(q) + 1e-9

    H = np.zeros((2, 3 + 2*n_landmarks))
    # w.r.t robot
    H[0,0] = -dx / r
    H[0,1] = -dy / r
    H[0,2] = 0.0

    H[1,0] = dy / q
    H[1,1] = -dx / q
    H[1,2] = -1.0

    # w.r.t the specific landmark
    idx = 3 + 2*lm_index_in_state
    H[0, idx+0] =  dx / r
    H[0, idx+1] =  dy / r

    H[1, idx+0] = -dy / q
    H[1, idx+1] =  dx / q

    return H

def meas_h_bearing_only(x_robot, x_lm):
    dx = x_lm[0] - x_robot[0]
    dy = x_lm[1] - x_robot[1]
    b = np.arctan2(dy, dx) - x_robot[2]
    return np.array([wrap_angle(b)])

def meas_H_bearing_only(x_robot, x_lm, lm_index_in_state, n_landmarks):
    xr, yr, th = x_robot
    lx, ly = x_lm
    dx, dy = lx - xr, ly - yr
    q = dx**2 + dy**2 + 1e-12

    H = np.zeros((1, 3 + 2*n_landmarks))
    H[0,0] =  dy / q
    H[0,1] = -dx / q
    H[0,2] = -1.0

    idx = 3 + 2*lm_index_in_state
    H[0, idx+0] = -dy / q
    H[0, idx+1] =  dx / q
    return H
