"""
Match Action Visualizer - WITH POSTGRESQL CACHING
Loads images from PostgreSQL database for instant access
"""
from PIL import Image, ImageDraw, ImageFont
import io
import random
import math
import asyncpg
import os
from typing import Tuple, Optional, Dict, List


class CoordinateMapper:
    """Maps match events to pitch coordinates (StatsBomb format: 120x80)"""
    
    PITCH_LENGTH = 120
    PITCH_WIDTH = 80
    
    POSITIONS = {
        'GK': (10, 40), 'CB': (25, 40), 'LCB': (25, 30), 'RCB': (25, 50),
        'FB': (25, 20), 'LB': (25, 15), 'RB': (25, 65), 'CDM': (40, 40),
        'CM': (55, 40), 'LCM': (55, 30), 'RCM': (55, 50), 'CAM': (70, 40),
        'W': (60, 15), 'LW': (60, 15), 'RW': (60, 65), 'ST': (90, 40),
    }
    
    @staticmethod
    def get_position_coordinates(position: str, is_home_team: bool) -> Tuple[float, float]:
        x, y = CoordinateMapper.POSITIONS.get(position, (60, 40))
        if not is_home_team:
            x = CoordinateMapper.PITCH_LENGTH - x
            y = CoordinateMapper.PITCH_WIDTH - y
        return x, y
    
    @staticmethod
    def get_action_coordinates(action: str, player_position: str, is_home_team: bool, 
                              scenario_type: Optional[str] = None) -> Tuple[float, float, float, float]:
        base_x, base_y = CoordinateMapper.get_position_coordinates(player_position, is_home_team)
        
        x_variance = random.uniform(-5, 5)
        y_variance = random.uniform(-5, 5)
        
        start_x = max(0, min(CoordinateMapper.PITCH_LENGTH, base_x + x_variance))
        start_y = max(0, min(CoordinateMapper.PITCH_WIDTH, base_y + y_variance))
        
        direction = 1 if is_home_team else -1
        
        if action in ['shoot', 'header']:
            if is_home_team:
                end_x = CoordinateMapper.PITCH_LENGTH
                end_y = 40 + random.uniform(-3.66, 3.66)
            else:
                end_x = 0
                end_y = 40 + random.uniform(-3.66, 3.66)
        elif action in ['pass', 'through_ball', 'key_pass']:
            end_x = start_x + (random.uniform(10, 25) * direction)
            end_y = start_y + random.uniform(-10, 10)
        elif action == 'cross':
            if is_home_team:
                end_x = random.uniform(100, 118)
                end_y = random.uniform(20, 60)
            else:
                end_x = random.uniform(2, 20)
                end_y = random.uniform(20, 60)
        elif action in ['dribble', 'cut_inside']:
            end_x = start_x + (random.uniform(5, 15) * direction)
            end_y = start_y + random.uniform(-5, 5)
        elif action == 'long_ball':
            end_x = start_x + (random.uniform(30, 50) * direction)
            end_y = start_y + random.uniform(-20, 20)
        elif action in ['tackle', 'interception', 'block']:
            end_x = start_x + (random.uniform(-3, 3) * direction)
            end_y = start_y + random.uniform(-3, 3)
        elif action == 'clearance':
            end_x = start_x + (random.uniform(20, 40) * direction)
            end_y = start_y + random.uniform(-15, 15)
        elif action in ['save', 'claim_cross']:
            end_x = start_x
            end_y = start_y
        else:
            end_x = start_x + random.uniform(-3, 3)
            end_y = start_y + random.uniform(-3, 3)
        
        end_x = max(0, min(CoordinateMapper.PITCH_LENGTH, end_x))
        end_y = max(0, min(CoordinateMapper.PITCH_WIDTH, end_y))
        
        return (start_x, start_y, end_x, end_y)


