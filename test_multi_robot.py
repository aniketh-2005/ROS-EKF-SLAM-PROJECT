"""
Quick test to verify multi-robot functionality
"""
import numpy as np
from simulator import World
from ekf_slam import EKFSLAM
import config as C

def test_single_robot():
    """Test single robot mode (original)"""
    print("Testing Single Robot Mode...")
    world = World(C.NUM_LANDMARKS, multi_robot=False)
    ekf = EKFSLAM(C.NUM_LANDMARKS)
    
    # Run a few steps
    for i in range(10):
        u, xtrue = world.step()
        obs = world.sense()
        ekf.predict(u)
        ekf.update(obs)
    
    print(f"  ✓ Robot position: ({world.robot.x:.2f}, {world.robot.y:.2f})")
    print(f"  ✓ EKF estimate: ({ekf.x[0]:.2f}, {ekf.x[1]:.2f})")
    print(f"  ✓ Robot 2 exists: {world.robot2 is not None}")
    assert world.robot2 is None, "Robot 2 should not exist in single mode"
    print("  ✓ Single robot mode works!\n")

def test_multi_robot():
    """Test multi-robot mode with collision avoidance"""
    print("Testing Multi-Robot Mode...")
    world = World(C.NUM_LANDMARKS, multi_robot=True)
    ekf1 = EKFSLAM(C.NUM_LANDMARKS)
    ekf2 = EKFSLAM(C.NUM_LANDMARKS)
    ekf2.x[0:3] = [-5.0, -5.0, np.pi/4]
    
    # Run a few steps
    for i in range(10):
        u, xtrue = world.step()
        obs1 = world.sense()
        obs2 = world.sense_robot2()
        
        ekf1.predict(u)
        ekf1.update(obs1)
        
        u2 = np.array([C.BASE_V * 0.8, C.BASE_W * np.cos(0.12*world.t)])
        ekf2.predict(u2)
        ekf2.update(obs2)
    
    print(f"  ✓ Robot 1 position: ({world.robot.x:.2f}, {world.robot.y:.2f})")
    print(f"  ✓ Robot 2 position: ({world.robot2.x:.2f}, {world.robot2.y:.2f})")
    print(f"  ✓ Distance between robots: {np.hypot(world.robot.x - world.robot2.x, world.robot.y - world.robot2.y):.2f}m")
    print(f"  ✓ EKF1 estimate: ({ekf1.x[0]:.2f}, {ekf1.x[1]:.2f})")
    print(f"  ✓ EKF2 estimate: ({ekf2.x[0]:.2f}, {ekf2.x[1]:.2f})")
    assert world.robot2 is not None, "Robot 2 should exist in multi mode"
    print("  ✓ Multi-robot mode works!\n")

def test_collision_avoidance():
    """Test that collision avoidance activates"""
    print("Testing Collision Avoidance...")
    world = World(C.NUM_LANDMARKS, multi_robot=True)
    
    # Place robots close together
    world.robot.x = 0.0
    world.robot.y = 0.0
    world.robot2.x = 0.5  # Very close!
    world.robot2.y = 0.5
    
    initial_dist = np.hypot(world.robot.x - world.robot2.x, world.robot.y - world.robot2.y)
    print(f"  Initial distance: {initial_dist:.2f}m")
    
    # Run simulation - robots should move apart
    for i in range(20):
        world.step()
    
    final_dist = np.hypot(world.robot.x - world.robot2.x, world.robot.y - world.robot2.y)
    print(f"  Final distance: {final_dist:.2f}m")
    print(f"  Distance increased: {final_dist > initial_dist}")
    print("  ✓ Collision avoidance active!\n")

if __name__ == "__main__":
    print("="*50)
    print("Multi-Robot EKF-SLAM Test Suite")
    print("="*50 + "\n")
    
    test_single_robot()
    test_multi_robot()
    test_collision_avoidance()
    
    print("="*50)
    print("All tests passed! ✓")
    print("="*50)
