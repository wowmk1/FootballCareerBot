"""
Season Management - Match Windows, Week Progression
INCLUDES EUROPEAN COMPETITION SUPPORT
"""
import asyncio
from datetime import datetime, timedelta, timezone
from database import db
import config
import logging

logger = logging.getLogger(__name__)

# EST timezone
EST = timezone(timedelta(hours=-5))

# Match window schedule: Mon/Wed/Sat 3-5 PM EST
MATCH_DAYS = [0, 2, 5]  # Monday, Wednesday, Saturday
MATCH_START_HOUR = 15  # 3:00 PM
MATCH_END_HOUR = 17    # 5:00 PM


def get_next_match_window():
    """Get the next match window datetime"""
    now = datetime.now(EST)
    
    # Check each upcoming day
    for days_ahead in range(7):
        check_date = now + timedelta(days=days_ahead)
        
        # If it's a match day
        if check_date.weekday() in MATCH_DAYS:
            # Set to 3 PM EST
            window_time = check_date.replace(hour=MATCH_START_HOUR, minute=0, second=0, microsecond=0)
            
            # If this window is in the future, return it
            if window_time > now:
                return window_time
    
    # Fallback: next Monday at 3 PM
    days_until_monday = (7 - now.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    
    next_monday = now + timedelta(days=days_until_monday)
    return next_monday.replace(hour=MATCH_START_HOUR, minute=0, second=0, microsecond=0)


def is_match_window_time():
    """
    Check if current time is match window time
    Returns: (is_window_time, is_start_time, is_end_time)
    """
    now = datetime.now(EST)
    current_day = now.weekday()
    current_hour = now.hour
    current_minute = now.minute
    
    # Not a match day
    if current_day not in MATCH_DAYS:
        return False, False, False
    
    # Check if it's the start of the window (3:00 PM exactly, with 5-min tolerance)
    is_start = (current_hour == MATCH_START_HOUR and current_minute < 5)
    
    # Check if it's the end of the window (5:00 PM exactly, with 5-min tolerance)
    is_end = (current_hour == MATCH_END_HOUR and current_minute < 5)
    
    # Check if we're within the window (3:00 PM - 5:00 PM)
    is_window = (MATCH_START_HOUR <= current_hour < MATCH_END_HOUR)
    
    return is_window, is_start, is_end


def should_send_warning(warning_type):
    """Check if we should send a specific warning"""
    now = datetime.now(EST)
    current_day = now.weekday()
    current_hour = now.hour
    current_minute = now.minute
    
    # Only send warnings on match days
    if current_day not in MATCH_DAYS:
        return False
    
    # 1 hour before (2:00 PM)
    if warning_type == 'pre_1h':
        return current_hour == 14 and current_minute < 5
    
    # 30 minutes before (2:30 PM)
    elif warning_type == 'pre_30m':
        return current_hour == 14 and 30 <= current_minute < 35
    
    # 15 minutes before (2:45 PM)
    elif warning_type == 'pre_15m':
        return current_hour == 14 and 45 <= current_minute < 50
    
    # 15 minutes before closing (4:45 PM)
    elif warning_type == 'closing_soon':
        return current_hour == 16 and 45 <= current_minute < 50
    
    return False


async def open_match_window():
    """Open match window - domestic + European"""
    logger.info("🟢 Opening match window...")
    
    async with db.pool.acquire() as conn:
        state = await conn.fetchrow('SELECT * FROM game_state')
        current_week = state['current_week']
        
        # Open domestic fixtures
        await conn.execute("""
            UPDATE fixtures 
            SET playable = TRUE 
            WHERE week_number = $1 AND played = FALSE
        """, current_week)
        
        # Open European fixtures if it's a European week
        if current_week in config.EUROPEAN_MATCH_WEEKS:
            logger.info(f"🏆 Opening European window for Week {current_week}")
            from utils.european_competitions import open_european_window
            await open_european_window(current_week)
        
        # Mark window as open
        await conn.execute("""
            UPDATE game_state 
            SET match_window_open = TRUE
        """)
    
    logger.info(f"✅ Match window opened for Week {current_week}")


async def close_match_window(bot=None):
    """Close match window and simulate unplayed matches"""
    logger.info("🔴 Closing match window...")
    
    async with db.pool.acquire() as conn:
        state = await conn.fetchrow('SELECT * FROM game_state')
        current_week = state['current_week']
        
        # Get unplayed domestic fixtures
        unplayed = await conn.fetch("""
            SELECT * FROM fixtures 
            WHERE week_number = $1 AND played = FALSE AND playable = TRUE
        """, current_week)
        
        logger.info(f"📊 Simulating {len(unplayed)} unplayed domestic matches...")
        
        # Simulate domestic matches
        from utils.match_engine import match_engine
        results = []
        
        for fixture in unplayed:
            result = await match_engine.simulate_npc_match(
                fixture['home_team_id'],
                fixture['away_team_id']
            )
            
            # Update fixture
            await conn.execute("""
                UPDATE fixtures 
                SET home_score = $1, away_score = $2, played = TRUE, playable = FALSE
                WHERE fixture_id = $3
            """, result['home_score'], result['away_score'], fixture['fixture_id'])
            
            # Update league tables
            await update_team_stats(
                conn, 
                fixture['home_team_id'], 
                result['home_score'], 
                result['away_score']
            )
            await update_team_stats(
                conn, 
                fixture['away_team_id'], 
                result['away_score'], 
                result['home_score']
            )
            
            results.append({
                'home_team_name': result['home_team'],
                'away_team_name': result['away_team'],
                'home_score': result['home_score'],
                'away_score': result['away_score']
            })
        
        # ✅ Close European window if it's a European week
        if current_week in config.EUROPEAN_MATCH_WEEKS:
            logger.info(f"🏆 Closing European window for Week {current_week}")
            from utils.european_competitions import close_european_window
            await close_european_window(current_week, bot=bot)
        
        # Mark window as closed
        await conn.execute("""
            UPDATE game_state 
            SET match_window_open = FALSE
        """)
    
    logger.info(f"✅ Match window closed. {len(results)} matches simulated")
    
    # Advance to next week
    await advance_week(bot=bot)
    
    return results


async def update_team_stats(conn, team_id, goals_for, goals_against):
    """Update team statistics after a match"""
    if goals_for > goals_against:
        won, drawn, lost, points = 1, 0, 0, 3
    elif goals_for == goals_against:
        won, drawn, lost, points = 0, 1, 0, 1
    else:
        won, drawn, lost, points = 0, 0, 1, 0
    
    await conn.execute("""
        UPDATE teams 
        SET played = played + 1,
            won = won + $1,
            drawn = drawn + $2,
            lost = lost + $3,
            goals_for = goals_for + $4,
            goals_against = goals_against + $5,
            points = points + $6
        WHERE team_id = $7
    """, won, drawn, lost, goals_for, goals_against, points, team_id)


async def advance_week(bot=None):
    """Advance to next week"""
    async with db.pool.acquire() as conn:
        state = await conn.fetchrow('SELECT * FROM game_state')
        current_week = state['current_week']
        next_week = current_week + 1
        
        # Check if season is over
        if next_week > config.SEASON_TOTAL_WEEKS:
            logger.info("🏁 Season complete! Starting new season...")
            await end_season(bot=bot)
            return
        
        # Advance week
        await conn.execute("""
            UPDATE game_state 
            SET current_week = $1
        """, next_week)
        
        logger.info(f"📅 Advanced to Week {next_week}")
        
        # Handle transfer windows
        if next_week in config.TRANSFER_WINDOW_WEEKS:
            logger.info("💼 Transfer window opening...")
            from utils.transfer_system import generate_offers
            await generate_offers()
        
        # Post weekly news
        if bot:
            try:
                from utils.event_poster import post_weekly_news_digest
                await post_weekly_news_digest(bot, current_week)
            except Exception as e:
                logger.warning(f"⚠️ Could not post weekly news: {e}")


async def end_season(bot=None):
    """End current season and start new one"""
    logger.info("🏁 Ending season...")
    
    async with db.pool.acquire() as conn:
        state = await conn.fetchrow('SELECT * FROM game_state')
        current_season = state['current_season']
        
        # Determine promotions/relegations
        from utils.league_system import process_promotions_relegations
        await process_promotions_relegations(bot=bot)
        
        # Reset all teams for new season
        await conn.execute("""
            UPDATE teams 
            SET played = 0, won = 0, drawn = 0, lost = 0,
                goals_for = 0, goals_against = 0, points = 0
        """)
        
        # Reset player season stats
        await conn.execute("""
            UPDATE players 
            SET season_goals = 0, season_assists = 0, season_apps = 0, season_motm = 0
        """)
        
        # Age players and update potential
        await db.age_all_players(bot=bot)
        
        # Generate new fixtures
        from utils.fixture_generator import generate_all_fixtures
        await generate_all_fixtures(f"{current_season + 1}/{current_season + 2}")
        
        # Draw European groups
        from utils.european_competitions import draw_groups
        await draw_groups(f"{current_season + 1}/{current_season + 2}")
        
        # Start new season
        await conn.execute("""
            UPDATE game_state 
            SET current_season = current_season + 1,
                current_week = 1,
                match_window_open = FALSE
        """)
        
        logger.info(f"✅ New season started: {current_season + 1}/{current_season + 2}")


# Warning functions
async def send_1h_warning(bot):
    """Send 1 hour warning"""
    logger.info("⏰ Sending 1-hour warning...")
    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name="match-results") or \
                  discord.utils.get(guild.text_channels, name="general")
        if channel:
            embed = discord.Embed(
                title="⏰ Match Window Opening Soon!",
                description="Match window opens in **1 HOUR** (3:00 PM EST)",
                color=discord.Color.orange()
            )
            await channel.send(embed=embed)


async def send_30m_warning(bot):
    """Send 30 minute warning"""
    logger.info("⏰ Sending 30-minute warning...")
    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name="match-results") or \
                  discord.utils.get(guild.text_channels, name="general")
        if channel:
            embed = discord.Embed(
                title="⏰ Match Window Opening Soon!",
                description="Match window opens in **30 MINUTES** (3:00 PM EST)",
                color=discord.Color.gold()
            )
            await channel.send(embed=embed)


async def send_15m_warning(bot):
    """Send 15 minute warning"""
    logger.info("⏰ Sending 15-minute warning...")
    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name="match-results") or \
                  discord.utils.get(guild.text_channels, name="general")
        if channel:
            embed = discord.Embed(
                title="⏰ Match Window Opening Soon!",
                description="Match window opens in **15 MINUTES** (3:00 PM EST)\n\nGet ready!",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)


async def send_closing_warning(bot):
    """Send closing soon warning"""
    logger.info("⏰ Sending closing warning...")
    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name="match-results") or \
                  discord.utils.get(guild.text_channels, name="general")
        if channel:
            embed = discord.Embed(
                title="⚠️ Match Window Closing Soon!",
                description="Match window closes in **15 MINUTES** (5:00 PM EST)\n\nPlay your matches now!",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)
