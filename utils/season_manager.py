"""
Season Manager - With Auto-Posting Weekly News Digest
"""
import discord
from database import db
from datetime import datetime, timedelta
import pytz
import config

EST = pytz.timezone('America/New_York')

MATCH_DAYS = [0, 2, 5]  # Monday=0, Wednesday=2, Saturday=5
MATCH_START_HOUR = 15  # 3 PM
MATCH_END_HOUR = 17  # 5 PM


def is_match_window_time():
    """Simple check: Is it Mon/Wed/Sat between 3-5 PM EST?"""
    now = datetime.now(EST)
    is_match_day = now.weekday() in MATCH_DAYS
    is_match_hours = MATCH_START_HOUR <= now.hour < MATCH_END_HOUR
    is_start = (now.hour == MATCH_START_HOUR and now.minute < 5)
    is_end = (now.hour == MATCH_END_HOUR and now.minute < 5)
    return (is_match_day and is_match_hours), is_start, is_end


def get_next_match_window():
    """Get next match window time"""
    now = datetime.now(EST)
    current_day = now.weekday()
    days_ahead = None

    for match_day in MATCH_DAYS:
        days_until = (match_day - current_day) % 7
        if days_until == 0 and now.hour < MATCH_START_HOUR:
            days_ahead = 0
            break
        elif days_until > 0:
            if days_ahead is None or days_until < days_ahead:
                days_ahead = days_until

    if days_ahead is None:
        days_ahead = (MATCH_DAYS[0] - current_day) % 7
        if days_ahead == 0:
            days_ahead = 7

    next_match = now + timedelta(days=days_ahead)
    next_match = next_match.replace(hour=MATCH_START_HOUR, minute=0, second=0, microsecond=0)
    return next_match


def should_send_warning(warning_type):
    """Check if we should send a warning right now"""
    now = datetime.now(EST)
    if now.weekday() not in MATCH_DAYS:
        return False

    if warning_type == 'pre_1h':
        return now.hour == 14 and now.minute < 5
    elif warning_type == 'pre_30m':
        return now.hour == 14 and 30 <= now.minute < 35
    elif warning_type == 'pre_15m':
        return now.hour == 14 and 45 <= now.minute < 50
    elif warning_type == 'closing_soon':
        return now.hour == 16 and 45 <= now.minute < 50
    return False


async def start_season():
    """Start the season"""
    state = await db.get_game_state()

    if state['season_started']:
        print("⚠️ Season already started")
        return False

    await db.update_game_state(
        season_started=True,
        current_week=1,
        current_season='2027/28',
        season_start_date=datetime.now(EST).isoformat()
    )

    await generate_season_fixtures()

    next_window = get_next_match_window()
    print(f"✅ Season started! Next match window: {next_window.strftime('%A, %B %d at %I:%M %p EST')}")
    return True


async def generate_season_fixtures():
    """Generate fixtures for all leagues"""
    from utils.fixture_generator import generate_all_fixtures
    await generate_all_fixtures()
    print(f"✅ Generated {config.SEASON_TOTAL_WEEKS} weeks of fixtures")


async def open_match_window():
    """Open the match window - with race condition protection"""

    # Use bot's lock if available
    from bot import bot
    if hasattr(bot, 'match_window_lock'):
        async with bot.match_window_lock:
            return await _open_match_window_internal()
    else:
        return await _open_match_window_internal()


async def _open_match_window_internal():
    """Internal implementation"""
    state = await db.get_game_state()

    # Double-check window not already open
    if state['match_window_open']:
        print("⚠️ Match window already open, skipping")
        return False

    current_week = state['current_week']

    async with db.pool.acquire() as conn:
        # Atomic update with WHERE clause
        result = await conn.execute(
            """UPDATE game_state
               SET match_window_open = TRUE
               WHERE id = 1
                 AND match_window_open = FALSE RETURNING id""",
        )

        if result == "UPDATE 0":
            print("⚠️ Another process already opened the window")
            return False

        await conn.execute(
            "UPDATE fixtures SET playable = TRUE WHERE week_number = $1 AND played = FALSE",
            current_week
        )

    print(f"✅ Match window OPENED for Week {current_week}")
    return True


