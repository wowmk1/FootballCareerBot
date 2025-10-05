import discord
from discord import app_commands
from discord.ext import commands
from database import db

class LeagueCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="league", description="View league tables and standings")
    @app_commands.describe(league="Which league to view")
    @app_commands.choices(league=[
        app_commands.Choice(name="Premier League", value="Premier League"),
        app_commands.Choice(name="Championship", value="Championship"),
        app_commands.Choice(name="League One", value="League One"),
    ])
    async def league(self, interaction: discord.Interaction, league: str = "Premier League"):
        """View league table"""
        
        teams = await db.get_league_table(league)
        
        if not teams:
            await interaction.response.send_message(
                f"❌ No teams found in {league}!",
                ephemeral=True
            )
            return
        
        state = await db.get_game_state()
        current_week = state['current_week'] if state['season_started'] else 0
        
        embed = discord.Embed(
            title=f"🏆 {league} Table",
            description=f"Week {current_week}/{38}",
            color=discord.Color.gold()
        )
        
        table_text = "```\nPos | Team                | Pld | Pts\n"
        table_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for idx, team in enumerate(teams, 1):
            team_name = team['team_name'][:18].ljust(18)
            
            if league == "Premier League":
                if idx <= 4:
                    pos = f"{idx}🟢"
                elif idx <= 6:
                    pos = f"{idx}🔵"
                elif idx == 7:
                    pos = f"{idx}🟡"
                elif idx >= 18:
                    pos = f"{idx}🔴"
                else:
                    pos = f"{idx}  "
            else:
                if idx <= 2:
                    pos = f"{idx}🟢"
                elif idx <= 6:
                    pos = f"{idx}🟡"
                elif idx >= 22:
                    pos = f"{idx}🔴"
                else:
                    pos = f"{idx}  "
            
            async with db.db.execute(
                "SELECT COUNT(*) as count FROM players WHERE team_id = ? AND retired = 0",
                (team['team_id'],)
            ) as cursor:
                result = await cursor.fetchone()
                player_count = result['count']
            
            marker = " ⭐" if player_count > 0 else "   "
            
            table_text += f"{pos.ljust(4)}| {team_name} | {str(team['played']).rjust(3)} | {str(team['points']).rjust(3)}{marker}\n"
        
        table_text += "```"
        
        embed.description = f"Week {current_week}/{38}\n\n{table_text}"
        
        if league == "Premier League":
            legend = (
                "🟢 Champions League | 🔵 Europa League\n"
                "🟡 Conference League | 🔴 Relegation | ⭐ Your team"
            )
        else:
            legend = (
                "🟢 Promotion | 🟡 Playoffs\n"
                "🔴 Relegation | ⭐ Your team"
            )
        
        embed.add_field(name="Legend", value=legend, inline=False)
        embed.set_footer(text="Use /standings for detailed stats")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="standings", description="View detailed league standings with stats")
    @app_commands.describe(league="Which league to view")
    @app_commands.choices(league=[
        app_commands.Choice(name="Premier League", value="Premier League"),
        app_commands.Choice(name="Championship", value="Championship"),
        app_commands.Choice(name="League One", value="League One"),
    ])
    async def standings(self, interaction: discord.Interaction, league: str = "Premier League"):
        """View detailed standings"""
        
        teams = await db.get_league_table(league)
        
        if not teams:
            await interaction.response.send_message(
                f"❌ No teams found in {league}!",
                ephemeral=True
            )
            return
        
        state = await db.get_game_state()
        current_week = state['current_week'] if state['season_started'] else 0
        
        embed = discord.Embed(
            title=f"📊 {league} - Full Standings",
            description=f"Week {current_week}/{38}",
            color=discord.Color.blue()
        )
        
        table_text = "```\nPos | Team           | P  W  D  L | GF GA GD | Pts\n"
        table_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for idx, team in enumerate(teams[:20], 1):
            team_name = team['team_name'][:14].ljust(14)
            gd = team['goals_for'] - team['goals_against']
            gd_str = f"+{gd}" if gd > 0 else str(gd)
            
            table_text += (
                f"{str(idx).rjust(2)} | {team_name} | "
                f"{str(team['played']).rjust(2)} "
                f"{str(team['won']).rjust(2)} "
                f"{str(team['drawn']).rjust(2)} "
                f"{str(team['lost']).rjust(2)} | "
                f"{str(team['goals_for']).rjust(2)} "
                f"{str(team['goals_against']).rjust(2)} "
                f"{gd_str.rjust(3)} | "
                f"{str(team['points']).rjust(3)}\n"
            )
        
        table_text += "```"
        
        embed.description = f"Week {current_week}/{38}\n\n{table_text}"
        
        async with db.db.execute("""
            SELECT p.player_name, p.season_goals, p.team_id, t.team_name
            FROM players p
            LEFT JOIN teams t ON p.team_id = t.team_id
            WHERE p.retired = 0 AND t.league = ? AND p.season_goals > 0
            ORDER BY p.season_goals DESC
            LIMIT 5
        """, (league,)) as cursor:
            top_scorers = await cursor.fetchall()
        
        if top_scorers:
            scorers_text = ""
            for idx, scorer in enumerate(top_scorers, 1):
                scorers_text += f"{idx}. **{scorer['player_name']}** ({scorer['team_name']}) - {scorer['season_goals']} goals\n"
            embed.add_field(name="⚽ Top Scorers (Players)", value=scorers_text, inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(LeagueCommands(bot))
