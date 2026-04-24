import pygame
import numpy as np
from utils import wrap_angle
import config as C
import math

# Initialize font (will be set in init_viz)
font_large = None
font_medium = None
font_small = None

def init_viz():
    """Initialize visualization resources"""
    global font_large, font_medium, font_small
    pygame.font.init()
    font_large = pygame.font.SysFont('Arial', 24, bold=True)
    font_medium = pygame.font.SysFont('Arial', 16)
    font_small = pygame.font.SysFont('Arial', 12)

def to_screen(p):
    cx, cy = C.WINDOW_SIZE[0]//2, C.WINDOW_SIZE[1]//2
    return int(cx + p[0]*C.WINDOW_SCALE), int(cy - p[1]*C.WINDOW_SCALE)

def draw_grid(screen):
    """Draw a realistic grid background"""
    grid_color = (220, 220, 230)
    major_grid_color = (180, 180, 200)
    
    cx, cy = C.WINDOW_SIZE[0]//2, C.WINDOW_SIZE[1]//2
    
    # Draw minor grid lines (1 meter spacing)
    for i in range(-30, 31):
        x_pos = cx + i * C.WINDOW_SCALE
        y_pos = cy + i * C.WINDOW_SCALE
        
        if 0 <= x_pos <= C.WINDOW_SIZE[0]:
            color = major_grid_color if i % 5 == 0 else grid_color
            width = 2 if i % 5 == 0 else 1
            pygame.draw.line(screen, color, (x_pos, 0), (x_pos, C.WINDOW_SIZE[1]), width)
        
        if 0 <= y_pos <= C.WINDOW_SIZE[1]:
            color = major_grid_color if i % 5 == 0 else grid_color
            width = 2 if i % 5 == 0 else 1
            pygame.draw.line(screen, color, (0, y_pos), (C.WINDOW_SIZE[0], y_pos), width)
    
    # Draw axes
    pygame.draw.line(screen, (100, 100, 120), (0, cy), (C.WINDOW_SIZE[0], cy), 3)
    pygame.draw.line(screen, (100, 100, 120), (cx, 0), (cx, C.WINDOW_SIZE[1]), 3)
    
    # Draw axis labels
    if font_small:
        x_label = font_small.render('X', True, (80, 80, 100))
        y_label = font_small.render('Y', True, (80, 80, 100))
        screen.blit(x_label, (C.WINDOW_SIZE[0] - 30, cy + 5))
        screen.blit(y_label, (cx + 5, 10))

