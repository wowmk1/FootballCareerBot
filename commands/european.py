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
    @app_commands.describe(
        competition="Competition to view (CL or EL)",
        team_name="Specific team to filter by (optional)"
    )
    @app_commands.choices(competition=[
        app_commands.Choice(name="Champions League", value="CL"),
        app_commands.Choice(name="Europa League", value="EL")
    ])
    async def european_fixtures(
        self, 
        interaction: discord.Interaction,
        competition: app_commands.Choice[str] = None,
        team_name: str = None
    ):
        await interaction.response.defer()
        
        competition_value = None
        filter_team_id = None
        display_team_name = None
        
        # If no competition specified, try to use user's team
        if not competition:
            player = await db.get_player(interaction.user.id)
            if player and player['team_id']:
                async with db.pool.acquire() as conn:
                    comp = await conn.fetchval("""
                        SELECT competition FROM european_groups
                        WHERE team_id = $1 LIMIT 1
                    """, player['team_id'])
                    
                    if comp:
                        competition_value = comp
                        filter_team_id = player['team_id']
                        display_team_name = player['team_name']
                    else:
                        await interaction.followup.send(
                            "Your team isn't in Europe! Specify a competition:\n"
                            "`/european_fixtures competition:CL` or `competition:EL`",
                            ephemeral=True
                        )
                        return
            else:
                await interaction.followup.send(
                    "Specify a competition:\n"
                    "`/european_fixtures competition:CL` or `competition:EL`",
                    ephemeral=True
                )
                return
        else:
            competition_value = competition.value
        
        # If team_name provided, find that team
        if team_name:
            async with db.pool.acquire() as conn:
                team = await conn.fetchrow("""
                    SELECT team_id, team_name FROM teams 
                    WHERE LOWER(team_name) LIKE LOWER($1)
                    UNION
                    SELECT team_id, team_name FROM european_teams
                    WHERE LOWER(team_name) LIKE LOWER($1)
                    LIMIT 1
                """, f"%{team_name}%")
                
                if team:
                    filter_team_id = team['team_id']
                    display_team_name = team['team_name']
                else:
                    await interaction.followup.send(f"Team '{team_name}' not found!", ephemeral=True)
                    return
        
        # Build query
        async with db.pool.acquire() as conn:
            if filter_team_id:
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
                """, competition_value, filter_team_id)
            else:
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
                    ORDER BY f.week_number
                    LIMIT 20
                """, competition_value)
        
        if not fixtures:
            await interaction.followup.send("No fixtures found!", ephemeral=True)
            return
        
        comp_name = "Champions League" if competition_value == 'CL' else "Europa League"
        
        if display_team_name:
            title = f"🏆 {comp_name} Fixtures"
            description = f"**{display_team_name}**"
        else:
            title = f"🏆 {comp_name} - All Fixtures"
            description = f"Showing first {len(fixtures)} fixtures"
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )
        
        for fixture in fixtures[:15]:  # Limit to 15 to avoid embed limits
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
    
    @app_commands.command(name="european_standings", description="View European group standings")
    @app_commands.describe(
        competition="Competition to view (CL or EL)",
        group="Group to view (A-H)"
    )
    @app_commands.choices(
        competition=[
            app_commands.Choice(name="Champions League", value="CL"),
            app_commands.Choice(name="Europa League", value="EL")
        ],
        group=[
            app_commands.Choice(name="Group A", value="A"),
            app_commands.Choice(name="Group B", value="B"),
            app_commands.Choice(name="Group C", value="C"),
            app_commands.Choice(name="Group D", value="D"),
            app_commands.Choice(name="Group E", value="E"),
            app_commands.Choice(name="Group F", value="F"),
            app_commands.Choice(name="Group G", value="G"),
            app_commands.Choice(name="Group H", value="H")
        ]
    )
    async def european_standings(
        self,
        interaction: discord.Interaction,
        competition: app_commands.Choice[str] = None,
        group: app_commands.Choice[str] = None
    ):
        await interaction.response.defer()
        
        competition_value = None
        group_value = None
        
        # If no params, try to use user's team
        if not competition or not group:
            player = await db.get_player(interaction.user.id)
            if player and player['team_id']:
                async with db.pool.acquire() as conn:
                    group_data = await conn.fetchrow("""
                        SELECT competition, group_name
                        FROM european_groups
                        WHERE team_id = $1
                    """, player['team_id'])
                    
                    if group_data:
                        competition_value = group_data['competition']
                        group_value = group_data['group_name']
                    else:
                        await interaction.followup.send(
                            "Your team isn't in Europe! Specify competition and group:\n"
                            "`/european_standings competition:CL group:A`",
                            ephemeral=True
                        )
                        return
            else:
                await interaction.followup.send(
                    "Specify competition and group:\n"
                    "`/european_standings competition:CL group:A`",
                    ephemeral=True
                )
                return
        else:
            competition_value = competition.value
            group_value = group.value
        
        # Get standings
        standings = await get_group_standings(competition_value, group_value)
        
        if not standings:
            await interaction.followup.send(
                f"No standings found for {competition_value} Group {group_value}!",
                ephemeral=True
            )
            return
        
        comp_name = "Champions League" if competition_value == 'CL' else "Europa League"
        
        embed = discord.Embed(
            title=f"🏆 {comp_name} - Group {group_value}",
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
    @app_commands.describe(
        competition="Competition to view (CL or EL)"
    )
    @app_commands.choices(competition=[
        app_commands.Choice(name="Champions League", value="CL"),
        app_commands.Choice(name="Europa League", value="EL")
    ])
    async def knockout_bracket(
        self,
        interaction: discord.Interaction,
        competition: app_commands.Choice[str] = None
    ):
        await interaction.response.defer()
        
        competition_value = None
        
        # If no competition specified, try to use user's team
        if not competition:
            player = await db.get_player(interaction.user.id)
            if player and player['team_id']:
                async with db.pool.acquire() as conn:
                    comp = await conn.fetchval("""
                        SELECT competition FROM european_groups
                        WHERE team_id = $1
                        LIMIT 1
                    """, player['team_id'])
                    
                    if comp:
                        competition_value = comp
                    else:
                        await interaction.followup.send(
                            "Your team isn't in Europe! Specify a competition:\n"
                            "`/knockout_bracket competition:CL` or `competition:EL`",
                            ephemeral=True
                        )
                        return
            else:
                await interaction.followup.send(
                    "Specify a competition:\n"
                    "`/knockout_bracket competition:CL` or `competition:EL`",
                    ephemeral=True
                )
                return
        else:
            competition_value = competition.value
        
        async with db.pool.acquire() as conn:
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
            """, competition_value)
        
        if not ties:
            await interaction.followup.send("Knockout stage hasn't started!", ephemeral=True)
            return
        
        comp_name = "Champions League" if competition_value == 'CL' else "Europa League"
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
