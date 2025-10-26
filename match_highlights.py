"""
Post-Match Highlights Generator
Creates animated GIF compilation of key match moments

✅ UPDATED: Works with new MatchVisualizer (no animation yet - static frames)
"""
import discord
from PIL import Image, ImageDraw, ImageFont
import io
from typing import List, Dict, Optional
from match_visualizer_final import MatchVisualizer, CoordinateMapper, generate_action_visualization
from database import db

class MatchHighlightsGenerator:
    """Generate animated highlights reel after match completion"""
    
    @staticmethod
    async def generate_match_highlights(match_id: int, max_highlights: int = 6,
                                       animated: bool = False) -> Optional[io.BytesIO]:
        """
        Generate highlights from match actions
        
        Args:
            match_id: The match ID
            max_highlights: Maximum number of actions to include (default 6)
            animated: If True, creates animated GIF. If False, creates static compilation
                      NOTE: Animation not yet implemented with new visualizer
            
        Returns:
            BytesIO buffer with GIF/PNG, or None if no highlights
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
                LIMIT 10
            """, match_id)
        
        if not highlights:
            return None
        
        # Convert to action representations
        action_frames = []
        total_frames_added = 0
        
        for i, highlight in enumerate(highlights):
            # Stop if we've reached max_highlights
            if total_frames_added >= max_highlights:
                break
            
            # ✅ Create one frame for EACH goal scored by this player
            if highlight['goals_scored'] > 0:
                goals_to_show = min(highlight['goals_scored'], max_highlights - total_frames_added)
                
                for goal_num in range(goals_to_show):
                    action = 'shoot'
                    success = True
                    is_goal = True
                    
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
                    
                    # Create static frame using new visualizer
                    img = MatchVisualizer.create_action_image(
                        action=action,
                        player_name=player['player_name'],
                        player_position=player['position'],
                        defender_name=None,
                        start_pos=(start_x, start_y),
                        end_pos=(end_x, end_y),
                        is_home=is_home,
                        success=success,
                        is_goal=is_goal
                    )
                    
                    action_frames.append(img)
                    total_frames_added += 1
                    
                    if total_frames_added >= max_highlights:
                        break
                
                continue
            
            # Handle assists (if no goals)
            if highlight['assists'] > 0 and total_frames_added < max_highlights:
                action = 'pass'
                success = True
                is_goal = False
            # Handle high-rated moments (if no goals/assists)
            elif total_frames_added < max_highlights:
                action = ['dribble', 'tackle', 'pass', 'interception'][i % 4]
                success = True
                is_goal = False
            else:
                continue
            
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
            
            # Create frame
            img = MatchVisualizer.create_action_image(
                action=action,
                player_name=player['player_name'],
                player_position=player['position'],
                defender_name=None,
                start_pos=(start_x, start_y),
                end_pos=(end_x, end_y),
                is_home=is_home,
                success=success,
                is_goal=is_goal
            )
            
            action_frames.append(img)
            total_frames_added += 1
        
        if not action_frames:
            return None
        
        # Create compilation as animated GIF (each frame holds for duration)
        buffer = io.BytesIO()
        action_frames[0].save(
            buffer,
            format='GIF',
            save_all=True,
            append_images=action_frames[1:],
            duration=2000,  # 2 seconds per goal/action
            loop=0
        )
        buffer.seek(0)
        return buffer
    
    @staticmethod
    async def generate_top_moment_animation(match_id: int) -> Optional[io.BytesIO]:
        """
        Generate image of the single best moment (MOTM or top goal)
        
        Returns:
            BytesIO buffer with PNG of best moment
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
        
        # Generate visualization for this moment
        action = 'shoot' if top_moment['goals_scored'] > 0 else 'pass'
        is_home = top_moment['team_id'] == match['home_team_id']
        
        player = {
            'player_name': top_moment['player_name'],
            'position': top_moment['position']
        }
        
        # Use the main function
        buffer = generate_action_visualization(
            action=action,
            player=player,
            defender=None,
            is_home=is_home,
            success=True,
            is_goal=top_moment['goals_scored'] > 0
        )
        
        return buffer


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
            - start_pos: tuple (optional, will be generated if not provided)
            - end_pos: tuple (optional, will be generated if not provided)
        """
        if match_id not in self.match_actions:
            self.match_actions[match_id] = []
        
        # Generate coordinates if not provided
        if 'start_pos' not in action_data or 'end_pos' not in action_data:
            start_x, start_y, end_x, end_y = CoordinateMapper.get_action_coordinates(
                action_data['action'],
                action_data['player']['position'],
                action_data['is_home']
            )
            action_data['start_pos'] = (start_x, start_y)
            action_data['end_pos'] = (end_x, end_y)
        
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
        
        # Generate frames for each action
        all_frames = []
        
        for action_data in selected_actions:
            # Create action visualization
            img = MatchVisualizer.create_action_image(
                action=action_data['action'],
                player_name=action_data['player']['player_name'],
                player_position=action_data['player']['position'],
                defender_name=action_data.get('defender', {}).get('player_name') if action_data.get('defender') else None,
                start_pos=action_data['start_pos'],
                end_pos=action_data['end_pos'],
                is_home=action_data['is_home'],
                success=action_data['success'],
                is_goal=action_data.get('is_goal', False)
            )
            
            all_frames.append(img)
            
            # Add separator frame with player name and minute
            separator = Image.new('RGB', (1408, 768), color='#000000')
            draw = ImageDraw.Draw(separator)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
            except:
                font = ImageFont.load_default()
            
            text = f"{action_data['minute']}' - {action_data['player']['player_name']}"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            draw.text(((1408 - text_width) // 2, 350), text, fill='white', font=font)
            
            all_frames.append(separator)
        
        # Create final GIF
        if not all_frames:
            return None
        
        buffer = io.BytesIO()
        all_frames[0].save(
            buffer,
            format='GIF',
            save_all=True,
            append_images=all_frames[1:],
            duration=2000,  # 2 seconds per frame
            loop=0
        )
        buffer.seek(0)
        
        return buffer


# Global instance for logging actions during matches
match_action_logger = MatchActionLogger()


# Example usage
async def example_usage():
    """Example of how to use the highlights generator"""
    
    # During a match, log actions:
    match_action_logger.log_action(
        match_id=123,
        action_data={
            'action': 'shoot',
            'player': {'player_name': 'Haaland', 'position': 'ST'},
            'defender': {'player_name': 'Van Dijk'},
            'is_home': True,
            'success': True,
            'is_goal': True,
            'minute': 34
        }
    )
    
    # After match ends, generate highlights:
    highlights_gif = await MatchHighlightsGenerator.generate_match_highlights(
        match_id=123,
        max_highlights=6
    )
    
    if highlights_gif:
        # Send to Discord
        await channel.send(
            content="⚽ **Match Highlights!**",
            file=discord.File(highlights_gif, 'highlights.gif')
        )
    
    # Or generate detailed highlights from logged actions:
    detailed_gif = await match_action_logger.generate_detailed_highlights(
        match_id=123,
        max_actions=8
    )
    
    if detailed_gif:
        await channel.send(
            content="🎬 **Full Match Replay!**",
            file=discord.File(detailed_gif, 'replay.gif')
        )
    
    # Clear logged actions after sending
    match_action_logger.clear_match_actions(123)
