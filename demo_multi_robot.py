"""
Demo script to quickly show both modes
Runs headless and saves comparison images
"""
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from simulator import World
from ekf_slam import EKFSLAM
import config as C

def run_mode(multi_robot=False, steps=300):
    """Run simulation in specified mode"""
    world = World(C.NUM_LANDMARKS, multi_robot=multi_robot)
    ekf1 = EKFSLAM(C.NUM_LANDMARKS)
    
    if multi_robot:
        ekf2 = EKFSLAM(C.NUM_LANDMARKS)
        ekf2.x[0:3] = [-5.0, -5.0, np.pi/4]
    else:
        ekf2 = None
    
    true_traj1 = []
    est_traj1 = []
    true_traj2 = []
    est_traj2 = []
    
    for step in range(steps):
        # Robot 1
        u, xtrue = world.step()
        obs = world.sense()
        ekf1.predict(u)
        ekf1.update(obs)
        
        true_traj1.append(xtrue.copy())
        est_traj1.append(ekf1.robot_state().copy())
        
        # Robot 2
        if multi_robot and ekf2 is not None:
            xtrue2 = np.array([world.robot2.x, world.robot2.y, world.robot2.th])
            obs2 = world.sense_robot2()
            u2 = np.array([C.BASE_V * 0.8, C.BASE_W * np.cos(0.12*world.t)])
            ekf2.predict(u2)
            ekf2.update(obs2)
            
            true_traj2.append(xtrue2.copy())
            est_traj2.append(ekf2.robot_state().copy())
    
    return {
        'true_traj1': np.array(true_traj1),
        'est_traj1': np.array(est_traj1),
        'true_traj2': np.array(true_traj2) if true_traj2 else None,
        'est_traj2': np.array(est_traj2) if est_traj2 else None,
        'landmarks': np.array([[lm.x, lm.y] for lm in world.landmarks])
    }

def create_comparison():
    """Create side-by-side comparison"""
    print("Running Single Robot Mode...")
    single = run_mode(multi_robot=False, steps=300)
    
    print("Running Multi-Robot Mode...")
    multi = run_mode(multi_robot=True, steps=300)
    
    # Create comparison plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # Single robot plot
    ax1.plot(single['true_traj1'][:,0], single['true_traj1'][:,1], 
             'b-', linewidth=2, label='True', alpha=0.7)
    ax1.plot(single['est_traj1'][:,0], single['est_traj1'][:,1], 
             'orange', linewidth=2, linestyle='--', label='Estimated', alpha=0.7)
    ax1.scatter(single['landmarks'][:,0], single['landmarks'][:,1], 
                marker='x', s=150, c='green', linewidths=3, label='Landmarks')
    ax1.set_xlabel('x [m]', fontsize=12)
    ax1.set_ylabel('y [m]', fontsize=12)
    ax1.set_title('Single Robot Mode (Original)', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.axis('equal')
    
    # Multi-robot plot
    ax2.plot(multi['true_traj1'][:,0], multi['true_traj1'][:,1], 
             'b-', linewidth=2, label='Robot 1 True', alpha=0.7)
    ax2.plot(multi['est_traj1'][:,0], multi['est_traj1'][:,1], 
             'orange', linewidth=2, linestyle='--', label='Robot 1 Est', alpha=0.7)
    
    if multi['true_traj2'] is not None:
        ax2.plot(multi['true_traj2'][:,0], multi['true_traj2'][:,1], 
                 'purple', linewidth=2, label='Robot 2 True', alpha=0.7)
        ax2.plot(multi['est_traj2'][:,0], multi['est_traj2'][:,1], 
                 'cyan', linewidth=2, linestyle='--', label='Robot 2 Est', alpha=0.7)
    
    ax2.scatter(multi['landmarks'][:,0], multi['landmarks'][:,1], 
                marker='x', s=150, c='green', linewidths=3, label='Landmarks')
    ax2.set_xlabel('x [m]', fontsize=12)
    ax2.set_ylabel('y [m]', fontsize=12)
    ax2.set_title('Multi-Robot Mode with Collision Avoidance', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.axis('equal')
    
    plt.tight_layout()
    
    os.makedirs('outputs', exist_ok=True)
    plt.savefig('outputs/mode_comparison.png', dpi=150, bbox_inches='tight')
    print("\n✓ Saved comparison to: outputs/mode_comparison.png")
    plt.close()
    
    # Calculate and display metrics
    rmse1_single = np.sqrt(np.mean(np.sum((single['true_traj1'][:,:2] - single['est_traj1'][:,:2])**2, axis=1)))
    rmse1_multi = np.sqrt(np.mean(np.sum((multi['true_traj1'][:,:2] - multi['est_traj1'][:,:2])**2, axis=1)))
    
    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON")
    print("="*60)
    print(f"Single Robot Mode:")
    print(f"  Robot 1 RMSE: {rmse1_single:.4f} m")
    print()
    print(f"Multi-Robot Mode:")
    print(f"  Robot 1 RMSE: {rmse1_multi:.4f} m")
    
    if multi['true_traj2'] is not None:
        rmse2_multi = np.sqrt(np.mean(np.sum((multi['true_traj2'][:,:2] - multi['est_traj2'][:,:2])**2, axis=1)))
        print(f"  Robot 2 RMSE: {rmse2_multi:.4f} m")
    
    print("="*60)

if __name__ == "__main__":
    print("="*60)
    print("Multi-Robot EKF-SLAM Demo")
    print("="*60)
    create_comparison()
    print("\n✓ Demo complete!")
