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
                title="Season Not Started",
                description="Waiting for first player to join...\n\nUse `/start` to create your player and begin the season!",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"Season {state['current_season']}",
            description=f"**Week {state['current_week']}/{config.SEASON_TOTAL_WEEKS}**",
            color=discord.Color.blue()
        )
        
        if state['match_window_open']:
            closes = datetime.fromisoformat(state['match_window_closes'])
            time_left = closes - datetime.now()
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            
            embed.add_field(
                name="Match Window: OPEN",
                value=f"Closes in **{hours}h {minutes}m**\nUse `/play_match` to play!",
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
                        name="Match Window: CLOSED",
                        value=f"Next window in **{time_str}**\nOpens: {next_match.strftime('%a, %b %d at %H:%M')}",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="Match Window",
                        value="Opening soon...",
                        inline=False
                    )
            else:
                embed.add_field(
                    name="Season Status",
                    value="Season completed!",
                    inline=False
                )
        
        embed.add_field(
            name="Match Schedule",
            value=f"**{config.MATCHES_PER_WEEK}** match days per week\n"
                  f"**{config.MATCH_WINDOW_HOURS}h** window to play each match\n"
                  f"**{config.MATCH_EVENTS_PER_GAME_MIN}-{config.MATCH_EVENTS_PER_GAME_MAX}** key moments per match",
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
                name="Season Progress",
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
                "You haven't created a player yet! Use `/start` to begin.",
                ephemeral=True
            )
            return
        
        if player['team_id'] == 'free_agent':
            await interaction.response.send_message(
                "You're a free agent! Sign with a team to see fixtures.",
                ephemeral=True
            )
            return
        
        fixtures = await db.get_player_team_fixtures(interaction.user.id, limit=10)
        
        if not fixtures:
            await interaction.response.send_message(
                "No upcoming fixtures found!",
                ephemeral=True
            )
            return
        
        team = await db.get_team(player['team_id'])
        
        embed = discord.Embed(
            title=f"{team['team_name']} Fixtures",
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
            
            venue = "Home" if is_home else "Away"
            
            status = ""
            if fixture['playable']:
                status = "**PLAYABLE NOW**"
            elif fixture['week_number'] == current_week:
                status = "This week"
            
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
                "You haven't created a player yet! Use `/start` to begin.",
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
                    "No matches played yet!",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="Recent Results",
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
                    f"No matches played yet for your team!",
                    ephemeral=True
                )
                return
            
            team = await db.get_team(player['team_id'])
            embed = discord.Embed(
                title=f"{team['team_name']} - Recent Results",
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
                result_emoji = "" if player and player['team_id'] == fixture['home_team_id'] else ""
            elif away_score > home_score:
                result_emoji = "" if player and player['team_id'] == fixture['away_team_id'] else ""
            else:
                result_emoji = ""
            
            if player and player['team_id'] not in ['free_agent'] and player['team_id'] in [fixture['home_team_id'], fixture['away_team_id']]:
                result_text = result_emoji
            else:
                result_emoji = ""
                result_text = ""
            
            embed.add_field(
                name=f"{result_text} Week {fixture['week_number']}",
                value=f"**{home_name}** {home_score} - {away_score} **{away_name}**",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="season_review", description="View the season review with champions, awards, and your achievements")
    async def season_review(self, interaction: discord.Interaction):
        """View detailed season review"""
        
        state = await db.get_game_state()
        
        if state['season_started']:
            await interaction.response.send_message(
                "The season is still in progress! Use this command after the season ends.",
                ephemeral=True
            )
            return
        
        # Get league champions (from last completed season)
        pl_table = await db.get_league_table('Premier League')
        champ_table = await db.get_league_table('Championship')
        l1_table = await db.get_league_table('League One')
        
        embed = discord.Embed(
            title=f"Season {config.CURRENT_SEASON} Review",
            description="Final standings, awards, and achievements",
            color=discord.Color.gold()
        )
        
        # Champions
        champions_text = ""
        if pl_table and pl_table[0]['points'] > 0:
            champ = pl_table[0]
            champions_text += f"**Premier League**: {champ['team_name']} ({champ['points']} pts)\n"
        if champ_table and champ_table[0]['points'] > 0:
            champ = champ_table[0]
            champions_text += f"**Championship**: {champ['team_name']} ({champ['points']} pts)\n"
        if l1_table and l1_table[0]['points'] > 0:
            champ = l1_table[0]
            champions_text += f"**League One**: {champ['team_name']} ({champ['points']} pts)\n"
        
        if champions_text:
            embed.add_field(name="Champions", value=champions_text, inline=False)
        
        # Promotion and Relegation
        if pl_table and len(pl_table) >= 3:
            relegated = [t['team_name'] for t in pl_table[-3:]]
            embed.add_field(
                name="Relegated from Premier League",
                value="\n".join(relegated),
                inline=True
            )
        
        if champ_table and len(champ_table) >= 2:
            promoted = [t['team_name'] for t in champ_table[:2]]
            embed.add_field(
                name="Promoted to Premier League",
                value="\n".join(promoted),
                inline=True
            )
        
        # Top Scorers
        async with db.pool.acquire() as conn:
            # User top scorers
            user_scorers = await conn.fetch(
                """SELECT p.player_name, p.season_goals, p.season_apps, t.team_name, p.league
                   FROM players p
                   LEFT JOIN teams t ON p.team_id = t.team_id
                   WHERE p.season_goals > 0
                   ORDER BY p.season_goals DESC
                   LIMIT 5"""
            )
            
            # NPC top scorers
            npc_scorers = await conn.fetch(
                """SELECT n.player_name, n.season_goals, n.season_apps, t.team_name, t.league
                   FROM npc_players n
                   LEFT JOIN teams t ON n.team_id = t.team_id
                   WHERE n.season_goals > 0
                   ORDER BY n.season_goals DESC
                   LIMIT 5"""
            )
        
        all_scorers = list(user_scorers) + list(npc_scorers)
        all_scorers.sort(key=lambda x: x['season_goals'], reverse=True)
        
        if all_scorers:
            top_5 = all_scorers[:5]
            scorers_text = ""
            for i, scorer in enumerate(top_5, 1):
                emoji = "1." if i == 1 else "2." if i == 2 else "3." if i == 3 else f"{i}."
                team = scorer['team_name'] if scorer['team_name'] else 'Free Agent'
                scorers_text += f"{emoji} {scorer['player_name']} - **{scorer['season_goals']}** goals ({team})\n"
            
            embed.add_field(name="Top Scorers", value=scorers_text, inline=False)
        
        # Your achievements (if user has a player)
        player = await db.get_player(interaction.user.id)
        if player:
            achievements = []
            
            if player['season_goals'] > 0:
                achievements.append(f"Goals: **{player['season_goals']}**")
            if player['season_assists'] > 0:
                achievements.append(f"Assists: **{player['season_assists']}**")
            if player['season_apps'] > 0:
                achievements.append(f"Appearances: **{player['season_apps']}**")
                avg_rating = f"{player['season_rating']:.1f}"
                achievements.append(f"Avg Rating: **{avg_rating}/10**")
            
            # Check if player's team got promoted/relegated
            if player['team_id'] != 'free_agent':
                team = await db.get_team(player['team_id'])
                if team:
                    table = await db.get_league_table(team['league'])
                    team_position = next((i+1 for i, t in enumerate(table) if t['team_id'] == team['team_id']), None)
                    
                    if team_position:
                        achievements.append(f"Team Finish: **{team_position}** in {team['league']}")
                        
                        if team['league'] == 'Championship' and team_position <= 2:
                            achievements.append("**PROMOTED TO PREMIER LEAGUE!**")
                        elif team['league'] == 'League One' and team_position <= 2:
                            achievements.append("**PROMOTED TO CHAMPIONSHIP!**")
                        elif team['league'] == 'Premier League' and team_position >= len(pl_table) - 2:
                            achievements.append("**Relegated to Championship**")
                        elif team['league'] == 'Championship' and team_position >= len(champ_table) - 2:
                            achievements.append("**Relegated to League One**")
            
            if achievements:
                embed.add_field(
                    name=f"Your Season - {player['player_name']}",
                    value="\n".join(achievements),
                    inline=False
                )
        
        embed.set_footer(text="Use /start to begin a new season!")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(SeasonCommands(bot))
