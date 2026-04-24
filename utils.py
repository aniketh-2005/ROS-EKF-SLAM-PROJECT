import numpy as np

def wrap_angle(a):
    """Wrap angle to [-pi, pi]."""
    return (a + np.pi) % (2*np.pi) - np.pi

def block_diag(A, B):
    """Create block diagonal matrix from A and B."""
    Ap, Bp = np.asarray(A), np.asarray(B)
    out = np.zeros((Ap.shape[0]+Bp.shape[0], Ap.shape[1]+Bp.shape[1]))
    out[:Ap.shape[0], :Ap.shape[1]] = Ap
    out[Ap.shape[0]:, Ap.shape[1]:] = Bp
    return out

def rot2d(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s],[s, c]])
