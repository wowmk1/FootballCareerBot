"""
Season Management - Two Windows on Same Days
12-2 PM: European (CL+EL) on European weeks
3-5 PM: Domestic (always) - advances week after close
"""
import asyncio
from datetime import datetime, timedelta, timezone
from database import db
import config
import logging

logger = logging.getLogger(__name__)

EST = timezone(timedelta(hours=-5))

# Match days (Mon/Wed/Sat)
MATCH_DAYS = [0, 2, 5]

# Window times
EUROPEAN_START_HOUR = 12  # 12 PM (Noon)
EUROPEAN_END_HOUR = 14    # 2 PM
DOMESTIC_START_HOUR = 15  # 3 PM
DOMESTIC_END_HOUR = 17    # 5 PM


def get_next_match_window():
    """Get the next match window datetime"""
    now = datetime.now(EST)
    
    for days_ahead in range(7):
        check_date = now + timedelta(days=days_ahead)
        
        if check_date.weekday() in MATCH_DAYS:
            # Check if European window is next
            european_time = check_date.replace(hour=EUROPEAN_START_HOUR, minute=0, second=0, microsecond=0)
            if european_time > now:
                return european_time
            
            # Otherwise check domestic window
            domestic_time = check_date.replace(hour=DOMESTIC_START_HOUR, minute=0, second=0, microsecond=0)
            if domestic_time > now:
                return domestic_time
    
    # Fallback: next Monday at noon
    days_until_monday = (7 - now.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    
    next_monday = now + timedelta(days=days_until_monday)
    return next_monday.replace(hour=EUROPEAN_START_HOUR, minute=0, second=0, microsecond=0)


def is_match_window_time():
    """
    Check if current time is match window time
    Returns: (is_window_time, is_start_time, is_end_time, window_type)
    window_type: 'european' or 'domestic'
    """
    now = datetime.now(EST)
    current_day = now.weekday()
    current_hour = now.hour
    current_minute = now.minute
    
    # Must be a match day
    if current_day not in MATCH_DAYS:
        return False, False, False, None
    
    # Check European window (12-2 PM)
    if EUROPEAN_START_HOUR <= current_hour < EUROPEAN_END_HOUR:
        is_start = (current_hour == EUROPEAN_START_HOUR and current_minute < 5)
        is_end = (current_hour == EUROPEAN_END_HOUR and current_minute < 5)
        return True, is_start, is_end, 'european'
    
    # Check Domestic window (3-5 PM)
    if DOMESTIC_START_HOUR <= current_hour < DOMESTIC_END_HOUR:
        is_start = (current_hour == DOMESTIC_START_HOUR and current_minute < 5)
        is_end = (current_hour == DOMESTIC_END_HOUR and current_minute < 5)
        return True, is_start, is_end, 'domestic'
    
    return False, False, False, None


def should_send_warning(warning_type):
    """Check if we should send warnings"""
    now = datetime.now(EST)
    current_day = now.weekday()
    current_hour = now.hour
    current_minute = now.minute
    
    if current_day not in MATCH_DAYS:
        return False
    
    # European warnings (11 AM, 11:30, 11:45, 1:45 PM)
    if warning_type == 'european_1h':  # 11 AM
        return current_hour == 11 and current_minute < 5
    elif warning_type == 'european_30m':  # 11:30 AM
        return current_hour == 11 and 30 <= current_minute < 35
    elif warning_type == 'european_15m':  # 11:45 AM
        return current_hour == 11 and 45 <= current_minute < 50
    elif warning_type == 'european_closing':  # 1:45 PM
        return current_hour == 13 and 45 <= current_minute < 50
    
    # Domestic warnings (2 PM, 2:30, 2:45, 4:45 PM)
    elif warning_type == 'domestic_1h':  # 2 PM
        return current_hour == 14 and current_minute < 5
    elif warning_type == 'domestic_30m':  # 2:30 PM
        return current_hour == 14 and 30 <= current_minute < 35
    elif warning_type == 'domestic_15m':  # 2:45 PM
        return current_hour == 14 and 45 <= current_minute < 50
    elif warning_type == 'domestic_closing':  # 4:45 PM
        return current_hour == 16 and 45 <= current_minute < 50
    
    return False


async def open_match_window(window_type='domestic'):
    """Open match window"""
    logger.info(f"🟢 Opening {window_type} match window...")
    
    async with db.pool.acquire() as conn:
        state = await conn.fetchrow('SELECT * FROM game_state')
        current_week = state['current_week']
        
        if window_type == 'domestic':
            # Open domestic fixtures
            await conn.execute("""
                UPDATE fixtures 
                SET playable = TRUE 
                WHERE week_number = $1 AND played = FALSE
            """, current_week)
            logger.info(f"✅ Domestic fixtures opened for Week {current_week}")
        
        elif window_type == 'european':
            # Open European fixtures if it's a European week
            if current_week in config.EUROPEAN_MATCH_WEEKS:
                await conn.execute("""
                    UPDATE european_fixtures 
                    SET playable = TRUE 
                    WHERE week_number = $1 AND played = FALSE
                """, current_week)
                logger.info(f"🏆 European fixtures (CL + EL) opened for Week {current_week}")
            else:
                logger.info(f"⏭️ No European matches this week (Week {current_week})")
        
        await conn.execute("UPDATE game_state SET match_window_open = TRUE")


async def close_match_window(window_type='domestic', bot=None):
    """Close match window and simulate unplayed matches"""
    logger.info(f"🔴 Closing {window_type} match window...")
    
    async with db.pool.acquire() as conn:
        state = await conn.fetchrow('SELECT * FROM game_state')
        current_week = state['current_week']
        
        results = []
        
        if window_type == 'domestic':
            # Simulate unplayed domestic fixtures
            unplayed = await conn.fetch("""
                SELECT * FROM fixtures 
                WHERE week_number = $1 AND played = FALSE AND playable = TRUE
            """, current_week)
            
            logger.info(f"📊 Simulating {len(unplayed)} unplayed domestic matches...")
            
            from utils.match_engine import match_engine
            
            for fixture in unplayed:
                result = await match_engine.simulate_npc_match(
                    fixture['home_team_id'],
                    fixture['away_team_id']
                )
                
                await conn.execute("""
                    UPDATE fixtures 
                    SET home_score = $1, away_score = $2, played = TRUE, playable = FALSE
                    WHERE fixture_id = $3
                """, result['home_score'], result['away_score'], fixture['fixture_id'])
                
                await update_team_stats(conn, fixture['home_team_id'], result['home_score'], result['away_score'])
                await update_team_stats(conn, fixture['away_team_id'], result['away_score'], result['home_score'])
                
                results.append({
                    'home_team_name': result['home_team'],
                    'away_team_name': result['away_team'],
                    'home_score': result['home_score'],
                    'away_score': result['away_score']
                })
            
            # ✅ Domestic window ALWAYS advances week
            logger.info(f"✅ Advancing from Week {current_week} to Week {current_week + 1}")
            await conn.execute("UPDATE game_state SET match_window_open = FALSE")
            await advance_week(bot=bot)
        
        elif window_type == 'european':
            # Close European window (both CL and EL)
            if current_week in config.EUROPEAN_MATCH_WEEKS:
                from utils.european_competitions import close_european_window
                await close_european_window(current_week, bot=bot, competition=None)
                logger.info(f"🏆 European matches closed for Week {current_week}")
            
            # ❌ European window does NOT advance week
            logger.info(f"⏸️ Week stays at {current_week} (domestic window at 3 PM)")
            await conn.execute("UPDATE game_state SET match_window_open = FALSE")
    
    return results


async def update_team_stats(conn, team_id, goals_for, goals_against):
    """Update team statistics"""
    if goals_for > goals_against:
        won, drawn, lost, points = 1, 0, 0, 3
    elif goals_for == goals_against:
        won, drawn, lost, points = 0, 1, 0, 1
    else:
        won, drawn, lost, points = 0, 0, 1, 0
    
    await conn.execute("""
        UPDATE teams 
        SET played = played + 1, won = won + $1, drawn = drawn + $2, lost = lost + $3,
            goals_for = goals_for + $4, goals_against = goals_against + $5, points = points + $6
        WHERE team_id = $7
    """, won, drawn, lost, goals_for, goals_against, points, team_id)


async def advance_week(bot=None):
    """Advance to next week"""
    async with db.pool.acquire() as conn:
        state = await conn.fetchrow('SELECT * FROM game_state')
        current_week = state['current_week']
        next_week = current_week + 1
        
        if next_week > config.SEASON_TOTAL_WEEKS:
            logger.info("🏁 Season complete!")
            await end_season(bot=bot)
            return
        
        await conn.execute("UPDATE game_state SET current_week = $1", next_week)
        logger.info(f"📅 Advanced to Week {next_week}")
        
        if next_week in config.TRANSFER_WINDOW_WEEKS:
            logger.info("💼 Transfer window opening...")
            from utils.transfer_system import generate_offers
            await generate_offers()
        
        if bot:
            try:
                from utils.event_poster import post_weekly_news_digest
                await post_weekly_news_digest(bot, current_week)
            except Exception as e:
                logger.warning(f"⚠️ Could not post weekly news: {e}")


async def end_season(bot=None):
    """End season"""
    logger.info("🏁 Ending season...")
    
    async with db.pool.acquire() as conn:
        state = await conn.fetchrow('SELECT * FROM game_state')
        current_season = state['current_season']
        
        from utils.league_system import process_promotions_relegations
        await process_promotions_relegations(bot=bot)
        
        await conn.execute("UPDATE teams SET played=0, won=0, drawn=0, lost=0, goals_for=0, goals_against=0, points=0")
        await conn.execute("UPDATE players SET season_goals=0, season_assists=0, season_apps=0, season_motm=0")
        
        await db.age_all_players(bot=bot)
        
        from utils.fixture_generator import generate_all_fixtures
        await generate_all_fixtures(f"{current_season + 1}/{current_season + 2}")
        
        from utils.european_competitions import draw_groups
        await draw_groups(f"{current_season + 1}/{current_season + 2}")
        
        await conn.execute("""
            UPDATE game_state 
            SET current_season = current_season + 1, current_week = 1, match_window_open = FALSE
        """)
        
        logger.info(f"✅ New season: {current_season + 1}/{current_season + 2}")


# Warning functions
async def send_1h_warning(bot):
    """Send 1 hour warning (for domestic 2 PM or European 11 AM)"""
    pass

async def send_30m_warning(bot):
    """Send 30 minute warning"""
    pass

async def send_15m_warning(bot):
    """Send 15 minute warning"""
    pass

async def send_closing_warning(bot):
    """Send closing warning"""
    pass
