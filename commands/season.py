"""
Simplified /season command - shows fixed schedule with BOTH European and Domestic windows
✅ FIXED: Shows European window (12-2pm) AND Domestic window (3-5pm) on European weeks
✅ FIXED: Checks if players are participating in European competitions
✅ FIXED: Passes current_week to is_match_window_time function
✅ FIXED: Only shows European matches on actual European weeks
"""
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
        """View season information - SIMPLIFIED with fixed schedule"""

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
            title=f"⚽ Season {state['current_season']}",
            description=f"**Week {state['current_week']}/{config.SEASON_TOTAL_WEEKS}**",
            color=discord.Color.blue()
        )

        # ============================================
        # MATCH WINDOW STATUS - WITH EUROPEAN SUPPORT
        # ============================================
        from utils.season_manager import is_match_window_time, get_next_match_window, EST
        
        current_week = state['current_week']
        is_window_time, _, _, window_type = is_match_window_time(current_week=current_week)
        window_open = state['match_window_open']
        
        # Check if this is a European competition week
        is_european_week = current_week in config.EUROPEAN_MATCH_WEEKS
        
        # Check if any players are in European competitions this week
        has_european_players = False
        if is_european_week:
            async with db.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT COUNT(*) as count
                    FROM players p
                    JOIN european_fixtures ef ON (ef.home_team_id = p.team_id OR ef.away_team_id = p.team_id)
                    WHERE p.retired = FALSE 
                    AND p.team_id != 'free_agent'
                    AND ef.week_number = $1
                    AND ef.played = FALSE
                """, current_week)
                has_european_players = result['count'] > 0
        
        # Get current time
        now = datetime.now(EST)
        
        # Get next match window
        next_window = get_next_match_window()
        # ✅ FIXED: Check if next window is actually on a European week, not just the hour
        next_is_european = (next_window.hour == 12 and current_week in config.EUROPEAN_MATCH_WEEKS)
        
        if is_european_week:
            # EUROPEAN COMPETITION WEEK - Show both windows
            if has_european_players:
                # Players are participating - show both windows with clear separation
                
                # Show which window is currently open/next
                if window_open and window_type == 'european':
                    embed.add_field(
                        name="🟢 YOUR MATCH: OPEN NOW",
                        value=f"**Match Type:** European (Champions/Europa League)\n"
                              f"**Window:** 12:00 PM - 2:00 PM EST\n"
                              f"**Closes in:** {((14 * 60) - (now.hour * 60 + now.minute))} minutes\n\n"
                              f"🎮 Use `/play_match` NOW!",
                        inline=False
                    )
                    embed.add_field(
                        name="⏰ League Match Later",
                        value=f"Your domestic league match opens at 3:00 PM EST (in {(15 - now.hour - 1)}h {(60 - now.minute)}m)",
                        inline=False
                    )
                elif window_open and window_type == 'domestic':
                    embed.add_field(
                        name="🟢 YOUR MATCH: OPEN NOW",
                        value=f"**Match Type:** League (Domestic)\n"
                              f"**Window:** 3:00 PM - 5:00 PM EST\n"
                              f"**Closes in:** {((17 * 60) - (now.hour * 60 + now.minute))} minutes\n\n"
                              f"🎮 Use `/play_match` NOW!",
                        inline=False
                    )
                    embed.add_field(
                        name="✅ European Match Complete",
                        value=f"Your Champions/Europa League match (12-2 PM) is finished",
                        inline=False
                    )
                else:
                    # Both windows closed - show next window with full context
                    # Calculate time until
                    time_until = next_window - now
                    days = time_until.days
                    hours = time_until.seconds // 3600
                    minutes = (time_until.seconds % 3600) // 60
                    
                    if days > 0:
                        time_str = f"{days}d {hours}h"
                    elif hours > 0:
                        time_str = f"{hours}h {minutes}m"
                    else:
                        time_str = f"{minutes}m"
                    
                    day_name = next_window.strftime('%A')
                    date_str = next_window.strftime('%B %d')
                    
                    # Use the pre-calculated next_is_european flag
                    if next_is_european:
                        embed.add_field(
                            name=f"🔴 YOUR NEXT MATCH: CLOSED",
                            value=f"**Match Type:** European (Champions/Europa League)\n"
                                  f"**Day:** {day_name}, {date_str}\n"
                                  f"**Opens:** 12:00 PM EST (in {time_str})\n\n"
                                  f"⏰ Your European match comes first!\n"
                                  f"💡 League match follows at 3:00 PM",
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name=f"🔴 YOUR NEXT MATCH: CLOSED",
                            value=f"**Match Type:** League (Domestic)\n"
                                  f"**Day:** {day_name}, {date_str}\n"
                                  f"**Opens:** 3:00 PM EST (in {time_str})\n\n"
                                  f"⏰ Come back then to play!",
                            inline=False
                        )
            else:
                # European week but no user players participating
                # Show BOTH that it's European day AND what the next window is
                
                # Calculate time info
                time_until = next_window - now
                days = time_until.days
                hours = time_until.seconds // 3600
                minutes = (time_until.seconds % 3600) // 60
                
                if days > 0:
                    time_str = f"{days}d {hours}h"
                elif hours > 0:
                    time_str = f"{hours}h {minutes}m"
                else:
                    time_str = f"{minutes}m"
                
                # Calculate time until domestic window (3 PM)
                day_name = next_window.strftime('%A')
                domestic_window_time = next_window.replace(hour=15, minute=0, second=0, microsecond=0)
                
                # If next window is European (12 PM), we need to calculate to domestic (3 PM same day)
                if next_is_european:
                    time_until_domestic = domestic_window_time - now
                    days_domestic = time_until_domestic.days
                    hours_domestic = time_until_domestic.seconds // 3600
                    minutes_domestic = (time_until_domestic.seconds % 3600) // 60
                    
                    if days_domestic > 0:
                        domestic_time_str = f"{days_domestic}d {hours_domestic}h"
                    elif hours_domestic > 0:
                        domestic_time_str = f"{hours_domestic}h {minutes_domestic}m"
                    else:
                        domestic_time_str = f"{minutes_domestic}m"
                else:
                    domestic_time_str = time_str
                
                # Show domestic window status specifically
                if window_open and window_type == 'domestic':
                    embed.add_field(
                        name="🟢 YOUR MATCH: OPEN NOW",
                        value=f"**Match Type:** League (Domestic)\n"
                              f"**Window:** 3:00 PM - 5:00 PM EST\n"
                              f"**Closes in:** {((17 * 60) - (now.hour * 60 + now.minute))} minutes\n\n"
                              f"🎮 Use `/play_match` NOW!",
                        inline=False
                    )
                    embed.add_field(
                        name="ℹ️ European Matches Today",
                        value=f"Champions League & Europa League matches (12-2 PM) also today, but you're not participating.",
                        inline=False
                    )
                else:
                    # Window closed - show YOUR match info prominently
                    embed.add_field(
                        name="🔴 YOUR MATCH: CLOSED",
                        value=f"**Match Type:** League (Domestic)\n"
                              f"**Day:** {day_name}\n"
                              f"**Opens:** 3:00 PM EST (in {domestic_time_str})\n\n"
                              f"⏰ Come back then to play!",
                        inline=False
                    )
                    embed.add_field(
                        name="ℹ️ European Day",
                        value=f"Champions League & Europa League matches also on {day_name} (12-2 PM), but you're not participating.",
                        inline=False
                    )
        else:
            # NORMAL WEEK - Only domestic window (no European matches today)
            if window_open:
                # Window is currently OPEN
                embed.add_field(
                    name="🟢 YOUR MATCH: OPEN NOW",
                    value=f"**Match Type:** League (Domestic)\n"
                          f"**Window:** 3:00 PM - 5:00 PM EST\n"
                          f"**Closes in:** {((17 * 60) - (now.hour * 60 + now.minute))} minutes\n\n"
                          f"🎮 Use `/play_match` NOW!",
                    inline=False
                )
            else:
                # Window is CLOSED - show next window
                day_name = next_window.strftime('%A')
                date_str = next_window.strftime('%B %d')
                
                # Calculate time until
                time_until = next_window - now
                days = time_until.days
                hours = time_until.seconds // 3600
                minutes = (time_until.seconds % 3600) // 60
                
                if days > 0:
                    time_str = f"{days}d {hours}h"
                elif hours > 0:
                    time_str = f"{hours}h {minutes}m"
                else:
                    time_str = f"{minutes}m"
                
                # ✅ FIXED: Regular domestic window only - no European message
                embed.add_field(
                    name="🔴 YOUR MATCH: CLOSED",
                    value=f"**Match Type:** League (Domestic)\n"
                          f"**Day:** {day_name}, {date_str}\n"
                          f"**Opens:** 3:00 PM EST (in {time_str})\n\n"
                          f"⏰ Come back then to play!",
                    inline=False
                )

        # ============================================
        # TRANSFER WINDOW STATUS
        # ============================================
        if current_week in config.TRANSFER_WINDOW_WEEKS:
            # Window is ACTIVE
            window_weeks = config.TRANSFER_WINDOW_WEEKS
            if current_week in window_weeks[:3]:
                window_name = "Winter Window"
                end_week = window_weeks[2]
            else:
                window_name = "Summer Window"
                end_week = window_weeks[5]
            
            embed.add_field(
                name="🔥 TRANSFER WINDOW ACTIVE",
                value=f"**{window_name}** (Weeks {window_weeks[0 if current_week <= 17 else 3]}-{end_week})\n"
                      f"Closes: End of Week {end_week}\n\n"
                      f"💼 Use `/offers` to view club interest!",
                inline=False
            )
        else:
            # Window is CLOSED - show when it opens
            if current_week < 15:
                opens_week = 15
                window_name = "Winter Window"
            elif current_week >= 17 and current_week < 30:
                opens_week = 30
                window_name = "Summer Window"
            else:
                opens_week = "Next season (Week 15)"
                window_name = "Winter Window"
            
            embed.add_field(
                name="💼 Transfer Window Closed",
                value=f"**{window_name}** opens: Week {opens_week}\n"
                      f"Weeks remaining: {opens_week - current_week if isinstance(opens_week, int) else 'N/A'}",
                inline=False
            )

        # ============================================
        # MATCH SCHEDULE INFO
        # ============================================
        schedule_text = f"**Mon/Wed/Sat** at 3:00-5:00 PM EST\n"
        if is_european_week:
            schedule_text = f"**European:** 12:00-2:00 PM EST\n**Domestic:** 3:00-5:00 PM EST\n"
        
        embed.add_field(
            name="📅 Fixed Schedule",
            value=f"{schedule_text}"
                  f"**{config.MATCH_WINDOW_HOURS}h** window per match day\n"
                  f"**{config.MATCH_EVENTS_PER_GAME_MIN}-{config.MATCH_EVENTS_PER_GAME_MAX}** key moments per match",
            inline=True
        )

        # ============================================
        # SEASON PROGRESS
        # ============================================
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

            # Progress bar
            bar_length = 10
            filled = int((progress / 100) * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)

            embed.add_field(
                name="📊 Season Progress",
                value=f"{bar} {progress:.0f}%\n{played}/{total} matches played",
                inline=True
            )

        embed.set_footer(text="Use /league fixtures to see your schedule!")

        await interaction.response.send_message(embed=embed)

    # Keep as method for /league to call
    async def fixtures(self, interaction: discord.Interaction):
        """View player's fixtures (called by /league command)"""

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

    # Keep as method for /league to call
    async def results(self, interaction: discord.Interaction):
        """View recent results (called by /league command)"""

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
                result_emoji = "✅" if player and player['team_id'] == fixture['home_team_id'] else "❌"
            elif away_score > home_score:
                result_emoji = "✅" if player and player['team_id'] == fixture['away_team_id'] else "❌"
            else:
                result_emoji = "🟰"

            if player and player['team_id'] not in ['free_agent'] and player['team_id'] in [fixture['home_team_id'],
                                                                                            fixture['away_team_id']]:
                result_text = result_emoji
            else:
                result_emoji = "⚽"
                result_text = "⚽"

            embed.add_field(
                name=f"{result_text} Week {fixture['week_number']}",
                value=f"**{home_name}** {home_score} - {away_score} **{away_name}**",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="season_review",
                          description="View the season review with champions, awards, and your achievements")
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
            embed.add_field(name="🏆 Champions", value=champions_text, inline=False)

        # Promotion and Relegation
        if pl_table and len(pl_table) >= 3:
            relegated = [t['team_name'] for t in pl_table[-3:]]
            embed.add_field(
                name="⬇️ Relegated from Premier League",
                value="\n".join(relegated),
                inline=True
            )

        if champ_table and len(champ_table) >= 2:
            promoted = [t['team_name'] for t in champ_table[:2]]
            embed.add_field(
                name="⬆️ Promoted to Premier League",
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
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                team = scorer['team_name'] if scorer['team_name'] else 'Free Agent'
                scorers_text += f"{emoji} {scorer['player_name']} - **{scorer['season_goals']}** goals ({team})\n"

            embed.add_field(name="👟 Top Scorers", value=scorers_text, inline=False)

        # Your achievements (if user has a player)
        player = await db.get_player(interaction.user.id)
        if player:
            achievements = []

            if player['season_goals'] > 0:
                achievements.append(f"⚽ Goals: **{player['season_goals']}**")
            if player['season_assists'] > 0:
                achievements.append(f"🅰️ Assists: **{player['season_assists']}**")
            if player['season_apps'] > 0:
                achievements.append(f"👕 Appearances: **{player['season_apps']}**")
                avg_rating = f"{player['season_rating']:.1f}"
                achievements.append(f"⭐ Avg Rating: **{avg_rating}/10**")

            # Check if player's team got promoted/relegated
            if player['team_id'] != 'free_agent':
                team = await db.get_team(player['team_id'])
                if team:
                    table = await db.get_league_table(team['league'])
                    team_position = next((i + 1 for i, t in enumerate(table) if t['team_id'] == team['team_id']), None)

                    if team_position:
                        achievements.append(f"📊 Team Finish: **{team_position}** in {team['league']}")

                        if team['league'] == 'Championship' and team_position <= 2:
                            achievements.append("🎉 **PROMOTED TO PREMIER LEAGUE!**")
                        elif team['league'] == 'League One' and team_position <= 2:
                            achievements.append("🎉 **PROMOTED TO CHAMPIONSHIP!**")
                        elif team['league'] == 'Premier League' and team_position >= len(pl_table) - 2:
                            achievements.append("⬇️ **Relegated to Championship**")
                        elif team['league'] == 'Championship' and team_position >= len(champ_table) - 2:
                            achievements.append("⬇️ **Relegated to League One**")

            if achievements:
                embed.add_field(
                    name=f"📈 Your Season - {player['player_name']}",
                    value="\n".join(achievements),
                    inline=False
                )

        embed.set_footer(text="Use /start to begin a new season!")

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(SeasonCommands(bot))
