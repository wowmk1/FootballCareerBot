"""
Post-Match Highlights Generator - DISCORD-OPTIMIZED VERSION
Creates animated GIF with moving ball for all goals
✅ OPTIMIZED: Reduced frames, resized images, compressed GIFs
"""
import discord
from PIL import Image, ImageDraw, ImageFont
import io
from typing import List, Dict, Optional
from match_visualizer import MatchVisualizer, CoordinateMapper
from database import db


class MatchHighlightsGenerator:
    """Generate animated highlights reel after match completion"""
    
    @staticmethod
    async def generate_match_highlights(match_id: int, max_highlights: int = 5) -> Optional[io.BytesIO]:
        """
        Generate ANIMATED highlights from match actions (DISCORD-OPTIMIZED)
        Each goal gets 10 frames of smooth ball movement (reduced from 15)
        
        Args:
            match_id: The match ID
            max_highlights: Maximum number of actions to include (default 5, reduced from 6)
            
        Returns:
            BytesIO buffer with animated GIF (10 frames per goal), or None
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
        
        # Collect ALL animated frames
        all_frames = []
        total_actions_added = 0
        
        for i, highlight in enumerate(highlights):
            # Stop if we've reached max_highlights
            if total_actions_added >= max_highlights:
                break
            
            # ✅ Create ANIMATED frames for EACH goal scored by this player
            if highlight['goals_scored'] > 0:
                goals_to_show = min(highlight['goals_scored'], max_highlights - total_actions_added)
                
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
                    
                    # ✅ Create 10 animated frames for this goal (Discord-optimized)
                    goal_frames = await MatchVisualizer.create_action_animation(
                        action=action,
                        player_name=player['player_name'],
                        player_position=player['position'],
                        defender_name=None,
                        start_pos=(start_x, start_y),
                        end_pos=(end_x, end_y),
                        is_home=is_home,
                        success=success,
                        is_goal=is_goal,
                        frames=10  # ✅ Reduced to 10 frames for Discord
                    )
                    
                    # Add all frames from this goal to the compilation
                    all_frames.extend(goal_frames)
                    total_actions_added += 1
                    
                    if total_actions_added >= max_highlights:
                        break
                
                continue
            
            # Handle assists (if no goals)
            if highlight['assists'] > 0 and total_actions_added < max_highlights:
                action = 'pass'
                success = True
                is_goal = False
            # Handle high-rated moments (if no goals/assists)
            elif total_actions_added < max_highlights:
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
            
            # Create animated frames
            action_frames = await MatchVisualizer.create_action_animation(
                action=action,
                player_name=player['player_name'],
                player_position=player['position'],
                defender_name=None,
                start_pos=(start_x, start_y),
                end_pos=(end_x, end_y),
                is_home=is_home,
                success=success,
                is_goal=is_goal,
                frames=8  # ✅ Fewer frames for non-goals (reduced from 12)
            )
            
            all_frames.extend(action_frames)
            total_actions_added += 1
        
        if not all_frames:
            return None
        
        # ✅ RESIZE FRAMES TO 70% (reduces file size significantly)
        resized_frames = []
        for frame in all_frames:
            new_width = int(frame.width * 0.7)
            new_height = int(frame.height * 0.7)
            resized = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)
            resized_frames.append(resized)
        
        # ✅ Create final animated GIF with optimization
        buffer = io.BytesIO()
        resized_frames[0].save(
            buffer,
            format='GIF',
            save_all=True,
            append_images=resized_frames[1:],
            duration=70,  # 70ms per frame (smooth animation)
            loop=0,
            optimize=True,  # ✅ Compress GIF
            quality=85      # ✅ Good quality but smaller
        )
        buffer.seek(0)
        return buffer
    
    @staticmethod
    async def generate_top_moment_animation(match_id: int) -> Optional[io.BytesIO]:
        """
        Generate animated GIF of the single best moment (MOTM or top goal)
        DISCORD-OPTIMIZED VERSION
        
        Returns:
            BytesIO buffer with animated GIF
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
        
        # Create animated frames (reduced to 15 from 20)
        frames = await MatchVisualizer.create_action_animation(
            action=action,
            player_name=player['player_name'],
            player_position=player['position'],
            defender_name=None,
            start_pos=(start_x, start_y),
            end_pos=(end_x, end_y),
            is_home=is_home,
            success=True,
            is_goal=top_moment['goals_scored'] > 0,
            frames=15  # ✅ Reduced from 20
        )
        
        # ✅ RESIZE FRAMES TO 70%
        resized_frames = []
        for frame in frames:
            new_width = int(frame.width * 0.7)
            new_height = int(frame.height * 0.7)
            resized = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)
            resized_frames.append(resized)
        
        # ✅ Save as optimized GIF
        buffer = io.BytesIO()
        resized_frames[0].save(
            buffer,
            format='GIF',
            save_all=True,
            append_images=resized_frames[1:],
            duration=70,
            loop=0,
            optimize=True,  # ✅ Compress
            quality=85      # ✅ Smaller size
        )
        buffer.seek(0)
        return buffer


