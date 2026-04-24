import pygame
import numpy as np
import math
from pygame.locals import *

# Initialize Pygame
pygame.init()

# Constants
WORLD_WIDTH, WORLD_HEIGHT = 600, 600
CAMERA_WIDTH, CAMERA_HEIGHT = 400, 300
MAP_WIDTH, MAP_HEIGHT = 400, 400
WINDOW_WIDTH = WORLD_WIDTH + max(CAMERA_WIDTH, MAP_WIDTH) + 30
WINDOW_HEIGHT = WORLD_HEIGHT + 150

# Colors
BLACK = (26, 26, 46)
WHITE = (255, 255, 255)
BLUE = (78, 205, 196)
RED = (255, 107, 107)
GREEN = (152, 216, 200)
YELLOW = (247, 220, 111)
ORANGE = (255, 160, 122)
CYAN = (69, 183, 209)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
PURPLE = (147, 112, 219)

class EKF_SLAM:
    def __init__(self):
        # Robot state [x, y, theta]
        self.state = np.array([100.0, 100.0, 0.0])
        
        # Covariance matrix (3x3 for robot pose)
        self.covariance = np.eye(3) * 1.0
        
        # Landmarks: list of {id, x, y, covariance, color, type}
        self.landmarks = []
        
        # Wall features: list of {id, x, y, covariance} (wall endpoints/corners)
        self.wall_features = []
        
        # Process noise
        self.Q = np.diag([0.1, 0.1, 0.05])
        
        # Measurement noise
        self.R = np.diag([5.0, 0.1])
        
        # Wall measurement noise (slightly higher)
        self.R_wall = np.diag([8.0, 0.15])
        
    def predict(self, v, omega, dt):
        """EKF Prediction step"""
        x, y, theta = self.state
        
        # Motion model
        if abs(omega) < 1e-5:
            # Straight line motion
            x_new = x + v * math.cos(theta) * dt
            y_new = y + v * math.sin(theta) * dt
            theta_new = theta
        else:
            # Arc motion
            x_new = x + v * math.cos(theta) * dt
            y_new = y + v * math.sin(theta) * dt
            theta_new = theta + omega * dt
        
        # Normalize angle
        theta_new = self.normalize_angle(theta_new)
        
        # Jacobian of motion model
        G = np.array([
            [1, 0, -v * math.sin(theta) * dt],
            [0, 1,  v * math.cos(theta) * dt],
            [0, 0,  1]
        ])
        
        # Update state
        self.state = np.array([x_new, y_new, theta_new])
        
        # Update covariance
        self.covariance = G @ self.covariance @ G.T + self.Q
        
    def update(self, landmark_id, measured_range, measured_bearing, true_landmark, is_wall=False):
        """EKF Update step when observing a landmark or wall feature"""
        x, y, theta = self.state
        
        # Choose appropriate list and noise
        features = self.wall_features if is_wall else self.landmarks
        R = self.R_wall if is_wall else self.R
        
        # Find if feature already exists
        feature_idx = None
        for i, feat in enumerate(features):
            if feat['id'] == landmark_id:
                feature_idx = i
                break
        
        # Initialize new feature if not seen before
        if feature_idx is None:
            feat_x = x + measured_range * math.cos(theta + measured_bearing)
            feat_y = y + measured_range * math.sin(theta + measured_bearing)
            
            new_feature = {
                'id': landmark_id,
                'x': feat_x,
                'y': feat_y,
                'covariance': np.eye(2) * 15.0 if is_wall else np.eye(2) * 10.0
            }
            
            if not is_wall:
                new_feature['color'] = true_landmark['color']
                new_feature['type'] = true_landmark['type']
            else:
                # Store the original wall position for matching
                new_feature['orig_x'] = true_landmark['orig_x'] if true_landmark else feat_x
                new_feature['orig_y'] = true_landmark['orig_y'] if true_landmark else feat_y
                new_feature['wall_idx'] = true_landmark.get('wall_idx', -1) if true_landmark else -1
                new_feature['point_id'] = true_landmark.get('point_id', -1) if true_landmark else -1
            
            features.append(new_feature)
            return
        
        # Update existing feature
        feature = features[feature_idx]
        feat_x, feat_y = feature['x'], feature['y']
        
        # Predicted measurement
        dx = feat_x - x
        dy = feat_y - y
        q = dx**2 + dy**2
        predicted_range = math.sqrt(q)
        predicted_bearing = math.atan2(dy, dx) - theta
        predicted_bearing = self.normalize_angle(predicted_bearing)
        
        # Innovation
        innovation_range = measured_range - predicted_range
        innovation_bearing = self.normalize_angle(measured_bearing - predicted_bearing)
        z = np.array([innovation_range, innovation_bearing])
        
        # Measurement Jacobian (w.r.t. robot pose)
        H = np.array([
            [-dx / predicted_range, -dy / predicted_range, 0],
            [dy / q, -dx / q, -1]
        ])
        
        # Innovation covariance
        S = H @ self.covariance @ H.T + R
        
        # Kalman gain
        K = self.covariance @ H.T @ np.linalg.inv(S)
        
        # Update state
        self.state += K @ z
        self.state[2] = self.normalize_angle(self.state[2])
        
        # Update covariance
        self.covariance = (np.eye(3) - K @ H) @ self.covariance
        
        # Update feature position (simplified)
        feat_innovation = np.array([
            measured_range * math.cos(theta + measured_bearing) - (feat_x - x),
            measured_range * math.sin(theta + measured_bearing) - (feat_y - y)
        ])
        
        K_feat = feature['covariance'] @ np.linalg.inv(feature['covariance'] + R)
        feature['x'] += K_feat[0, 0] * feat_innovation[0]
        feature['y'] += K_feat[1, 1] * feat_innovation[1]
        feature['covariance'] = (np.eye(2) - K_feat) @ feature['covariance']
        
    @staticmethod
    def normalize_angle(angle):
        """Normalize angle to [-pi, pi]"""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle


