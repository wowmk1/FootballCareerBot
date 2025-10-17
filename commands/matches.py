import discord
from discord import app_commands
from discord.ext import commands
from database import db

class MatchCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="play_match", description="Play your next available match")
    async def play_match(self, interaction: discord.Interaction):
        """Play next match - checks BOTH domestic AND European fixtures"""
        
        await interaction.response.defer()
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.followup.send("❌ You don't have a player! Use `/start` to begin.", ephemeral=True)
            return
        
        if player['retired']:
            await interaction.followup.send("🏆 Your player has retired! Use `/start` to create a new player.", ephemeral=True)
            return
        
        if not player['team_id'] or player['team_id'] == 'free_agent':
            await interaction.followup.send("❌ You need to be on a team!", ephemeral=True)
            return
        
        async with db.pool.acquire() as conn:
            # Check for European fixture FIRST (priority over domestic)
            european_fixture = await conn.fetchrow("""
                SELECT f.*,
                       COALESCE(ht.team_name, eht.team_name) as home_name,
                       COALESCE(at.team_name, eat.team_name) as away_name
                FROM european_fixtures f
                LEFT JOIN teams ht ON f.home_team_id = ht.team_id
                LEFT JOIN teams at ON f.away_team_id = at.team_id
                LEFT JOIN european_teams eht ON f.home_team_id = eht.team_id
                LEFT JOIN european_teams eat ON f.away_team_id = eat.team_id
                WHERE (f.home_team_id = $1 OR f.away_team_id = $1)
                AND f.playable = TRUE
                AND f.played = FALSE
                ORDER BY f.week_number
                LIMIT 1
            """, player['team_id'])
            
            if european_fixture:
                comp_name = "Champions League" if european_fixture['competition'] == 'CL' else "Europa League"
                leg_text = f" (Leg {european_fixture['leg']})" if european_fixture['leg'] > 1 else ""
                
                await interaction.followup.send(
                    f"🏆 **{comp_name}** match available{leg_text}!\n"
                    f"**{european_fixture['home_name']}** vs **{european_fixture['away_name']}**\n\n"
                    f"Starting match...",
                    ephemeral=False
                )
                
                # Start European match
                from utils import match_engine
                
                if not match_engine.match_engine:
                    await interaction.followup.send("❌ Match engine not initialized! Contact an admin.", ephemeral=True)
                    return
                
                await match_engine.match_engine.start_match(
                    dict(european_fixture),
                    interaction,
                    is_european=True
                )
                return
            
            # Check for domestic fixture
            domestic_fixture = await conn.fetchrow("""
                SELECT f.*, 
                       ht.team_name as home_name,
                       at.team_name as away_name
                FROM fixtures f
                JOIN teams ht ON f.home_team_id = ht.team_id
                JOIN teams at ON f.away_team_id = at.team_id
                WHERE (f.home_team_id = $1 OR f.away_team_id = $1)
                AND f.playable = TRUE
                AND f.played = FALSE
                ORDER BY f.week_number
                LIMIT 1
            """, player['team_id'])
            
            if domestic_fixture:
                await interaction.followup.send(
                    f"⚽ Domestic match available!\n"
                    f"**{domestic_fixture['home_name']}** vs **{domestic_fixture['away_name']}**\n\n"
                    f"Starting match...",
                    ephemeral=False
                )
                
                from utils import match_engine
                
                if not match_engine.match_engine:
                    await interaction.followup.send("❌ Match engine not initialized! Contact an admin.", ephemeral=True)
                    return
                
                await match_engine.match_engine.start_match(
                    dict(domestic_fixture),
                    interaction,
                    is_european=False
                )
                return
            
            await interaction.followup.send(
                "⏳ No playable matches available!\n"
                "• You may have already played this week's match\n"
                "• Wait for the next match window to open\n"
                "• Use `/season` to check match schedule",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(MatchCommands(bot))
