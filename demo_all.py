#!/usr/bin/env python3
"""
Comprehensive demo launcher - runs all visualization features
"""
import os
import sys
import subprocess

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def run_demo():
    """Run all demo scripts in sequence"""
    
    print_header("EKF-SLAM COMPREHENSIVE DEMO")
    print("This script will demonstrate all visualization capabilities.")
    print("Each demo will run automatically. Press ESC to skip any demo.\n")
    
    input("Press ENTER to start...")
    
    # 1. Test visualization
    print_header("1/5: Testing Visualization Components")
    print("This will show an animated test of the rendering engine.")
    print("Watch the robot move in a circle with FOV cone and uncertainty ellipse.")
    input("Press ENTER to continue...")
    
    try:
        subprocess.run([sys.executable, "test_viz.py"], check=True)
    except subprocess.CalledProcessError:
        print("⚠ Test skipped or failed")
    except KeyboardInterrupt:
        print("\n⚠ Demo interrupted by user")
        return
    
    # 2. Generate screenshot
    print_header("2/5: Generating Demo Screenshot")
    print("Creating a single-frame demonstration image...")
    
    try:
        subprocess.run([sys.executable, "generate_demo_screenshot.py"], check=True)
        print("✓ Screenshot saved to outputs/demo_screenshot.png")
    except subprocess.CalledProcessError:
        print("⚠ Screenshot generation failed")
    except KeyboardInterrupt:
        print("\n⚠ Demo interrupted by user")
        return
    
    # 3. Run main simulation
    print_header("3/5: Running Main EKF-SLAM Simulation")
    print("This is the full simulation with all features enabled.")
    print("Controls:")
    print("  - SPACE: Pause/Resume")
    print("  - ESC: Exit")
    print("\nWatch for:")
    print("  - Robot trajectory (blue = true, orange = estimated)")
    print("  - Landmarks (circles = true, squares = estimated)")
    print("  - Uncertainty ellipses shrinking over time")
    print("  - FOV cone showing camera view")
    print("  - Real-time metrics in the info panel")
    input("\nPress ENTER to start simulation...")
    
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
        print("✓ Simulation complete. Plots saved to outputs/")
    except subprocess.CalledProcessError:
        print("⚠ Simulation failed")
    except KeyboardInterrupt:
        print("\n⚠ Demo interrupted by user")
        return
    
    # 4. Mode comparison
    print_header("4/5: Comparing Range-Bearing vs Bearing-Only Modes")
    print("Running both modes and generating comparison plots...")
    print("This will take about 30 seconds...")
    
    try:
        subprocess.run([sys.executable, "compare_modes.py"], check=True)
        print("✓ Comparison complete. See outputs/mode_comparison.png")
    except subprocess.CalledProcessError:
        print("⚠ Comparison failed")
    except KeyboardInterrupt:
        print("\n⚠ Demo interrupted by user")
        return
    
    # 5. Animation (optional)
    print_header("5/5: Creating Animated GIF (Optional)")
    print("This will create an animated GIF of the simulation.")
    print("⚠ Warning: This may take 1-2 minutes and create a large file.")
    
    response = input("Do you want to create the animation? (y/N): ").strip().lower()
    
    if response == 'y':
        print("\nGenerating animation... Please wait...")
        try:
            subprocess.run([sys.executable, "save_animation.py"], check=True)
            print("✓ Animation saved to outputs/ekf_slam_demo.gif")
        except subprocess.CalledProcessError:
            print("⚠ Animation generation failed")
        except KeyboardInterrupt:
            print("\n⚠ Demo interrupted by user")
            return
    else:
        print("Animation skipped.")
    
    # Summary
    print_header("DEMO COMPLETE!")
    print("All outputs have been saved to the 'outputs/' directory:")
    print("\nGenerated files:")
    
    outputs_dir = "outputs"
    if os.path.exists(outputs_dir):
        files = os.listdir(outputs_dir)
        for f in sorted(files):
            filepath = os.path.join(outputs_dir, f)
            size = os.path.getsize(filepath)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024*1024:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size/1024/1024:.1f} MB"
            print(f"  - {f:30s} ({size_str})")
    
    print("\n" + "="*70)
    print("Thank you for exploring the EKF-SLAM visualization!")
    print("="*70 + "\n")

if __name__ == '__main__':
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\n⚠ Demo interrupted by user. Exiting...")
        sys.exit(0)