class Robot:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.theta = 0.0
        self.radius = 15
        self.speed = 0
        self.angular_speed = 0
        self.max_speed = 60
        self.max_angular_speed = 2.0
        
    def update(self, dt, walls):
        """Update robot position with collision detection"""
        if abs(self.speed) > 0.1 or abs(self.angular_speed) > 0.01:
            # Calculate new position
            new_x = self.x + self.speed * math.cos(self.theta) * dt
            new_y = self.y + self.speed * math.sin(self.theta) * dt
            new_theta = self.theta + self.angular_speed * dt
            
            # Normalize angle
            new_theta = EKF_SLAM.normalize_angle(new_theta)
            
            # Check collision
            if not self.check_collision(new_x, new_y, walls):
                self.x = new_x
                self.y = new_y
                self.theta = new_theta
                return True
        return False
    
    def check_collision(self, x, y, walls):
        """Check if robot collides with any wall"""
        for wall in walls:
            dist = self.distance_to_segment(x, y, wall['x1'], wall['y1'], 
                                           wall['x2'], wall['y2'])
            if dist < self.radius:
                return True
        return False
    
    @staticmethod
    def distance_to_segment(px, py, x1, y1, x2, y2):
        """Calculate distance from point to line segment"""
        dx = x2 - x1
        dy = y2 - y1
        l2 = dx * dx + dy * dy
        
        if l2 == 0:
            return math.sqrt((px - x1)**2 + (py - y1)**2)
        
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / l2))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        
        return math.sqrt((px - proj_x)**2 + (py - proj_y)**2)
    
    def detect_landmarks(self, landmarks, walls):
        """Detect landmarks within camera FOV"""
        view_distance = 150
        view_angle = math.pi / 3  # 60 degrees
        
        detected = []
        
        for landmark in landmarks:
            dx = landmark['x'] - self.x
            dy = landmark['y'] - self.y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance <= view_distance:
                angle = math.atan2(dy, dx) - self.theta
                angle = EKF_SLAM.normalize_angle(angle)
                
                if abs(angle) <= view_angle / 2:
                    # Check if not blocked by walls
                    if not self.is_blocked_by_wall_point(landmark['x'], landmark['y'], walls):
                        detected.append({
                            **landmark,
                            'range': distance,
                            'bearing': angle
                        })
        
        return detected
    
    def detect_wall_features(self, walls):
        """Detect wall endpoints/corners within camera FOV"""
        view_distance = 180
        view_angle = math.pi / 3
        
        detected = []
        seen_points = set()
        
        for wall_idx, wall in enumerate(walls):
            # Check both endpoints
            for point_id, (px, py) in enumerate([(wall['x1'], wall['y1']), 
                                                   (wall['x2'], wall['y2'])]):
                # Create unique ID for this point
                point_key = f"{int(px)}_{int(py)}"
                if point_key in seen_points:
                    continue
                
                dx = px - self.x
                dy = py - self.y
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance <= view_distance:
                    angle = math.atan2(dy, dx) - self.theta
                    angle = EKF_SLAM.normalize_angle(angle)
                    
                    if abs(angle) <= view_angle / 2:
                        # Simple line-of-sight check
                        if not self.is_point_blocked(px, py, walls):
                            feature_id = f"wall_{point_key}"
                            detected.append({
                                'id': feature_id,
                                'x': px,
                                'y': py,
                                'range': distance,
                                'bearing': angle,
                                'wall_idx': wall_idx,
                                'point_id': point_id
                            })
                            seen_points.add(point_key)
        
        return detected
    
    def is_point_blocked(self, px, py, walls):
        """Check if point is blocked by walls (simplified)"""
        # Check if line from robot to point crosses any wall
        for wall in walls:
            # Skip the wall if point is one of its endpoints
            if (abs(px - wall['x1']) < 5 and abs(py - wall['y1']) < 5) or \
               (abs(px - wall['x2']) < 5 and abs(py - wall['y2']) < 5):
                continue
                
            if self.line_intersects_wall(self.x, self.y, px, py, wall):
                return True
        return False
    
    def is_blocked_by_wall_point(self, px, py, walls):
        """Check if point is blocked by a wall"""
        for wall in walls:
            if self.line_intersects_wall(self.x, self.y, px, py, wall):
                return True
        return False
    
    @staticmethod
    def line_intersects_wall(x1, y1, x2, y2, wall):
        """Check if line intersects with wall"""
        wx1, wy1 = wall['x1'], wall['y1']
        wx2, wy2 = wall['x2'], wall['y2']
        
        denom = (wx2 - wx1) * (y2 - y1) - (wy2 - wy1) * (x2 - x1)
        
        if abs(denom) < 0.001:
            return False
        
        t = ((wy1 - y1) * (x2 - x1) - (wx1 - x1) * (y2 - y1)) / denom
        u = ((wy1 - y1) * (wx2 - wx1) - (wx1 - x1) * (wy2 - wy1)) / denom
        
        return 0.1 <= t <= 0.9 and 0.1 <= u <= 0.9


