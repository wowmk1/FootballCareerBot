from database import db
from datetime import datetime, timedelta
import config
from utils.event_poster import post_weekly_news_digest
from utils.transfer_window_manager import (
    check_and_update_transfer_window,
    process_weekly_transfer_offers,
    simulate_npc_transfers,
    is_transfer_window_open
)


async def start_season():
    """Initialize and start the season with SCHEDULED match windows"""
    from utils.fixture_generator import generate_all_fixtures

    await db.update_game_state(
        season_started=True,
        current_week=1,
        season_start_date=datetime.now().isoformat(),
        fixtures_generated=False
    )

    await generate_all_fixtures()

    # Schedule first match window at a predictable time
    now = datetime.now()
    next_match = now.replace(hour=config.MATCH_START_HOUR, minute=0, second=0, microsecond=0)

    # If today's start hour has passed, schedule for tomorrow
    if now.hour >= config.MATCH_START_HOUR:
        next_match = next_match + timedelta(days=1)

    await db.update_game_state(
        next_match_day=next_match.isoformat()
    )

    print(f"✅ Season {config.CURRENT_SEASON} started!")
    print(f"📅 First match window: {next_match.strftime('%A, %B %d at %I:%M %p')}")
    print(f"⏰ Players have time to join before matches start!")


async def advance_week():
    """Advance to the next week - 1 REAL DAY = 1 GAME WEEK"""
    state = await db.get_game_state()

    if not state['season_started']:
        print("⚠️ Season hasn't started yet")
        return

    current_week = state['current_week']

    if current_week >= config.SEASON_TOTAL_WEEKS:
        await end_season()
        return

    new_week = current_week + 1

    print(f"\n{'=' * 60}")
    print(f"ADVANCING TO WEEK {new_week}")
    print(f"{'=' * 60}")

    # ============================================
    # SCHEDULE NEXT MATCH DAY (Mon/Wed/Sat pattern)
    # ============================================
    now = datetime.now()
    current_day = now.weekday()  # 0=Monday, 2=Wednesday, 5=Saturday

    # Determine next match day
    if current_day < 2:  # Before Wednesday
        # Next match is Wednesday
        days_until_next = 2 - current_day
    elif current_day < 5:  # Before Saturday
        # Next match is Saturday
        days_until_next = 5 - current_day
    else:  # Saturday or Sunday
        # Next match is Monday
        days_until_next = (7 - current_day) % 7
        if days_until_next == 0:
            days_until_next = 2  # If Monday, go to Wednesday

    next_match = now + timedelta(days=days_until_next)
    next_match = next_match.replace(hour=config.MATCH_START_HOUR, minute=0, second=0, microsecond=0)

    print(f"📅 Week {new_week} scheduled for:")
    print(f"   {next_match.strftime('%A, %B %d at %I:%M %p')}")

    await db.update_game_state(
        current_week=new_week,
        next_match_day=next_match.isoformat()
    )
    # ============================================

    # CHECK AND UPDATE TRANSFER WINDOW
    await check_and_update_transfer_window()
    window_active = await is_transfer_window_open(new_week)

    # GENERATE TRANSFER OFFERS IF WINDOW IS OPEN
    if window_active:
        print(f"\n🔥 Transfer Window is OPEN for Week {new_week}")
        try:
            from bot import bot
            offers_count = await process_weekly_transfer_offers(bot)
            print(f"✅ Generated {offers_count} transfer offers")
        except Exception as e:
            print(f"❌ Error generating offers: {e}")

        # SIMULATE NPC TRANSFERS
        try:
            npc_count = await simulate_npc_transfers()
            print(f"✅ Simulated {npc_count} NPC transfers")
        except Exception as e:
            print(f"❌ Error simulating NPC transfers: {e}")
    else:
        print(f"❌ Transfer window is CLOSED for Week {new_week}")

    print(f"\n✅ Advanced to Week {new_week}/{config.SEASON_TOTAL_WEEKS}")
    print(f"{'=' * 60}\n")


async def open_match_window(bot=None):
    """Open match window for current week - ALL FIXTURES PLAYABLE"""
    state = await db.get_game_state()

    if not state['season_started']:
        return

    current_week = state['current_week']

    # Make ALL fixtures for this week playable
    async with db.pool.acquire() as conn:
        await conn.execute('''
            UPDATE fixtures
            SET playable = TRUE
            WHERE week_number = $1
              AND played = FALSE
        ''', current_week)

        # Count how many fixtures are now playable
        result = await conn.fetchrow('''
            SELECT COUNT(*) as count 
            FROM fixtures 
            WHERE week_number = $1 AND playable = TRUE AND played = FALSE
        ''', current_week)
        playable_count = result['count']

    window_closes = datetime.now() + timedelta(hours=config.MATCH_WINDOW_HOURS)

    await db.update_game_state(
        match_window_open=True,
        match_window_closes=window_closes.isoformat()
    )

    print(f"✅ Match window opened for Week {current_week}")
    print(f"⚽ {playable_count} fixtures available to play")
    print(f"⏰ Window closes at {window_closes.strftime('%Y-%m-%d %H:%M')}")

    # POST WEEKLY NEWS TO CHANNELS
    if bot:
        try:
            for guild in bot.guilds:
                await post_weekly_news_digest(bot, guild)
            print(f"✅ Posted weekly news to all servers")
        except Exception as e:
            print(f"⚠️ Could not post weekly news: {e}")

    # NOTIFY MATCH WINDOW OPEN
    if bot:
        await bot.notify_match_window_open()


async def close_match_window():
    """Close match window and auto-simulate unplayed matches"""
    from utils.match_simulator import simulate_match

    state = await db.get_game_state()
    current_week = state['current_week']

    # Auto-simulate ALL unplayed matches
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM fixtures WHERE week_number = $1 AND played = FALSE AND playable = TRUE",
            current_week
        )
        unplayed = [dict(row) for row in rows]

    if unplayed:
    print(f"🤖 Auto-simulating {len(unplayed)} unplayed matches for Week {current_week}...")
    for fixture in unplayed:
        await simulate_match(fixture)
    print(f"✅ Week {current_week} simulation complete!")
    else:
    print(f"✅ Week {current_week}: All matches were played by users!")

    # Mark all fixtures as unplayable since week is over
    async with db.pool.acquire() as conn:
        await conn.execute('''
            UPDATE fixtures
            SET playable = FALSE
            WHERE week_number = $1
        ''', current_week)

    await db.update_game_state(
        match_window_open=False,
        match_window_closes=None,
        last_match_day=datetime.now().isoformat()
    )

    print(f"✅ Match window closed for Week {current_week}")


async def check_match_day_trigger(bot=None):
    """Check if it's time to open/close match window"""
    state = await db.get_game_state()

    if not state['season_started']:
        return False

    # PRIORITY 1: Check if match window should close
    if state['match_window_open']:
        if state['match_window_closes']:
            closes = datetime.fromisoformat(state['match_window_closes'])
            if datetime.now() >= closes:
                await close_match_window()

                # After closing, immediately advance to next week
                print(f"🏁 Week {state['current_week']} complete! Advancing...")
                await advance_week()

                return True
        return False

    # PRIORITY 2: Check if it's time to open next match window
    if state['next_match_day']:
        next_match = datetime.fromisoformat(state['next_match_day'])
        if datetime.now() >= next_match:
            await open_match_window(bot)
            return True

    return False