async def close_match_window(bot=None):
    """Close match window and simulate unplayed matches"""
    state = await db.get_game_state()
    current_week = state['current_week']

    async with db.pool.acquire() as conn:
        unplayed = await conn.fetch(
            """SELECT *
               FROM fixtures
               WHERE week_number = $1
                 AND played = FALSE
                 AND playable = TRUE""",
            current_week
        )

    from utils.match_simulator import simulate_match

    simulated_count = 0
    for fixture in unplayed:
        await simulate_match(dict(fixture))
        simulated_count += 1

    if simulated_count > 0:
        print(f"⚽ Simulated {simulated_count} unplayed matches")

    async with db.pool.acquire() as conn:
        results = await conn.fetch("""
                                   SELECT f.*,
                                          t1.team_name as home_team_name,
                                          t2.team_name as away_team_name
                                   FROM fixtures f
                                            JOIN teams t1 ON f.home_team_id = t1.team_id
                                            JOIN teams t2 ON f.away_team_id = t2.team_id
                                   WHERE f.week_number = $1
                                     AND f.played = TRUE
                                   ORDER BY f.fixture_id DESC LIMIT 10
                                   """, current_week)
    week_results = [dict(r) for r in results]

    if bot:
        await bot.notify_match_window_closed(week_results)

    await db.update_game_state(match_window_open=False)

    print(f"✅ Match window CLOSED for Week {current_week}")
    print(f"   Time: {datetime.now(EST).strftime('%A %I:%M %p EST')}")

    await advance_week(bot=bot)


async def check_contract_morale(bot=None):
    """Apply morale penalty AND send warnings for expiring contracts"""
    from utils.form_morale_system import update_player_morale

    async with db.pool.acquire() as conn:
        expiring_players = await conn.fetch("""
                                            SELECT user_id, player_name, contract_years, contract_wage, team_id
                                            FROM players
                                            WHERE retired = FALSE
                                              AND contract_years <= 1
                                              AND team_id != 'free_agent'
                                            """)

    affected = 0
    warned = 0

    for player in expiring_players:
        # Apply morale penalty
        await update_player_morale(player['user_id'], 'contract_expiring')
        affected += 1

        # ✅ NEW: SEND WARNING DM
        if player['contract_years'] == 1 and bot:
            try:
                user = await bot.fetch_user(player['user_id'])

                embed = discord.Embed(
                    title="⚠️ CONTRACT EXPIRING SOON!",
                    description=f"**{player['player_name']}**\nYour contract expires in **1 year**!",
                    color=discord.Color.orange()
                )

                # Get team name
                team = await db.get_team(player['team_id'])
                team_name = team['team_name'] if team else player['team_id']

                embed.add_field(
                    name="💼 Current Contract",
                    value=f"**{team_name}**\n£{player['contract_wage']:,}/week\n1 year remaining",
                    inline=True
                )

                embed.add_field(
                    name="📋 Next Steps",
                    value="• Wait for renewal offer during transfer windows\n"
                          "• Or explore other clubs\n"
                          "• Transfer windows: Weeks 15-17, 30-32",
                    inline=False
                )

                embed.add_field(
                    name="⚠️ Warning",
                    value="Expiring contracts reduce morale!\nSecure your future soon.",
                    inline=False
                )

                await user.send(embed=embed)
                warned += 1
                print(f"  ✉️ Warned {player['player_name']} about expiring contract")
            except Exception as e:
                print(f"  ⚠️ Could not warn user {player['user_id']}: {e}")

    if affected > 0:
        print(f"  😰 {affected} players affected by contract uncertainty")
        print(f"  ✉️ Sent {warned} contract warnings")


async def advance_week(bot=None):
    """Advance to next week with auto-posting news"""
    state = await db.get_game_state()
    current_week = state['current_week']
    next_week = current_week + 1

    if next_week > config.SEASON_TOTAL_WEEKS:
        await end_season(bot=bot)
        return

    await db.update_game_state(current_week=next_week)

    await check_contract_morale(bot=bot)

    # ============================================
    # 🆕 AUTO-POST WEEKLY NEWS DIGEST
    # ============================================
    if bot:
        from utils.event_poster import post_weekly_news_digest
        try:
            await post_weekly_news_digest(bot, current_week)
            print(f"📰 Posted weekly news digest for Week {current_week}")
        except Exception as e:
            print(f"⚠️ Could not post news digest: {e}")

    # ============================================
    # TRANSFER WINDOW MANAGEMENT
    # ============================================
    FIRST_WEEK_OF_WINDOWS = [15, 30]

    if next_week in FIRST_WEEK_OF_WINDOWS:
        await open_transfer_window()

        from utils.transfer_window_manager import process_weekly_transfer_offers
        try:
            offers_generated = await process_weekly_transfer_offers(bot=bot)
            print(f"💼 Week {next_week}: Generated {offers_generated} initial transfer offers (WINDOW OPENS)")
        except Exception as e:
            print(f"⚠️ Could not generate transfer offers: {e}")
            import traceback
            traceback.print_exc()

    elif current_week in config.TRANSFER_WINDOW_WEEKS and next_week not in config.TRANSFER_WINDOW_WEEKS:
        await close_transfer_window()

    elif next_week in config.TRANSFER_WINDOW_WEEKS and next_week not in FIRST_WEEK_OF_WINDOWS:
        from utils.transfer_window_manager import generate_offers_for_eligible_players
        try:
            offers_generated = await generate_offers_for_eligible_players(bot=bot)
            if offers_generated > 0:
                print(f"💼 Week {next_week}: Generated {offers_generated} offers for eligible players (ONGOING WINDOW)")
            else:
                print(f"💼 Week {next_week}: No eligible players for new offers (ONGOING WINDOW)")
        except Exception as e:
            print(f"⚠️ Could not generate eligible player offers: {e}")

    print(f"📅 Advanced to Week {next_week}")
    next_window = get_next_match_window()
    print(f"   Next match: {next_window.strftime('%A, %B %d at %I:%M %p EST')}")


