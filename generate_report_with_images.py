"""
Generate comprehensive project report with images
"""
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

# Import the base report generation
exec(open('generate_report.py').read().replace('if __name__ == "__main__":', 'if False:'))

def add_images_to_report():
    """Add images to the existing report"""
    doc = Document('EKF_SLAM_Project_Report.docx')
    
    # Find the Results section and add images
    print("Adding images to report...")
    
    # Add a new section for visual results
    doc.add_page_break()
    doc.add_heading('Appendix E: Visual Results', 1)
    
    # Add trajectory comparison
    if os.path.exists('outputs/mode_comparison.png'):
        doc.add_heading('Mode Comparison', 2)
        doc.add_paragraph('Side-by-side comparison of single robot and multi-robot modes:')
        doc.add_picture('outputs/mode_comparison.png', width=Inches(6.0))
        doc.add_paragraph()
    
    # Add trajectory plot
    if os.path.exists('outputs/trajectory.png'):
        doc.add_heading('Trajectory Visualization', 2)
        doc.add_paragraph('Robot trajectories showing true vs estimated paths:')
        doc.add_picture('outputs/trajectory.png', width=Inches(5.5))
        doc.add_paragraph()
    
    # Add landmarks plot
    if os.path.exists('outputs/landmarks.png'):
        doc.add_heading('Landmark Estimation', 2)
        doc.add_paragraph('True vs estimated landmark positions:')
        doc.add_picture('outputs/landmarks.png', width=Inches(5.5))
        doc.add_paragraph()
    
    # Add demo screenshot
    if os.path.exists('outputs/demo_screenshot.png'):
        doc.add_heading('Pygame Visualization Screenshot', 2)
        doc.add_paragraph('Real-time visualization showing robot, landmarks, and uncertainty ellipses:')
        doc.add_picture('outputs/demo_screenshot.png', width=Inches(5.5))
        doc.add_paragraph()
    
    # Save enhanced report
    doc.save('EKF_SLAM_Project_Report_Complete.docx')
    print("✓ Enhanced report with images: EKF_SLAM_Project_Report_Complete.docx")

if __name__ == "__main__":
    add_images_to_report()