class MazeEnvironment:
    def __init__(self):
        # Define maze walls
        self.walls = [
            # Outer walls
            {'x1': 50, 'y1': 50, 'x2': 550, 'y2': 50},
            {'x1': 550, 'y1': 50, 'x2': 550, 'y2': 550},
            {'x1': 550, 'y1': 550, 'x2': 50, 'y2': 550},
            {'x1': 50, 'y1': 550, 'x2': 50, 'y2': 50},
            # Inner walls
            {'x1': 150, 'y1': 50, 'x2': 150, 'y2': 200},
            {'x1': 250, 'y1': 150, 'x2': 250, 'y2': 350},
            {'x1': 350, 'y1': 50, 'x2': 350, 'y2': 250},
            {'x1': 450, 'y1': 200, 'x2': 450, 'y2': 550},
            {'x1': 50, 'y1': 250, 'x2': 200, 'y2': 250},
            {'x1': 300, 'y1': 400, 'x2': 550, 'y2': 400},
        ]
        
        # Define landmarks
        self.landmarks = [
            {'id': 0, 'x': 120, 'y': 120, 'color': RED, 'type': 'circle'},
            {'id': 1, 'x': 400, 'y': 150, 'color': CYAN, 'type': 'square'},
            {'id': 2, 'x': 180, 'y': 350, 'color': BLUE, 'type': 'circle'},
            {'id': 3, 'x': 480, 'y': 480, 'color': ORANGE, 'type': 'square'},
            {'id': 4, 'x': 320, 'y': 280, 'color': GREEN, 'type': 'circle'},
            {'id': 5, 'x': 500, 'y': 100, 'color': YELLOW, 'type': 'square'},
        ]