async def open_transfer_window():
    """Open transfer window"""
    await db.update_game_state(transfer_window_active=True)
    print("💼 Transfer window OPENED")


async def close_transfer_window():
    """Close transfer window"""
    from utils.transfer_window_manager import simulate_npc_transfers
    try:
        npc_transfers = await simulate_npc_transfers()
        print(f"💼 {npc_transfers} NPC transfers completed")
    except Exception as e:
        print(f"⚠️ Could not simulate NPC transfers: {e}")
        import traceback
        traceback.print_exc()

    await db.update_game_state(transfer_window_active=False)

    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE transfer_offers SET status = 'expired' WHERE status = 'pending'"
        )

    print("💼 Transfer window CLOSED")


async def end_season(bot=None):
    """End the season with awards ceremony"""
    state = await db.get_game_state()
    current_season = state['current_season']

    print(f"🏆 Season {current_season} complete!")

    # ============================================
    # ✅ NEW: CALCULATE SEASON AWARDS
    # ============================================
    awards = {}

    async with db.pool.acquire() as conn:
        # Golden Boot (Top Scorer)
        golden_boot = await conn.fetchrow("""
                                          SELECT p.player_name, p.season_goals, p.user_id, t.team_name
                                          FROM players p
                                                   LEFT JOIN teams t ON p.team_id = t.team_id
                                          WHERE p.retired = FALSE
                                          ORDER BY p.season_goals DESC LIMIT 1
                                          """)
        if golden_boot and golden_boot['season_goals'] > 0:
            awards['golden_boot'] = dict(golden_boot)

        # Most Assists
        most_assists = await conn.fetchrow("""
                                           SELECT p.player_name, p.season_assists, p.user_id, t.team_name
                                           FROM players p
                                                    LEFT JOIN teams t ON p.team_id = t.team_id
                                           WHERE p.retired = FALSE
                                           ORDER BY p.season_assists DESC LIMIT 1
                                           """)
        if most_assists and most_assists['season_assists'] > 0:
            awards['most_assists'] = dict(most_assists)

        # Player of the Year (Highest Average Rating)
        poty = await conn.fetchrow("""
                                   SELECT p.player_name, p.season_rating, p.season_apps, p.user_id, t.team_name
                                   FROM players p
                                            LEFT JOIN teams t ON p.team_id = t.team_id
                                   WHERE p.retired = FALSE
                                     AND p.season_apps >= 10
                                   ORDER BY p.season_rating DESC LIMIT 1
                                   """)
        if poty and poty['season_rating'] > 0:
            awards['poty'] = dict(poty)

        # Most MOTM Awards
        most_motm = await conn.fetchrow("""
                                        SELECT p.player_name, p.season_motm, p.user_id, t.team_name
                                        FROM players p
                                                 LEFT JOIN teams t ON p.team_id = t.team_id
                                        WHERE p.retired = FALSE
                                        ORDER BY p.season_motm DESC LIMIT 1
                                        """)
        if most_motm and most_motm['season_motm'] > 0:
            awards['most_motm'] = dict(most_motm)

        # Young Player of the Year (Under 23)
        ypoty = await conn.fetchrow("""
                                    SELECT p.player_name, p.overall_rating, p.age, p.user_id, t.team_name
                                    FROM players p
                                             LEFT JOIN teams t ON p.team_id = t.team_id
                                    WHERE p.retired = FALSE
                                      AND p.age < 23
                                      AND p.season_apps >= 5
                                    ORDER BY p.overall_rating DESC, p.season_rating DESC LIMIT 1
                                    """)
        if ypoty:
            awards['ypoty'] = dict(ypoty)

    # ✅ POST AWARDS TO ALL SERVERS
    if bot:
        for guild in bot.guilds:
            try:
                news_channel = discord.utils.get(guild.text_channels, name="news-feed")
                if not news_channel:
                    news_channel = discord.utils.get(guild.text_channels, name="general")

                if news_channel:
                    embed = discord.Embed(
                        title=f"🏆 Season {current_season} AWARDS",
                        description="Celebrating the best performers of the season!",
                        color=discord.Color.gold()
                    )

                    if 'golden_boot' in awards:
                        a = awards['golden_boot']
                        embed.add_field(
                            name="👟 GOLDEN BOOT",
                            value=f"**{a['player_name']}** ({a['team_name']})\n{a['season_goals']} goals",
                            inline=False
                        )

                    if 'most_assists' in awards:
                        a = awards['most_assists']
                        embed.add_field(
                            name="🅰️ MOST ASSISTS",
                            value=f"**{a['player_name']}** ({a['team_name']})\n{a['season_assists']} assists",
                            inline=False
                        )

                    if 'poty' in awards:
                        a = awards['poty']
                        embed.add_field(
                            name="⭐ PLAYER OF THE YEAR",
                            value=f"**{a['player_name']}** ({a['team_name']})\n{a['season_rating']:.2f} avg rating ({a['season_apps']} apps)",
                            inline=False
                        )

                    if 'most_motm' in awards:
                        a = awards['most_motm']
                        embed.add_field(
                            name="🌟 MOST MOTM AWARDS",
                            value=f"**{a['player_name']}** ({a['team_name']})\n{a['season_motm']} MOTM awards",
                            inline=False
                        )

                    if 'ypoty' in awards:
                        a = awards['ypoty']
                        embed.add_field(
                            name="🎯 YOUNG PLAYER OF THE YEAR",
                            value=f"**{a['player_name']}** ({a['team_name']})\nAge {a['age']} • {a['overall_rating']} OVR",
                            inline=False
                        )

                    embed.set_footer(text=f"Season {current_season} Complete • Next season starts soon!")

                    await news_channel.send(embed=embed)
                    print(f"  🏆 Posted awards to {guild.name}")
            except Exception as e:
                print(f"  ⚠️ Could not post awards to {guild.name}: {e}")

        # ✅ SEND DMs TO AWARD WINNERS
        for award_name, award_data in awards.items():
            if 'user_id' in award_data:
                try:
                    user = await bot.fetch_user(award_data['user_id'])

                    award_titles = {
                        'golden_boot': '👟 GOLDEN BOOT',
                        'most_assists': '🅰️ MOST ASSISTS',
                        'poty': '⭐ PLAYER OF THE YEAR',
                        'most_motm': '🌟 MOST MOTM AWARDS',
                        'ypoty': '🎯 YOUNG PLAYER OF THE YEAR'
                    }

                    embed = discord.Embed(
                        title=f"🏆 CONGRATULATIONS!",
                        description=f"You won: **{award_titles.get(award_name, award_name.replace('_', ' ').title())}**!",
                        color=discord.Color.gold()
                    )
                    embed.add_field(
                        name="🎉 Amazing Achievement",
                        value=f"You were the best in the league this season!",
                        inline=False
                    )
                    await user.send(embed=embed)
                    print(f"  🏆 Sent award DM to {award_data['player_name']}")
                except Exception as e:
                    print(f"  ⚠️ Could not send award DM: {e}")

    # ============================================
    # END OF AWARDS - Continue with existing code
    # ============================================

    await db.age_all_players()
    retired_count = await db.retire_old_players()
    print(f"👴 {retired_count} players retired")

    async with db.pool.acquire() as conn:
        await conn.execute("""
                           UPDATE players
                           SET season_goals   = 0,
                               season_assists = 0,
                               season_apps    = 0,
                               season_rating  = 0.0,
                               season_motm    = 0,
                               form           = 50,
                               morale         = 75
                           """)

        await conn.execute("""
                           UPDATE npc_players
                           SET season_goals   = 0,
                               season_assists = 0,
                               season_apps    = 0
                           """)

        await conn.execute("""
                           UPDATE teams
                           SET played        = 0,
                               won           = 0,
                               drawn         = 0,
                               lost          = 0,
                               goals_for     = 0,
                               goals_against = 0,
                               points        = 0,
                               form          = ''
                           """)

    print(f"✅ All players reset - fresh start for next season!")

    year = int(current_season.split('/')[0])
    new_season = f"{year + 1}/{str(year + 2)[-2:]}"

    await db.update_game_state(
        current_season=new_season,
        current_week=0,
        fixtures_generated=False,
        season_started=False
    )

    print(f"✅ Ready for Season {new_season}")


