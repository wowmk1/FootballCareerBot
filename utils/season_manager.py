from database import db
from datetime import datetime, timedelta
import config

async def start_season():
    """Initialize and start the season"""
    from utils.fixture_generator import generate_all_fixtures
    
    await db.update_game_state(
        season_started=True,
        current_week=1,
        season_start_date=datetime.now().isoformat(),
        fixtures_generated=False
    )
    
    await generate_all_fixtures()
    
    # Schedule first match day
    next_match = datetime.now() + timedelta(days=1)
    next_match = next_match.replace(hour=config.MATCH_START_HOUR, minute=0, second=0, microsecond=0)
    
    await db.update_game_state(
        next_match_day=next_match.isoformat()
    )
    
    print(f"✅ Season {config.CURRENT_SEASON} started!")
    print(f"📅 First match day scheduled for {next_match.strftime('%Y-%m-%d %H:%M')}")

async def open_match_window():
    """Open match window for current week"""
    state = await db.get_game_state()
    
    if not state['season_started']:
        return
    
    current_week = state['current_week']
    
    # Mark fixtures as playable
    await db.db.execute('''
        UPDATE fixtures 
        SET playable = 1 
        WHERE week_number = ? AND played = 0
    ''', (current_week,))
    await db.db.commit()
    
    # Set window close time
    window_closes = datetime.now() + timedelta(hours=config.MATCH_WINDOW_HOURS)
    
    await db.update_game_state(
        match_window_open=True,
        match_window_closes=window_closes.isoformat()
    )
    
    print(f"✅ Match window opened for Week {current_week}")
    print(f"⏰ Window closes at {window_closes.strftime('%Y-%m-%d %H:%M')}")

async def close_match_window():
    """Close match window and auto-simulate unplayed matches"""
    from utils.match_simulator import simulate_all_matches
    
    state = await db.get_game_state()
    current_week = state['current_week']
    
    # Get unplayed fixtures
    async with db.db.execute(
        "SELECT * FROM fixtures WHERE week_number = ? AND played = 0 AND playable = 1",
        (current_week,)
    ) as cursor:
        rows = await cursor.fetchall()
        unplayed = [dict(row) for row in rows]
    
    # Auto-simulate them
    if unplayed:
        print(f"⏰ Auto-simulating {len(unplayed)} unplayed matches...")
        for fixture in unplayed:
            from utils.match_simulator import simulate_match
            await simulate_match(fixture)
    
    # Mark fixtures as no longer playable
    await db.db.execute('''
        UPDATE fixtures 
        SET playable = 0 
        WHERE week_number = ?
    ''', (current_week,))
    
    await db.update_game_state(
        match_window_open=False,
        match_window_closes=None,
        last_match_day=datetime.now().isoformat()
    )
    
    await db.db.commit()
    
    print(f"✅ Match window closed for Week {current_week}")

async def advance_week():
    """Advance to the next week"""
    state = await db.get_game_state()
    
    if not state['season_started']:
        print("⚠️ Season hasn't started yet")
        return
    
    current_week = state['current_week']
    
    if current_week >= config.SEASON_TOTAL_WEEKS:
        await end_season()
        return
    
    # Close any open match window first
    if state['match_window_open']:
        await close_match_window()
    
    new_week = current_week + 1
    
    # Schedule next match day
    next_match = datetime.now() + timedelta(days=2)
    next_match = next_match.replace(hour=config.MATCH_START_HOUR, minute=0, second=0, microsecond=0)
    
    await db.update_game_state(
        current_week=new_week,
        next_match_day=next_match.isoformat() if new_week <= config.SEASON_TOTAL_WEEKS else None
    )
    
    print(f"✅ Advanced to Week {new_week}/{config.SEASON_TOTAL_WEEKS}")
    
    if new_week <= config.SEASON_TOTAL_WEEKS:
        print(f"📅 Next match day: {next_match.strftime('%Y-%m-%d %H:%M')}")

async def check_match_day_trigger():
    """Check if it's time to open match window (called by background task)"""
    state = await db.get_game_state()
    
    if not state['season_started']:
        return False
    
    # If window already open, check if it should close
    if state['match_window_open']:
        if state['match_window_closes']:
            closes = datetime.fromisoformat(state['match_window_closes'])
            if datetime.now() >= closes:
                await close_match_window()
                await advance_week()
                return True
        return False
    
    # Check if it's time to open window
    if state['next_match_day']:
        next_match = datetime.fromisoformat(state['next_match_day'])
        if datetime.now() >= next_match:
            await open_match_window()
            return True
    
    return False

async def end_season():
    """End the current season"""
    
    print("🏁 Season ending...")
    
    await db.age_all_players()
    
    retirements = await db.retire_old_players()
    
    await db.db.execute("""
        UPDATE players SET
        season_goals = 0,
        season_assists = 0,
        season_apps = 0,
        season_rating = 0.0
        WHERE retired = 0
    """)
    
    await db.db.execute("""
        UPDATE teams SET
        played = 0,
        won = 0,
        drawn = 0,
        lost = 0,
        goals_for = 0,
        goals_against = 0,
        points = 0,
        form = ''
    """)
    
    await db.db.commit()
    
    await db.add_news(
        f"Season {config.CURRENT_SEASON} Concludes",
        f"The season has ended! {retirements} players have retired. New season begins soon.",
        "league_news",
        None,
        10,
        config.SEASON_TOTAL_WEEKS
    )
    
    await db.update_game_state(
        season_started=False,
        current_week=0,
        fixtures_generated=False,
        match_window_open=False
    )
    
    print(f"✅ Season ended. {retirements} retirements processed.")
    print("⏳ Ready for new season to start")
