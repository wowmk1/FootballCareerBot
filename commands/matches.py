import discord
from discord import app_commands
from discord.ext import commands
from database import db

class MatchCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="play_match", description="Play your next match (when window is open)")
    async def play_match(self, interaction: discord.Interaction):
        """Start an interactive match"""
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet! Use `/start` to begin.",
                ephemeral=True
            )
            return
        
        if player['retired']:
            await interaction.response.send_message(
                "🏆 Your player has retired! Use `/start` to create a new player.",
                ephemeral=True
            )
            return
        
        if player['team_id'] == 'free_agent':
            await interaction.response.send_message(
                "❌ You're a free agent! You need to join a team first.",
                ephemeral=True
            )
            return
        
        state = await db.get_game_state()
        
        if not state['match_window_open']:
            await interaction.response.send_message(
                "⏰ Match window is currently **CLOSED**!\n\n"
                f"Use `/season` to see when the next match window opens.",
                ephemeral=True
            )
            return
        
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT * FROM fixtures 
                   WHERE (home_team_id = $1 OR away_team_id = $1)
                   AND playable = TRUE AND played = FALSE
                   LIMIT 1""",
                player['team_id']
            )
            fixture = dict(row) if row else None
        
        if not fixture:
            await interaction.response.send_message(
                "❌ No playable matches found!\n\n"
                "• You may have already played this week's match\n"
                "• Or there are no matches scheduled yet",
                ephemeral=True
            )
            return
        
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM active_matches WHERE fixture_id = $1",
                fixture['fixture_id']
            )
            existing_match = dict(row) if row else None
        
        if existing_match:
            await interaction.response.send_message(
                f"⚠️ This match is already in progress!\n\n"
                f"Check <#{existing_match['channel_id']}> to join or spectate.",
                ephemeral=True
            )
            return
        
        from utils import match_engine
        
        if not match_engine.match_engine:
            await interaction.response.send_message(
                "❌ Match engine not initialized! Contact an admin.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        await match_engine.match_engine.start_match(fixture, interaction)

async def setup(bot):
    await bot.add_cog(MatchCommands(bot))
