import discord
from discord import app_commands
from discord.ext import commands
from database import db
import config
from datetime import datetime, timedelta

class SeasonCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="season", description="View current season information and schedule")
    async def season(self, interaction: discord.Interaction):
        """View season information"""
        
        state = await db.get_game_state()
        
        if not state['season_started']:
            embed = discord.Embed(
                title="📅 Season Not Started",
                description="The season will begin when the first player creates their character with `/start`!",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="ℹ️ How It Works",
                value=(
                    f"• Season has **{config.SEASON_TOTAL_WEEKS} weeks**\n"
                    f"• **{config.MATCHES_PER_WEEK} match days** per week\n"
                    f"• Match days: **Monday, Wednesday, Saturday**\n"
                    f"• Match windows: **{config.MATCH_WINDOW_HOURS} hours** to play\n"
                    f"• Everyone plays in the same week together"
                ),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            return
        
        progress_pct = (state['current_week'] / config.SEASON_TOTAL_WEEKS) * 100
        progress_bar = self._create_progress_bar(progress_pct)
        
        embed = discord.Embed(
            title=f"📅 Season {state['current_season']}",
            description=f"Week **{state['current_week']}** of **{config.SEASON_TOTAL_WEEKS}**",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📊 Season Progress",
            value=f"{progress_bar}\n{int(progress_pct)}% Complete",
            inline=False
        )
        
        if state['match_window_open']:
            window_closes = datetime.fromisoformat(state['match_window_closes'])
            time_left = window_closes - datetime.now()
            
            if time_left.total_seconds() > 0:
                hours = int(time_left.total_seconds() // 3600)
                minutes = int((time_left.total_seconds() % 3600) // 60)
                
                embed.add_field(
                    name="🎮 MATCH WINDOW OPEN!",
                    value=f"⏰ **{hours}h {minutes}m** remaining\nUse `/play_match` to play your game!",
                    inline=False
                )
        elif state['next_match_day']:
            next_match = datetime.fromisoformat(state['next_match_day'])
            time_until = next_match - datetime.now()
            
            if time_until.total_seconds() > 0:
                days = time_until.days
                hours = time_until.seconds // 3600
                
                if days > 0:
                    time_str = f"{days}d {hours}h"
                else:
                    time_str = f"{hours}h"
                
                embed.add_field(
                    name="⏰ Next Match Day",
                    value=f"In **{time_str}**\n{next_match.strftime('%A at %I:%M %p')}",
                    inline=True
                )
        
        if state['last_match_day']:
            last_match = datetime.fromisoformat(state['last_match_day'])
            embed.add_field(
                name="📅 Last Match Day",
                value=f"{last_match.strftime('%B %d, %Y')}\nWeek {state['current_week']} completed",
                inline=True
            )
        
        weeks_left = config.SEASON_TOTAL_WEEKS - state['current_week']
        embed.add_field(
            name="🏁 Season Status",
            value=f"**{weeks_left} weeks** remaining\n{weeks_left * config.MATCHES_PER_WEEK} match days left",
            inline=True
        )
        
        embed.add_field(
            name="📋 Match Schedule",
            value=(
                f"**{config.MATCHES_PER_WEEK} matches per week:**\n"
                f"• Monday at {config.MATCH_START_HOUR}:00\n"
                f"• Wednesday at {config.MATCH_START_HOUR}:00\n"
                f"• Saturday at {config.MATCH_START_HOUR}:00\n"
                f"• {config.MATCH_WINDOW_HOURS}h window to play each"
            ),
            inline=False
        )
        
        async with db.db.execute(
            "SELECT COUNT(*) as count FROM players WHERE retired = 0"
        ) as cursor:
            result = await cursor.fetchone()
            player_count = result['count']
        
        embed.add_field(
            name="👥 Active Players",
            value=f"**{player_count}** players in the league",
            inline=True
        )
        
        if state['season_start_date']:
            start_date = datetime.fromisoformat(state['season_start_date'])
            embed.add_field(
                name="🎬 Season Started",
                value=start_date.strftime('%B %d, %Y'),
                inline=True
            )
        
        embed.set_footer(text="Use /play_match during match windows to play!")
        
        await interaction.response.send_message(embed=embed)
    
    def _create_progress_bar(self, percentage: float, length: int = 20) -> str:
        """Create a visual progress bar"""
        filled = int((percentage / 100) * length)
        empty = length - filled
        return f"[{'█' * filled}{'░' * empty}]"

async def setup(bot):
    await bot.add_cog(SeasonCommands(bot))
