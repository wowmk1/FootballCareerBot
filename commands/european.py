"""
European Competition Commands - UNIFIED ACTION MENU
"""

import discord
from discord import app_commands
from discord.ext import commands
from database import db
from utils.football_data_api import get_team_crest_url, get_competition_logo
import config

class European(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="european", description="🏆 European competition tools")
    @app_commands.describe(
        action="Choose what to view",
        competition="Competition (CL/EL)",
        group="Group for standings (A-H)",
        team_name="Filter by team name",
        home_team="Home team for match card",
        away_team="Away team for match card"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="📋 Fixtures", value="fixtures"),
            app_commands.Choice(name="📊 Standings", value="standings"),
            app_commands.Choice(name="🎯 Match Card", value="match"),
            app_commands.Choice(name="🏆 Knockout Bracket", value="bracket")
        ],
        competition=[
            app_commands.Choice(name="⭐ Champions League", value="CL"),
            app_commands.Choice(name="🌟 Europa League", value="EL")
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
    async def european(
        self,
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        competition: app_commands.Choice[str] = None,
        group: app_commands.Choice[str] = None,
        team_name: str = None,
        home_team: str = None,
        away_team: str = None
    ):
        """Unified European competition command"""
        if action.value == "fixtures":
            await self._show_fixtures(interaction, competition, team_name)
        elif action.value == "standings":
            await self._show_standings(interaction, competition, group)
        elif action.value == "match":
            await self._show_match(interaction, home_team, away_team)
        elif action.value == "bracket":
            await self._show_bracket(interaction, competition)
    
    async def _show_fixtures(self, interaction, competition, team_name):
        """Show European fixtures"""
        await interaction.response.defer()
        
        competition_value = None
        filter_team_id = None
        display_team_name = None
        
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
                            "❌ Your team isn't in Europe! Specify:\n"
                            "`/european action:fixtures competition:CL`",
                            ephemeral=True
                        )
                        return
            else:
                await interaction.followup.send(
                    "❌ Specify a competition:\n"
                    "`/european action:fixtures competition:CL`",
                    ephemeral=True
                )
                return
        else:
            competition_value = competition.value
        
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
                    await interaction.followup.send(f"❌ Team '{team_name}' not found!", ephemeral=True)
                    return
        
        async with db.pool.acquire() as conn:
            if filter_team_id:
                fixtures = await conn.fetch("""
                    SELECT f.*, f.home_team_id, f.away_team_id,
                           COALESCE(ht.team_name, eht.team_name) as home_name,
                           COALESCE(at.team_name, eat.team_name) as away_name
                    FROM european_fixtures f
                    LEFT JOIN teams ht ON f.home_team_id = ht.team_id
                    LEFT JOIN teams at ON f.away_team_id = at.team_id
                    LEFT JOIN european_teams eht ON f.home_team_id = eht.team_id
                    LEFT JOIN european_teams eat ON f.away_team_id = eat.team_id
                    WHERE f.competition = $1
                      AND (f.home_team_id = $2 OR f.away_team_id = $2)
                    ORDER BY f.week_number, f.fixture_id
                """, competition_value, filter_team_id)
            else:
                fixtures = await conn.fetch("""
                    SELECT f.*, f.home_team_id, f.away_team_id,
                           COALESCE(ht.team_name, eht.team_name) as home_name,
                           COALESCE(at.team_name, eat.team_name) as away_name
                    FROM european_fixtures f
                    LEFT JOIN teams ht ON f.home_team_id = ht.team_id
                    LEFT JOIN teams at ON f.away_team_id = at.team_id
                    LEFT JOIN european_teams eht ON f.home_team_id = eht.team_id
                    LEFT JOIN european_teams eat ON f.away_team_id = eat.team_id
                    WHERE f.competition = $1
                    ORDER BY f.week_number, f.fixture_id
                    LIMIT 12
                """, competition_value)
        
        if not fixtures:
            await interaction.followup.send("❌ No fixtures found!", ephemeral=True)
            return
        
        comp_name = "Champions League" if competition_value == 'CL' else "Europa League"
        comp_emoji = "⭐" if competition_value == 'CL' else "🌟"
        comp_color = discord.Color.blue() if competition_value == 'CL' else discord.Color.gold()
        
        embeds = []
        for idx, fixture in enumerate(fixtures[:10]):
            home_crest = get_team_crest_url(fixture['home_team_id'])
            away_crest = get_team_crest_url(fixture['away_team_id'])
            comp_logo = get_competition_logo(comp_name)
            
            if fixture['played']:
                status_emoji = "✅"
                status_text = "Full Time"
                score_display = f"**{fixture['home_score']} - {fixture['away_score']}**"
            elif fixture.get('playable'):
                status_emoji = "🟢"
                status_text = "Live - Play Now!"
                score_display = "**VS**"
            else:
                status_emoji = "⏳"
                status_text = "Upcoming"
                score_display = "**VS**"
            
            if fixture['stage'] == 'group':
                stage_display = f"Group {fixture.get('group_name', '?')} • Week {fixture['week_number']}"
            else:
                leg_text = f" - Leg {fixture['leg']}" if fixture.get('leg', 1) > 1 else ""
                stage_display = f"{fixture['stage'].title()}{leg_text} • Week {fixture['week_number']}"
            
            embed = discord.Embed(
                title=f"{comp_emoji} {comp_name}",
                description=f"**{fixture['home_name']}** {score_display} **{fixture['away_name']}**",
                color=comp_color
            )
            
            if comp_logo:
                embed.set_thumbnail(url=comp_logo)
            if home_crest:
                embed.set_author(name=fixture['home_name'], icon_url=home_crest)
            if away_crest:
                embed.set_footer(text=fixture['away_name'], icon_url=away_crest)
            
            embed.add_field(name="📋 Status", value=f"{status_emoji} **{status_text}**", inline=True)
            embed.add_field(name="🏆 Stage", value=stage_display, inline=True)
            embed.add_field(name="📅 Week", value=f"**{fixture['week_number']}**", inline=True)
            embeds.append(embed)
        
        if len(embeds) == 1:
            await interaction.followup.send(embed=embeds[0])
        else:
            count_msg = f"**{comp_emoji} Showing {len(embeds)} {comp_name} fixtures**"
            if display_team_name:
                count_msg += f" for **{display_team_name}**"
            await interaction.followup.send(count_msg)
            for i in range(0, len(embeds), 10):
                await interaction.followup.send(embeds=embeds[i:i+10])
    
    async def _show_standings(self, interaction, competition, group):
        """Show group standings"""
        await interaction.response.defer()
        
        competition_value = None
        group_value = None
        
        if not competition or not group:
            player = await db.get_player(interaction.user.id)
            if player and player['team_id']:
                async with db.pool.acquire() as conn:
                    group_data = await conn.fetchrow("""
                        SELECT competition, group_name FROM european_groups WHERE team_id = $1
                    """, player['team_id'])
                    
                    if group_data:
                        competition_value = group_data['competition']
                        group_value = group_data['group_name']
                    else:
                        await interaction.followup.send(
                            "❌ Your team isn't in Europe! Specify:\n"
                            "`/european action:standings competition:CL group:A`",
                            ephemeral=True
                        )
                        return
            else:
                await interaction.followup.send(
                    "❌ Specify competition and group:\n"
                    "`/european action:standings competition:CL group:A`",
                    ephemeral=True
                )
                return
        else:
            competition_value = competition.value
            group_value = group.value
        
        async with db.pool.acquire() as conn:
            standings = await conn.fetch("""
                SELECT g.*, g.team_id,
                       COALESCE(t.team_name, et.team_name) as team_name,
                       (g.goals_for - g.goals_against) as goal_difference
                FROM european_groups g
                LEFT JOIN teams t ON g.team_id = t.team_id
                LEFT JOIN european_teams et ON g.team_id = et.team_id
                WHERE g.competition = $1 AND g.group_name = $2
                ORDER BY g.points DESC, goal_difference DESC, g.goals_for DESC
            """, competition_value, group_value)
        
        if not standings:
            await interaction.followup.send(f"❌ No standings found for Group {group_value}!", ephemeral=True)
            return
        
        comp_name = "Champions League" if competition_value == 'CL' else "Europa League"
        comp_emoji = "⭐" if competition_value == 'CL' else "🌟"
        comp_color = discord.Color.blue() if competition_value == 'CL' else discord.Color.gold()
        comp_logo = get_competition_logo(comp_name)
        
        embed = discord.Embed(
            title=f"{comp_emoji} {comp_name}",
            description=f"**Group {group_value} Standings**",
            color=comp_color
        )
        
        if comp_logo:
            embed.set_thumbnail(url=comp_logo)
        
        if standings:
            leader = standings[0]
            leader_crest = get_team_crest_url(leader['team_id'])
            if leader_crest:
                embed.set_author(name=f"🥇 Group Leaders: {leader['team_name']}", icon_url=leader_crest)
        
        table = "```\n"
        table += "Pos │ Team              │ Pld │  W  D  L │ GF GA GD │ Pts\n"
        table += "────┼───────────────────┼─────┼──────────┼──────────┼────\n"
        
        for idx, team in enumerate(standings, 1):
            pos_emoji = "🟢" if idx <= 2 else "🟡" if idx == 3 else "🔴"
            team_name = team['team_name'][:17].ljust(17)
            gd = team['goal_difference']
            gd_str = f"{gd:+3}"
            
            table += f" {pos_emoji}{idx} │ {team_name} │  {team['played']}  │ "
            table += f" {team['won']}  {team['drawn']}  {team['lost']} │ "
            table += f"{team['goals_for']:2} {team['goals_against']:2} {gd_str} │ {team['points']:2}\n"
        
        table += "```\n🟢 Qualified for R16  │  🟡 Europa League  │  🔴 Eliminated"
        embed.add_field(name="📊 Group Standings", value=table, inline=False)
        
        crest_display = ""
        for idx, team in enumerate(standings, 1):
            crest = get_team_crest_url(team['team_id'])
            if crest:
                medal = ["🥇", "🥈", "🥉", "4️⃣"][idx-1] if idx <= 4 else f"{idx}."
                crest_display += f"{medal} [{team['team_name']}]({crest})\n"
        
        if crest_display:
            embed.add_field(name="🏅 Teams", value=crest_display[:1024], inline=False)
        
        await interaction.followup.send(embed=embed)
    
    async def _show_match(self, interaction, home_team, away_team):
        """Show detailed match card"""
        await interaction.response.defer()
        
        if not home_team:
            player = await db.get_player(interaction.user.id)
            if player and player['team_id']:
                async with db.pool.acquire() as conn:
                    match = await conn.fetchrow("""
                        SELECT f.*, f.home_team_id, f.away_team_id,
                               COALESCE(ht.team_name, eht.team_name) as home_name,
                               COALESCE(at.team_name, eat.team_name) as away_name
                        FROM european_fixtures f
                        LEFT JOIN teams ht ON f.home_team_id = ht.team_id
                        LEFT JOIN teams at ON f.away_team_id = at.team_id
                        LEFT JOIN european_teams eht ON f.home_team_id = eht.team_id
                        LEFT JOIN european_teams eat ON f.away_team_id = eat.team_id
                        WHERE (f.home_team_id = $1 OR f.away_team_id = $1)
                          AND f.played = FALSE
                        ORDER BY f.week_number LIMIT 1
                    """, player['team_id'])
            else:
                await interaction.followup.send(
                    "❌ Specify teams:\n`/european action:match home_team:Real Madrid away_team:Barcelona`",
                    ephemeral=True
                )
                return
        else:
            async with db.pool.acquire() as conn:
                match = await conn.fetchrow("""
                    SELECT f.*, f.home_team_id, f.away_team_id,
                           COALESCE(ht.team_name, eht.team_name) as home_name,
                           COALESCE(at.team_name, eat.team_name) as away_name
                    FROM european_fixtures f
                    LEFT JOIN teams ht ON f.home_team_id = ht.team_id
                    LEFT JOIN teams at ON f.away_team_id = at.team_id
                    LEFT JOIN european_teams eht ON f.home_team_id = eht.team_id
                    LEFT JOIN european_teams eat ON f.away_team_id = eat.team_id
                    WHERE LOWER(COALESCE(ht.team_name, eht.team_name)) LIKE LOWER($1)
                      AND LOWER(COALESCE(at.team_name, eat.team_name)) LIKE LOWER($2)
                    ORDER BY f.week_number DESC LIMIT 1
                """, f"%{home_team}%", f"%{away_team}%" if away_team else "%")
        
        if not match:
            await interaction.followup.send("❌ Match not found!", ephemeral=True)
            return
        
        comp_name = "Champions League" if match['competition'] == 'CL' else "Europa League"
        comp_emoji = "⭐" if match['competition'] == 'CL' else "🌟"
        comp_color = discord.Color.blue() if match['competition'] == 'CL' else discord.Color.gold()
        
        home_crest = get_team_crest_url(match['home_team_id'])
        away_crest = get_team_crest_url(match['away_team_id'])
        comp_logo = get_competition_logo(comp_name)
        
        if match['played']:
            status_emoji = "✅"
            status_text = "Full Time"
            score = f"**{match['home_score']} - {match['away_score']}**"
            if match['home_score'] > match['away_score']:
                result_text = f"🏆 **{match['home_name']} wins!**"
            elif match['away_score'] > match['home_score']:
                result_text = f"🏆 **{match['away_name']} wins!**"
            else:
                result_text = "🤝 **Draw!**"
        elif match.get('playable'):
            status_emoji = "🟢"
            status_text = "⚡ LIVE - Play Now!"
            score = "**VS**"
            result_text = "Use `/play_match` to play!"
        else:
            status_emoji = "⏳"
            status_text = "Upcoming"
            score = "**VS**"
            result_text = f"Match scheduled for Week {match['week_number']}"
        
        if match['stage'] == 'group':
            stage_display = f"Group {match.get('group_name', '?')}"
            stage_emoji = "📊"
        else:
            leg_text = f" - Leg {match['leg']}" if match.get('leg', 1) > 1 else ""
            stage_display = f"{match['stage'].title()}{leg_text}"
            stage_emoji = "🏆"
        
        embed = discord.Embed(
            title=f"{comp_emoji} {comp_name}",
            description=f"## {match['home_name']} {score} {match['away_name']}\n\n{result_text}",
            color=comp_color
        )
        
        if comp_logo:
            embed.set_thumbnail(url=comp_logo)
        if home_crest:
            embed.set_author(name=match['home_name'], icon_url=home_crest)
        else:
            embed.set_author(name=match['home_name'])
        if away_crest:
            embed.set_footer(text=match['away_name'], icon_url=away_crest)
        else:
            embed.set_footer(text=match['away_name'])
        
        embed.add_field(name=f"{stage_emoji} Stage", value=f"**{stage_display}**", inline=True)
        embed.add_field(name="📅 Week", value=f"**{match['week_number']}**", inline=True)
        embed.add_field(name=f"{status_emoji} Status", value=f"**{status_text}**", inline=True)
        
        if match['stage'] != 'group':
            importance = "🔥 **Knockout Match!**"
        elif match.get('group_name'):
            importance = f"**Group {match['group_name']} Match**"
        else:
            importance = "**European Fixture**"
        
        embed.add_field(name="🎯 Match Type", value=importance, inline=True)
        embed.add_field(name="⏰ Kickoff", value=f"**Week {match['week_number']} window**", inline=True)
        embed.add_field(name="🏟️ Venue", value=f"**{match['home_name']} (Home)**", inline=True)
        
        await interaction.followup.send(embed=embed)
    
    async def _show_bracket(self, interaction, competition):
        """Show knockout bracket"""
        await interaction.response.defer()
        
        competition_value = None
        
        if not competition:
            player = await db.get_player(interaction.user.id)
            if player and player['team_id']:
                async with db.pool.acquire() as conn:
                    comp = await conn.fetchval("""
                        SELECT competition FROM european_groups WHERE team_id = $1 LIMIT 1
                    """, player['team_id'])
                    if comp:
                        competition_value = comp
                    else:
                        await interaction.followup.send("❌ Your team isn't in Europe!", ephemeral=True)
                        return
            else:
                await interaction.followup.send("❌ Specify: `/european action:bracket competition:CL`", ephemeral=True)
                return
        else:
            competition_value = competition.value
        
        async with db.pool.acquire() as conn:
            ties = await conn.fetch("""
                SELECT k.*, k.home_team_id, k.away_team_id, k.winner_team_id,
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
                ORDER BY CASE k.stage
                    WHEN 'r16' THEN 1
                    WHEN 'quarters' THEN 2
                    WHEN 'semis' THEN 3
                    WHEN 'final' THEN 4
                END
            """, competition_value)
        
        if not ties:
            await interaction.followup.send("⏳ Knockout stage hasn't started yet!", ephemeral=True)
            return
        
        comp_name = "Champions League" if competition_value == 'CL' else "Europa League"
        comp_emoji = "⭐" if competition_value == 'CL' else "🌟"
        comp_color = discord.Color.blue() if competition_value == 'CL' else discord.Color.gold()
        comp_logo = get_competition_logo(comp_name)
        
        embed = discord.Embed(
            title=f"{comp_emoji} {comp_name} Knockout Bracket",
            description="**Road to the Final**",
            color=comp_color
        )
        
        if comp_logo:
            embed.set_thumbnail(url=comp_logo)
        
        final_winner = next((t for t in ties if t['stage'] == 'final' and t['winner_team_id']), None)
        if final_winner:
            winner_crest = get_team_crest_url(final_winner['winner_team_id'])
            if winner_crest:
                embed.set_author(name=f"🏆 CHAMPIONS: {final_winner['winner_name']}", icon_url=winner_crest)
        
        stages = {'r16': [], 'quarters': [], 'semis': [], 'final': []}
        for tie in ties:
            stages[tie['stage']].append(tie)
        
        stage_info = {
            'r16': {'name': 'Round of 16', 'emoji': '⚡'},
            'quarters': {'name': 'Quarter-Finals', 'emoji': '🔥'},
            'semis': {'name': 'Semi-Finals', 'emoji': '💫'},
            'final': {'name': 'Final', 'emoji': '🏆'}
        }
        
        for stage_key, stage_ties in stages.items():
            if not stage_ties:
                continue
            
            info = stage_info[stage_key]
            field_value = ""
            
            for tie in stage_ties:
                if tie['winner_team_id']:
                    if tie.get('penalties_taken'):
                        field_value += f"~~{tie['home_name']}~~ vs ~~{tie['away_name']}~~\n"
                        field_value += f"👑 **{tie['winner_name']}** (Penalties)\n\n"
                    else:
                        if stage_key == 'final':
                            field_value += f"**{tie['home_name']}** {tie['first_leg_home_score']}-{tie['first_leg_away_score']} **{tie['away_name']}**\n"
                        else:
                            field_value += f"**{tie['home_name']}** vs **{tie['away_name']}**\n"
                            field_value += f"Aggregate: {tie['aggregate_home']}-{tie['aggregate_away']}\n"
                        field_value += f"👑 **Winner: {tie['winner_name']}**\n\n"
                else:
                    field_value += f"**{tie['home_name']}** vs **{tie['away_name']}**\n"
                    if tie.get('first_leg_played'):
                        field_value += f"Leg 1: {tie['first_leg_home_score']}-{tie['first_leg_away_score']}\n"
                    if tie.get('second_leg_played'):
                        field_value += f"Leg 2: {tie['second_leg_home_score']}-{tie['second_leg_away_score']}\n"
                    field_value += "⏳ To be decided\n\n"
            
            embed.add_field(name=f"{info['emoji']} {info['name']}", value=field_value or "Not started", inline=False)
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(European(bot))
