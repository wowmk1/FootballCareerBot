```python
"""
European Competition Commands
"""

import discord
from discord import app_commands
from discord.ext import commands
from database import db
from utils.european_competitions import get_group_standings
import config

class European(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="european_fixtures", description="View European fixtures")
    async def european_fixtures(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        player = await db.get_player(interaction.user.id)
        if not player or not player['team_id']:
            await interaction.followup.send("You don't have a team!", ephemeral=True)
            return
        
        async with db.pool.acquire() as conn:
            competition = await conn.fetchval("""
                SELECT competition FROM european_groups
                WHERE team_id = $1
                LIMIT 1
            """, player['team_id'])
            
            if not competition:
                await interaction.followup.send("Your team isn't in Europe!", ephemeral=True)
                return
            
            fixtures = await conn.fetch("""
                SELECT f.*,
                       COALESCE(ht.team_name, eht.team_name) as home_name,
                       COALESCE(at.team_name, eat.team_name) as away_name
                FROM european_fixtures f
                LEFT JOIN teams ht ON f.home_team_id = ht.team_id
                LEFT JOIN teams at ON f.away_team_id = at.team_id
                LEFT JOIN european_teams eht ON f.home_team_id = eht.team_id
                LEFT JOIN european_teams eat ON f.away_team_id = eat.team_id
                WHERE f.competition = $1
                  AND (f.home_team_id = $2 OR f.away_team_id = $2)
                ORDER BY f.week_number
            """, competition, player['team_id'])
        
        if not fixtures:
            await interaction.followup.send("No fixtures found!", ephemeral=True)
            return
        
        comp_name = "Champions League" if competition == 'CL' else "Europa League"
        embed = discord.Embed(
            title=f"🏆 {comp_name} Fixtures",
            description=f"**{player['team_name']}**",
            color=discord.Color.blue()
        )
        
        for fixture in fixtures[:10]:
            if fixture['played']:
                result = f"{fixture['home_score']}-{fixture['away_score']}"
                status = "✅"
            elif fixture['playable']:
                result = "vs"
                status = "🟢"
            else:
                result = "vs"
                status = "⏳"
            
            leg_text = f" (Leg {fixture['leg']})" if fixture['leg'] and fixture['leg'] > 1 else ""
            
            embed.add_field(
                name=f"{status} Week {fixture['week_number']} - {fixture['stage'].title()}{leg_text}",
                value=f"{fixture['home_name']} {result} {fixture['away_name']}",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="european_standings", description="View European standings")
    async def european_standings(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        player = await db.get_player(interaction.user.id)
        if not player:
            await interaction.followup.send("You don't have a player!", ephemeral=True)
            return
        
        async with db.pool.acquire() as conn:
            group_data = await conn.fetchrow("""
                SELECT competition, group_name
                FROM european_groups
                WHERE team_id = $1
            """, player['team_id'])
            
            if not group_data:
                await interaction.followup.send("Your team isn't in Europe!", ephemeral=True)
                return
        
        standings = await get_group_standings(group_data['competition'], group_data['group_name'])
        
        comp_name = "Champions League" if group_data['competition'] == 'CL' else "Europa League"
        
        embed = discord.Embed(
            title=f"🏆 {comp_name} - Group {group_data['group_name']}",
            color=discord.Color.gold()
        )
        
        table = "```\n"
        table += "Pos | Team              | P | W | D | L | GF | GA | GD | Pts\n"
        table += "-" * 65 + "\n"
        
        for idx, team in enumerate(standings, 1):
            qualifier = "🟢" if idx <= 2 else "  "
            team_name = team['team_name'][:17].ljust(17)
            gd = team['goal_difference']
            
            table += f"{qualifier}{idx}  | {team_name} | {team['played']} | {team['won']} | "
            table += f"{team['drawn']} | {team['lost']} | {team['goals_for']} | "
            table += f"{team['goals_against']} | {gd:+3} | {team['points']}\n"
        
        table += "```\n🟢 = Qualified for knockout stage"
        embed.description = table
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="knockout_bracket", description="View knockout bracket")
    async def knockout_bracket(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        player = await db.get_player(interaction.user.id)
        if not player:
            await interaction.followup.send("You don't have a player!", ephemeral=True)
            return
        
        async with db.pool.acquire() as conn:
            competition = await conn.fetchval("""
                SELECT competition FROM european_groups
                WHERE team_id = $1
                LIMIT 1
            """, player['team_id'])
            
            if not competition:
                await interaction.followup.send("Your team isn't in Europe!", ephemeral=True)
                return
            
            ties = await conn.fetch("""
                SELECT k.*,
                       COALESCE(ht.team_name, eht.team_name) as home_name,
                       COALESCE(at.team_name, eat.team_name) as away_name,
                       COALESCE(wt.team_name, ewt.team_name) as winner_name
                FROM european_knockout k
                LEFT JOIN teams ht ON k.home_team_id = ht.team_id
                LEFT JOIN teams at ON k.away_team_id = at.team_id
                LEFT JOIN teams wt ON k.winner_team_id = wt.team_id
                LEFT JOIN european_teams eht ON k.home_team_id = eht.team_id
                LEFT JOIN european_teams eat ON k.away_team_id = eat.team_id
                LEFT JOIN european_teams ewt ON k.winner_team_id = ewt.team_id
                WHERE k.competition = $1
                ORDER BY 
                    CASE k.stage
                        WHEN 'r16' THEN 1
                        WHEN 'quarters' THEN 2
                        WHEN 'semis' THEN 3
                        WHEN 'final' THEN 4
                    END
            """, competition)
        
        if not ties:
            await interaction.followup.send("Knockout stage hasn't started!", ephemeral=True)
            return
        
        comp_name = "Champions League" if competition == 'CL' else "Europa League"
        embed = discord.Embed(
            title=f"🏆 {comp_name} Knockout Bracket",
            color=discord.Color.blue()
        )
        
        stages = {'r16': [], 'quarters': [], 'semis': [], 'final': []}
        for tie in ties:
            stages[tie['stage']].append(tie)
        
        for stage_name, stage_ties in stages.items():
            if not stage_ties:
                continue
            
            stage_display = {
                'r16': 'Round of 16',
                'quarters': 'Quarter-Finals',
                'semis': 'Semi-Finals',
                'final': 'Final'
            }[stage_name]
            
            field_value = ""
            for tie in stage_ties:
                if tie['winner_team_id']:
                    if tie['penalties_taken']:
                        field_value += f"~~{tie['home_name']}~~ vs ~~{tie['away_name']}~~\n"
                        field_value += f"**Winner: {tie['winner_name']}** (Penalties)\n\n"
                    else:
                        if stage_name == 'final':
                            field_value += f"{tie['home_name']} {tie['first_leg_home_score']}-{tie['first_leg_away_score']} {tie['away_name']}\n"
                        else:
                            field_value += f"{tie['home_name']} (Agg: {tie['aggregate_home']}-{tie['aggregate_away']}) {tie['away_name']}\n"
                        field_value += f"**Winner: {tie['winner_name']}**\n\n"
                else:
                    field_value += f"{tie['home_name']} vs {tie['away_name']}\n"
                    if tie['first_leg_played']:
                        field_value += f"First Leg: {tie['first_leg_home_score']}-{tie['first_leg_away_score']}\n"
                    if tie['second_leg_played']:
                        field_value += f"Second Leg: {tie['second_leg_home_score']}-{tie['second_leg_away_score']}\n"
                    field_value += "\n"
            
            embed.add_field(
                name=f"⚡ {stage_display}",
                value=field_value or "Not started",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(European(bot))
```

---
