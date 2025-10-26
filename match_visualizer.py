"""
Match Action Visualizer - Enhanced Version
Generates high-quality real-time visualizations for player actions during matches
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import random
import math
from typing import Tuple, Optional, Dict

class CoordinateMapper:
    """Maps match events to pitch coordinates (StatsBomb format: 120x80)"""
    
    # Pitch dimensions (StatsBomb standard)
    PITCH_LENGTH = 120
    PITCH_WIDTH = 80
    
    # Position base coordinates (x, y)
    POSITIONS = {
        'GK': (10, 40),
        'CB': (25, 40),
        'LCB': (25, 30),
        'RCB': (25, 50),
        'FB': (25, 20),
        'LB': (25, 15),
        'RB': (25, 65),
        'CDM': (40, 40),
        'CM': (55, 40),
        'LCM': (55, 30),
        'RCM': (55, 50),
        'CAM': (70, 40),
        'W': (60, 15),
        'LW': (60, 15),
        'RW': (60, 65),
        'ST': (90, 40),
    }
    
    @staticmethod
    def get_position_coordinates(position: str, is_home_team: bool) -> Tuple[float, float]:
        """Get default coordinates for player positions"""
        x, y = CoordinateMapper.POSITIONS.get(position, (60, 40))
        
        if not is_home_team:
            # Flip coordinates for away team (they attack opposite direction)
            x = CoordinateMapper.PITCH_LENGTH - x
            y = CoordinateMapper.PITCH_WIDTH - y
            
        return x, y
    
    @staticmethod
    def get_action_coordinates(action: str, player_position: str, is_home_team: bool, 
                              scenario_type: Optional[str] = None) -> Tuple[float, float, float, float]:
        """Generate realistic coordinates for different actions"""
        
        base_x, base_y = CoordinateMapper.get_position_coordinates(player_position, is_home_team)
        
        # Add variance for realism
        x_variance = random.uniform(-5, 5)
        y_variance = random.uniform(-5, 5)
        
        start_x = max(0, min(CoordinateMapper.PITCH_LENGTH, base_x + x_variance))
        start_y = max(0, min(CoordinateMapper.PITCH_WIDTH, base_y + y_variance))
        
        # Calculate end coordinates based on action
        direction = 1 if is_home_team else -1
        
        if action in ['shoot', 'header']:
            # Shots go toward goal
            if is_home_team:
                end_x = CoordinateMapper.PITCH_LENGTH
                end_y = 40 + random.uniform(-3.66, 3.66)  # Goal is 7.32m wide
            else:
                end_x = 0
                end_y = 40 + random.uniform(-3.66, 3.66)
                
        elif action in ['pass', 'through_ball', 'key_pass']:
            # Forward passes
            end_x = start_x + (random.uniform(10, 25) * direction)
            end_y = start_y + random.uniform(-10, 10)
            
        elif action == 'cross':
            # Crosses go into the box
            if is_home_team:
                end_x = random.uniform(100, 118)
                end_y = random.uniform(20, 60)
            else:
                end_x = random.uniform(2, 20)
                end_y = random.uniform(20, 60)
                
        elif action in ['dribble', 'cut_inside']:
            # Dribbles move forward
            end_x = start_x + (random.uniform(5, 15) * direction)
            end_y = start_y + random.uniform(-5, 5)
            
        elif action == 'long_ball':
            # Long passes
            end_x = start_x + (random.uniform(30, 50) * direction)
            end_y = start_y + random.uniform(-20, 20)
            
        elif action in ['tackle', 'interception', 'block']:
            # Defensive actions - small movement
            end_x = start_x + (random.uniform(-3, 3) * direction)
            end_y = start_y + random.uniform(-3, 3)
            
        elif action == 'clearance':
            # Clearances go far
            end_x = start_x + (random.uniform(20, 40) * direction)
            end_y = start_y + random.uniform(-15, 15)
            
        elif action in ['save', 'claim_cross']:
            # GK actions
            end_x = start_x
            end_y = start_y
            
        else:
            # Default: small movement
            end_x = start_x + random.uniform(-3, 3)
            end_y = start_y + random.uniform(-3, 3)
        
        # Clamp to pitch boundaries
        end_x = max(0, min(CoordinateMapper.PITCH_LENGTH, end_x))
        end_y = max(0, min(CoordinateMapper.PITCH_WIDTH, end_y))
        
        return (start_x, start_y, end_x, end_y)


class QuickMatchVisualizer:
    """Generate high-quality static images showing actions"""
    
    # Image dimensions (5x scale of StatsBomb pitch)
    WIDTH = 600
    HEIGHT = 400
    SCALE = 5  # 120x80 -> 600x400
    
    # Enhanced Colors
    GRASS_COLOR = '#1a5d1a'  # Rich grass green
    GRASS_STRIPE_COLOR = '#165016'  # Darker stripe for pattern
    LINE_COLOR = '#ffffff'
    PLAYER_COLOR = '#0066ff'
    PLAYER_SHADOW = '#003380'
    DEFENDER_COLOR = '#ff3333'
    DEFENDER_SHADOW = '#991f1f'
    SUCCESS_COLOR = '#00ff00'
    SUCCESS_GLOW = '#00ff0040'
    FAIL_COLOR = '#ff0000'
    FAIL_GLOW = '#ff000040'
    BALL_COLOR = '#ffffff'
    BALL_SHADOW = '#cccccc'
    GOAL_GOLD = '#FFD700'
    
    @staticmethod
    def draw_grass_pattern(img: Image.Image):
        """Draw realistic grass stripes"""
        draw = ImageDraw.Draw(img)
        stripe_width = 40
        for i in range(0, QuickMatchVisualizer.WIDTH, stripe_width * 2):
            draw.rectangle([i, 0, i + stripe_width, QuickMatchVisualizer.HEIGHT],
                          fill=QuickMatchVisualizer.GRASS_STRIPE_COLOR)
    
    @staticmethod
    def draw_pitch(draw: ImageDraw.Draw):
        """Draw a detailed football pitch with all markings"""
        # Outer border
        draw.rectangle([0, 0, QuickMatchVisualizer.WIDTH-1, QuickMatchVisualizer.HEIGHT-1], 
                      outline=QuickMatchVisualizer.LINE_COLOR, width=3)
        
        # Halfway line
        draw.line([QuickMatchVisualizer.WIDTH//2, 0, 
                  QuickMatchVisualizer.WIDTH//2, QuickMatchVisualizer.HEIGHT], 
                 fill=QuickMatchVisualizer.LINE_COLOR, width=3)
        
        # Center circle
        center_x = QuickMatchVisualizer.WIDTH // 2
        center_y = QuickMatchVisualizer.HEIGHT // 2
        radius = 50
        draw.ellipse([center_x-radius, center_y-radius, center_x+radius, center_y+radius],
                    outline=QuickMatchVisualizer.LINE_COLOR, width=3)
        
        # Center spot
        draw.ellipse([center_x-4, center_y-4, center_x+4, center_y+4],
                    fill=QuickMatchVisualizer.LINE_COLOR)
        
        # Penalty boxes
        box_width = 90
        box_height = 220
        box_y = (QuickMatchVisualizer.HEIGHT - box_height) // 2
        
        # Left penalty box
        draw.rectangle([0, box_y, box_width, box_y + box_height],
                      outline=QuickMatchVisualizer.LINE_COLOR, width=3)
        
        # Right penalty box  
        draw.rectangle([QuickMatchVisualizer.WIDTH - box_width, box_y, 
                       QuickMatchVisualizer.WIDTH, box_y + box_height],
                      outline=QuickMatchVisualizer.LINE_COLOR, width=3)
        
        # 6-yard boxes
        small_box_width = 30
        small_box_height = 110
        small_box_y = (QuickMatchVisualizer.HEIGHT - small_box_height) // 2
        
        # Left 6-yard box
        draw.rectangle([0, small_box_y, small_box_width, small_box_y + small_box_height],
                      outline=QuickMatchVisualizer.LINE_COLOR, width=3)
        
        # Right 6-yard box
        draw.rectangle([QuickMatchVisualizer.WIDTH - small_box_width, small_box_y, 
                       QuickMatchVisualizer.WIDTH, small_box_y + small_box_height],
                      outline=QuickMatchVisualizer.LINE_COLOR, width=3)
        
        # Penalty spots
        penalty_spot_x = 60
        # Left penalty spot
        draw.ellipse([penalty_spot_x-4, center_y-4, penalty_spot_x+4, center_y+4],
                    fill=QuickMatchVisualizer.LINE_COLOR)
        # Right penalty spot
        draw.ellipse([QuickMatchVisualizer.WIDTH - penalty_spot_x-4, center_y-4, 
                     QuickMatchVisualizer.WIDTH - penalty_spot_x+4, center_y+4],
                    fill=QuickMatchVisualizer.LINE_COLOR)
        
        # Penalty arcs
        arc_radius = 50
        # Left arc
        draw.arc([penalty_spot_x - arc_radius, center_y - arc_radius,
                 penalty_spot_x + arc_radius, center_y + arc_radius],
                start=310, end=50, fill=QuickMatchVisualizer.LINE_COLOR, width=3)
        # Right arc
        draw.arc([QuickMatchVisualizer.WIDTH - penalty_spot_x - arc_radius, center_y - arc_radius,
                 QuickMatchVisualizer.WIDTH - penalty_spot_x + arc_radius, center_y + arc_radius],
                start=130, end=230, fill=QuickMatchVisualizer.LINE_COLOR, width=3)
        
        # Corner arcs
        corner_radius = 15
        # Top left
        draw.arc([0, 0, corner_radius*2, corner_radius*2],
                start=0, end=90, fill=QuickMatchVisualizer.LINE_COLOR, width=3)
        # Top right
        draw.arc([QuickMatchVisualizer.WIDTH - corner_radius*2, 0,
                 QuickMatchVisualizer.WIDTH, corner_radius*2],
                start=90, end=180, fill=QuickMatchVisualizer.LINE_COLOR, width=3)
        # Bottom left
        draw.arc([0, QuickMatchVisualizer.HEIGHT - corner_radius*2,
                 corner_radius*2, QuickMatchVisualizer.HEIGHT],
                start=270, end=360, fill=QuickMatchVisualizer.LINE_COLOR, width=3)
        # Bottom right
        draw.arc([QuickMatchVisualizer.WIDTH - corner_radius*2, 
                 QuickMatchVisualizer.HEIGHT - corner_radius*2,
                 QuickMatchVisualizer.WIDTH, QuickMatchVisualizer.HEIGHT],
                start=180, end=270, fill=QuickMatchVisualizer.LINE_COLOR, width=3)
        
        # Goals (3D effect)
        goal_width = 8
        goal_height = 44
        goal_y = (QuickMatchVisualizer.HEIGHT - goal_height) // 2
        
        # Left goal
        draw.rectangle([0, goal_y, goal_width, goal_y + goal_height],
                      fill=QuickMatchVisualizer.LINE_COLOR, outline='#cccccc', width=2)
        # Right goal
        draw.rectangle([QuickMatchVisualizer.WIDTH - goal_width, goal_y,
                       QuickMatchVisualizer.WIDTH, goal_y + goal_height],
                      fill=QuickMatchVisualizer.LINE_COLOR, outline='#cccccc', width=2)
    
    @staticmethod
    def scale_coords(x: float, y: float) -> Tuple[int, int]:
        """Scale StatsBomb coords (120x80) to image coords (600x400)"""
        return int(x * QuickMatchVisualizer.SCALE), int(y * QuickMatchVisualizer.SCALE)
    
    @staticmethod
    def draw_glow(draw: ImageDraw.Draw, x: int, y: int, color: str, size: int = 30):
        """Draw a glowing effect"""
        for i in range(4):
            radius = size + (i * 8)
            alpha = 255 - (i * 50)
            draw.ellipse([x-radius, y-radius, x+radius, y+radius],
                        outline=color, width=2)
    
    @staticmethod
    def draw_arrow(draw: ImageDraw.Draw, start: Tuple[int, int], end: Tuple[int, int], 
                   color: str, width: int = 5, glow: bool = True):
        """Draw an enhanced arrow with glow effect"""
        # Glow effect
        if glow:
            for offset in range(3, 0, -1):
                alpha = 255 - (offset * 60)
                glow_color = color + f'{alpha:02x}'
                draw.line([start[0], start[1], end[0], end[1]], 
                         fill=glow_color, width=width + offset*2)
        
        # Main line
        draw.line([start[0], start[1], end[0], end[1]], fill=color, width=width)
        
        # Enhanced arrow head
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        arrow_length = 18
        arrow_angle = math.pi / 5  # 36 degrees
        
        left_x = end[0] - arrow_length * math.cos(angle - arrow_angle)
        left_y = end[1] - arrow_length * math.sin(angle - arrow_angle)
        right_x = end[0] - arrow_length * math.cos(angle + arrow_angle)
        right_y = end[1] - arrow_length * math.sin(angle + arrow_angle)
        
        draw.polygon([end, (int(left_x), int(left_y)), (int(right_x), int(right_y))],
                    fill=color, outline=color)
    
    @staticmethod
    def draw_curved_path(draw: ImageDraw.Draw, start: Tuple[int, int], end: Tuple[int, int],
                        color: str, curve_height: int = 35):
        """Draw an enhanced curved dribble path with glow"""
        points = []
        for i in range(20):
            t = i / 19
            # Quadratic bezier curve
            x = start[0] + (end[0] - start[0]) * t
            y = start[1] + (end[1] - start[1]) * t + curve_height * (4 * t * (1 - t))
            points.append((x, y))
        
        # Draw glow trail
        for i, point in enumerate(points):
            alpha = int(100 + 155 * (i / len(points)))
            radius = 4 + i // 4
            # Outer glow
            draw.ellipse([point[0]-radius-3, point[1]-radius-3, 
                         point[0]+radius+3, point[1]+radius+3],
                        fill=color + '40')
            # Inner circle
            draw.ellipse([point[0]-radius, point[1]-radius, 
                         point[0]+radius, point[1]+radius],
                        fill=color)
    
    @staticmethod
    def draw_player(draw: ImageDraw.Draw, x: int, y: int, color: str, 
                   shadow_color: str, size: int = 18):
        """Draw a player with shadow and 3D effect"""
        # Shadow
        draw.ellipse([x-size+2, y-size+2, x+size+2, y+size+2],
                    fill=shadow_color)
        
        # Outer ring (border)
        draw.ellipse([x-size, y-size, x+size, y+size],
                    fill='white', outline='white', width=2)
        
        # Inner circle (jersey)
        draw.ellipse([x-size+3, y-size+3, x+size-3, y+size-3],
                    fill=color, outline='white', width=2)
        
        # Highlight for 3D effect
        highlight_offset = 4
        draw.ellipse([x-highlight_offset, y-highlight_offset, 
                     x+highlight_offset, y+highlight_offset],
                    fill='#ffffff60')
    
    @staticmethod
    def draw_ball(draw: ImageDraw.Draw, x: int, y: int, size: int = 10):
        """Draw a 3D ball with shading"""
        # Shadow
        draw.ellipse([x-size+1, y-size+1, x+size+1, y+size+1],
                    fill='#00000060')
        
        # Ball body
        draw.ellipse([x-size, y-size, x+size, y+size],
                    fill=QuickMatchVisualizer.BALL_COLOR,
                    outline='#cccccc', width=2)
        
        # Highlight for 3D effect
        highlight_size = size // 2
        draw.ellipse([x-highlight_size, y-highlight_size, 
                     x+highlight_size-2, y+highlight_size-2],
                    fill='#ffffff80')
        
        # Pentagon pattern (simplified)
        draw.line([x-3, y-3, x+3, y-3], fill='#000000', width=1)
        draw.line([x-3, y+3, x+3, y+3], fill='#000000', width=1)
    
    @staticmethod
    def get_font(size: int = 20):
        """Get font, with fallback"""
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        except:
            try:
                return ImageFont.truetype("arial.ttf", size)
            except:
                return ImageFont.load_default()
    
    @staticmethod
    def draw_text_with_shadow(draw: ImageDraw.Draw, position: Tuple[int, int], 
                             text: str, font, color: str, shadow_offset: int = 2):
        """Draw text with shadow for better readability"""
        x, y = position
        # Shadow
        draw.text((x + shadow_offset, y + shadow_offset), text, 
                 fill='#000000aa', font=font)
        # Main text
        draw.text((x, y), text, fill=color, font=font)
    
    @staticmethod
    def create_action_image(action: str, player_name: str, player_position: str,
                          defender_name: Optional[str], start_pos: Tuple[float, float],
                          end_pos: Tuple[float, float], success: bool,
                          is_goal: bool = False) -> Image.Image:
        """
        Create a high-quality static image showing the action
        
        Args:
            action: Action type (shoot, pass, dribble, etc.)
            player_name: Name of the player
            player_position: Player's position (ST, CM, etc.)
            defender_name: Name of defender (if applicable)
            start_pos: (x, y) in StatsBomb coords
            end_pos: (x, y) in StatsBomb coords
            success: Whether action succeeded
            is_goal: Whether it resulted in a goal
        """
        # Create base image with grass pattern
        img = Image.new('RGB', (QuickMatchVisualizer.WIDTH, QuickMatchVisualizer.HEIGHT),
                       color=QuickMatchVisualizer.GRASS_COLOR)
        QuickMatchVisualizer.draw_grass_pattern(img)
        
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # Draw pitch
        QuickMatchVisualizer.draw_pitch(draw)
        
        # Scale coordinates
        sx, sy = QuickMatchVisualizer.scale_coords(start_pos[0], start_pos[1])
        ex, ey = QuickMatchVisualizer.scale_coords(end_pos[0], end_pos[1])
        
        # Determine color based on success
        if is_goal:
            action_color = QuickMatchVisualizer.GOAL_GOLD
        else:
            action_color = QuickMatchVisualizer.SUCCESS_COLOR if success else QuickMatchVisualizer.FAIL_COLOR
        
        # Draw action-specific visualization
        if action in ['pass', 'through_ball', 'key_pass', 'cross', 'long_ball']:
            # Draw pass arrow with glow
            QuickMatchVisualizer.draw_arrow(draw, (sx, sy), (ex, ey), action_color, width=6)
            
            # Draw ball at end position
            QuickMatchVisualizer.draw_ball(draw, ex, ey, size=10)
            
        elif action in ['shoot', 'header']:
            # Draw shot trajectory with enhanced effects
            QuickMatchVisualizer.draw_arrow(draw, (sx, sy), (ex, ey), action_color, width=7)
            
            # Explosion/impact effect at end
            QuickMatchVisualizer.draw_glow(draw, ex, ey, action_color, size=25)
            for i in range(3):
                radius = 12 + (i * 6)
                draw.ellipse([ex-radius, ey-radius, ex+radius, ey+radius],
                           outline=action_color, width=3)
            
            # Ball
            QuickMatchVisualizer.draw_ball(draw, ex, ey, size=12)
            
        elif action in ['dribble', 'cut_inside']:
            # Draw curved dribble path with enhanced trail
            QuickMatchVisualizer.draw_curved_path(draw, (sx, sy), (ex, ey), action_color, curve_height=40)
            
            # Ball at end
            QuickMatchVisualizer.draw_ball(draw, ex, ey, size=10)
            
        elif action in ['tackle', 'block', 'interception']:
            # Draw defensive action with impact
            # Impact starburst
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                line_end_x = sx + int(20 * math.cos(rad))
                line_end_y = sy + int(20 * math.sin(rad))
                draw.line([sx, sy, line_end_x, line_end_y], 
                         fill=action_color, width=4)
            
            # Impact circles
            for i in range(3):
                radius = 18 + (i * 8)
                draw.ellipse([sx-radius, sy-radius, sx+radius, sy+radius],
                           outline=action_color, width=3)
            
        elif action == 'clearance':
            # Long clearance arrow with emphasis
            QuickMatchVisualizer.draw_arrow(draw, (sx, sy), (ex, ey), action_color, width=6)
            QuickMatchVisualizer.draw_ball(draw, ex, ey, size=9)
            
        else:
            # Generic action - enhanced line
            QuickMatchVisualizer.draw_arrow(draw, (sx, sy), (ex, ey), action_color, width=5)
        
        # Draw defender if exists
        if defender_name and action not in ['save', 'claim_cross']:
            # Place defender near action
            dx, dy = (ex + sx) // 2, (ey + sy) // 2
            QuickMatchVisualizer.draw_player(draw, dx, dy, 
                                            QuickMatchVisualizer.DEFENDER_COLOR,
                                            QuickMatchVisualizer.DEFENDER_SHADOW, size=18)
        
        # Draw player
        QuickMatchVisualizer.draw_player(draw, sx, sy, 
                                        QuickMatchVisualizer.PLAYER_COLOR,
                                        QuickMatchVisualizer.PLAYER_SHADOW, size=18)
        
        # Add text overlays
        font_large = QuickMatchVisualizer.get_font(26)
        font_medium = QuickMatchVisualizer.get_font(20)
        font_small = QuickMatchVisualizer.get_font(16)
        
        # Result text at top
        if is_goal:
            result_text = "⚽ GOAL!"
            text_color = QuickMatchVisualizer.GOAL_GOLD
        elif success:
            result_text = "✓ SUCCESS"
            text_color = QuickMatchVisualizer.SUCCESS_COLOR
        else:
            result_text = "✗ FAILED"
            text_color = QuickMatchVisualizer.FAIL_COLOR
        
        # Draw text background with rounded corners
        bbox = draw.textbbox((0, 0), result_text, font=font_large)
        text_width = bbox[2] - bbox[0] + 30
        text_height = bbox[3] - bbox[1] + 15
        
        # Semi-transparent background
        draw.rectangle([10, 10, 10 + text_width, 10 + text_height],
                      fill='#000000cc', outline='white', width=3)
        QuickMatchVisualizer.draw_text_with_shadow(draw, (25, 15), result_text, 
                                                  font_large, text_color, shadow_offset=3)
        
        # Action type at bottom left
        action_text = action.replace('_', ' ').upper()
        action_bbox = draw.textbbox((0, 0), action_text, font=font_medium)
        action_width = action_bbox[2] - action_bbox[0] + 30
        
        draw.rectangle([10, QuickMatchVisualizer.HEIGHT - 50, 
                       10 + action_width, QuickMatchVisualizer.HEIGHT - 10],
                      fill='#000000cc', outline='white', width=3)
        QuickMatchVisualizer.draw_text_with_shadow(draw, (25, QuickMatchVisualizer.HEIGHT - 45), 
                                                  action_text, font_medium, 'white')
        
        # Player name at bottom right
        player_text = f"{player_name} ({player_position})"
        player_bbox = draw.textbbox((0, 0), player_text, font=font_small)
        player_width = player_bbox[2] - player_bbox[0] + 30
        
        draw.rectangle([QuickMatchVisualizer.WIDTH - player_width - 10, 
                       QuickMatchVisualizer.HEIGHT - 40,
                       QuickMatchVisualizer.WIDTH - 10, 
                       QuickMatchVisualizer.HEIGHT - 10],
                      fill='#000000cc', outline='white', width=2)
        QuickMatchVisualizer.draw_text_with_shadow(
            draw, 
            (QuickMatchVisualizer.WIDTH - player_width + 5, QuickMatchVisualizer.HEIGHT - 35),
            player_text, font_small, 'white')
        
        return img


class SimpleAnimator:
    """Generate high-quality animated GIFs for actions"""
    
    @staticmethod
    def create_action_gif(action: str, player_name: str, player_position: str,
                         defender_name: Optional[str], start_pos: Tuple[float, float],
                         end_pos: Tuple[float, float], success: bool,
                         is_goal: bool = False, frames: int = 15) -> io.BytesIO:
        """
        Create an enhanced animated GIF showing the action
        
        Args:
            action: Action type
            player_name: Player's name
            player_position: Player's position
            defender_name: Defender's name (optional)
            start_pos: Start coordinates
            end_pos: End coordinates
            success: Whether successful
            is_goal: Whether it resulted in a goal
            frames: Number of frames to generate
            
        Returns:
            BytesIO buffer containing the GIF
        """
        images = []
        
        sx, sy = QuickMatchVisualizer.scale_coords(start_pos[0], start_pos[1])
        ex, ey = QuickMatchVisualizer.scale_coords(end_pos[0], end_pos[1])
        
        for frame in range(frames):
            # Create base image with grass pattern
            img = Image.new('RGB', (QuickMatchVisualizer.WIDTH, QuickMatchVisualizer.HEIGHT),
                           color=QuickMatchVisualizer.GRASS_COLOR)
            QuickMatchVisualizer.draw_grass_pattern(img)
            
            draw = ImageDraw.Draw(img, 'RGBA')
            
            # Draw pitch
            QuickMatchVisualizer.draw_pitch(draw)
            
            # Calculate progress with easing
            progress = frame / (frames - 1) if frames > 1 else 1
            # Ease-out effect
            eased_progress = 1 - (1 - progress) ** 2
            
            # Current position
            if action in ['dribble', 'cut_inside']:
                # Curved path
                current_x = sx + (ex - sx) * eased_progress
                current_y = sy + (ey - sy) * eased_progress + 35 * (4 * eased_progress * (1-eased_progress))
            else:
                current_x = sx + (ex - sx) * eased_progress
                current_y = sy + (ey - sy) * eased_progress
            
            # Draw trail
            if frame > 0:
                if action in ['dribble', 'cut_inside']:
                    # Curved trail
                    for i in range(frame + 1):
                        t = i / frames
                        trail_x = sx + (ex - sx) * t
                        trail_y = sy + (ey - sy) * t + 35 * (4 * t * (1-t))
                        alpha = int(80 + 175 * (i / (frame + 1)))
                        radius = 3 + i // 3
                        
                        # Glow
                        draw.ellipse([trail_x-radius-2, trail_y-radius-2, 
                                     trail_x+radius+2, trail_y+radius+2],
                                    fill='#ffff0060')
                        # Core
                        draw.ellipse([trail_x-radius, trail_y-radius, 
                                     trail_x+radius, trail_y+radius],
                                    fill='#ffff00')
                else:
                    # Straight trail with glow
                    for offset in range(2, 0, -1):
                        draw.line([sx, sy, current_x, current_y],
                                 fill=f'#ffff00{60-offset*20:02x}', width=4 + offset*2)
                    draw.line([sx, sy, current_x, current_y],
                             fill='#ffff00', width=4)
            
            # Draw player at start
            QuickMatchVisualizer.draw_player(draw, sx, sy, 
                                            QuickMatchVisualizer.PLAYER_COLOR,
                                            QuickMatchVisualizer.PLAYER_SHADOW, size=18)
            
            # Draw defender if exists
            if defender_name and action not in ['save', 'claim_cross']:
                dx = (ex + sx) // 2
                dy = (ey + sy) // 2
                QuickMatchVisualizer.draw_player(draw, dx, dy, 
                                                QuickMatchVisualizer.DEFENDER_COLOR,
                                                QuickMatchVisualizer.DEFENDER_SHADOW, size=18)
            
            # Draw ball at current position with pulsing effect
            ball_size = 10 + int(3 * math.sin(progress * math.pi))
            QuickMatchVisualizer.draw_ball(draw, int(current_x), int(current_y), size=ball_size)
            
            # Add action label
            font = QuickMatchVisualizer.get_font(22)
            action_text = action.replace('_', ' ').upper()
            action_bbox = draw.textbbox((0, 0), action_text, font=font)
            action_width = action_bbox[2] - action_bbox[0] + 30
            
            draw.rectangle([10, 10, 10 + action_width, 50], 
                          fill='#000000cc', outline='white', width=3)
            QuickMatchVisualizer.draw_text_with_shadow(draw, (25, 15), action_text, 
                                                      font, 'white')
            
            images.append(img)
        
        # Add final result frames (hold for emphasis)
        final_img = Image.new('RGB', (QuickMatchVisualizer.WIDTH, QuickMatchVisualizer.HEIGHT),
                             color=QuickMatchVisualizer.GRASS_COLOR)
        QuickMatchVisualizer.draw_grass_pattern(final_img)
        
        draw = ImageDraw.Draw(final_img, 'RGBA')
        QuickMatchVisualizer.draw_pitch(draw)
        
        # Determine final color
        if is_goal:
            final_color = QuickMatchVisualizer.GOAL_GOLD
        else:
            final_color = QuickMatchVisualizer.SUCCESS_COLOR if success else QuickMatchVisualizer.FAIL_COLOR
        
        # Draw complete action on final frame
        if action in ['shoot', 'header']:
            QuickMatchVisualizer.draw_arrow(draw, (sx, sy), (ex, ey), final_color, width=7)
            QuickMatchVisualizer.draw_glow(draw, ex, ey, final_color, size=30)
        elif action in ['pass', 'through_ball', 'key_pass', 'cross']:
            QuickMatchVisualizer.draw_arrow(draw, (sx, sy), (ex, ey), final_color, width=6)
        elif action in ['dribble', 'cut_inside']:
            QuickMatchVisualizer.draw_curved_path(draw, (sx, sy), (ex, ey), final_color)
        
        # Draw players
        QuickMatchVisualizer.draw_player(draw, sx, sy, 
                                        QuickMatchVisualizer.PLAYER_COLOR,
                                        QuickMatchVisualizer.PLAYER_SHADOW, size=18)
        
        if defender_name and action not in ['save', 'claim_cross']:
            dx = (ex + sx) // 2
            dy = (ey + sy) // 2
            QuickMatchVisualizer.draw_player(draw, dx, dy, 
                                            QuickMatchVisualizer.DEFENDER_COLOR,
                                            QuickMatchVisualizer.DEFENDER_SHADOW, size=18)
        
        # Ball at end
        QuickMatchVisualizer.draw_ball(draw, ex, ey, size=12)
        
        # Result text
        font_large = QuickMatchVisualizer.get_font(32)
        if is_goal:
            result_text = "⚽ GOAL!"
            text_color = QuickMatchVisualizer.GOAL_GOLD
        elif success:
            result_text = "✓ SUCCESS!"
            text_color = QuickMatchVisualizer.SUCCESS_COLOR
        else:
            result_text = "✗ FAILED!"
            text_color = QuickMatchVisualizer.FAIL_COLOR
        
        bbox = draw.textbbox((0, 0), result_text, font=font_large)
        text_width = bbox[2] - bbox[0] + 40
        text_x = (QuickMatchVisualizer.WIDTH - text_width) // 2
        
        # Animated result overlay
        draw.rectangle([text_x, 140, text_x + text_width, 220],
                      fill='#000000dd', outline='white', width=4)
        QuickMatchVisualizer.draw_text_with_shadow(draw, (text_x + 20, 155), 
                                                  result_text, font_large, text_color, 
                                                  shadow_offset=3)
        
        # Hold final frame
        for _ in range(4):
            images.append(final_img)
        
        # Save as GIF
        buffer = io.BytesIO()
        images[0].save(
            buffer,
            format='GIF',
            save_all=True,
            append_images=images[1:],
            duration=70,  # 70ms per frame (smoother)
            loop=0
        )
        buffer.seek(0)
        
        return buffer


# Helper function for easy integration
def generate_action_visualization(action: str, player: Dict, defender: Optional[Dict],
                                 is_home: bool, success: bool, is_goal: bool = False,
                                 animated: bool = False) -> io.BytesIO:
    """
    Main function to generate high-quality visualization
    
    Args:
        action: Action type (shoot, pass, dribble, etc.)
        player: Player dict with name, position
        defender: Defender dict (optional)
        is_home: Whether player is on home team
        success: Whether action succeeded
        is_goal: Whether resulted in a goal
        animated: True for GIF, False for static image
        
    Returns:
        BytesIO buffer with PNG or GIF
    """
    # Generate coordinates
    start_x, start_y, end_x, end_y = CoordinateMapper.get_action_coordinates(
        action, player['position'], is_home
    )
    
    defender_name = defender['player_name'] if defender else None
    
    if animated:
        # Generate animated GIF
        return SimpleAnimator.create_action_gif(
            action=action,
            player_name=player['player_name'],
            player_position=player['position'],
            defender_name=defender_name,
            start_pos=(start_x, start_y),
            end_pos=(end_x, end_y),
            success=success,
            is_goal=is_goal
        )
    else:
        # Generate static image
        img = QuickMatchVisualizer.create_action_image(
            action=action,
            player_name=player['player_name'],
            player_position=player['position'],
            defender_name=defender_name,
            start_pos=(start_x, start_y),
            end_pos=(end_x, end_y),
            success=success,
            is_goal=is_goal
        )
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer
