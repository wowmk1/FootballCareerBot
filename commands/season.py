import discord
from discord import app_commands
from discord.ext import commands
from database import db
import config
from datetime import datetime

class SeasonCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="season", description="View current season status and schedule")
    async def season(self, interaction: discord.Interaction):
        """View season information"""
        
        state = await db.get_game_state()
        
        if not state['season_started']:
            embed = discord.Embed(
                title="⏳ Season Not Started",
                description="Waiting for first player to join...\n\nUse `/start` to create your player and begin the season!",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"📅 Season {state['current_season']}",
            description=f"**Week {state['current_week']}/{config.SEASON_TOTAL_WEEKS}**",
            color=discord.Color.blue()
        )
        
        if state['match_window_open']:
            closes = datetime.fromisoformat(state['match_window_closes'])
            time_left = closes - datetime.now()
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            
            embed.add_field(
                name="🟢 Match Window: OPEN",
                value=f"⏰ Closes in **{hours}h {minutes}m**\n💡 Use `/play_match` to play!",
                inline=False
            )
        else:
            if state['next_match_day']:
                next_match = datetime.fromisoformat(state['next_match_day'])
                time_until = next_match - datetime.now()
                
                if time_until.total_seconds() > 0:
                    days = time_until.days
                    hours = int(time_until.seconds // 3600)
                    minutes = int((time_until.seconds % 3600) // 60)
                    
                    if days > 0:
                        time_str = f"{days}d {hours}h"
                    else:
                        time_str = f"{hours}h {minutes}m"
                    
                    embed.add_field(
                        name="🔴 Match Window: CLOSED",
                        value=f"⏰ Next window in **{time_str}**\n📅 Opens: {next_match.strftime('%a, %b %d at %H:%M')}",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="⏰ Match Window",
                        value="Opening soon...",
                        inline=False
                    )
            else:
                embed.add_field(
                    name="🏁 Season Status",
                    value="Season completed!",
                    inline=False
                )
        
        embed.add_field(
            name="📊 Match Schedule",
            value=f"• **{config.MATCHES_PER_WEEK}** match days per week\n"
                  f"• **{config.MATCH_WINDOW_HOURS}h** window to play each match\n"
                  f"• **{config.MATCH_EVENTS_PER_GAME}** key moments per match",
            inline=False
        )
        
        async with db.pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT COUNT(*) as count FROM fixtures WHERE played = TRUE"
            )
            played = result['count']
            
            result = await conn.fetchrow(
                "SELECT COUNT(*) as count FROM fixtures"
            )
            total = result['count']
        
        if total > 0:
            progress = (played / total) * 100
            embed.add_field(
                name="⚽ Season Progress",
                value=f"{played}/{total} matches played ({progress:.1f}%)",
                inline=False
            )
        
        if state['last_match_day']:
            last = datetime.fromisoformat(state['last_match_day'])
            embed.set_footer(text=f"Last match day: {last.strftime('%a, %b %d at %H:%M')}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="fixtures", description="View your upcoming matches")
    async def fixtures(self, interaction: discord.Interaction):
        """View player's fixtures"""
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet! Use `/start` to begin.",
                ephemeral=True
            )
            return
        
        if player['team_id'] == 'free_agent':
            await interaction.response.send_message(
                "❌ You're a free agent! Sign with a team to see fixtures.",
                ephemeral=True
            )
            return
        
        fixtures = await db.get_player_team_fixtures(interaction.user.id, limit=10)
        
        if not fixtures:
            await interaction.response.send_message(
                "📅 No upcoming fixtures found!",
                ephemeral=True
            )
            return
        
        team = await db.get_team(player['team_id'])
        
        embed = discord.Embed(
            title=f"📅 {team['team_name']} Fixtures",
            description=f"Upcoming matches for {player['player_name']}",
            color=discord.Color.blue()
        )
        
        state = await db.get_game_state()
        current_week = state['current_week']
        
        for fixture in fixtures[:8]:
            is_home = fixture['home_team_id'] == player['team_id']
            opponent_id = fixture['away_team_id'] if is_home else fixture['home_team_id']
            
            opponent = await db.get_team(opponent_id)
            opponent_name = opponent['team_name'] if opponent else opponent_id
            
            venue = "🏠 Home" if is_home else "✈️ Away"
            
            status = ""
            if fixture['playable']:
                status = "🟢 **PLAYABLE NOW**"
            elif fixture['week_number'] == current_week:
                status = "⏳ This week"
            
            embed.add_field(
                name=f"Week {fixture['week_number']} - {venue}",
                value=f"**vs {opponent_name}**\n{status}",
                inline=False
            )
        
        embed.set_footer(text="Use /play_match when your match is playable!")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="results", description="View recent match results")
    async def results(self, interaction: discord.Interaction):
        """View recent results"""
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet! Use `/start` to begin.",
                ephemeral=True
            )
            return
        
        if player['team_id'] == 'free_agent':
            async with db.pool.acquire() as conn:
                rows = await conn.fetch(
                    """SELECT * FROM fixtures 
                       WHERE played = TRUE 
                       ORDER BY week_number DESC 
                       LIMIT 10"""
                )
                fixtures = [dict(row) for row in rows]
            
            if not fixtures:
                await interaction.response.send_message(
                    "📊 No matches played yet!",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="📊 Recent Results",
                description="Latest match results across all leagues",
                color=discord.Color.blue()
            )
        else:
            async with db.pool.acquire() as conn:
                rows = await conn.fetch(
                    """SELECT * FROM fixtures 
                       WHERE (home_team_id = $1 OR away_team_id = $1) 
                       AND played = TRUE 
                       ORDER BY week_number DESC 
                       LIMIT 10""",
                    player['team_id']
                )
                fixtures = [dict(row) for row in rows]
            
            if not fixtures:
                await interaction.response.send_message(
                    f"📊 No matches played yet for your team!",
                    ephemeral=True
                )
                return
            
            team = await db.get_team(player['team_id'])
            embed = discord.Embed(
                title=f"📊 {team['team_name']} - Recent Results",
                description=f"Latest matches for {player['player_name']}'s team",
                color=discord.Color.blue()
            )
        
        for fixture in fixtures[:8]:
            home_team = await db.get_team(fixture['home_team_id'])
            away_team = await db.get_team(fixture['away_team_id'])
            
            home_name = home_team['team_name'] if home_team else fixture['home_team_id']
            away_name = away_team['team_name'] if away_team else fixture['away_team_id']
            
            home_score = fixture['home_score'] or 0
            away_score = fixture['away_score'] or 0
            
            if home_score > away_score:
                result_emoji = "🟢" if player and player['team_id'] == fixture['home_team_id'] else "🔴"
            elif away_score > home_score:
                result_emoji = "🟢" if player and player['team_id'] == fixture['away_team_id'] else "🔴"
            else:
                result_emoji = "🟡"
            
            if player and player['team_id'] not in ['free_agent'] and player['team_id'] in [fixture['home_team_id'], fixture['away_team_id']]:
                result_text = result_emoji
            else:
                result_emoji = "⚽"
                result_text = ""
            
            embed.add_field(
                name=f"{result_text} Week {fixture['week_number']}",
                value=f"**{home_name}** {home_score} - {away_score} **{away_name}**",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(SeasonCommands(bot))