class MatchVisualizer:
    """Create match action visualizations with PostgreSQL caching"""
    
    # Goal positions
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
    
    # In-memory cache (loaded from database once per session)
    _assets_cache = None
    _db_pool = None
    
    @staticmethod
    async def init_db_pool():
        """Initialize database connection pool"""
        if MatchVisualizer._db_pool is None:
            from database import db  # Your existing db module
            MatchVisualizer._db_pool = db.pool
    
    @staticmethod
    async def load_image_from_db(image_key: str) -> Image.Image:
        """Load image from PostgreSQL database"""
        await MatchVisualizer.init_db_pool()
        
        async with MatchVisualizer._db_pool.acquire() as conn:
            # Update last accessed timestamp
            row = await conn.fetchrow("""
                UPDATE image_cache 
                SET last_accessed = CURRENT_TIMESTAMP 
                WHERE image_key = $1
                RETURNING image_data, image_format
            """, image_key)
            
            if not row:
                raise Exception(f"Image '{image_key}' not found in cache! Run setup_image_cache.py first.")
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(row['image_data']))
            return image
    
    @staticmethod
    async def load_assets():
        """Load all visual assets from database (cached in memory after first load)"""
        # Return memory cache if already loaded
        if MatchVisualizer._assets_cache is not None:
            return MatchVisualizer._assets_cache
        
        try:
            print("🔄 Loading assets from PostgreSQL...")
            
            # Load all images from database
            stadium = (await MatchVisualizer.load_image_from_db('stadium')).convert('RGB')
            player_home = (await MatchVisualizer.load_image_from_db('player_home')).convert('RGBA')
            player_away = (await MatchVisualizer.load_image_from_db('player_away')).convert('RGBA')
            defender_home = (await MatchVisualizer.load_image_from_db('defender_home')).convert('RGBA')
            defender_away = (await MatchVisualizer.load_image_from_db('defender_away')).convert('RGBA')
            goalie_home = (await MatchVisualizer.load_image_from_db('goalie_home')).convert('RGBA')
            goalie_away = (await MatchVisualizer.load_image_from_db('goalie_away')).convert('RGBA')
            ball = (await MatchVisualizer.load_image_from_db('ball')).convert('RGBA')
            
            # Cache in memory
            MatchVisualizer._assets_cache = {
                'stadium': stadium,
                'player_home': player_home,
                'player_away': player_away,
                'defender_home': defender_home,
                'defender_away': defender_away,
                'goalie_home': goalie_home,
                'goalie_away': goalie_away,
                'ball': ball
            }
            
            print("✅ Assets loaded from database and cached in memory!")
            return MatchVisualizer._assets_cache
            
        except Exception as e:
            raise Exception(f"Failed to load assets from database. Error: {e}\nDid you run setup_image_cache.py?")
    
    @staticmethod
    def map_coordinates(pitch_x: float, pitch_y: float) -> Tuple[int, int]:
        norm_x = pitch_x / 120.0
        screen_x = MatchVisualizer.LEFT_GOAL_X + \
                   (MatchVisualizer.RIGHT_GOAL_X - MatchVisualizer.LEFT_GOAL_X) * norm_x
        
        norm_y = pitch_y / 80.0
        if norm_y < 0.5:
            screen_y = MatchVisualizer.FIELD_TOP + \
                      (MatchVisualizer.LEFT_GOAL_Y - MatchVisualizer.FIELD_TOP) * (norm_y / 0.5)
        else:
            screen_y = MatchVisualizer.LEFT_GOAL_Y + \
                      (MatchVisualizer.FIELD_BOTTOM - MatchVisualizer.LEFT_GOAL_Y) * ((norm_y - 0.5) / 0.5)
        
        return int(screen_x), int(screen_y)
    
    @staticmethod
    def get_scale_factor(pitch_y: float) -> float:
        norm_y = pitch_y / 80.0
        return 0.25 + 0.15 * norm_y
    
    @staticmethod
    def remove_grass(player_img: Image.Image) -> Image.Image:
        cleaned = player_img.copy()
        pixels = cleaned.load()
        
        for y in range(cleaned.height):
            for x in range(cleaned.width):
                r, g, b, a = pixels[x, y]
                if a > 0 and g > 100 and r < 150 and b < 150:
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
        sx, sy = start
        ex, ey = end
        
        for i in range(2, 0, -1):
            alpha = 40 + i * 20
            draw.line([sx, sy, ex, ey], fill=f'{color}{alpha:02x}', width=width + i * 2)
        
        draw.line([sx, sy, ex, ey], fill=color, width=width)
        
        angle = math.atan2(ey - sy, ex - sx)
        arrow_size = 12
        
        left_x = ex - arrow_size * math.cos(angle - math.pi/6)
        left_y = ey - arrow_size * math.sin(angle - math.pi/6)
        right_x = ex - arrow_size * math.cos(angle + math.pi/6)
        right_y = ey - arrow_size * math.sin(angle + math.pi/6)
        
        draw.polygon([(ex, ey), (left_x, left_y), (right_x, right_y)], fill=color)
    
    @staticmethod
    def draw_glow(draw: ImageDraw.Draw, x: int, y: int, color: str, size: int = 18):
        for i in range(3, 0, -1):
            alpha = 40 + i * 20
            radius = size + i * 4
            draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=f'{color}{alpha:02x}')
    
    @staticmethod
    def draw_curved_path(draw: ImageDraw.Draw, start: Tuple[int, int], 
                        end: Tuple[int, int], color: str):
        sx, sy = start
        ex, ey = end
        
        points = []
        for i in range(30):
            t = i / 29
            x = sx + (ex - sx) * t
            y = sy + (ey - sy) * t + 25 * (4 * t * (1-t))
            points.append((x, y))
        
        for i in range(2, 0, -1):
            alpha = 50 + i * 20
            for j in range(len(points)-1):
                draw.line([points[j], points[j+1]], fill=f'{color}{alpha:02x}', width=4 + i * 2)
        
        for i in range(len(points)-1):
            draw.line([points[i], points[i+1]], fill=color, width=4)
    
    @staticmethod
    async def create_action_image(action: str, player_name: str, player_position: str,
                          defender_name: Optional[str], start_pos: Tuple[float, float],
                          end_pos: Tuple[float, float], is_home: bool, success: bool, 
                          is_goal: bool = False) -> Image.Image:
        """Create STATIC action image"""
        
        assets = await MatchVisualizer.load_assets()
        stadium = assets['stadium']
        
        overlay = Image.new('RGBA', stadium.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, 'RGBA')
        
        sx, sy = MatchVisualizer.map_coordinates(*start_pos)
        ex, ey = MatchVisualizer.map_coordinates(*end_pos)
        
        start_scale = MatchVisualizer.get_scale_factor(start_pos[1])
        end_scale = MatchVisualizer.get_scale_factor(end_pos[1])
        
        if is_goal:
            action_color = MatchVisualizer.GOAL_GOLD
        else:
            action_color = MatchVisualizer.SUCCESS_COLOR if success else MatchVisualizer.FAIL_COLOR
        
        # Draw action
        if action in ['shoot', 'header']:
            MatchVisualizer.draw_arrow(draw, (sx, sy), (ex, ey), action_color, width=5)
            MatchVisualizer.draw_glow(draw, ex, ey, action_color, size=20)
        elif action in ['pass', 'through_ball', 'key_pass', 'cross', 'clearance']:
            MatchVisualizer.draw_arrow(draw, (sx, sy), (ex, ey), action_color, width=4)
        elif action in ['dribble', 'cut_inside']:
            MatchVisualizer.draw_curved_path(draw, (sx, sy), (ex, ey), action_color)
        elif action in ['tackle', 'interception', 'block', 'save', 'claim_cross']:
            MatchVisualizer.draw_glow(draw, sx, sy, action_color, size=18)
        
        stadium = stadium.convert('RGBA')
        stadium = Image.alpha_composite(stadium, overlay)
        
        # Add player
        is_goalie = action in ['save', 'claim_cross'] or player_position == 'GK'
        
        if is_goalie:
            player_cutout = assets['goalie_home'] if is_home else assets['goalie_away']
        else:
            player_cutout = assets['player_home'] if is_home else assets['player_away']
        
        player_size = int(100 * start_scale)
        player_scaled = player_cutout.resize((player_size, player_size), Image.Resampling.LANCZOS)
        player_clean = MatchVisualizer.remove_grass(player_scaled)
        
        player_x = sx - player_size // 2
        player_y = sy - player_size
        stadium.paste(player_clean, (player_x, player_y), player_clean)
        
        # Add defender
        if defender_name and action not in ['save', 'claim_cross']:
            dx, dy = (sx + ex) // 2, (sy + ey) // 2
            mid_scale = (start_scale + end_scale) / 2
            defender_size = int(100 * mid_scale)
            
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
        
        # UI
        stadium = stadium.convert('RGB')
        draw = ImageDraw.Draw(stadium)
        
        font_med = MatchVisualizer.get_font(22)
        font_large = MatchVisualizer.get_font(30)
        
        name_text = f"{player_name} ({player_position})"
        draw.rectangle([10, 10, 280, 50], fill='#000000bb', outline='white', width=2)
        draw.text((20, 16), name_text, fill='white', font=font_med)
        
        action_text = action.replace('_', ' ').upper()
        draw.rectangle([10, 60, 280, 100], fill='#000000bb', outline='white', width=2)
        draw.text((20, 66), action_text, fill=action_color, font=font_med)
        
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
    
    @staticmethod
    async def create_action_animation(action: str, player_name: str, player_position: str,
                               defender_name: Optional[str], start_pos: Tuple[float, float],
                               end_pos: Tuple[float, float], is_home: bool, success: bool, 
                               is_goal: bool = False, frames: int = 15) -> List[Image.Image]:
        """Create ANIMATED action frames"""
        
        assets = await MatchVisualizer.load_assets()
        stadium = assets['stadium']
        
        sx, sy = MatchVisualizer.map_coordinates(*start_pos)
        ex, ey = MatchVisualizer.map_coordinates(*end_pos)
        
        start_scale = MatchVisualizer.get_scale_factor(start_pos[1])
        end_scale = MatchVisualizer.get_scale_factor(end_pos[1])
        
        if is_goal:
            action_color = MatchVisualizer.GOAL_GOLD
        else:
            action_color = MatchVisualizer.SUCCESS_COLOR if success else MatchVisualizer.FAIL_COLOR
        
        is_goalie = action in ['save', 'claim_cross'] or player_position == 'GK'
        
        if is_goalie:
            player_cutout = assets['goalie_home'] if is_home else assets['goalie_away']
        else:
            player_cutout = assets['player_home'] if is_home else assets['player_away']
        
        animation_frames = []
        
        for frame_num in range(frames):
            img = stadium.copy().convert('RGBA')
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay, 'RGBA')
            
            progress = frame_num / (frames - 1)
            eased = progress * progress * (3 - 2 * progress)
            
            if action in ['dribble', 'cut_inside']:
                current_x = sx + (ex - sx) * eased
                current_y = sy + (ey - sy) * eased + 25 * (4 * eased * (1-eased))
            else:
                current_x = sx + (ex - sx) * eased
                current_y = sy + (ey - sy) * eased
            
            # Draw trail
            if frame_num > 0:
                if action in ['dribble', 'cut_inside']:
                    for i in range(frame_num + 1):
                        t = i / frames
                        trail_x = sx + (ex - sx) * t
                        trail_y = sy + (ey - sy) * t + 25 * (4 * t * (1-t))
                        for r in range(2, 0, -1):
                            draw.ellipse([trail_x-r, trail_y-r, trail_x+r, trail_y+r],
                                       fill=f'{action_color}{60:02x}')
                else:
                    for i in range(2, 0, -1):
                        alpha = 40 + i * 20
                        draw.line([sx, sy, current_x, current_y],
                                fill=f'{action_color}{alpha:02x}', width=4 + i * 2)
                    draw.line([sx, sy, current_x, current_y], fill=action_color, width=4)
            
            if action in ['shoot', 'header'] and progress > 0.5:
                glow_intensity = int((progress - 0.5) * 2 * 60)
                for r in range(30, 10, -3):
                    draw.ellipse([ex-r, ey-r, ex+r, ey+r],
                                fill=f'{action_color}{glow_intensity:02x}')
            
            img = Image.alpha_composite(img, overlay)
            
            # Add player
            player_size = int(100 * start_scale)
            player_scaled = player_cutout.resize((player_size, player_size), Image.Resampling.LANCZOS)
            player_clean = MatchVisualizer.remove_grass(player_scaled)
            
            player_x = sx - player_size // 2
            player_y = sy - player_size
            img.paste(player_clean, (player_x, player_y), player_clean)
            
            # Add defender
            if defender_name and action not in ['save', 'claim_cross']:
                dx, dy = (sx + ex) // 2, (sy + ey) // 2
                mid_scale = (start_scale + end_scale) / 2
                defender_size = int(100 * mid_scale)
                
                defender_cutout = assets['defender_away'] if is_home else assets['defender_home']
                defender_scaled = defender_cutout.resize((defender_size, defender_size), Image.Resampling.LANCZOS)
                defender_clean = MatchVisualizer.remove_grass(defender_scaled)
                
                defender_x = dx - defender_size // 2
                defender_y = dy - defender_size
                img.paste(defender_clean, (defender_x, defender_y), defender_clean)
            
            # Add ball
            current_pitch_y = start_pos[1] + (end_pos[1] - start_pos[1]) * progress
            ball_scale = MatchVisualizer.get_scale_factor(current_pitch_y)
            pulse = 1.0 + 0.15 * math.sin(progress * math.pi)
            ball_size = int(35 * ball_scale * pulse)
            ball_scaled = assets['ball'].resize((ball_size, ball_size), Image.Resampling.LANCZOS)
            
            ball_x = int(current_x) - ball_size // 2
            ball_y = int(current_y) - ball_size // 2
            img.paste(ball_scaled, (ball_x, ball_y), ball_scaled)
            
            # UI
            img = img.convert('RGB')
            draw = ImageDraw.Draw(img)
            
            font_med = MatchVisualizer.get_font(22)
            font_large = MatchVisualizer.get_font(30)
            
            name_text = f"{player_name} ({player_position})"
            draw.rectangle([10, 10, 280, 50], fill='#000000bb', outline='white', width=2)
            draw.text((20, 16), name_text, fill='white', font=font_med)
            
            action_text = action.replace('_', ' ').upper()
            draw.rectangle([10, 60, 280, 100], fill='#000000bb', outline='white', width=2)
            draw.text((20, 66), action_text, fill=action_color, font=font_med)
            
            if frame_num >= frames - 3:
                if is_goal:
                    result_text = "⚽ GOAL!"
                elif success:
                    result_text = "✓ SUCCESS"
                else:
                    result_text = "✗ FAILED"
                
                result_width = 250
                result_x = (img.width - result_width) // 2
                draw.rectangle([result_x, img.height - 70, result_x + result_width, img.height - 20],
                              fill='#000000bb', outline='white', width=3)
                draw.text((result_x + 35, img.height - 62), result_text, fill=action_color, font=font_large)
            
            animation_frames.append(img)
        
        return animation_frames