def draw_robot(screen, pose, color=(0,0,255), est=False, draw_fov=False):
    """Draw a realistic robot with body, wheels, and direction indicator"""
    x, y, th = pose
    p = np.array([x, y])
    screen_pos = to_screen(p)
    
    # Robot dimensions
    body_radius = 12 if not est else 10
    wheel_length = 8
    wheel_width = 3
    
    # Draw FOV cone for true robot
    if draw_fov and not est:
        fov_length = C.MAX_RANGE * C.WINDOW_SCALE
        fov_angle = C.FOV / 2
        
        # Create FOV triangle points
        fov_points = [screen_pos]
        for angle in np.linspace(th - fov_angle, th + fov_angle, 20):
            fov_x = x + C.MAX_RANGE * np.cos(angle)
            fov_y = y + C.MAX_RANGE * np.sin(angle)
            fov_points.append(to_screen([fov_x, fov_y]))
        
        # Draw semi-transparent FOV
        fov_surface = pygame.Surface(C.WINDOW_SIZE, pygame.SRCALPHA)
        pygame.draw.polygon(fov_surface, (*color, 30), fov_points)
        screen.blit(fov_surface, (0, 0))
        pygame.draw.lines(fov_surface, (*color, 80), False, [fov_points[0], fov_points[-1]], 1)
        pygame.draw.lines(fov_surface, (*color, 80), False, [fov_points[0], fov_points[len(fov_points)//2]], 1)
        screen.blit(fov_surface, (0, 0))
    
    # Draw wheels
    wheel_offset = body_radius * 0.7
    left_wheel_center = p + wheel_offset * np.array([-np.sin(th), np.cos(th)])
    right_wheel_center = p + wheel_offset * np.array([np.sin(th), -np.cos(th)])
    
    wheel_color = tuple(max(0, c - 50) for c in color)
    
    for wheel_center in [left_wheel_center, right_wheel_center]:
        wheel_p1 = wheel_center + (wheel_length/2/C.WINDOW_SCALE) * np.array([np.cos(th), np.sin(th)])
        wheel_p2 = wheel_center - (wheel_length/2/C.WINDOW_SCALE) * np.array([np.cos(th), np.sin(th)])
        pygame.draw.line(screen, wheel_color, to_screen(wheel_p1), to_screen(wheel_p2), wheel_width)
    
    # Draw robot body (circle with gradient effect)
    for r in range(body_radius, 0, -2):
        alpha = int(255 * (r / body_radius))
        shade = tuple(int(c * (0.6 + 0.4 * r / body_radius)) for c in color)
        pygame.draw.circle(screen, shade, screen_pos, r)
    
    # Draw direction indicator (arrow)
    arrow_length = body_radius * 1.5
    arrow_base = p + (body_radius * 0.3 / C.WINDOW_SCALE) * np.array([np.cos(th), np.sin(th)])
    arrow_tip = p + (arrow_length / C.WINDOW_SCALE) * np.array([np.cos(th), np.sin(th)])
    
    # Arrow shaft
    pygame.draw.line(screen, (255, 255, 255), to_screen(arrow_base), to_screen(arrow_tip), 3)
    
    # Arrow head
    arrow_head_length = 6
    arrow_head_angle = math.pi / 6
    left_head = arrow_tip - (arrow_head_length / C.WINDOW_SCALE) * np.array([
        np.cos(th - arrow_head_angle), np.sin(th - arrow_head_angle)
    ])
    right_head = arrow_tip - (arrow_head_length / C.WINDOW_SCALE) * np.array([
        np.cos(th + arrow_head_angle), np.sin(th + arrow_head_angle)
    ])
    
    pygame.draw.polygon(screen, (255, 255, 255), [
        to_screen(arrow_tip), to_screen(left_head), to_screen(right_head)
    ])
    
    # Draw outline
    outline_color = tuple(max(0, c - 80) for c in color)
    pygame.draw.circle(screen, outline_color, screen_pos, body_radius, 2)
    
    # Add label
    if font_small:
        label = "EST" if est else "TRUE"
        text = font_small.render(label, True, outline_color)
        screen.blit(text, (screen_pos[0] - 15, screen_pos[1] + body_radius + 5))

def draw_landmark(screen, lm, color=(0,150,0), est=False, lm_id=None):
    """Draw a realistic landmark with 3D effect"""
    screen_pos = to_screen(lm)
    size = 8 if not est else 6
    
    # Draw shadow
    shadow_offset = 3
    pygame.draw.circle(screen, (100, 100, 100, 100), 
                      (screen_pos[0] + shadow_offset, screen_pos[1] + shadow_offset), 
                      size, 0)
    
    # Draw landmark with gradient
    if est:
        # Estimated landmarks are squares
        rect = pygame.Rect(screen_pos[0] - size, screen_pos[1] - size, size * 2, size * 2)
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, tuple(max(0, c - 80) for c in color), rect, 2)
    else:
        # True landmarks are circles with gradient
        for r in range(size, 0, -1):
            shade = tuple(int(c * (0.5 + 0.5 * r / size)) for c in color)
            pygame.draw.circle(screen, shade, screen_pos, r)
        pygame.draw.circle(screen, tuple(max(0, c - 80) for c in color), screen_pos, size, 2)
    
    # Draw landmark ID
    if lm_id is not None and font_small:
        label = f"L{lm_id}"
        text = font_small.render(label, True, (50, 50, 50))
        screen.blit(text, (screen_pos[0] + size + 3, screen_pos[1] - size))

def draw_ellipse(screen, mean, cov, color=(200,0,0), n_std=2):
    """Draw covariance ellipse with better styling"""
    import numpy.linalg as LA
    sub = cov[:2,:2]
    if not np.all(np.isfinite(sub)): return
    try:
        w, v = LA.eig(sub)
    except LA.LinAlgError:
        return
    w = np.maximum(w, 1e-12)
    order = np.argsort(w)[::-1]
    w, v = w[order], v[:,order]
    angle = np.arctan2(v[1,0], v[0,0])
    
    # Draw multiple confidence levels
    for std_mult in [3, 2, 1]:
        a, b = std_mult*np.sqrt(np.real(w[0])), std_mult*np.sqrt(np.real(w[1]))
        pts = []
        for t in np.linspace(0, 2*np.pi, 50):
            q = np.array([a*np.cos(t), b*np.sin(t)])
            rot = np.array([[np.cos(angle), -np.sin(angle)],
                            [np.sin(angle),  np.cos(angle)]])
            p = mean[:2] + rot @ q
            pts.append(to_screen(p))
        
        if len(pts) >= 2:
            alpha = 255 - (std_mult - 1) * 60
            line_width = 2 if std_mult == 2 else 1
            adjusted_color = tuple(list(color) + [alpha]) if len(color) == 3 else color
            pygame.draw.lines(screen, color, True, pts, line_width)

def draw_trajectory(screen, trajectory, color=(100, 100, 255), label=None):
    """Draw robot trajectory path"""
    if len(trajectory) < 2:
        return
    
    points = [to_screen(pos[:2]) for pos in trajectory]
    
    # Draw trajectory line with gradient
    for i in range(len(points) - 1):
        alpha = int(100 + 155 * (i / len(points)))
        shade = tuple(int(c * (0.5 + 0.5 * i / len(points))) for c in color)
        pygame.draw.line(screen, shade, points[i], points[i + 1], 2)
    
    # Draw start marker
    if len(points) > 0:
        pygame.draw.circle(screen, (0, 255, 0), points[0], 6)
        pygame.draw.circle(screen, (0, 180, 0), points[0], 6, 2)
        if font_small:
            start_text = font_small.render("START", True, (0, 150, 0))
            screen.blit(start_text, (points[0][0] + 10, points[0][1] - 10))

def draw_observation_lines(screen, robot_pos, landmarks, observations):
    """Draw lines from robot to observed landmarks"""
    robot_screen = to_screen(robot_pos[:2])
    
    for (lm_id, z, R) in observations:
        if lm_id < len(landmarks):
            lm_pos = landmarks[lm_id]
            lm_screen = to_screen([lm_pos.x, lm_pos.y])
            
            # Draw dashed line
            draw_dashed_line(screen, robot_screen, lm_screen, (255, 200, 0), dash_length=5)

def draw_dashed_line(screen, start, end, color, dash_length=10):
    """Draw a dashed line between two points"""
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    distance = math.hypot(dx, dy)
    
    if distance == 0:
        return
    
    dashes = int(distance / dash_length)
    for i in range(0, dashes, 2):
        start_pos = (
            x1 + (dx * i / dashes),
            y1 + (dy * i / dashes)
        )
        end_pos = (
            x1 + (dx * (i + 1) / dashes),
            y1 + (dy * (i + 1) / dashes)
        )
        pygame.draw.line(screen, color, start_pos, end_pos, 1)

def draw_performance_overlay(screen, fps, step):
    """Draw FPS and performance info in top-left corner"""
    if not font_small:
        return
    
    overlay_texts = [
        f"FPS: {fps:.1f}",
        f"Step: {step}",
    ]
    
    y_pos = 10
    for text in overlay_texts:
        # Draw background
        text_surface = font_small.render(text, True, (255, 255, 255))
        bg_rect = text_surface.get_rect(topleft=(10, y_pos))
        bg_rect.inflate_ip(10, 4)
        
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surface, (0, 0, 0, 150), bg_surface.get_rect(), border_radius=5)
        screen.blit(bg_surface, bg_rect.topleft)
        
        # Draw text
        screen.blit(text_surface, (15, y_pos + 2))
        y_pos += 25

def draw_info_panel(screen, step, rmse, n_landmarks_init, robot_true, robot_est, ekf):
    """Draw information panel with stats"""
    panel_width = 280
    panel_height = C.WINDOW_SIZE[1]
    panel_x = C.WINDOW_SIZE[0] - panel_width
    
    # Draw semi-transparent background
    panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surface, (40, 40, 50, 220), (0, 0, panel_width, panel_height))
    pygame.draw.line(panel_surface, (100, 100, 120), (0, 0), (0, panel_height), 3)
    screen.blit(panel_surface, (panel_x, 0))
    
    y_offset = 20
    line_height = 25
    
    # Title
    if font_large:
        title = font_large.render("EKF-SLAM", True, (255, 255, 255))
        screen.blit(title, (panel_x + 20, y_offset))
        y_offset += 40
    
    # Draw sections
    sections = [
        ("SIMULATION", [
            f"Step: {step}/{C.SIM_STEPS}",
            f"Time: {step * C.DT:.1f}s",
            f"Mode: {'Bearing' if C.USE_BEARING_ONLY else 'Range+Bearing'}",
        ]),
        ("ROBOT STATE (TRUE)", [
            f"X: {robot_true[0]:6.2f} m",
            f"Y: {robot_true[1]:6.2f} m",
            f"θ: {math.degrees(robot_true[2]):6.1f}°",
        ]),
        ("ROBOT STATE (EST)", [
            f"X: {robot_est[0]:6.2f} m",
            f"Y: {robot_est[1]:6.2f} m",
            f"θ: {math.degrees(robot_est[2]):6.1f}°",
        ]),
        ("ERROR", [
            f"ΔX: {abs(robot_true[0] - robot_est[0]):6.3f} m",
            f"ΔY: {abs(robot_true[1] - robot_est[1]):6.3f} m",
            f"Δθ: {abs(math.degrees(wrap_angle(robot_true[2] - robot_est[2]))):6.2f}°",
        ]),
        ("LANDMARKS", [
            f"Initialized: {n_landmarks_init}/{C.NUM_LANDMARKS}",
            f"Total: {C.NUM_LANDMARKS}",
        ]),
        ("UNCERTAINTY", [
            f"Pos Cov: {np.trace(ekf.P[0:2, 0:2]):.4f}",
            f"Ang Cov: {ekf.P[2, 2]:.4f}",
        ])
    ]
    
    for section_title, items in sections:
        # Section header
        if font_medium:
            header = font_medium.render(section_title, True, (100, 200, 255))
            screen.blit(header, (panel_x + 15, y_offset))
            y_offset += line_height
        
        # Section items
        if font_small:
            for item in items:
                text = font_small.render(item, True, (220, 220, 220))
                screen.blit(text, (panel_x + 25, y_offset))
                y_offset += line_height - 5
        
        y_offset += 10
    
    # Legend at bottom
    y_offset = panel_height - 180
    if font_medium:
        legend_title = font_medium.render("LEGEND", True, (100, 200, 255))
        screen.blit(legend_title, (panel_x + 15, y_offset))
        y_offset += 30
    
    legend_items = [
        ((30, 30, 220), "■ True Robot"),
        ((220, 80, 0), "■ Est. Robot"),
        ((0, 140, 0), "● True Landmark"),
        ((0, 180, 0), "□ Est. Landmark"),
        ((200, 0, 0), "○ Uncertainty"),
    ]
    
    for color, text in legend_items:
        if font_small:
            pygame.draw.circle(screen, color, (panel_x + 25, y_offset + 6), 5)
            label = font_small.render(text, True, (220, 220, 220))
            screen.blit(label, (panel_x + 40, y_offset))
            y_offset += 22