# ============================================
# WARNING FUNCTIONS
# ============================================

async def send_1h_warning(bot):
    """Send 1 hour warning"""
    state = await db.get_game_state()
    if state['match_window_open']:
        return

    for guild in bot.guilds:
        try:
            channel = discord.utils.get(guild.text_channels, name="match-results")
            if not channel:
                channel = discord.utils.get(guild.text_channels, name="general")

            if channel:
                embed = discord.Embed(
                    title="⏰ Match Window Opening in 1 Hour!",
                    description=f"**Week {state['current_week']}** matches start at **3:00 PM EST**!",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="🕒 Opens At",
                    value="**3:00 PM EST** (in 1 hour)",
                    inline=False
                )
                embed.add_field(
                    name="⚡ Get Ready",
                    value="Use `/play_match` when the window opens!",
                    inline=False
                )
                await channel.send(embed=embed)
                print(f"✅ Sent 1h warning to {guild.name}")
        except Exception as e:
            print(f"⚠️ Could not send 1h warning to {guild.name}: {e}")


async def send_30m_warning(bot):
    """Send 30 minute warning via DM"""
    state = await db.get_game_state()
    if state['match_window_open']:
        return

    async with db.pool.acquire() as conn:
        players = await conn.fetch("""
                                   SELECT user_id, player_name
                                   FROM players
                                   WHERE retired = FALSE
                                     AND team_id != 'free_agent'
                                   """)

    for player in players:
        try:
            user = await bot.fetch_user(player['user_id'])
            embed = discord.Embed(
                title="⏰ Match Starting in 30 Minutes!",
                description=f"**Week {state['current_week']}** match window opens at **3:00 PM EST**!",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="🕒 Opens At",
                value="**3:00 PM EST** (in 30 minutes)",
                inline=False
            )
            await user.send(embed=embed)
        except:
            pass

    print(f"✅ Sent 30min warnings to {len(players)} players")


