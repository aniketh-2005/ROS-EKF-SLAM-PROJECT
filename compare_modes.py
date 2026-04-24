#!/usr/bin/env python3
"""
Compare Range-Bearing vs Bearing-Only modes side by side
Generates comparison plots showing performance differences
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from simulator import World
from ekf_slam import EKFSLAM
import config as C

def run_simulation(use_bearing_only=False):
    """Run simulation and return trajectories and metrics"""
    # Temporarily override config
    original_mode = C.USE_BEARING_ONLY
    C.USE_BEARING_ONLY = use_bearing_only
    
    world = World(C.NUM_LANDMARKS)
    ekf = EKFSLAM(C.NUM_LANDMARKS)
    
    true_traj = []
    est_traj = []
    errors = []
    uncertainties = []
    
    for step in range(C.SIM_STEPS):
        u, xtrue = world.step()
        obs = world.sense()
        ekf.predict(u)
        ekf.update(obs)
        
        true_traj.append(xtrue.copy())
        est_traj.append(ekf.robot_state().copy())
        
        # Calculate error
        error = np.linalg.norm(xtrue[:2] - ekf.robot_state()[:2])
        errors.append(error)
        
        # Track uncertainty
        uncertainty = np.trace(ekf.P[0:2, 0:2])
        uncertainties.append(uncertainty)
    
    # Restore config
    C.USE_BEARING_ONLY = original_mode
    
    true_traj = np.array(true_traj)
    est_traj = np.array(est_traj)
    
    # Get final landmark estimates
    lm_est = []
    for i in range(C.NUM_LANDMARKS):
        idx = 3 + 2*i
        if ekf.lm_inited[i]:
            lm_est.append(ekf.x[idx:idx+2].copy())
    
    lm_true = np.array([[lm.x, lm.y] for lm in world.landmarks])
    
    return {
        'true_traj': true_traj,
        'est_traj': est_traj,
        'errors': np.array(errors),
        'uncertainties': np.array(uncertainties),
        'lm_true': lm_true,
        'lm_est': np.array(lm_est) if lm_est else np.array([]),
        'n_lm_init': len(lm_est)
    }

def create_comparison_plots():
    """Generate comprehensive comparison plots"""
    os.makedirs("outputs", exist_ok=True)
    
    print("Running Range-Bearing mode...")
    rb_results = run_simulation(use_bearing_only=False)
    
    print("Running Bearing-Only mode...")
    bo_results = run_simulation(use_bearing_only=True)
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 10))
    
    # 1. Trajectories comparison
    ax1 = plt.subplot(2, 3, 1)
    ax1.plot(rb_results['true_traj'][:,0], rb_results['true_traj'][:,1], 
             'k-', linewidth=2, label='True', alpha=0.7)
    ax1.plot(rb_results['est_traj'][:,0], rb_results['est_traj'][:,1], 
             'b-', linewidth=1.5, label='Range-Bearing Est.')
    ax1.scatter(rb_results['lm_true'][:,0], rb_results['lm_true'][:,1], 
                c='green', marker='*', s=200, label='Landmarks', zorder=5)
    ax1.set_xlabel('X [m]')
    ax1.set_ylabel('Y [m]')
    ax1.set_title('Range-Bearing Mode')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.axis('equal')
    
    ax2 = plt.subplot(2, 3, 2)
    ax2.plot(bo_results['true_traj'][:,0], bo_results['true_traj'][:,1], 
             'k-', linewidth=2, label='True', alpha=0.7)
    ax2.plot(bo_results['est_traj'][:,0], bo_results['est_traj'][:,1], 
             'r-', linewidth=1.5, label='Bearing-Only Est.')
    ax2.scatter(bo_results['lm_true'][:,0], bo_results['lm_true'][:,1], 
                c='green', marker='*', s=200, label='Landmarks', zorder=5)
    ax2.set_xlabel('X [m]')
    ax2.set_ylabel('Y [m]')
    ax2.set_title('Bearing-Only Mode')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.axis('equal')
    
    # 2. Position error over time
    ax3 = plt.subplot(2, 3, 3)
    time = np.arange(len(rb_results['errors'])) * C.DT
    ax3.plot(time, rb_results['errors'], 'b-', linewidth=2, label='Range-Bearing', alpha=0.8)
    ax3.plot(time, bo_results['errors'], 'r-', linewidth=2, label='Bearing-Only', alpha=0.8)
    ax3.set_xlabel('Time [s]')
    ax3.set_ylabel('Position Error [m]')
    ax3.set_title('Position Error Over Time')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 3. Uncertainty over time
    ax4 = plt.subplot(2, 3, 4)
    ax4.plot(time, rb_results['uncertainties'], 'b-', linewidth=2, label='Range-Bearing', alpha=0.8)
    ax4.plot(time, bo_results['uncertainties'], 'r-', linewidth=2, label='Bearing-Only', alpha=0.8)
    ax4.set_xlabel('Time [s]')
    ax4.set_ylabel('Position Uncertainty (Trace of Cov)')
    ax4.set_title('Uncertainty Over Time')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 4. Landmark estimation accuracy
    ax5 = plt.subplot(2, 3, 5)
    if len(rb_results['lm_est']) > 0:
        ax5.scatter(rb_results['lm_true'][:,0], rb_results['lm_true'][:,1], 
                   c='green', marker='*', s=300, label='True', zorder=5, edgecolors='black', linewidths=2)
        ax5.scatter(rb_results['lm_est'][:,0], rb_results['lm_est'][:,1], 
                   c='blue', marker='o', s=150, label='Range-Bearing Est.', alpha=0.7)
        # Draw error lines
        for i in range(min(len(rb_results['lm_true']), len(rb_results['lm_est']))):
            ax5.plot([rb_results['lm_true'][i,0], rb_results['lm_est'][i,0]],
                    [rb_results['lm_true'][i,1], rb_results['lm_est'][i,1]],
                    'b--', alpha=0.5, linewidth=1)
    ax5.set_xlabel('X [m]')
    ax5.set_ylabel('Y [m]')
    ax5.set_title('Landmark Estimation (Range-Bearing)')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    ax5.axis('equal')
    
    ax6 = plt.subplot(2, 3, 6)
    if len(bo_results['lm_est']) > 0:
        ax6.scatter(bo_results['lm_true'][:,0], bo_results['lm_true'][:,1], 
                   c='green', marker='*', s=300, label='True', zorder=5, edgecolors='black', linewidths=2)
        ax6.scatter(bo_results['lm_est'][:,0], bo_results['lm_est'][:,1], 
                   c='red', marker='o', s=150, label='Bearing-Only Est.', alpha=0.7)
        # Draw error lines
        for i in range(min(len(bo_results['lm_true']), len(bo_results['lm_est']))):
            ax6.plot([bo_results['lm_true'][i,0], bo_results['lm_est'][i,0]],
                    [bo_results['lm_true'][i,1], bo_results['lm_est'][i,1]],
                    'r--', alpha=0.5, linewidth=1)
    ax6.set_xlabel('X [m]')
    ax6.set_ylabel('Y [m]')
    ax6.set_title('Landmark Estimation (Bearing-Only)')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    ax6.axis('equal')
    
    plt.tight_layout()
    plt.savefig('outputs/mode_comparison.png', dpi=150, bbox_inches='tight')
    print("✓ Comparison plot saved to outputs/mode_comparison.png")
    
    # Print statistics
    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON")
    print("="*60)
    
    print("\nRange-Bearing Mode:")
    print(f"  Final Position RMSE: {rb_results['errors'][-1]:.4f} m")
    print(f"  Mean Position Error: {np.mean(rb_results['errors']):.4f} m")
    print(f"  Final Uncertainty:   {rb_results['uncertainties'][-1]:.4f}")
    print(f"  Landmarks Initialized: {rb_results['n_lm_init']}/{C.NUM_LANDMARKS}")
    
    print("\nBearing-Only Mode:")
    print(f"  Final Position RMSE: {bo_results['errors'][-1]:.4f} m")
    print(f"  Mean Position Error: {np.mean(bo_results['errors']):.4f} m")
    print(f"  Final Uncertainty:   {bo_results['uncertainties'][-1]:.4f}")
    print(f"  Landmarks Initialized: {bo_results['n_lm_init']}/{C.NUM_LANDMARKS}")
    
    print("\nImprovement (Range-Bearing vs Bearing-Only):")
    error_improvement = (1 - rb_results['errors'][-1] / bo_results['errors'][-1]) * 100
    print(f"  Position Error: {error_improvement:+.1f}%")
    
    print("="*60)

if __name__ == '__main__':
    create_comparison_plots()
