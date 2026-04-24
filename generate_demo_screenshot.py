#!/usr/bin/env python3
"""
Generate a demo screenshot showing the enhanced visualization
This creates a single frame showing all features
"""
import pygame
import numpy as np
from viz import (init_viz, draw_grid, draw_robot, draw_landmark, 
                 draw_ellipse, draw_trajectory, draw_observation_lines, 
                 draw_info_panel, to_screen)
import config as C

def generate_demo():
    pygame.init()
    screen = pygame.display.set_mode(C.WINDOW_SIZE)
    pygame.display.set_caption("EKF-SLAM Demo Screenshot")
    init_viz()
    
    # Create demo data
    true_traj = []
    est_traj = []
    
    # Generate circular trajectory
    for i in range(100):
        t = i * 0.1
        true_traj.append(np.array([
            8 * np.cos(t),
            8 * np.sin(t),
            t
        ]))
        # Add some error to estimated trajectory
        est_traj.append(np.array([
            8 * np.cos(t) + 0.3 * np.sin(3*t),
            8 * np.sin(t) + 0.3 * np.cos(3*t),
            t + 0.1 * np.sin(2*t)
        ]))
    
    # Current robot poses
    robot_true = true_traj[-1]
    robot_est = est_traj[-1]
    
    # Landmarks
    landmarks_true = [
        (10, 10),
        (-10, 10),
        (-10, -10),
        (10, -10)
    ]
    
    landmarks_est = [
        (10.2, 9.8),
        (-9.9, 10.1),
        (-10.1, -9.9),
        (9.8, -10.2)
    ]
    
    # Mock observations (robot can see landmarks 0 and 1)
    class MockLandmark:
        def __init__(self, x, y):
            self.x = x
            self.y = y
    
    mock_landmarks = [MockLandmark(x, y) for x, y in landmarks_true]
    observations = [
        (0, np.array([1.0, 0.5]), np.eye(2)),
        (1, np.array([1.2, -0.3]), np.eye(2))
    ]
    
    # Mock EKF
    class MockEKF:
        def __init__(self):
            self.P = np.eye(11) * 0.3
            self.P[0:2, 0:2] = np.array([[0.2, 0.05], [0.05, 0.15]])
            self.lm_inited = np.array([True, True, True, True])
    
    ekf = MockEKF()
    
    # Draw everything
    screen.fill((245, 245, 250))
    
    # Grid
    draw_grid(screen)
    
    # Trajectories
    draw_trajectory(screen, true_traj, color=(30, 30, 220))
    draw_trajectory(screen, est_traj, color=(220, 80, 0))
    
    # Observation lines
    draw_observation_lines(screen, robot_true, mock_landmarks, observations)
    
    # Landmarks with ellipses
    for i, (lm_true, lm_est) in enumerate(zip(landmarks_true, landmarks_est)):
        # Estimated landmark with uncertainty
        cov = np.array([[0.4, 0.1], [0.1, 0.3]])
        draw_ellipse(screen, np.array(lm_est), cov, color=(0, 120, 0))
        draw_landmark(screen, lm_est, (0, 180, 0), est=True, lm_id=i)
        
        # True landmark
        draw_landmark(screen, lm_true, (0, 140, 0), est=False, lm_id=i)
    
    # Robot uncertainty
    draw_ellipse(screen, robot_est[:2], ekf.P[0:2, 0:2], color=(200, 0, 0))
    
    # Robots
    draw_robot(screen, robot_est, (220, 80, 0), est=True, draw_fov=False)
    draw_robot(screen, robot_true, (30, 30, 220), est=False, draw_fov=True)
    
    # Info panel
    draw_info_panel(screen, 100, 0.35, 4, robot_true, robot_est, ekf)
    
    # Save screenshot
    pygame.display.flip()
    pygame.image.save(screen, "outputs/demo_screenshot.png")
    print("✓ Demo screenshot saved to outputs/demo_screenshot.png")
    
    # Keep window open for a moment
    pygame.time.wait(2000)
    pygame.quit()

if __name__ == '__main__':
    import os
    os.makedirs("outputs", exist_ok=True)
    generate_demo()
