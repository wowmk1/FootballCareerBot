import discord
from discord import app_commands
from discord.ext import commands
from database import db
from utils.football_data_api import get_team_crest_url, get_competition_logo

class LeagueCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def league(self, interaction: discord.Interaction, league: str = "Premier League"):
        """View league standings (called by /league_info command)"""
        
        table = await db.get_league_table(league)
        
        if not table:
            await interaction.response.send_message(
                f"❌ No data found for {league}!",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"🏆 {league} Table",
            color=discord.Color.blue()
        )
        
        # ADD COMPETITION LOGO - but use set_author to keep it out of the way
        comp_logo = get_competition_logo(league)
        if comp_logo:
            embed.set_author(name=league, icon_url=comp_logo)
        
        # Build table with FIXED spacing
        lines = []
        lines.append("```")
        # Header
        lines.append("Pos Team                 Pld  W  D  L   GF  GA  GD Pts")
        lines.append("─" * 62)
        
        for pos, team in enumerate(table, 1):
            gd = team['goals_for'] - team['goals_against']
            # Format GD with sign
            if gd > 0:
                gd_str = f"+{gd}"
            elif gd == 0:
                gd_str = " 0"
            else:
                gd_str = str(gd)
            
            # Pad GD to exactly 3 characters (right-aligned)
            gd_str = gd_str.rjust(3)
            
            # Truncate and pad team name to exactly 20 characters
            team_name = team['team_name'][:20].ljust(20)
            
            # Position emoji
            if pos <= 4:
                emoji = "🟢"
            elif pos <= 6:
                emoji = "🔵"
            elif pos >= len(table) - 2:
                emoji = "🔴"
            else:
                emoji = "  "
            
            # Build line with exact spacing
            line = f"{emoji}{pos:2} {team_name} {team['played']:3} {team['won']:2} {team['drawn']:2} {team['lost']:2} {team['goals_for']:3} {team['goals_against']:3} {gd_str} {team['points']:3}"
            lines.append(line)
        
        lines.append("```")
        
        embed.description = "\n".join(lines)
        
        # Dynamic key based on league
        if league == "Premier League":
            key_text = "🟢 Champions League (Top 4)\n🔵 Europa League (5-6)\n🔴 Relegation (Bottom 3)"
        elif league == "Championship":
            key_text = "🟢 Promotion to Premier League (Top 2)\n🟡 Playoffs (3-6)\n🔴 Relegation to League One (Bottom 3)"
        elif league == "League One":
            key_text = "🟢 Promotion to Championship (Top 2)\n🟡 Playoffs (3-6)\n🔴 Relegation to League Two (Bottom 4)"
        else:
            key_text = "🟢 Promotion\n🔴 Relegation"
        
        embed.add_field(
            name="🔑 Key",
            value=key_text,
            inline=False
        )
        
        state = await db.get_game_state()
        embed.set_footer(text=f"Season {state['current_season']} • Week {state['current_week']} • Leaders: {table[0]['team_name']}")
        
        await interaction.response.send_message(embed=embed)
    
    async def top_scorers(self, interaction: discord.Interaction):
        """View top scorers (called by /league_info command)"""
        
        player = await db.get_player(interaction.user.id)
        
        if player and player['league']:
            league = player['league']
        else:
            league = "Premier League"
        
        async with db.pool.acquire() as conn:
            user_rows = await conn.fetch(
                """SELECT p.player_name, p.season_goals, p.season_assists, p.season_apps, t.team_name
                   FROM players p
                   LEFT JOIN teams t ON p.team_id = t.team_id
                   WHERE p.league = $1 AND p.retired = FALSE
                   ORDER BY p.season_goals DESC
                   LIMIT 10""",
                league
            )
            
            npc_rows = await conn.fetch(
                """SELECT n.player_name, n.season_goals, n.season_assists, n.season_apps, t.team_name
                   FROM npc_players n
                   LEFT JOIN teams t ON n.team_id = t.team_id
                   WHERE t.league = $1 AND n.retired = FALSE
                   ORDER BY n.season_goals DESC
                   LIMIT 10""",
                league
            )
        
        all_scorers = []
        for row in user_rows:
            all_scorers.append(dict(row))
        for row in npc_rows:
            all_scorers.append(dict(row))
        
        all_scorers.sort(key=lambda x: x['season_goals'], reverse=True)
        all_scorers = all_scorers[:10]
        
        if not all_scorers:
            await interaction.response.send_message(
                f"📊 No goals scored yet in {league}!",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"👟 {league} - Top Scorers",
            color=discord.Color.gold()
        )
        
        # ADD LEAGUE LOGO using set_author instead of thumbnail
        comp_logo = get_competition_logo(league)
        if comp_logo:
            embed.set_author(name=f"{league} Top Scorers", icon_url=comp_logo)
        
        scorers_text = ""
        for i, scorer in enumerate(all_scorers, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            team_name = scorer['team_name'] if scorer['team_name'] else 'Free Agent'
            
            scorers_text += f"{emoji} **{scorer['player_name']}** ({team_name})\n"
            scorers_text += f"   ⚽ {scorer['season_goals']} goals | 🅰️ {scorer['season_assists']} assists | 👕 {scorer['season_apps']} apps\n\n"
        
        embed.description = scorers_text
        
        state = await db.get_game_state()
        embed.set_footer(text=f"Season {state['current_season']} • Week {state['current_week']}")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(LeagueCommands(bot))