async def end_season():
    """End the current season with relegation and promotion"""

    print("\n🏁 SEASON ENDING...")

    await db.age_all_players()
    retirements = await db.retire_old_players()

    # Balance squads after retirements
    from utils.npc_transfer_system import balance_team_squads
    await balance_team_squads()

    print("⚖️ Processing relegation and promotion...")

    pl_table = await db.get_league_table('Premier League')
    champ_table = await db.get_league_table('Championship')
    l1_table = await db.get_league_table('League One')

    relegated_from_pl = pl_table[-3:] if len(pl_table) >= 3 else []
    promoted_to_pl = champ_table[:2] if len(champ_table) >= 2 else []
    relegated_from_champ = champ_table[-3:] if len(champ_table) >= 3 else []
    promoted_to_champ = l1_table[:2] if len(l1_table) >= 2 else []

    async with db.pool.acquire() as conn:
        for team in relegated_from_pl:
            await conn.execute(
                "UPDATE teams SET league = 'Championship' WHERE team_id = $1",
                team['team_id']
            )
            await conn.execute(
                "UPDATE players SET league = 'Championship' WHERE team_id = $1 AND retired = FALSE",
                team['team_id']
            )

            await db.add_news(
                f"RELEGATION: {team['team_name']} Relegated",
                f"{team['team_name']} have been relegated to the Championship.",
                "league_news",
                None,
                10
            )
            print(f"  ⬇️ {team['team_name']} relegated to Championship")

        for team in promoted_to_pl:
            await conn.execute(
                "UPDATE teams SET league = 'Premier League' WHERE team_id = $1",
                team['team_id']
            )
            await conn.execute(
                "UPDATE players SET league = 'Premier League' WHERE team_id = $1 AND retired = FALSE",
                team['team_id']
            )

            await db.add_news(
                f"PROMOTION: {team['team_name']} Promoted!",
                f"Congratulations to {team['team_name']} on winning promotion to the Premier League!",
                "league_news",
                None,
                10
            )
            print(f"  ⬆️ {team['team_name']} promoted to Premier League")

        # Similar for Championship <-> League One
        for team in relegated_from_champ:
            await conn.execute(
                "UPDATE teams SET league = 'League One' WHERE team_id = $1",
                team['team_id']
            )
            await conn.execute(
                "UPDATE players SET league = 'League One' WHERE team_id = $1 AND retired = FALSE",
                team['team_id']
            )

            await db.add_news(
                f"{team['team_name']} Relegated to League One",
                f"{team['team_name']} drop down to League One.",
                "league_news",
                None,
                7
            )
            print(f"  ⬇️ {team['team_name']} relegated to League One")

        for team in promoted_to_champ:
            await conn.execute(
                "UPDATE teams SET league = 'Championship' WHERE team_id = $1",
                team['team_id']
            )
            await conn.execute(
                "UPDATE players SET league = 'Championship' WHERE team_id = $1 AND retired = FALSE",
                team['team_id']
            )

            await db.add_news(
                f"{team['team_name']} Promoted to Championship!",
                f"{team['team_name']} celebrate promotion!",
                "league_news",
                None,
                8
            )
            print(f"  ⬆️ {team['team_name']} promoted to Championship")

    # Announce champions
    if pl_table:
        champion = pl_table[0]
        await db.add_news(
            f"CHAMPIONS: {champion['team_name']} Win Premier League!",
            f"{champion['team_name']} are Premier League champions with {champion['points']} points!",
            "league_news",
            None,
            10
        )
        print(f"  🏆 Premier League Champions: {champion['team_name']}")

    # Decrease contract years
    async with db.pool.acquire() as conn:
        await conn.execute("""
            UPDATE players
            SET contract_years = GREATEST(0, contract_years - 1)
            WHERE retired = FALSE
        """)

        await conn.execute("""
            UPDATE players
            SET team_id = 'free_agent', league = NULL
            WHERE contract_years = 0 AND retired = FALSE
        """)

    # Reset season stats
    async with db.pool.acquire() as conn:
        await conn.execute("""
            UPDATE players
            SET season_goals = 0, season_assists = 0, 
                season_apps = 0, season_rating = 0.0, season_motm = 0
            WHERE retired = FALSE
        """)

        await conn.execute("""
            UPDATE teams
            SET played = 0, won = 0, drawn = 0, lost = 0,
                goals_for = 0, goals_against = 0, points = 0, form = ''
        """)

        await conn.execute("""
            UPDATE npc_players
            SET season_goals = 0, season_assists = 0, season_apps = 0
            WHERE retired = FALSE
        """)

    await db.add_news(
        f"Season {config.CURRENT_SEASON} Concludes",
        f"The season has ended! Promotions and relegations complete. {retirements} players retired.",
        "league_news",
        None,
        10,
        config.SEASON_TOTAL_WEEKS
    )

    await db.update_game_state(
        season_started=False,
        current_week=0,
        fixtures_generated=False,
        match_window_open=False,
        transfer_window_active=False
    )

    print(f"✅ Season ended. {retirements} retirements. Ready for new season.")