def draw_world(screen, robot, maze, detected_landmarks, detected_walls):
    """Draw the world view"""
    # Background
    pygame.draw.rect(screen, BLACK, (10, 10, WORLD_WIDTH, WORLD_HEIGHT))
    
    # Draw walls
    for wall in maze.walls:
        pygame.draw.line(screen, WHITE, (wall['x1'] + 10, wall['y1'] + 10),
                        (wall['x2'] + 10, wall['y2'] + 10), 3)
        
        # Draw wall endpoints (to visualize what's being detected)
        pygame.draw.circle(screen, PURPLE, (int(wall['x1'] + 10), int(wall['y1'] + 10)), 4)
        pygame.draw.circle(screen, PURPLE, (int(wall['x2'] + 10), int(wall['y2'] + 10)), 4)
    
    # Draw landmarks
    for landmark in maze.landmarks:
        x, y = landmark['x'] + 10, landmark['y'] + 10
        if landmark['type'] == 'circle':
            pygame.draw.circle(screen, landmark['color'], (int(x), int(y)), 10)
        else:
            pygame.draw.rect(screen, landmark['color'], (x - 8, y - 8, 16, 16))
        pygame.draw.circle(screen, WHITE, (int(x), int(y)), 10, 2)
    
    # Draw FOV cone
    view_dist = 180
    view_angle = math.pi / 3
    points = [(robot.x + 10, robot.y + 10)]
    
    for i in range(20):
        angle = robot.theta - view_angle/2 + (view_angle * i / 19)
        px = robot.x + 10 + view_dist * math.cos(angle)
        py = robot.y + 10 + view_dist * math.sin(angle)
        points.append((px, py))
    
    s = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(s, (255, 255, 255, 20), points)
    screen.blit(s, (10, 10))
    
    # Highlight detected wall features
    for wall_feat in detected_walls:
        wx = int(wall_feat['x'] + 10)
        wy = int(wall_feat['y'] + 10)
        pygame.draw.circle(screen, YELLOW, (wx, wy), 6, 2)
    
    # Draw robot
    rx, ry = int(robot.x + 10), int(robot.y + 10)
    pygame.draw.circle(screen, BLUE, (rx, ry), robot.radius)
    
    # Direction indicator
    end_x = rx + int(robot.radius * 1.5 * math.cos(robot.theta))
    end_y = ry + int(robot.radius * 1.5 * math.sin(robot.theta))
    pygame.draw.line(screen, WHITE, (rx, ry), (end_x, end_y), 3)