async def generate_action_visualization(action: str, player: Dict, defender: Optional[Dict],
                                 is_home: bool, success: bool, is_goal: bool = False,
                                 animated: bool = False) -> io.BytesIO:
    """
    Generate action visualization (async version for database)
    
    Args:
        action: Action type
        player: Dict with 'player_name' and 'position'
        defender: Optional defender dict
        is_home: True for home (RED), False for away (BLUE)
        success: Whether action succeeded
        is_goal: Whether it's a goal
        animated: If True, returns GIF. If False, static PNG
    
    Returns:
        BytesIO buffer with PNG or GIF
    """
    start_x, start_y, end_x, end_y = CoordinateMapper.get_action_coordinates(
        action, player['position'], is_home
    )
    
    defender_name = defender['player_name'] if defender else None
    
    if animated:
        frames = await MatchVisualizer.create_action_animation(
            action=action,
            player_name=player['player_name'],
            player_position=player['position'],
            defender_name=defender_name,
            start_pos=(start_x, start_y),
            end_pos=(end_x, end_y),
            is_home=is_home,
            success=success,
            is_goal=is_goal,
            frames=15
        )
        
        buffer = io.BytesIO()
        frames[0].save(
            buffer,
            format='GIF',
            save_all=True,
            append_images=frames[1:],
            duration=70,
            loop=0
        )
        buffer.seek(0)
        return buffer
    else:
        img = await MatchVisualizer.create_action_image(
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
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer
