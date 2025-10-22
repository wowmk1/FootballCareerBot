"""
Post-Match Highlights Generator
Creates animated GIF compilation of key match moments
"""
import discord
from PIL import Image
import io
from typing import List, Dict, Optional
from match_visualizer import SimpleAnimator, CoordinateMapper
from database import db

class MatchHighlightsGenerator:
    """Generate animated highlights reel after match completion"""
    
    @staticmethod
    async def generate_match_highlights(match_id: int, max_highlights: int = 6,
                                       animated: bool = True) -> Optional[io.BytesIO]:
        """
        Generate animated highlights from match actions
        
        Args:
            match_id: The match ID
            max_highlights: Maximum number of actions to include (default 6)
            animated: If True, creates animated GIF. If False, creates static compilation
            
        Returns:
            BytesIO buffer with GIF, or None if no highlights
        """
        
        # Fetch key moments from match
        async with db.pool.acquire() as conn:
            # Get match info
            match = await conn.fetchrow("""
                SELECT am.*, f.home_team_id, f.away_team_id
                FROM active_matches am
                JOIN fixtures f ON am.fixture_id = f.fixture_id
                WHERE am.match_id = $1
            """, match_id)
            
            if not match:
                return None
            
            # Get key actions from match_participants
            # (Goals, assists, high-rated moments)
            highlights = await conn.fetch("""
                SELECT 
                    mp.user_id,
                    mp.goals_scored,
                    mp.assists,
                    mp.match_rating,
                    p.player_name,
                    p.position,
                    mp.team_id
                FROM match_participants mp
                JOIN players p ON mp.user_id = p.user_id
                WHERE mp.match_id = $1
                  AND mp.user_id IS NOT NULL
                  AND (mp.goals_scored > 0 OR mp.assists > 0 OR mp.match_rating >= 7.5)
                ORDER BY 
                    mp.goals_scored DESC,
                    mp.assists DESC,
                    mp.match_rating DESC
                LIMIT $2
            """, match_id, max_highlights)
        
        if not highlights:
            return None
        
        # Convert to action representations
        action_frames = []
        
        for i, highlight in enumerate(highlights):
            # Determine action type based on stats
            if highlight['goals_scored'] > 0:
                action = 'shoot'
                success = True
                is_goal = True
            elif highlight['assists'] > 0:
                action = 'pass'
                success = True
                is_goal = False
            else:
                # High-rated moment - varied action
                action = ['dribble', 'tackle', 'pass', 'interception'][i % 4]
                success = True
                is_goal = False
            
            is_home = highlight['team_id'] == match['home_team_id']
            
            player = {
                'player_name': highlight['player_name'],
                'position': highlight['position'],
                'user_id': highlight['user_id']
            }
            
            # Generate coordinates
            start_x, start_y, end_x, end_y = CoordinateMapper.get_action_coordinates(
                action, player['position'], is_home
            )
            
            # Generate frame
            if animated:
                # Generate animated sequence for this action
                gif_buffer = SimpleAnimator.create_action_gif(
                    action=action,
                    player_name=player['player_name'],
                    player_position=player['position'],
                    defender_name=None,
                    start_pos=(start_x, start_y),
                    end_pos=(end_x, end_y),
                    success=success,
                    is_goal=is_goal,
                    frames=10  # Shorter for compilation
                )
                
                # Extract frames from the GIF
                gif_buffer.seek(0)
                gif_img = Image.open(gif_buffer)
                
                frames_for_action = []
                try:
                    while True:
                        frames_for_action.append(gif_img.copy())
                        gif_img.seek(gif_img.tell() + 1)
                except EOFError:
                    pass
                
                action_frames.extend(frames_for_action)
            else:
                # Static compilation - create one frame per action
                from match_visualizer import QuickMatchVisualizer
                
                img = QuickMatchVisualizer.create_action_image(
                    action=action,
                    player_name=player['player_name'],
                    player_position=player['position'],
                    defender_name=None,
                    start_pos=(start_x, start_y),
                    end_pos=(end_x, end_y),
                    success=success,
                    is_goal=is_goal
                )
                
                action_frames.append(img)
        
        if not action_frames:
            return None
        
        # Create compilation
        if animated:
            # Save as animated GIF
            buffer = io.BytesIO()
            action_frames[0].save(
                buffer,
                format='GIF',
                save_all=True,
                append_images=action_frames[1:],
                duration=100,  # 100ms per frame
                loop=0
            )
            buffer.seek(0)
            return buffer
        else:
            # Create grid of static images
            return MatchHighlightsGenerator._create_static_grid(action_frames)
    
    @staticmethod
    def _create_static_grid(images: List[Image.Image], cols: int = 3) -> io.BytesIO:
        """Create a grid of images"""
        if not images:
            return None
        
        # Calculate grid dimensions
        n_images = len(images)
        rows = (n_images + cols - 1) // cols
        
        # Get image size (assuming all same size)
        img_width, img_height = images[0].size
        
        # Create grid
        grid_width = img_width * cols
        grid_height = img_height * rows
        grid = Image.new('RGB', (grid_width, grid_height), color='#1a1a1a')
        
        # Paste images
        for idx, img in enumerate(images):
            row = idx // cols
            col = idx % cols
            x = col * img_width
            y = row * img_height
            grid.paste(img, (x, y))
        
        # Save to buffer
        buffer = io.BytesIO()
        grid.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer
    
    @staticmethod
    async def generate_top_moment_animation(match_id: int) -> Optional[io.BytesIO]:
        """
        Generate animated GIF of the single best moment (MOTM or top goal)
        Faster than full highlights - just one action animated
        
        Returns:
            BytesIO buffer with animated GIF of best moment
        """
        
        async with db.pool.acquire() as conn:
            # Get match info
            match = await conn.fetchrow("""
                SELECT am.*, f.home_team_id, f.away_team_id
                FROM active_matches am
                JOIN fixtures f ON am.fixture_id = f.fixture_id
                WHERE am.match_id = $1
            """, match_id)
            
            if not match:
                return None
            
            # Get MOTM or highest scorer
            top_moment = await conn.fetchrow("""
                SELECT 
                    mp.user_id,
                    mp.goals_scored,
                    mp.match_rating,
                    p.player_name,
                    p.position,
                    mp.team_id
                FROM match_participants mp
                JOIN players p ON mp.user_id = p.user_id
                WHERE mp.match_id = $1
                  AND mp.user_id IS NOT NULL
                ORDER BY 
                    mp.match_rating DESC,
                    mp.goals_scored DESC
                LIMIT 1
            """, match_id)
            
            if not top_moment:
                return None
        
        # Generate animation for this moment
        action = 'shoot' if top_moment['goals_scored'] > 0 else 'pass'
        is_home = top_moment['team_id'] == match['home_team_id']
        
        player = {
            'player_name': top_moment['player_name'],
            'position': top_moment['position']
        }
        
        start_x, start_y, end_x, end_y = CoordinateMapper.get_action_coordinates(
            action, player['position'], is_home
        )
        
        gif_buffer = SimpleAnimator.create_action_gif(
            action=action,
            player_name=player['player_name'],
            player_position=player['position'],
            defender_name=None,
            start_pos=(start_x, start_y),
            end_pos=(end_x, end_y),
            success=True,
            is_goal=top_moment['goals_scored'] > 0,
            frames=15  # Full animation for best moment
        )
        
        return gif_buffer