def draw_camera_view(screen, detected_landmarks, detected_walls):
    """Draw the camera view"""
    x_offset = WORLD_WIDTH + 20
    y_offset = 10
    
    # Background
    pygame.draw.rect(screen, (15, 15, 30), (x_offset, y_offset, CAMERA_WIDTH, CAMERA_HEIGHT))
    
    # Crosshair
    pygame.draw.line(screen, GRAY, (x_offset + CAMERA_WIDTH//2, y_offset),
                    (x_offset + CAMERA_WIDTH//2, y_offset + CAMERA_HEIGHT), 1)
    pygame.draw.line(screen, GRAY, (x_offset, y_offset + CAMERA_HEIGHT//2),
                    (x_offset + CAMERA_WIDTH, y_offset + CAMERA_HEIGHT//2), 1)
    
    # Draw detected landmarks
    for landmark in detected_landmarks:
        screen_x = x_offset + CAMERA_WIDTH//2 + int(landmark['bearing'] * 300)
        screen_y = y_offset + CAMERA_HEIGHT//2 - int((150 / landmark['range']) * 50)
        size = max(10, int(800 / landmark['range']))
        
        if landmark['type'] == 'circle':
            pygame.draw.circle(screen, landmark['color'], (screen_x, screen_y), size//2)
        else:
            pygame.draw.rect(screen, landmark['color'], 
                           (screen_x - size//2, screen_y - size//2, size, size))
        
        # Info text
        font = pygame.font.Font(None, 16)
        text = font.render(f"ID:{landmark['id']}", True, WHITE)
        screen.blit(text, (screen_x - 20, screen_y + size//2 + 5))
    
    # Draw detected wall features
    for wall in detected_walls:
        screen_x = x_offset + CAMERA_WIDTH//2 + int(wall['bearing'] * 300)
        screen_y = y_offset + CAMERA_HEIGHT//2 - int((150 / wall['range']) * 50)
        size = max(8, int(600 / wall['range']))
        
        pygame.draw.circle(screen, PURPLE, (screen_x, screen_y), size//2, 2)
        pygame.draw.circle(screen, YELLOW, (screen_x, screen_y), 3)
    
    # Info
    font = pygame.font.Font(None, 18)
    text = font.render(f"Landmarks: {len(detected_landmarks)} | Walls: {len(detected_walls)}", 
                      True, BLUE)
    screen.blit(text, (x_offset + 10, y_offset + 10))
    
    # Border
    pygame.draw.rect(screen, WHITE, (x_offset, y_offset, CAMERA_WIDTH, CAMERA_HEIGHT), 2)


def draw_slam_map(screen, ekf, maze):
    """Draw the SLAM map"""
    x_offset = WORLD_WIDTH + 20
    y_offset = CAMERA_HEIGHT + 20
    scale = 0.67
    
    # Background
    pygame.draw.rect(screen, BLACK, (x_offset, y_offset, MAP_WIDTH, MAP_HEIGHT))
    
    # Draw grid
    for i in range(0, MAP_WIDTH + 1, 40):
        pygame.draw.line(screen, DARK_GRAY, (x_offset + i, y_offset),
                        (x_offset + i, y_offset + MAP_HEIGHT), 1)
        pygame.draw.line(screen, DARK_GRAY, (x_offset, y_offset + i),
                        (x_offset + MAP_WIDTH, y_offset + i), 1)
    
    # Group wall features by their original wall index
    wall_groups = {}
    for wall_feat in ekf.wall_features:
        if 'wall_idx' in wall_feat and wall_feat['wall_idx'] >= 0:
            wall_idx = wall_feat['wall_idx']
            if wall_idx not in wall_groups:
                wall_groups[wall_idx] = {}
            point_id = wall_feat.get('point_id', -1)
            if point_id >= 0:
                wall_groups[wall_idx][point_id] = wall_feat
    
    # Draw reconstructed walls - only if both endpoints are mapped
    for wall_idx, points in wall_groups.items():
        # Check if we have both endpoints (point_id 0 and 1)
        if 0 in points and 1 in points:
            feat1 = points[0]
            feat2 = points[1]
            
            x1 = int(feat1['x'] * scale) + x_offset
            y1 = int(feat1['y'] * scale) + y_offset
            x2 = int(feat2['x'] * scale) + x_offset
            y2 = int(feat2['y'] * scale) + y_offset
            
            # Draw the wall line
            pygame.draw.line(screen, PURPLE, (x1, y1), (x2, y2), 3)
    
    # Draw wall features with uncertainty
    for wall_feat in ekf.wall_features:
        wx = int(wall_feat['x'] * scale) + x_offset
        wy = int(wall_feat['y'] * scale) + y_offset
        
        # Draw uncertainty
        cov = wall_feat['covariance']
        std_x = int(math.sqrt(cov[0, 0]) * scale * 3)
        std_y = int(math.sqrt(cov[1, 1]) * scale * 3)
        
        s = pygame.Surface((max(std_x * 2, 10), max(std_y * 2, 10)), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (147, 112, 219, 40), (0, 0, max(std_x * 2, 10), max(std_y * 2, 10)))
        screen.blit(s, (wx - std_x, wy - std_y))
        
        # Draw wall point
        pygame.draw.circle(screen, PURPLE, (wx, wy), 4)
        pygame.draw.circle(screen, YELLOW, (wx, wy), 2)
    
    # Draw estimated landmarks
    for landmark in ekf.landmarks:
        lx = int(landmark['x'] * scale) + x_offset
        ly = int(landmark['y'] * scale) + y_offset
        
        # Uncertainty ellipse
        cov = landmark['covariance']
        std_x = int(math.sqrt(cov[0, 0]) * scale * 3)
        std_y = int(math.sqrt(cov[1, 1]) * scale * 3)
        
        s = pygame.Surface((std_x * 2, std_y * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (255, 107, 107, 50), (0, 0, std_x * 2, std_y * 2))
        screen.blit(s, (lx - std_x, ly - std_y))
        
        # Landmark
        if landmark['type'] == 'circle':
            pygame.draw.circle(screen, landmark['color'], (lx, ly), 5)
        else:
            pygame.draw.rect(screen, landmark['color'], (lx - 4, ly - 4, 8, 8))
        
        # ID
        font = pygame.font.Font(None, 14)
        text = font.render(str(landmark['id']), True, WHITE)
        screen.blit(text, (lx + 7, ly - 5))
    
    # Draw robot estimate
    rx = int(ekf.state[0] * scale) + x_offset
    ry = int(ekf.state[1] * scale) + y_offset
    
    # Uncertainty ellipse
    std_x = int(math.sqrt(ekf.covariance[0, 0]) * scale * 5)
    std_y = int(math.sqrt(ekf.covariance[1, 1]) * scale * 5)
    
    s = pygame.Surface((std_x * 2, std_y * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (78, 205, 196, 100), (0, 0, std_x * 2, std_y * 2), 2)
    screen.blit(s, (rx - std_x, ry - std_y))
    
    pygame.draw.circle(screen, BLUE, (rx, ry), 8)
    
    # Direction
    end_x = rx + int(15 * math.cos(ekf.state[2]))
    end_y = ry + int(15 * math.sin(ekf.state[2]))
    pygame.draw.line(screen, WHITE, (rx, ry), (end_x, end_y), 2)
    
    # Count complete walls (both endpoints mapped)
    complete_walls = sum(1 for points in wall_groups.values() if 0 in points and 1 in points)
    
    # Info
    font = pygame.font.Font(None, 18)
    text = font.render(f"Landmarks: {len(ekf.landmarks)}/{len(maze.landmarks)}", True, BLUE)
    screen.blit(text, (x_offset + 10, y_offset + 10))
    
    text = font.render(f"Wall Points: {len(ekf.wall_features)}", True, PURPLE)
    screen.blit(text, (x_offset + 10, y_offset + 28))
    
    text = font.render(f"Complete Walls: {complete_walls}/{len(maze.walls)}", True, PURPLE)
    screen.blit(text, (x_offset + 10, y_offset + 46))
    
    text = font.render(f"Pos: ({int(ekf.state[0])}, {int(ekf.state[1])})", True, BLUE)
    screen.blit(text, (x_offset + 10, y_offset + 64))
    
    theta_deg = int(math.degrees(ekf.state[2]))
    text = font.render(f"θ: {theta_deg}°", True, BLUE)
    screen.blit(text, (x_offset + 10, y_offset + 82))
    
    # Border
    pygame.draw.rect(screen, WHITE, (x_offset, y_offset, MAP_WIDTH, MAP_HEIGHT), 2)


def main():
    # Setup
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Camera-Based EKF-SLAM System with Wall Mapping")
    clock = pygame.time.Clock()
    
    # Initialize components
    maze = MazeEnvironment()
    robot = Robot(100, 100)
    ekf = EKF_SLAM()
    
    # Main loop
    running = True
    dt = 0.05
    
    font_title = pygame.font.Font(None, 30)
    font_text = pygame.font.Font(None, 18)
    
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
        
        # Handle input
        keys = pygame.key.get_pressed()
        robot.speed = 0
        robot.angular_speed = 0
        
        if keys[K_UP] or keys[K_w]:
            robot.speed = robot.max_speed
        if keys[K_DOWN] or keys[K_s]:
            robot.speed = -robot.max_speed
        if keys[K_LEFT] or keys[K_a]:
            robot.angular_speed = robot.max_angular_speed
        if keys[K_RIGHT] or keys[K_d]:
            robot.angular_speed = -robot.max_angular_speed
        
        # Update robot
        moved = robot.update(dt, maze.walls)
        
        # EKF Prediction
        if moved:
            ekf.predict(robot.speed, robot.angular_speed, dt)
        
        # Detect landmarks
        detected_landmarks = robot.detect_landmarks(maze.landmarks, maze.walls)
        
        # Detect wall features
        detected_walls = robot.detect_wall_features(maze.walls)
        
        # EKF Update for landmarks
        for landmark in detected_landmarks:
            true_lm = next(lm for lm in maze.landmarks if lm['id'] == landmark['id'])
            ekf.update(landmark['id'], landmark['range'], landmark['bearing'], 
                      true_lm, is_wall=False)
        
        # EKF Update for wall features
        for wall_feat in detected_walls:
            # Pass the original wall information
            wall_info = {
                'orig_x': wall_feat['x'],
                'orig_y': wall_feat['y'],
                'wall_idx': wall_feat['wall_idx'],
                'point_id': wall_feat['point_id']
            }
            ekf.update(wall_feat['id'], wall_feat['range'], wall_feat['bearing'],
                      wall_info, is_wall=True)
        
        # Draw
        screen.fill((20, 20, 40))
        
        
        # Draw views
        draw_world(screen, robot, maze, detected_landmarks, detected_walls)
        draw_camera_view(screen, detected_landmarks, detected_walls)
        draw_slam_map(screen, ekf, maze)
        
        # Labels
        label_world = font_text.render("Environment View", True, WHITE)
        screen.blit(label_world, (15, WORLD_HEIGHT + 15))
        
        label_camera = font_text.render("Camera View", True, WHITE)
        screen.blit(label_camera, (WORLD_WIDTH + 25, CAMERA_HEIGHT + 5))
        
        label_map = font_text.render("SLAM Map (Estimated)", True, WHITE)
        screen.blit(label_map, (WORLD_WIDTH + 25, CAMERA_HEIGHT + MAP_HEIGHT + 25))
        
        pygame.display.flip()
        clock.tick(20)
    
    pygame.quit()


if __name__ == "__main__":
    main()