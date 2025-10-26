"""
Match Action Visualizer - FINAL VERSION
Complete code with correct team colors, positions, and all assets
"""
from PIL import Image, ImageDraw, ImageFont
import io
import random
import math
from typing import Tuple, Optional, Dict


class CoordinateMapper:
    """Maps match events to pitch coordinates (StatsBomb format: 120x80)"""
    
    PITCH_LENGTH = 120
    PITCH_WIDTH = 80
    
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
        """Get base coordinates for a player position"""
        x, y = CoordinateMapper.POSITIONS.get(position, (60, 40))
        if not is_home_team:
            # Away team attacks opposite direction
            x = CoordinateMapper.PITCH_LENGTH - x
            y = CoordinateMapper.PITCH_WIDTH - y
        return x, y
    
    @staticmethod
    def get_action_coordinates(action: str, player_position: str, is_home_team: bool, 
                              scenario_type: Optional[str] = None) -> Tuple[float, float, float, float]:
        """Generate realistic start and end coordinates for an action"""
        base_x, base_y = CoordinateMapper.get_position_coordinates(player_position, is_home_team)
        
        # Add some variance for realism
        x_variance = random.uniform(-5, 5)
        y_variance = random.uniform(-5, 5)
        
        start_x = max(0, min(CoordinateMapper.PITCH_LENGTH, base_x + x_variance))
        start_y = max(0, min(CoordinateMapper.PITCH_WIDTH, base_y + y_variance))
        
        direction = 1 if is_home_team else -1
        
        # Calculate end position based on action type
        if action in ['shoot', 'header']:
            # Shots go toward goal
            if is_home_team:
                end_x = CoordinateMapper.PITCH_LENGTH
                end_y = 40 + random.uniform(-3.66, 3.66)  # Goal width
            else:
                end_x = 0
                end_y = 40 + random.uniform(-3.66, 3.66)
                
        elif action in ['pass', 'through_ball', 'key_pass']:
            # Forward passes
            end_x = start_x + (random.uniform(10, 25) * direction)
            end_y = start_y + random.uniform(-10, 10)
            
        elif action == 'cross':
            # Crosses into the box
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
            # Defensive actions - minimal movement
            end_x = start_x + (random.uniform(-3, 3) * direction)
            end_y = start_y + random.uniform(-3, 3)
            
        elif action == 'clearance':
            # Clearances go far
            end_x = start_x + (random.uniform(20, 40) * direction)
            end_y = start_y + random.uniform(-15, 15)
            
        elif action in ['save', 'claim_cross']:
            # GK actions stay in place
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


