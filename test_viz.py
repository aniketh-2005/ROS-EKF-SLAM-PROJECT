#!/usr/bin/env python3
"""
Quick test script to verify the enhanced visualization works
"""
import pygame
import numpy as np
from viz import init_viz, draw_grid, draw_robot, draw_landmark, draw_ellipse, draw_info_panel
import config as C

def test_visualization():
    pygame.init()
    screen = pygame.display.set_mode(C.WINDOW_SIZE)
    pygame.display.set_caption("EKF-SLAM Visualization Test")
    init_viz()
    
    clock = pygame.time.Clock()
    running = True
    
    # Test data
    robot_pose = np.array([0.0, 0.0, 0.0])
    landmark_pos = np.array([5.0, 5.0])
    
    # Simple mock EKF object
    class MockEKF:
        def __init__(self):
            self.P = np.eye(11) * 0.5
            self.lm_inited = np.array([True, True, False, False])
    
    ekf = MockEKF()
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Animate robot
        robot_pose[0] = 5 * np.sin(pygame.time.get_ticks() / 1000)
        robot_pose[1] = 5 * np.cos(pygame.time.get_ticks() / 1000)
        robot_pose[2] = pygame.time.get_ticks() / 1000
        
        # Draw
        screen.fill((245, 245, 250))
        draw_grid(screen)
        
        # Draw landmark
        draw_landmark(screen, landmark_pos, (0, 140, 0), est=False, lm_id=0)
        
        # Draw robot with FOV
        draw_robot(screen, robot_pose, (30, 30, 220), est=False, draw_fov=True)
        
        # Draw uncertainty ellipse
        cov = np.array([[0.5, 0.1], [0.1, 0.3]])
        draw_ellipse(screen, robot_pose[:2], cov, color=(200, 0, 0))
        
        # Draw info panel
        draw_info_panel(screen, 100, 0.5, 2, robot_pose, robot_pose, ekf)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    print("✓ Visualization test completed successfully!")

if __name__ == '__main__':
    test_visualization()
