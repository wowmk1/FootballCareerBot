"""
Match Action Visualizer
Generates real-time visualizations for player actions during matches
"""
from PIL import Image, ImageDraw, ImageFont
import io
import random
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
    """Generate simple static images showing actions"""
    
    # Image dimensions (5x scale of StatsBomb pitch)
    WIDTH = 600
    HEIGHT = 400
    SCALE = 5  # 120x80 -> 600x400
    
    # Colors
    GRASS_COLOR = '#2d5016'
    LINE_COLOR = 'white'
    PLAYER_COLOR = '#0066ff'
    DEFENDER_COLOR = '#ff3333'
    SUCCESS_COLOR = '#00ff00'
    FAIL_COLOR = '#ff0000'
    BALL_COLOR = '#ffffff'
    
    @staticmethod
    def draw_pitch(draw: ImageDraw.Draw):
        """Draw a football pitch with markings"""
        # Outer border
        draw.rectangle([0, 0, QuickMatchVisualizer.WIDTH-1, QuickMatchVisualizer.HEIGHT-1], 
                      outline=QuickMatchVisualizer.LINE_COLOR, width=3)
        
        # Halfway line
        draw.line([QuickMatchVisualizer.WIDTH//2, 0, 
                  QuickMatchVisualizer.WIDTH//2, QuickMatchVisualizer.HEIGHT], 
                 fill=QuickMatchVisualizer.LINE_COLOR, width=2)
        
        # Center circle
        center_x = QuickMatchVisualizer.WIDTH // 2
        center_y = QuickMatchVisualizer.HEIGHT // 2
        radius = 50
        draw.ellipse([center_x-radius, center_y-radius, center_x+radius, center_y+radius],
                    outline=QuickMatchVisualizer.LINE_COLOR, width=2)
        
        # Penalty boxes (simplified)
        box_width = 100
        box_height = 200
        box_y = (QuickMatchVisualizer.HEIGHT - box_height) // 2
        
        # Left penalty box
        draw.rectangle([0, box_y, box_width, box_y + box_height],
                      outline=QuickMatchVisualizer.LINE_COLOR, width=2)
        
        # Right penalty box  
        draw.rectangle([QuickMatchVisualizer.WIDTH - box_width, box_y, 
                       QuickMatchVisualizer.WIDTH, box_y + box_height],
                      outline=QuickMatchVisualizer.LINE_COLOR, width=2)
        
        # Goals
        goal_width = 10
        goal_height = 60
        goal_y = (QuickMatchVisualizer.HEIGHT - goal_height) // 2
        
        draw.rectangle([0, goal_y, goal_width, goal_y + goal_height],
                      fill=QuickMatchVisualizer.LINE_COLOR)
        draw.rectangle([QuickMatchVisualizer.WIDTH - goal_width, goal_y,
                       QuickMatchVisualizer.WIDTH, goal_y + goal_height],
                      fill=QuickMatchVisualizer.LINE_COLOR)
    
    @staticmethod
    def scale_coords(x: float, y: float) -> Tuple[int, int]:
        """Scale StatsBomb coords (120x80) to image coords (600x400)"""
        return int(x * QuickMatchVisualizer.SCALE), int(y * QuickMatchVisualizer.SCALE)
    
    @staticmethod
    def draw_arrow(draw: ImageDraw.Draw, start: Tuple[int, int], end: Tuple[int, int], 
                   color: str, width: int = 4):
        """Draw an arrow from start to end"""
        # Main line
        draw.line([start[0], start[1], end[0], end[1]], fill=color, width=width)
        
        # Arrow head
        import math
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        arrow_length = 15
        arrow_angle = math.pi / 6  # 30 degrees
        
        left_x = end[0] - arrow_length * math.cos(angle - arrow_angle)
        left_y = end[1] - arrow_length * math.sin(angle - arrow_angle)
        right_x = end[0] - arrow_length * math.cos(angle + arrow_angle)
        right_y = end[1] - arrow_length * math.sin(angle + arrow_angle)
        
        draw.polygon([end, (int(left_x), int(left_y)), (int(right_x), int(right_y))],
                    fill=color)
    
    @staticmethod
    def draw_curved_path(draw: ImageDraw.Draw, start: Tuple[int, int], end: Tuple[int, int],
                        color: str, curve_height: int = 30):
        """Draw a curved dribble path"""
        points = []
        for i in range(15):
            t = i / 14
            # Quadratic bezier curve
            x = start[0] + (end[0] - start[0]) * t
            y = start[1] + (end[1] - start[1]) * t + curve_height * (4 * t * (1 - t))
            points.append((x, y))
        
        # Draw path as series of circles
        for i, point in enumerate(points):
            radius = 3 + i // 3  # Gradually larger
            draw.ellipse([point[0]-radius, point[1]-radius, 
                         point[0]+radius, point[1]+radius],
                        fill=color)
    
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
    def create_action_image(action: str, player_name: str, player_position: str,
                          defender_name: Optional[str], start_pos: Tuple[float, float],
                          end_pos: Tuple[float, float], success: bool,
                          is_goal: bool = False) -> Image.Image:
        """
        Create a static image showing the action
        
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
        # Create base image
        img = Image.new('RGB', (QuickMatchVisualizer.WIDTH, QuickMatchVisualizer.HEIGHT),
                       color=QuickMatchVisualizer.GRASS_COLOR)
        draw = ImageDraw.Draw(img)
        
        # Draw pitch
        QuickMatchVisualizer.draw_pitch(draw)
        
        # Scale coordinates
        sx, sy = QuickMatchVisualizer.scale_coords(start_pos[0], start_pos[1])
        ex, ey = QuickMatchVisualizer.scale_coords(end_pos[0], end_pos[1])
        
        # Determine color based on success
        action_color = QuickMatchVisualizer.SUCCESS_COLOR if success else QuickMatchVisualizer.FAIL_COLOR
        
        # Draw action-specific visualization
        if action in ['pass', 'through_ball', 'key_pass', 'cross', 'long_ball']:
            # Draw pass arrow
            QuickMatchVisualizer.draw_arrow(draw, (sx, sy), (ex, ey), action_color, width=5)
            
            # Draw ball at end position
            draw.ellipse([ex-8, ey-8, ex+8, ey+8],
                        fill=QuickMatchVisualizer.BALL_COLOR,
                        outline='black', width=2)
            
        elif action in ['shoot', 'header']:
            # Draw shot trajectory (thicker line)
            if is_goal:
                shot_color = '#FFD700'  # Gold for goal
            else:
                shot_color = action_color
                
            QuickMatchVisualizer.draw_arrow(draw, (sx, sy), (ex, ey), shot_color, width=6)
            
            # Explosion effect at end
            for i in range(3):
                radius = 10 + (i * 5)
                alpha = 255 - (i * 70)
                draw.ellipse([ex-radius, ey-radius, ex+radius, ey+radius],
                           outline=shot_color, width=3)
            
        elif action in ['dribble', 'cut_inside']:
            # Draw curved dribble path
            QuickMatchVisualizer.draw_curved_path(draw, (sx, sy), (ex, ey), action_color)
            
            # Ball at end
            draw.ellipse([ex-8, ey-8, ex+8, ey+8],
                        fill=QuickMatchVisualizer.BALL_COLOR,
                        outline='black', width=2)
            
        elif action in ['tackle', 'block', 'interception']:
            # Draw defensive action
            # Impact point
            draw.line([sx-10, sy-10, sx+10, sy+10], fill=action_color, width=4)
            draw.line([sx+10, sy-10, sx-10, sy+10], fill=action_color, width=4)
            
            # Circle around impact
            draw.ellipse([sx-20, sy-20, sx+20, sy+20],
                        outline=action_color, width=3)
            
        elif action == 'clearance':
            # Long clearance arrow
            QuickMatchVisualizer.draw_arrow(draw, (sx, sy), (ex, ey), action_color, width=5)
            
        else:
            # Generic action - simple line
            draw.line([sx, sy, ex, ey], fill=action_color, width=4)
        
        # Draw player
        draw.ellipse([sx-15, sy-15, sx+15, sy+15],
                    fill=QuickMatchVisualizer.PLAYER_COLOR,
                    outline='white', width=3)
        
        # Draw defender if exists
        if defender_name and action not in ['save', 'claim_cross']:
            # Place defender near action
            dx, dy = (ex + sx) // 2, (ey + sy) // 2
            draw.ellipse([dx-15, dy-15, dx+15, dy+15],
                        fill=QuickMatchVisualizer.DEFENDER_COLOR,
                        outline='white', width=3)
        
        # Add text overlays
        font_large = QuickMatchVisualizer.get_font(24)
        font_medium = QuickMatchVisualizer.get_font(18)
        font_small = QuickMatchVisualizer.get_font(14)
        
        # Result text at top
        if is_goal:
            result_text = "⚽ GOAL!"
            text_color = '#FFD700'
        elif success:
            result_text = "✓ SUCCESS"
            text_color = QuickMatchVisualizer.SUCCESS_COLOR
        else:
            result_text = "✗ FAILED"
            text_color = QuickMatchVisualizer.FAIL_COLOR
        
        # Draw text background
        bbox = draw.textbbox((0, 0), result_text, font=font_large)
        text_width = bbox[2] - bbox[0] + 20
        text_height = bbox[3] - bbox[1] + 10
        draw.rectangle([10, 10, 10 + text_width, 10 + text_height],
                      fill='black', outline='white', width=2)
        draw.text((20, 15), result_text, fill=text_color, font=font_large)
        
        # Action type at bottom left
        action_text = action.replace('_', ' ').upper()
        draw.rectangle([10, QuickMatchVisualizer.HEIGHT - 45, 250, QuickMatchVisualizer.HEIGHT - 10],
                      fill='black', outline='white', width=2)
        draw.text((20, QuickMatchVisualizer.HEIGHT - 40), action_text, 
                 fill='white', font=font_medium)
        
        # Player name at bottom right
        player_text = f"{player_name} ({player_position})"
        player_bbox = draw.textbbox((0, 0), player_text, font=font_small)
        player_width = player_bbox[2] - player_bbox[0] + 20
        draw.rectangle([QuickMatchVisualizer.WIDTH - player_width - 10, 
                       QuickMatchVisualizer.HEIGHT - 35,
                       QuickMatchVisualizer.WIDTH - 10, 
                       QuickMatchVisualizer.HEIGHT - 10],
                      fill='black', outline='white', width=2)
        draw.text((QuickMatchVisualizer.WIDTH - player_width, QuickMatchVisualizer.HEIGHT - 30),
                 player_text, fill='white', font=font_small)
        
        return img


class SimpleAnimator:
    """Generate simple animated GIFs for actions"""
    
    @staticmethod
    def create_action_gif(action: str, player_name: str, player_position: str,
                         defender_name: Optional[str], start_pos: Tuple[float, float],
                         end_pos: Tuple[float, float], success: bool,
                         is_goal: bool = False, frames: int = 12) -> io.BytesIO:
        """
        Create an animated GIF showing the action
        
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
            # Create base image
            img = Image.new('RGB', (QuickMatchVisualizer.WIDTH, QuickMatchVisualizer.HEIGHT),
                           color=QuickMatchVisualizer.GRASS_COLOR)
            draw = ImageDraw.Draw(img)
            
            # Draw pitch
            QuickMatchVisualizer.draw_pitch(draw)
            
            # Calculate progress
            progress = frame / (frames - 1) if frames > 1 else 1
            
            # Current position
            current_x = sx + (ex - sx) * progress
            current_y = sy + (ey - sy) * progress
            
            # Draw trail
            if action in ['dribble', 'cut_inside']:
                # Curved trail
                for i in range(frame + 1):
                    t = i / frames
                    trail_x = sx + (ex - sx) * t
                    trail_y = sy + (ey - sy) * t + 20 * (4 * t * (1-t))
                    opacity = int(100 + 155 * (i / (frame + 1)))
                    trail_color = f'#{opacity:02x}{opacity:02x}00'
                    draw.ellipse([trail_x-3, trail_y-3, trail_x+3, trail_y+3],
                                fill=trail_color)
            else:
                # Straight trail
                if frame > 0:
                    draw.line([sx, sy, current_x, current_y],
                             fill='yellow', width=3)
            
            # Draw player at start
            draw.ellipse([sx-15, sy-15, sx+15, sy+15],
                        fill=QuickMatchVisualizer.PLAYER_COLOR,
                        outline='white', width=3)
            
            # Draw defender if exists
            if defender_name and action not in ['save', 'claim_cross']:
                dx = (ex + sx) // 2
                dy = (ey + sy) // 2
                draw.ellipse([dx-15, dy-15, dx+15, dy+15],
                            fill=QuickMatchVisualizer.DEFENDER_COLOR,
                            outline='white', width=3)
            
            # Draw ball at current position
            ball_size = 8 + int(2 * progress)  # Ball grows slightly
            draw.ellipse([current_x-ball_size, current_y-ball_size,
                         current_x+ball_size, current_y+ball_size],
                        fill='white', outline='black', width=2)
            
            # Add action label
            font = QuickMatchVisualizer.get_font(20)
            action_text = action.replace('_', ' ').upper()
            draw.rectangle([10, 10, 200, 45], fill='black', outline='white', width=2)
            draw.text((20, 15), action_text, fill='white', font=font)
            
            images.append(img)
        
        # Add final result frames (hold for emphasis)
        final_img = Image.new('RGB', (QuickMatchVisualizer.WIDTH, QuickMatchVisualizer.HEIGHT),
                             color=QuickMatchVisualizer.GRASS_COLOR)
        draw = ImageDraw.Draw(final_img)
        QuickMatchVisualizer.draw_pitch(draw)
        
        # Draw complete action on final frame
        if action in ['shoot', 'header']:
            color = '#FFD700' if is_goal else (QuickMatchVisualizer.SUCCESS_COLOR if success 
                                              else QuickMatchVisualizer.FAIL_COLOR)
            QuickMatchVisualizer.draw_arrow(draw, (sx, sy), (ex, ey), color, width=6)
        elif action in ['pass', 'through_ball', 'key_pass', 'cross']:
            color = QuickMatchVisualizer.SUCCESS_COLOR if success else QuickMatchVisualizer.FAIL_COLOR
            QuickMatchVisualizer.draw_arrow(draw, (sx, sy), (ex, ey), color, width=5)
        
        # Draw players
        draw.ellipse([sx-15, sy-15, sx+15, sy+15],
                    fill=QuickMatchVisualizer.PLAYER_COLOR,
                    outline='white', width=3)
        
        if defender_name:
            dx = (ex + sx) // 2
            dy = (ey + sy) // 2
            draw.ellipse([dx-15, dy-15, dx+15, dy+15],
                        fill=QuickMatchVisualizer.DEFENDER_COLOR,
                        outline='white', width=3)
        
        # Result text
        font_large = QuickMatchVisualizer.get_font(28)
        if is_goal:
            result_text = "⚽ GOAL!"
            text_color = '#FFD700'
        elif success:
            result_text = "✓ SUCCESS!"
            text_color = QuickMatchVisualizer.SUCCESS_COLOR
        else:
            result_text = "✗ FAILED!"
            text_color = QuickMatchVisualizer.FAIL_COLOR
        
        bbox = draw.textbbox((0, 0), result_text, font=font_large)
        text_width = bbox[2] - bbox[0] + 30
        text_x = (QuickMatchVisualizer.WIDTH - text_width) // 2
        
        draw.rectangle([text_x, 150, text_x + text_width, 210],
                      fill='black', outline='white', width=3)
        draw.text((text_x + 15, 160), result_text, fill=text_color, font=font_large)
        
        # Hold final frame
        for _ in range(3):
            images.append(final_img)
        
        # Save as GIF
        buffer = io.BytesIO()
        images[0].save(
            buffer,
            format='GIF',
            save_all=True,
            append_images=images[1:],
            duration=80,  # 80ms per frame
            loop=0
        )
        buffer.seek(0)
        
        return buffer


# Helper function for easy integration
def generate_action_visualization(action: str, player: Dict, defender: Optional[Dict],
                                 is_home: bool, success: bool, is_goal: bool = False,
                                 animated: bool = False) -> io.BytesIO:
    """
    Main function to generate visualization
    
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