class MatchVisualizer:
    """Create match action visualizations on real stadium"""
    
    # ASSET PATHS - UPDATE THESE TO YOUR FILE LOCATIONS
    STADIUM_IMAGE_PATH = "https://i.imgur.com/7kJf34C.jpeg"
    PLAYER_HOME_PATH = "https://i.imgur.com/9KXzzpq.png"  # RED
    PLAYER_AWAY_PATH = "https://i.imgur.com/5pTYlbS.png"  # BLUE
    DEFENDER_HOME_PATH = "https://i.imgur.com/GgpU26d.png"  # RED
    DEFENDER_AWAY_PATH = "https://i.imgur.com/Z8pibql.png"  # BLUE
    GOALIE_HOME_PATH = "https://i.imgur.com/4j6Vnva.png"  # RED
    GOALIE_AWAY_PATH = "https://i.imgur.com/LcaDRG1.png"  # BLUE
    BALL_PATH = "https://i.imgur.com/39woCj8.png"
    
    # EXACT goal positions from pink markers in reference images
    LEFT_GOAL_X = 158
    LEFT_GOAL_Y = 460
    RIGHT_GOAL_X = 1262
    RIGHT_GOAL_Y = 460
    
    # Field boundaries
    FIELD_TOP = 350
    FIELD_BOTTOM = 620
    
    # Colors
    SUCCESS_COLOR = '#00ff00'
    FAIL_COLOR = '#ff0000'
    GOAL_GOLD = '#FFD700'
    
    @staticmethod
    def load_assets():
        """Load all visual assets"""
        stadium = Image.open(MatchVisualizer.STADIUM_IMAGE_PATH).convert('RGB')
        player_home = Image.open(MatchVisualizer.PLAYER_HOME_PATH).convert('RGBA')
        player_away = Image.open(MatchVisualizer.PLAYER_AWAY_PATH).convert('RGBA')
        defender_home = Image.open(MatchVisualizer.DEFENDER_HOME_PATH).convert('RGBA')
        defender_away = Image.open(MatchVisualizer.DEFENDER_AWAY_PATH).convert('RGBA')
        goalie_home = Image.open(MatchVisualizer.GOALIE_HOME_PATH).convert('RGBA')
        goalie_away = Image.open(MatchVisualizer.GOALIE_AWAY_PATH).convert('RGBA')
        ball = Image.open(MatchVisualizer.BALL_PATH).convert('RGBA')
        
        return {
            'stadium': stadium,
            'player_home': player_home,
            'player_away': player_away,
            'defender_home': defender_home,
            'defender_away': defender_away,
            'goalie_home': goalie_home,
            'goalie_away': goalie_away,
            'ball': ball
        }
    
    @staticmethod
    def map_coordinates(pitch_x: float, pitch_y: float) -> Tuple[int, int]:
        """Convert pitch coordinates (120x80) to screen pixels with perspective"""
        # X: Linear from left goal to right goal
        norm_x = pitch_x / 120.0
        screen_x = MatchVisualizer.LEFT_GOAL_X + \
                   (MatchVisualizer.RIGHT_GOAL_X - MatchVisualizer.LEFT_GOAL_X) * norm_x
        
        # Y: Perspective mapping (back to front)
        norm_y = pitch_y / 80.0
        if norm_y < 0.5:
            # Back half
            screen_y = MatchVisualizer.FIELD_TOP + \
                      (MatchVisualizer.LEFT_GOAL_Y - MatchVisualizer.FIELD_TOP) * (norm_y / 0.5)
        else:
            # Front half
            screen_y = MatchVisualizer.LEFT_GOAL_Y + \
                      (MatchVisualizer.FIELD_BOTTOM - MatchVisualizer.LEFT_GOAL_Y) * ((norm_y - 0.5) / 0.5)
        
        return int(screen_x), int(screen_y)
    
    @staticmethod
    def get_scale_factor(pitch_y: float) -> float:
        """Calculate scale based on depth (perspective)"""
        norm_y = pitch_y / 80.0
        return 0.25 + 0.15 * norm_y
    
    @staticmethod
    def remove_grass(player_img: Image.Image) -> Image.Image:
        """Remove green grass circle from cutout"""
        cleaned = player_img.copy()
        pixels = cleaned.load()
        
        for y in range(cleaned.height):
            for x in range(cleaned.width):
                r, g, b, a = pixels[x, y]
                if a > 0:
                    # Remove green grass
                    if g > 100 and r < 150 and b < 150:
                        pixels[x, y] = (r, g, b, 0)
        return cleaned
    
    @staticmethod
    def get_font(size: int) -> ImageFont.FreeTypeFont:
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        except:
            return ImageFont.load_default()
    
    @staticmethod
    def draw_arrow(draw: ImageDraw.Draw, start: Tuple[int, int], 
                  end: Tuple[int, int], color: str, width: int = 4):
        """Draw arrow with glow effect"""
        sx, sy = start
        ex, ey = end
        
        # Glow
        for i in range(2, 0, -1):
            alpha = 40 + i * 20
            draw.line([sx, sy, ex, ey], fill=f'{color}{alpha:02x}', width=width + i * 2)
        
        # Main line
        draw.line([sx, sy, ex, ey], fill=color, width=width)
        
        # Arrow head
        angle = math.atan2(ey - sy, ex - sx)
        arrow_size = 12
        
        left_x = ex - arrow_size * math.cos(angle - math.pi/6)
        left_y = ey - arrow_size * math.sin(angle - math.pi/6)
        right_x = ex - arrow_size * math.cos(angle + math.pi/6)
        right_y = ey - arrow_size * math.sin(angle + math.pi/6)
        
        draw.polygon([(ex, ey), (left_x, left_y), (right_x, right_y)], fill=color)
    
    @staticmethod
    def draw_glow(draw: ImageDraw.Draw, x: int, y: int, color: str, size: int = 18):
        """Draw glowing circle effect"""
        for i in range(3, 0, -1):
            alpha = 40 + i * 20
            radius = size + i * 4
            draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=f'{color}{alpha:02x}')
    
    @staticmethod
    def draw_curved_path(draw: ImageDraw.Draw, start: Tuple[int, int], 
                        end: Tuple[int, int], color: str):
        """Draw curved dribble path"""
        sx, sy = start
        ex, ey = end
        
        points = []
        for i in range(30):
            t = i / 29
            x = sx + (ex - sx) * t
            y = sy + (ey - sy) * t + 25 * (4 * t * (1-t))
            points.append((x, y))
        
        # Glow
        for i in range(2, 0, -1):
            alpha = 50 + i * 20
            for j in range(len(points)-1):
                draw.line([points[j], points[j+1]], fill=f'{color}{alpha:02x}', width=4 + i * 2)
        
        # Main curve
        for i in range(len(points)-1):
            draw.line([points[i], points[i+1]], fill=color, width=4)
    
    @staticmethod
    def create_action_image(action: str, player_name: str, player_position: str,
                          defender_name: Optional[str], start_pos: Tuple[float, float],
                          end_pos: Tuple[float, float], is_home: bool, success: bool, 
                          is_goal: bool = False) -> Image.Image:
        """Create the complete visualization"""
        
        assets = MatchVisualizer.load_assets()
        stadium = assets['stadium']
        
        # Create overlay for drawing
        overlay = Image.new('RGBA', stadium.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, 'RGBA')
        
        # Map coordinates
        sx, sy = MatchVisualizer.map_coordinates(*start_pos)
        ex, ey = MatchVisualizer.map_coordinates(*end_pos)
        
        start_scale = MatchVisualizer.get_scale_factor(start_pos[1])
        end_scale = MatchVisualizer.get_scale_factor(end_pos[1])
        
        # Determine color
        if is_goal:
            action_color = MatchVisualizer.GOAL_GOLD
        else:
            action_color = MatchVisualizer.SUCCESS_COLOR if success else MatchVisualizer.FAIL_COLOR
        
        # Draw action based on type
        if action in ['shoot', 'header']:
            MatchVisualizer.draw_arrow(draw, (sx, sy), (ex, ey), action_color, width=5)
            MatchVisualizer.draw_glow(draw, ex, ey, action_color, size=20)
        elif action in ['pass', 'through_ball', 'key_pass', 'cross', 'clearance']:
            MatchVisualizer.draw_arrow(draw, (sx, sy), (ex, ey), action_color, width=4)
        elif action in ['dribble', 'cut_inside']:
            MatchVisualizer.draw_curved_path(draw, (sx, sy), (ex, ey), action_color)
        elif action in ['tackle', 'interception', 'block', 'save', 'claim_cross']:
            MatchVisualizer.draw_glow(draw, sx, sy, action_color, size=18)
        
        # Composite overlay
        stadium = stadium.convert('RGBA')
        stadium = Image.alpha_composite(stadium, overlay)
        
        # Select correct player cutout
        is_goalie = action in ['save', 'claim_cross'] or player_position == 'GK'
        
        if is_goalie:
            player_cutout = assets['goalie_home'] if is_home else assets['goalie_away']
        else:
            player_cutout = assets['player_home'] if is_home else assets['player_away']
        
        # Add player
        player_size = int(100 * start_scale)
        player_scaled = player_cutout.resize((player_size, player_size), Image.Resampling.LANCZOS)
        player_clean = MatchVisualizer.remove_grass(player_scaled)
        
        player_x = sx - player_size // 2
        player_y = sy - player_size
        stadium.paste(player_clean, (player_x, player_y), player_clean)
        
        # Add defender (opposite team)
        if defender_name and action not in ['save', 'claim_cross']:
            dx, dy = (sx + ex) // 2, (sy + ey) // 2
            mid_scale = (start_scale + end_scale) / 2
            defender_size = int(100 * mid_scale)
            
            # Defender is opposite team
            defender_cutout = assets['defender_away'] if is_home else assets['defender_home']
            defender_scaled = defender_cutout.resize((defender_size, defender_size), Image.Resampling.LANCZOS)
            defender_clean = MatchVisualizer.remove_grass(defender_scaled)
            
            defender_x = dx - defender_size // 2
            defender_y = dy - defender_size
            stadium.paste(defender_clean, (defender_x, defender_y), defender_clean)
        
        # Add ball
        ball_size = int(35 * end_scale)
        ball_scaled = assets['ball'].resize((ball_size, ball_size), Image.Resampling.LANCZOS)
        
        ball_x = ex - ball_size // 2
        ball_y = ey - ball_size // 2
        stadium.paste(ball_scaled, (ball_x, ball_y), ball_scaled)
        
        # Convert to RGB for final rendering
        stadium = stadium.convert('RGB')
        draw = ImageDraw.Draw(stadium)
        
        # Add UI overlays
        font_med = MatchVisualizer.get_font(22)
        font_large = MatchVisualizer.get_font(30)
        
        # Player name box
        name_text = f"{player_name} ({player_position})"
        draw.rectangle([10, 10, 280, 50], fill='#000000bb', outline='white', width=2)
        draw.text((20, 16), name_text, fill='white', font=font_med)
        
        # Action box
        action_text = action.replace('_', ' ').upper()
        draw.rectangle([10, 60, 280, 100], fill='#000000bb', outline='white', width=2)
        draw.text((20, 66), action_text, fill=action_color, font=font_med)
        
        # Result box (centered bottom)
        if is_goal:
            result_text = "⚽ GOAL!"
        elif success:
            result_text = "✓ SUCCESS"
        else:
            result_text = "✗ FAILED"
        
        result_width = 250
        result_x = (stadium.width - result_width) // 2
        draw.rectangle([result_x, stadium.height - 70, result_x + result_width, stadium.height - 20],
                      fill='#000000bb', outline='white', width=3)
        draw.text((result_x + 35, stadium.height - 62), result_text, fill=action_color, font=font_large)
        
        return stadium