async def send_15m_warning(bot):
    """Send 15 minute warning"""
    state = await db.get_game_state()
    if state['match_window_open']:
        return

    for guild in bot.guilds:
        try:
            channel = discord.utils.get(guild.text_channels, name="match-results")
            if not channel:
                channel = discord.utils.get(guild.text_channels, name="general")

            if channel:
                embed = discord.Embed(
                    title="🚨 Match Window Opening VERY Soon!",
                    description=f"**Week {state['current_week']}** matches start in **15 minutes**!",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="🕒 Opens At",
                    value="**3:00 PM EST** (in 15 minutes)",
                    inline=False
                )
                await channel.send(embed=embed)
                print(f"✅ Sent 15min warning to {guild.name}")
        except Exception as e:
            print(f"⚠️ Could not send 15min warning to {guild.name}: {e}")


async def send_closing_warning(bot):
    """Send warning that window is closing soon"""
    state = await db.get_game_state()
    current_week = state['current_week']

    if not state['match_window_open']:
        return

    async with db.pool.acquire() as conn:
        all_players = await conn.fetch("""
                                       SELECT user_id, player_name
                                       FROM players
                                       WHERE retired = FALSE
                                         AND team_id != 'free_agent'
                                       """)

        played_players = await conn.fetch("""
                                          SELECT DISTINCT user_id
                                          FROM match_participants mp
                                                   JOIN active_matches am ON mp.match_id = am.match_id
                                                   JOIN fixtures f ON am.fixture_id = f.fixture_id
                                          WHERE f.week_number = $1
                                          """, current_week)

        played_ids = {p['user_id'] for p in played_players}

    warned = 0
    for player in all_players:
        if player['user_id'] not in played_ids:
            try:
                user = await bot.fetch_user(player['user_id'])
                embed = discord.Embed(
                    title="⚠️ Match Window Closing in 15 Minutes!",
                    description=f"**You haven't played your Week {current_week} match!**",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="⏰ Closes At",
                    value="**5:00 PM EST** (in 15 minutes)",
                    inline=False
                )
                embed.add_field(
                    name="🚨 URGENT",
                    value="Use `/play_match` **NOW** or your match will be auto-simulated!",
                    inline=False
                )
                await user.send(embed=embed)
                warned += 1
            except:
                pass

    if warned > 0:
        print(f"⚠️ Sent closing warnings to {warned} players")
