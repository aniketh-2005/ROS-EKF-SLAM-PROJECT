#!/usr/bin/env python3
"""
Run EKF-SLAM simulation and save as animated GIF
"""
import os
import numpy as np
import pygame
from PIL import Image
from simulator import World
from ekf_slam import EKFSLAM
import config as C
from viz import (draw_robot, draw_landmark, draw_ellipse, draw_grid, 
                 draw_trajectory, draw_observation_lines, draw_info_panel, init_viz)

def save_animation(output_path="outputs/ekf_slam_animation.gif", frame_skip=3, duration=50):
    """
    Run simulation and save as animated GIF
    
    Args:
        output_path: Path to save the GIF
        frame_skip: Only save every Nth frame (to reduce file size)
        duration: Duration of each frame in milliseconds
    """
    os.makedirs("outputs", exist_ok=True)
    
    pygame.init()
    screen = pygame.display.set_mode(C.WINDOW_SIZE)
    pygame.display.set_caption("EKF-SLAM: Generating Animation...")
    init_viz()

    world = World(C.NUM_LANDMARKS)
    ekf = EKFSLAM(C.NUM_LANDMARKS)

    true_traj = []
    est_traj = []
    frames = []

    print("Generating animation frames...")
    
    for step in range(C.SIM_STEPS):
        # Progress indicator
        if step % 50 == 0:
            print(f"  Frame {step}/{C.SIM_STEPS}")
        
        # Simulation step
        u, xtrue = world.step()
        obs = world.sense()
        ekf.predict(u)
        ekf.update(obs)

        true_traj.append(xtrue.copy())
        est_traj.append(ekf.robot_state().copy())

        # Render (only save every frame_skip frames)
        if step % frame_skip == 0:
            screen.fill((245, 245, 250))
            
            draw_grid(screen)
            draw_trajectory(screen, true_traj, color=(30, 30, 220))
            draw_trajectory(screen, est_traj, color=(220, 80, 0))
            
            if len(obs) > 0:
                draw_observation_lines(screen, xtrue, world.landmarks, obs)
            
            for i in range(C.NUM_LANDMARKS):
                idx = 3 + 2*i
                if ekf.lm_inited[i]:
                    lm_est = ekf.x[idx:idx+2]
                    draw_ellipse(screen, lm_est, ekf.P[idx:idx+2, idx:idx+2], color=(0,120,0))
                    draw_landmark(screen, lm_est, (0,180,0), est=True, lm_id=i)
            
            for i, lm in enumerate(world.landmarks):
                draw_landmark(screen, (lm.x, lm.y), (0,140,0), est=False, lm_id=i)
            
            draw_ellipse(screen, ekf.robot_state()[:2], ekf.P[0:2,0:2], color=(200,0,0))
            draw_robot(screen, ekf.robot_state(), (220,80,0), est=True, draw_fov=False)
            draw_robot(screen, xtrue, (30,30,220), est=False, draw_fov=True)
            
            current_rmse = float(np.sqrt(np.mean(np.sum((np.array(true_traj)[:,:2] - np.array(est_traj)[:,:2])**2, axis=1))))
            draw_info_panel(screen, step, current_rmse, int(np.sum(ekf.lm_inited)), 
                           xtrue, ekf.robot_state(), ekf)
            
            pygame.display.flip()
            
            # Capture frame
            frame_data = pygame.surfarray.array3d(screen)
            frame_data = np.transpose(frame_data, (1, 0, 2))  # Pygame uses (width, height, channels)
            frames.append(Image.fromarray(frame_data))

    pygame.quit()

    # Save as GIF
    print(f"\nSaving animation to {output_path}...")
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        optimize=False
    )
    
    print(f"✓ Animation saved! ({len(frames)} frames)")
    print(f"  File: {output_path}")
    print(f"  Size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")

if __name__ == '__main__':
    # Generate a shorter animation for demo (adjust SIM_STEPS in config for full version)
    save_animation(
        output_path="outputs/ekf_slam_demo.gif",
        frame_skip=5,  # Save every 5th frame
        duration=50    # 50ms per frame = 20 FPS
    )
