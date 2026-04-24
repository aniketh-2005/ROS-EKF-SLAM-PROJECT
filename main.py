import os
import json
import numpy as np
import matplotlib.pyplot as plt
import pygame
from simulator import World
from ekf_slam import EKFSLAM
import config as C
from viz import (draw_robot, draw_landmark, draw_ellipse, draw_grid, 
                 draw_trajectory, draw_observation_lines, draw_info_panel, 
                 draw_performance_overlay, init_viz)

def ensure_dirs():
    os.makedirs("outputs", exist_ok=True)

def show_menu():
    """Display menu to choose simulation mode"""
    pygame.init()
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("EKF-SLAM: Select Mode")
    clock = pygame.time.Clock()
    
    font_title = pygame.font.SysFont('Arial', 32, bold=True)
    font_option = pygame.font.SysFont('Arial', 24)
    font_desc = pygame.font.SysFont('Arial', 16)
    
    selected = 0  # 0 = single robot, 1 = multi-robot
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    selected = 1 - selected
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    pygame.quit()
                    return selected
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return None
        
        screen.fill((245, 245, 250))
        
        # Title
        title = font_title.render("EKF-SLAM Simulation", True, (30, 30, 30))
        screen.blit(title, (300 - title.get_width()//2, 40))
        
        # Options
        options = [
            ("Single Robot Mode", "Standard EKF-SLAM with one robot"),
            ("Multi-Robot Mode", "Two robots with collision avoidance")
        ]
        
        for i, (opt, desc) in enumerate(options):
            y_pos = 150 + i * 100
            color = (220, 80, 0) if i == selected else (80, 80, 80)
            bg_color = (255, 240, 220) if i == selected else (230, 230, 230)
            
            # Background box
            pygame.draw.rect(screen, bg_color, (50, y_pos - 10, 500, 80), border_radius=10)
            pygame.draw.rect(screen, color, (50, y_pos - 10, 500, 80), 3, border_radius=10)
            
            # Option text
            opt_text = font_option.render(opt, True, color)
            screen.blit(opt_text, (300 - opt_text.get_width()//2, y_pos + 5))
            
            # Description
            desc_text = font_desc.render(desc, True, (100, 100, 100))
            screen.blit(desc_text, (300 - desc_text.get_width()//2, y_pos + 35))
        
        # Instructions
        inst = font_desc.render("Use UP/DOWN arrows to select, ENTER to confirm", True, (120, 120, 120))
        screen.blit(inst, (300 - inst.get_width()//2, 360))
        
        pygame.display.flip()
        clock.tick(30)

def run():
    ensure_dirs()
    
    # Show menu to select mode
    mode = show_menu()
    if mode is None:
        return
    
    C.MULTI_ROBOT_MODE = (mode == 1)
    
    pygame.init()
    screen = pygame.display.set_mode(C.WINDOW_SIZE)
    title = "EKF-SLAM: Multi-Robot with Collision Avoidance" if C.MULTI_ROBOT_MODE else "EKF-SLAM: Camera-Based Localization & Mapping"
    pygame.display.set_caption(title)
    clock = pygame.time.Clock()
    
    # Initialize visualization
    init_viz()

    world = World(C.NUM_LANDMARKS, multi_robot=C.MULTI_ROBOT_MODE)
    ekf = EKFSLAM(C.NUM_LANDMARKS)
    
    # Second EKF for robot 2
    if C.MULTI_ROBOT_MODE:
        ekf2 = EKFSLAM(C.NUM_LANDMARKS)
        ekf2.x[0:3] = [-5.0, -5.0, np.pi/4]  # Initialize at robot2's position
    else:
        ekf2 = None

    true_traj = []
    est_traj = []
    true_traj2 = []
    est_traj2 = []
    lms_true = np.array([[lm.x, lm.y] for lm in world.landmarks])

    running = True
    paused = False
    step = 0
    fps_clock = pygame.time.Clock()
    
    while running and step < C.SIM_STEPS:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_ESCAPE:
                    running = False

        if not paused:
            # --- dynamics ---
            u, xtrue = world.step()
            # --- observations ---
            obs = world.sense()

            # --- EKF ---
            ekf.predict(u)
            ekf.update(obs)

            # log
            true_traj.append(xtrue.copy())
            est_traj.append(ekf.robot_state().copy())
            
            # Robot 2 processing
            if C.MULTI_ROBOT_MODE and ekf2 is not None:
                xtrue2 = np.array([world.robot2.x, world.robot2.y, world.robot2.th])
                obs2 = world.sense_robot2()
                
                # Simple control for robot 2 (could be improved)
                u2 = np.array([C.BASE_V * 0.8, C.BASE_W * np.cos(0.12*world.t)])
                ekf2.predict(u2)
                ekf2.update(obs2)
                
                true_traj2.append(xtrue2.copy())
                est_traj2.append(ekf2.robot_state().copy())
            
            step += 1

        # --- Draw ---
        screen.fill((245, 245, 250))
        
        # Draw grid background
        draw_grid(screen)
        
        # Draw trajectories
        draw_trajectory(screen, true_traj, color=(30, 30, 220), label="True")
        draw_trajectory(screen, est_traj, color=(220, 80, 0), label="Estimated")
        
        # Draw observation lines
        if len(obs) > 0:
            draw_observation_lines(screen, xtrue, world.landmarks, obs)
        
        # Draw estimated landmarks & covariance ellipses
        for i in range(C.NUM_LANDMARKS):
            idx = 3 + 2*i
            if ekf.lm_inited[i]:
                lm_est = ekf.x[idx:idx+2]
                # Draw ellipse first (behind landmark)
                draw_ellipse(screen, lm_est, ekf.P[idx:idx+2, idx:idx+2], color=(0,120,0))
                draw_landmark(screen, lm_est, (0,180,0), est=True, lm_id=i)
        
        # Draw true landmarks
        for i, lm in enumerate(world.landmarks):
            draw_landmark(screen, (lm.x, lm.y), (0,140,0), est=False, lm_id=i)
        
        # Draw robot covariance ellipse
        draw_ellipse(screen, ekf.robot_state()[:2], ekf.P[0:2,0:2], color=(200,0,0))
        
        # Draw robots (estimated first, then true on top)
        draw_robot(screen, ekf.robot_state(), (220,80,0), est=True, draw_fov=False)
        draw_robot(screen, xtrue, (30,30,220), est=False, draw_fov=True)
        
        # Draw robot 2 if in multi-robot mode
        if C.MULTI_ROBOT_MODE and ekf2 is not None and len(true_traj2) > 0:
            # Draw trajectory for robot 2
            draw_trajectory(screen, true_traj2, color=(180, 30, 180), label="True R2")
            draw_trajectory(screen, est_traj2, color=(0, 180, 180), label="Est R2")
            
            # Draw robot 2 covariance
            draw_ellipse(screen, ekf2.robot_state()[:2], ekf2.P[0:2,0:2], color=(0,180,180))
            
            # Draw robot 2
            xtrue2 = np.array([world.robot2.x, world.robot2.y, world.robot2.th])
            draw_robot(screen, ekf2.robot_state(), (0,180,180), est=True, draw_fov=False)
            draw_robot(screen, xtrue2, (180,30,180), est=False, draw_fov=True)
        
        # Calculate current RMSE
        if len(true_traj) > 0:
            current_rmse = float(np.sqrt(np.mean(np.sum((np.array(true_traj)[:,:2] - np.array(est_traj)[:,:2])**2, axis=1))))
        else:
            current_rmse = 0.0
        
        # Draw info panel
        draw_info_panel(screen, step, current_rmse, int(np.sum(ekf.lm_inited)), 
                       xtrue, ekf.robot_state(), ekf)
        
        # Draw performance overlay
        draw_performance_overlay(screen, fps_clock.get_fps(), step)
        
        # Draw pause indicator
        if paused:
            pause_font = pygame.font.SysFont('Arial', 36, bold=True)
            pause_text = pause_font.render("PAUSED", True, (255, 100, 100))
            text_rect = pause_text.get_rect(center=(C.WINDOW_SIZE[0]//2, 50))
            # Draw background for text
            bg_rect = text_rect.inflate(20, 10)
            pygame.draw.rect(screen, (0, 0, 0, 180), bg_rect)
            screen.blit(pause_text, text_rect)

        pygame.display.flip()
        fps_clock.tick(60)

    pygame.quit()

    # Save plots
    true_traj = np.array(true_traj)
    est_traj = np.array(est_traj)

    plt.figure(figsize=(10, 8))
    plt.plot(true_traj[:,0], true_traj[:,1], label='Robot 1 True', linewidth=2)
    plt.plot(est_traj[:,0], est_traj[:,1], label='Robot 1 EKF', linewidth=2, linestyle='--')
    
    if C.MULTI_ROBOT_MODE and len(true_traj2) > 0:
        true_traj2_arr = np.array(true_traj2)
        est_traj2_arr = np.array(est_traj2)
        plt.plot(true_traj2_arr[:,0], true_traj2_arr[:,1], label='Robot 2 True', linewidth=2, color='purple')
        plt.plot(est_traj2_arr[:,0], est_traj2_arr[:,1], label='Robot 2 EKF', linewidth=2, linestyle='--', color='cyan')
    
    plt.scatter(lms_true[:,0], lms_true[:,1], marker='x', s=100, label='Landmarks', color='green')
    plt.axis('equal')
    plt.legend()
    plt.xlabel('x [m]')
    plt.ylabel('y [m]')
    title = 'Multi-Robot Trajectory with Collision Avoidance' if C.MULTI_ROBOT_MODE else 'Trajectory'
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.savefig('outputs/trajectory.png', dpi=150)
    plt.close()

    # Landmarks final
    lm_est_list = []
    for i in range(C.NUM_LANDMARKS):
        idx = 3 + 2*i
        if ekf.lm_inited[i]:
            lm_est_list.append(ekf.x[idx:idx+2].copy())
    if lm_est_list:
        lm_est = np.array(lm_est_list)
        plt.figure()
        plt.scatter(lms_true[:,0], lms_true[:,1], marker='x', label='True LMs')
        plt.scatter(lm_est[:,0], lm_est[:,1], marker='o', label='Estimated LMs')
        plt.axis('equal')
        plt.legend()
        plt.xlabel('x [m]')
        plt.ylabel('y [m]')
        plt.title('Landmarks')
        plt.savefig('outputs/landmarks.png', dpi=150)
        plt.close()

    # Simple RMSE for robot pose (x,y only)
    rmse = float(np.sqrt(np.mean(np.sum((true_traj[:,:2] - est_traj[:,:2])**2, axis=1))))
    
    result_data = {
        "mode": "multi_robot" if C.MULTI_ROBOT_MODE else "single_robot",
        "robot1_rmse_xy": rmse,
        "n_landmarks_inited": int(np.sum(ekf.lm_inited)),
        "bearing_only": bool(C.USE_BEARING_ONLY),
        "steps": int(C.SIM_STEPS)
    }
    
    if C.MULTI_ROBOT_MODE and len(true_traj2) > 0:
        true_traj2_arr = np.array(true_traj2)
        est_traj2_arr = np.array(est_traj2)
        rmse2 = float(np.sqrt(np.mean(np.sum((true_traj2_arr[:,:2] - est_traj2_arr[:,:2])**2, axis=1))))
        result_data["robot2_rmse_xy"] = rmse2
        result_data["robot2_landmarks_inited"] = int(np.sum(ekf2.lm_inited))
    
    with open("outputs/final_state.json", "w") as f:
        json.dump(result_data, f, indent=2)

if __name__ == '__main__':
    run()