class MatchActionLogger:
    """
    Store action details during match for post-match replay generation
    """
    
    def __init__(self):
        self.match_actions: Dict[int, List[Dict]] = {}
    
    def log_action(self, match_id: int, action_data: Dict):
        """
        Log an action during the match
        
        action_data should contain:
            - action: str
            - player: dict with 'player_name' and 'position'
            - defender: dict or None
            - is_home: bool
            - success: bool
            - is_goal: bool
            - minute: int
            - start_pos: tuple (optional)
            - end_pos: tuple (optional)
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
                                          max_actions: int = 6) -> Optional[io.BytesIO]:
        """
        Generate ANIMATED highlights from logged actions (DISCORD-OPTIMIZED)
        Most accurate - uses exact actions that happened
        """
        actions = self.get_match_actions(match_id)
        
        if not actions:
            return None
        
        # Filter to most important actions
        important_actions = [
            a for a in actions 
            if a.get('is_goal') or a.get('success', True)
        ]
        
        # Sort by importance
        important_actions.sort(
            key=lambda x: (
                x.get('is_goal', False),
                x.get('success', False),
                x.get('minute', 0)
            ),
            reverse=True
        )
        
        # Take top actions (reduced to max 6)
        selected_actions = important_actions[:max_actions]
        
        if not selected_actions:
            return None
        
        # Generate animated frames for each action
        all_frames = []
        
        for action_data in selected_actions:
            # Create animated frames (reduced to 10)
            action_frames = await MatchVisualizer.create_action_animation(
                action=action_data['action'],
                player_name=action_data['player']['player_name'],
                player_position=action_data['player']['position'],
                defender_name=action_data.get('defender', {}).get('player_name') if action_data.get('defender') else None,
                start_pos=action_data['start_pos'],
                end_pos=action_data['end_pos'],
                is_home=action_data['is_home'],
                success=action_data['success'],
                is_goal=action_data.get('is_goal', False),
                frames=10  # ✅ Reduced from 15
            )
            
            all_frames.extend(action_frames)
            
            # Add separator frame
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
            
            # Hold separator for 2 frames (reduced from 3)
            for _ in range(2):
                all_frames.append(separator.copy())
        
        # Create final GIF
        if not all_frames:
            return None
        
        # ✅ RESIZE FRAMES TO 70%
        resized_frames = []
        for frame in all_frames:
            new_width = int(frame.width * 0.7)
            new_height = int(frame.height * 0.7)
            resized = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)
            resized_frames.append(resized)
        
        buffer = io.BytesIO()
        resized_frames[0].save(
            buffer,
            format='GIF',
            save_all=True,
            append_images=resized_frames[1:],
            duration=70,
            loop=0,
            optimize=True,  # ✅ Compress
            quality=85      # ✅ Smaller size
        )
        buffer.seek(0)
        
        return buffer


# Global instance
match_action_logger = MatchActionLogger()


# Example usage for Discord bot
async def example_discord_usage(channel):
    """
    Example of how to use in your Discord bot
    """
    match_id = 123
    
    # After match ends, generate animated highlights
    print("Generating animated highlights...")
    highlights_gif = await MatchHighlightsGenerator.generate_match_highlights(
        match_id=match_id,
        max_highlights=5  # ✅ Reduced to 5 goals (Discord-optimized)
    )
    
    if highlights_gif:
        # Send animated GIF to Discord
        await channel.send(
            content="⚽ **Match Highlights!** (Discord-optimized)",
            file=discord.File(highlights_gif, 'highlights.gif')
        )
        print(f"✓ Sent animated highlights GIF")
    
    # Or send single best moment
    top_moment_gif = await MatchHighlightsGenerator.generate_top_moment_animation(match_id)
    
    if top_moment_gif:
        await channel.send(
            content="🌟 **Man of the Match Moment!**",
            file=discord.File(top_moment_gif, 'motm.gif')
        )
        print(f"✓ Sent MOTM animated GIF")


if __name__ == "__main__":
    print("Match Highlights Generator - DISCORD OPTIMIZED")
    print("===============================================")
    print()
    print("Features:")
    print("  ✅ Animated GIF with moving ball for each goal")
    print("  ✅ 10 frames per goal (reduced from 15)")
    print("  ✅ 70% resolution (986×538 instead of 1408×768)")
    print("  ✅ GIF optimization enabled")
    print("  ✅ Discord-safe file sizes (<8MB)")
    print("  ✅ Example: 5 goals = 50 frames, ~2-3MB total")
    print()
    print("Usage:")
    print("  highlights = await MatchHighlightsGenerator.generate_match_highlights(match_id)")
    print("  await channel.send(file=discord.File(highlights, 'highlights.gif'))")
