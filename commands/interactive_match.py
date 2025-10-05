import discord
from discord import app_commands
from discord.ext import commands
from database import db
import config

class InteractiveMatchCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="play_match", description="Start your interactive match during match windows")
    async def play_match(self, interaction: discord.Interaction):
        """Start interactive match for current match window"""
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet! Use `/start` to begin.",
                ephemeral=True
            )
            return
        
        if player['retired']:
            await interaction.response.send_message(
                "🏆 Your player has retired!",
                ephemeral=True
            )
            return
        
        if player['team_id'] == 'free_agent':
            await interaction.response.send_message(
                "❌ You need to be signed to a club to play matches!",
                ephemeral=True
            )
            return
        
        # Check if match window is open
        state = await db.get_game_state()
        
        if not state['match_window_open']:
            await interaction.response.send_message(
                "❌ No match window is currently open!\n\n"
                f"• Match windows open on **Monday, Wednesday, Saturday** at **{config.MATCH_START_HOUR}:00**\n"
                f"• Each window lasts **{config.MATCH_WINDOW_HOURS} hours**\n"
                f"• Use `/season` to check the schedule",
                ephemeral=True
            )
            return
        
        current_week = state['current_week']
        
        # Find playable fixture for player's team
        async with db.db.execute("""
            SELECT * FROM fixtures 
            WHERE (home_team_id = ? OR away_team_id = ?)
            AND week_number = ?
            AND playable = 1
            AND played = 0
            LIMIT 1
        """, (player['team_id'], player['team_id'], current_week)) as cursor:
            row = await cursor.fetchone()
            fixture = dict(row) if row else None
        
        if not fixture:
            await interaction.response.send_message(
                "❌ No playable match found for your team!\n\n"
                "• Your team may have already played this week\n"
                "• Use `/fixtures` to see your schedule\n"
                "• Use `/results` to see completed matches",
                ephemeral=True
            )
            return
        
        # Check if match already active
        async with db.db.execute(
            "SELECT match_id FROM active_matches WHERE fixture_id = ?",
            (fixture['fixture_id'],)
        ) as cursor:
            existing = await cursor.fetchone()
        
        if existing:
            await interaction.response.send_message(
                "⚽ This match is already in progress!\n\n"
                "Check the match channel or wait for it to finish.",
                ephemeral=True
            )
            return
        
        # Defer response as match creation takes time
        await interaction.response.defer()
        
        # Start match using match engine
        from utils.match_engine import match_engine
        
        match_id = await match_engine.start_interactive_match(
            fixture['fixture_id'],
            interaction.guild,
            interaction.channel
        )
        
        if not match_id:
            await interaction.followup.send(
                "❌ Could not start match. Please try again or contact an admin.",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "✅ Match starting! Check the match channel.",
                ephemeral=True
            )
    
    @app_commands.command(name="match_status", description="Check if any matches are currently active")
    async def match_status(self, interaction: discord.Interaction):
        """Check active matches"""
        
        async with db.db.execute("""
            SELECT am.*, 
                   ht.team_name as home_name,
                   at.team_name as away_name
            FROM active_matches am
            JOIN teams ht ON am.home_team_id = ht.team_id
            JOIN teams at ON am.away_team_id = at.team_id
        """) as cursor:
            rows = await cursor.fetchall()
            matches = [dict(row) for row in rows]
        
        if not matches:
            await interaction.response.send_message(
                "📊 No matches currently active.\n\n"
                "Use `/play_match` during match windows to start your game!",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="⚽ Active Matches",
            description=f"**{len(matches)} match(es) in progress:**",
            color=discord.Color.green()
        )
        
        for match in matches:
            status_text = {
                'waiting': '⏳ Waiting for players',
                'active': '🎮 In progress',
                'finishing': '🏁 Finishing up'
            }.get(match['match_state'], '❓ Unknown')
            
            embed.add_field(
                name=f"{match['home_name']} vs {match['away_name']}",
                value=(
                    f"Score: **{match['home_score']}-{match['away_score']}**\n"
                    f"Status: {status_text}\n"
                    f"Events: {match['events_completed']}/{config.MATCH_EVENTS_PER_GAME}"
                ),
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(InteractiveMatchCommands(bot))