class MatchActionLogger:
    """
    Store action details during match for post-match replay generation
    This gives us more detailed highlights with exact actions that happened
    """
    
    def __init__(self):
        self.match_actions: Dict[int, List[Dict]] = {}
    
    def log_action(self, match_id: int, action_data: Dict):
        """
        Log an action during the match
        
        action_data should contain:
            - action: str
            - player: dict
            - defender: dict or None
            - is_home: bool
            - success: bool
            - is_goal: bool
            - minute: int
            - start_pos: tuple
            - end_pos: tuple
        """
        if match_id not in self.match_actions:
            self.match_actions[match_id] = []
        
        self.match_actions[match_id].append(action_data)
    
    def get_match_actions(self, match_id: int) -> List[Dict]:
        """Get all logged actions for a match"""
        return self.match_actions.get(match_id, [])
    
    def clear_match_actions(self, match_id: int):
        """Clear actions after match is complete"""
        if match_id in self.match_actions:
            del self.match_actions[match_id]
    
    async def generate_detailed_highlights(self, match_id: int, 
                                          max_actions: int = 8) -> Optional[io.BytesIO]:
        """
        Generate highlights from logged actions
        This is more accurate than database-based highlights
        """
        actions = self.get_match_actions(match_id)
        
        if not actions:
            return None
        
        # Filter to most important actions
        important_actions = [
            a for a in actions 
            if a.get('is_goal') or a.get('success', True)
        ]
        
        # Sort by importance (goals first, then successful actions)
        important_actions.sort(
            key=lambda x: (
                x.get('is_goal', False),
                x.get('success', False),
                x.get('minute', 0)
            ),
            reverse=True
        )
        
        # Take top actions
        selected_actions = important_actions[:max_actions]
        
        if not selected_actions:
            return None
        
        # Generate animated frames for each action
        all_frames = []
        
        for action_data in selected_actions:
            gif_buffer = SimpleAnimator.create_action_gif(
                action=action_data['action'],
                player_name=action_data['player']['player_name'],
                player_position=action_data['player']['position'],
                defender_name=action_data.get('defender', {}).get('player_name') if action_data.get('defender') else None,
                start_pos=action_data['start_pos'],
                end_pos=action_data['end_pos'],
                success=action_data['success'],
                is_goal=action_data.get('is_goal', False),
                frames=10
            )
            
            # Extract frames
            gif_buffer.seek(0)
            gif_img = Image.open(gif_buffer)
            
            try:
                while True:
                    all_frames.append(gif_img.copy())
                    gif_img.seek(gif_img.tell() + 1)
            except EOFError:
                pass
            
            # Add separator frames (black screen with "Next Action")
            from match_visualizer import QuickMatchVisualizer
            from PIL import ImageDraw, ImageFont
            
            separator = Image.new('RGB', (600, 400), color='#000000')
            draw = ImageDraw.Draw(separator)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
            except:
                font = ImageFont.load_default()
            
            text = f"{action_data['minute']}' - {action_data['player']['player_name']}"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            draw.text(((600 - text_width) // 2, 180), text, fill='white', font=font)
            
            # Add separator 3 times (hold for 0.3s)
            for _ in range(3):
                all_frames.append(separator.copy())
        
        # Create final GIF
        if not all_frames:
            return None
        
        buffer = io.BytesIO()
        all_frames[0].save(
            buffer,
            format='GIF',
            save_all=True,
            append_images=all_frames[1:],
            duration=100,
            loop=0
        )
        buffer.seek(0)
        
        return buffer


# Global instance for logging actions during matches
match_action_logger = MatchActionLogger()
