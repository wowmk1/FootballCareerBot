import discord
from discord import app_commands
from discord.ext import commands
from database import db

# Achievement definitions
ACHIEVEMENTS = {
    'first_goal': {
        'name': 'First Goal',
        'description': 'Score your first career goal',
        'icon': '⚽',
        'category': 'scoring',
        'rarity': 'common',
        'requirement': {'career_goals': 1}
    },
    'hat_trick': {
        'name': 'Hat-trick Hero',
        'description': 'Score 3 goals in a single match',
        'icon': '🎩',
        'category': 'scoring',
        'rarity': 'rare',
        'requirement': {'match_goals': 3}
    },
    'iron_man': {
        'name': 'Iron Man',
        'description': 'Maintain a 30-day training streak',
        'icon': '💪',
        'category': 'training',
        'rarity': 'epic',
        'requirement': {'training_streak': 30}
    },
    'transfer_listed': {
        'name': 'Transfer Listed',
        'description': 'Receive 10+ transfer offers in a window',
        'icon': '💼',
        'category': 'transfers',
        'rarity': 'rare',
        'requirement': {'transfer_offers': 10}
    },
    'legend_status': {
        'name': 'Legend',
        'description': 'Play 500 career matches',
        'icon': '👑',
        'category': 'appearances',
        'rarity': 'legendary',
        'requirement': {'career_apps': 500}
    },
    'century': {
        'name': 'Century',
        'description': 'Score 100 career goals',
        'icon': '💯',
        'category': 'scoring',
        'rarity': 'epic',
        'requirement': {'career_goals': 100}
    },
    'playmaker': {
        'name': 'Playmaker',
        'description': 'Record 50 career assists',
        'icon': '🎨',
        'category': 'assists',
        'rarity': 'rare',
        'requirement': {'career_assists': 50}
    },
    'world_class': {
        'name': 'World Class',
        'description': 'Reach 85+ overall rating',
        'icon': '⭐',
        'category': 'progression',
        'rarity': 'epic',
        'requirement': {'overall_rating': 85}
    },
    'treble_winner': {
        'name': 'Treble Winner',
        'description': 'Win league, FA Cup, and League Cup in same season',
        'icon': '🏆',
        'category': 'trophies',
        'rarity': 'legendary',
        'requirement': {'trophies': ['league', 'fa_cup', 'league_cup']}
    }
}

class AchievementCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="achievements", description="View your unlocked achievements")
    async def achievements(self, interaction: discord.Interaction):
        """Display player achievements"""
        
        player = await db.get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message("❌ No player found!", ephemeral=True)
            return
        
        # Get unlocked achievements
        async with db.pool.acquire() as conn:
            unlocked = await conn.fetch("""
                SELECT achievement_id, unlocked_at
                FROM player_achievements
                WHERE user_id = $1
                ORDER BY unlocked_at DESC
            """, player['user_id'])
        
        unlocked_ids = [a['achievement_id'] for a in unlocked]
        
        # Categorize achievements
        categories = {}
        for ach_id, ach_data in ACHIEVEMENTS.items():
            cat = ach_data['category']
            if cat not in categories:
                categories[cat] = {'unlocked': [], 'locked': []}
            
            if ach_id in unlocked_ids:
                categories[cat]['unlocked'].append((ach_id, ach_data))
            else:
                categories[cat]['locked'].append((ach_id, ach_data))
        
        # Build embed
        embed = discord.Embed(
            title=f"🏆 {player['player_name']}'s Achievements",
            description=f"**{len(unlocked_ids)}/{len(ACHIEVEMENTS)}** Unlocked",
            color=discord.Color.gold()
        )
        
        # Progress bar
        progress = len(unlocked_ids) / len(ACHIEVEMENTS)
        bar_length = 20
        filled = int(progress * bar_length)
        progress_bar = "█" * filled + "░" * (bar_length - filled)
        
        embed.add_field(
            name="📊 Overall Progress",
            value=f"{progress_bar} {int(progress * 100)}%",
            inline=False
        )
        
        # Show achievements by category
        for category, achs in categories.items():
            if achs['unlocked']:
                unlocked_text = ""
                for ach_id, ach_data in achs['unlocked'][:5]:
                    rarity_emoji = {'common': '⚪', 'rare': '🔵', 'epic': '🟣', 'legendary': '🟠'}
                    unlocked_text += f"{ach_data['icon']} {rarity_emoji.get(ach_data['rarity'], '')} **{ach_data['name']}**\n"
                
                embed.add_field(
                    name=f"✅ {category.title()}",
                    value=unlocked_text,
                    inline=True
                )
        
        # Show next achievements to unlock
        next_achievable = []
        for ach_id, ach_data in ACHIEVEMENTS.items():
            if ach_id in unlocked_ids:
                continue
            
            req = ach_data['requirement']
            progress_val = 0
            total_val = 1
            
            for key, value in req.items():
                if key in player:
                    progress_val = player[key]
                    total_val = value
                    if progress_val >= total_val * 0.5:  # At least 50% progress
                        next_achievable.append((ach_id, ach_data, progress_val, total_val))
        
        if next_achievable:
            next_text = ""
            for ach_id, ach_data, current, total in next_achievable[:3]:
                percentage = int((current / total) * 100)
                next_text += f"{ach_data['icon']} **{ach_data['name']}** - {percentage}%\n"
            
            embed.add_field(
                name="🎯 Close to Unlocking",
                value=next_text,
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

async def check_achievement_unlock(user_id: int, event_type: str, event_data: dict, bot=None):
    """Check if player unlocked any achievements"""
    player = await db.get_player(user_id)
    if not player:
        return
    
    newly_unlocked = []
    
    for ach_id, ach_data in ACHIEVEMENTS.items():
        # Check if already unlocked
        async with db.pool.acquire() as conn:
            exists = await conn.fetchrow(
                "SELECT 1 FROM player_achievements WHERE user_id = $1 AND achievement_id = $2",
                user_id, ach_id
            )
            
            if exists:
                continue
        
        # Check requirements
        req = ach_data['requirement']
        unlocked = False
        
        # Standard stat requirements
        for key, value in req.items():
            if key in player and player[key] >= value:
                unlocked = True
            elif key == 'match_goals' and event_data.get('match_goals', 0) >= value:
                unlocked = True
            elif key == 'transfer_offers' and event_data.get('transfer_offers', 0) >= value:
                unlocked = True
        
        if unlocked:
            # Unlock achievement
            async with db.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO player_achievements (user_id, achievement_id)
                    VALUES ($1, $2)
                """, user_id, ach_id)
            
            newly_unlocked.append((ach_id, ach_data))
    
    # Send notifications
    if newly_unlocked and bot:
        for ach_id, ach_data in newly_unlocked:
            try:
                user = await bot.fetch_user(user_id)
                
                rarity_colors = {
                    'common': discord.Color.light_grey(),
                    'rare': discord.Color.blue(),
                    'epic': discord.Color.purple(),
                    'legendary': discord.Color.orange()
                }
                
                embed = discord.Embed(
                    title=f"{ach_data['icon']} ACHIEVEMENT UNLOCKED!",
                    description=f"**{ach_data['name']}**\n{ach_data['description']}",
                    color=rarity_colors.get(ach_data['rarity'], discord.Color.gold())
                )
                embed.add_field(
                    name="Rarity",
                    value=ach_data['rarity'].title(),
                    inline=True
                )
                
                await user.send(embed=embed)
            except:
                pass

async def setup(bot):
    await bot.add_cog(AchievementCommands(bot))
    
    # Initialize achievements in database
    async with db.pool.acquire() as conn:
        for ach_id, ach_data in ACHIEVEMENTS.items():
            await conn.execute("""
                INSERT INTO achievements (achievement_id, achievement_name, description, icon, category, rarity)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (achievement_id) DO NOTHING
            """, ach_id, ach_data['name'], ach_data['description'], 
                 ach_data['icon'], ach_data['category'], ach_data['rarity'])