def generate_action_visualization(action: str, player: Dict, defender: Optional[Dict],
                                 is_home: bool, success: bool, is_goal: bool = False) -> io.BytesIO:
    """
    Main function to generate action visualization
    
    Args:
        action: Action type ('shoot', 'pass', 'dribble', 'tackle', etc.)
        player: Dict with 'player_name' and 'position' keys
        defender: Optional Dict with 'player_name' key (or None)
        is_home: True if home team (RED), False if away team (BLUE)
        success: Whether the action succeeded
        is_goal: Whether action resulted in a goal
    
    Returns:
        BytesIO buffer containing PNG image
    """
    # Generate coordinates
    start_x, start_y, end_x, end_y = CoordinateMapper.get_action_coordinates(
        action, player['position'], is_home
    )
    
    defender_name = defender['player_name'] if defender else None
    
    # Create visualization
    img = MatchVisualizer.create_action_image(
        action=action,
        player_name=player['player_name'],
        player_position=player['position'],
        defender_name=defender_name,
        start_pos=(start_x, start_y),
        end_pos=(end_x, end_y),
        is_home=is_home,
        success=success,
        is_goal=is_goal
    )
    
    # Return as buffer
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


if __name__ == "__main__":
    # EXAMPLE USAGE
    
    # Example 1: Home team goal
    player = {'player_name': 'Haaland', 'position': 'ST'}
    defender = {'player_name': 'Van Dijk'}
    
    image_buffer = generate_action_visualization(
        action='shoot',
        player=player,
        defender=defender,
        is_home=True,  # HOME = RED
        success=True,
        is_goal=True
    )
    
    with open('home_goal.png', 'wb') as f:
        f.write(image_buffer.read())
    
    # Example 2: Away team pass
    player2 = {'player_name': 'De Bruyne', 'position': 'CM'}
    
    image_buffer2 = generate_action_visualization(
        action='pass',
        player=player2,
        defender=None,
        is_home=False,  # AWAY = BLUE
        success=True,
        is_goal=False
    )
    
    with open('away_pass.png', 'wb') as f:
        f.write(image_buffer2.read())
    
    print("✓ Match visualizations generated!")
    print("  Home team = RED jerseys")
    print("  Away team = BLUE jerseys")
