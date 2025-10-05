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
    
    async with db.pool.acquire() as conn:
        await conn.execute('''
            UPDATE fixtures 
            SET playable = TRUE 
            WHERE week_number = $1 AND played = FALSE
        ''', current_week)
    
    window_closes = datetime.now() + timedelta(hours=config.MATCH_WINDOW_HOURS)
    
    await db.update_game_state(
        match_window_open=True,
        match_window_closes=window_closes.isoformat()
    )
    
    print(f"✅ Match window opened for Week {current_week}")
    print(f"⏰ Window closes at {window_closes.strftime('%Y-%m-%d %H:%M')}")
    
    # Generate transfer offers if window is open
    from utils.transfer_window_manager import (
        is_transfer_window_open,
        generate_offers_for_player,
        send_offer_notification,
        get_current_transfer_window
    )
    
    if await is_transfer_window_open(current_week):
        print(f"📬 Generating weekly transfer offers...")
        
        try:
            # Import bot instance
            from bot import bot
            
            # Get all active players
            async with db.pool.acquire() as conn:
                players = await conn.fetch(
                    "SELECT user_id FROM players WHERE retired = FALSE AND team_id != 'free_agent'"
                )
            
            for player_row in players:
                user_id = player_row['user_id']
                player = await db.get_player(user_id)
                
                # Skip if already transferred this window
                if player.get('last_transfer_window') == get_current_transfer_window(current_week):
                    continue
                
                # Generate 2-4 offers
                offers = await generate_offers_for_player(player, current_week, num_offers=3)
                
                # Send DM notification
                if offers:
                    await send_offer_notification(bot, user_id, len(offers))
            
            print(f"✅ Transfer offers generated and notifications sent")
        except Exception as e:
            print(f"⚠️ Could not send transfer notifications: {e}")

async def close_match_window():
    """Close match window and auto-simulate unplayed matches"""
    from utils.match_simulator import simulate_match
    
    state = await db.get_game_state()
    current_week = state['current_week']
    
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM fixtures WHERE week_number = $1 AND played = FALSE AND playable = TRUE",
            current_week
        )
        unplayed = [dict(row) for row in rows]
    
    if unplayed:
        print(f"⏰ Auto-simulating {len(unplayed)} unplayed matches...")
        for fixture in unplayed:
            await simulate_match(fixture)
    
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
    
    if state['match_window_open']:
        await close_match_window()
    
    new_week = current_week + 1
    
    next_match = datetime.now() + timedelta(days=2)
    next_match = next_match.replace(hour=config.MATCH_START_HOUR, minute=0, second=0, microsecond=0)
    
    await db.update_game_state(
        current_week=new_week,
        next_match_day=next_match.isoformat() if new_week <= config.SEASON_TOTAL_WEEKS else None
    )
    
    print(f"✅ Advanced to Week {new_week}/{config.SEASON_TOTAL_WEEKS}")
    
    # Check and update transfer window status
    from utils.transfer_window_manager import check_and_update_transfer_window
    window_active = await check_and_update_transfer_window()
    
    if window_active:
        print(f"🔓 Transfer window active - Week {new_week}")
    
    if new_week <= config.SEASON_TOTAL_WEEKS:
        print(f"📅 Next match day: {next_match.strftime('%Y-%m-%d %H:%M')}")

async def check_match_day_trigger():
    """Check if it's time to open match window"""
    state = await db.get_game_state()
    
    if not state['season_started']:
        return False
    
    if state['match_window_open']:
        if state['match_window_closes']:
            closes = datetime.fromisoformat(state['match_window_closes'])
            if datetime.now() >= closes:
                await close_match_window()
                await advance_week()
                return True
        return False
    
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
    
    async with db.pool.acquire() as conn:
        await conn.execute("""
            UPDATE players SET
            season_goals = 0,
            season_assists = 0,
            season_apps = 0,
            season_rating = 0.0
            WHERE retired = FALSE
        """)
        
        await conn.execute("""
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
        match_window_open=False,
        transfer_window_active=False
    )
    
    print(f"✅ Season ended. {retirements} retirements processed.")
    print("⏳ Ready for new season to start")
