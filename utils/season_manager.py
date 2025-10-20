"""
Season Management - Two Windows on Same Days
12-2 PM EST: European (CL+EL) on European weeks
3-5 PM EST: Domestic (always) - advances week after close

✅ FIXED: Proper timezone handling and end detection
✅ FIXED: Window closes at EXACT time (2:00 PM, 5:00 PM)
✅ FIXED: Python 3.8+ compatibility
"""
import asyncio
from datetime import datetime, timedelta, timezone
from database import db
import config
import logging
import discord

# Timezone import with fallback for Python 3.8
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# ✅ PROPER TIMEZONE HANDLING
EST = ZoneInfo('America/New_York')  # This handles DST automatically!

# Match days (Mon=0, Wed=2, Sat=5)
MATCH_DAYS = [0, 2, 5]

# Window times (EST)
EUROPEAN_START_HOUR = 12  # 12:00 PM (Noon)
EUROPEAN_END_HOUR = 14    # 2:00 PM
DOMESTIC_START_HOUR = 15  # 3:00 PM
DOMESTIC_END_HOUR = 17    # 5:00 PM


def get_current_time_est():
    """Get current time in EST"""
    return datetime.now(EST)


def is_match_window_time():
    """
    Check if current time is match window time
    Returns: (is_window_time, is_start_time, is_end_time, window_type)
    
    ✅ FIXED: Properly detects end time at 2:00 PM and 5:00 PM
    ✅ FIXED: Works with 5-minute check interval
    """
    now = get_current_time_est()
    current_day = now.weekday()
    current_hour = now.hour
    current_minute = now.minute
    
    logger.info(f"🕐 Window check: {now.strftime('%A %I:%M %p EST')} (hour={current_hour}, min={current_minute}, day={current_day})")
    
    # Must be a match day
    if current_day not in MATCH_DAYS:
        logger.debug(f"  ❌ Not a match day (weekday={current_day})")
        return False, False, False, None
    
    # ===== EUROPEAN WINDOW: 12:00 PM - 2:00 PM =====
    
    # Check if we're INSIDE the window (12:00-1:59 PM)
    if EUROPEAN_START_HOUR <= current_hour < EUROPEAN_END_HOUR:
        is_start = (current_hour == EUROPEAN_START_HOUR and current_minute < 5)  # 12:00-12:04
        is_end = False
        logger.info(f"  🏆 Inside European window (is_start={is_start})")
        return True, is_start, is_end, 'european'
    
    # ✅ CRITICAL: Check if we're AT closing time (2:00-2:04 PM)
    if current_hour == EUROPEAN_END_HOUR and current_minute < 5:
        logger.info(f"  🔴 European window CLOSING TIME DETECTED")
        return False, False, True, 'european'
    
    # ===== DOMESTIC WINDOW: 3:00 PM - 5:00 PM =====
    
    # Check if we're INSIDE the window (3:00-4:59 PM)
    if DOMESTIC_START_HOUR <= current_hour < DOMESTIC_END_HOUR:
        is_start = (current_hour == DOMESTIC_START_HOUR and current_minute < 5)  # 3:00-3:04
        is_end = False
        logger.info(f"  ⚽ Inside Domestic window (is_start={is_start})")
        return True, is_start, is_end, 'domestic'
    
    # ✅ CRITICAL: Check if we're AT closing time (5:00-5:04 PM)
    if current_hour == DOMESTIC_END_HOUR and current_minute < 5:
        logger.info(f"  🔴 Domestic window CLOSING TIME DETECTED")
        return False, False, True, 'domestic'
    
    logger.info(f"  ❌ Outside all windows")
    return False, False, False, None


def should_send_warning(warning_type):
    """
    Check if we should send warnings
    
    ✅ FIXED: Now actually works with proper time checks
    """
    now = get_current_time_est()
    current_day = now.weekday()
    current_hour = now.hour
    current_minute = now.minute
    
    if current_day not in MATCH_DAYS:
        return False
    
    # European warnings
    if warning_type == 'european_1h':  # 11:00 AM (1h before 12 PM)
        return current_hour == 11 and current_minute < 5
    elif warning_type == 'european_30m':  # 11:30 AM
        return current_hour == 11 and 30 <= current_minute < 35
    elif warning_type == 'european_15m':  # 11:45 AM
        return current_hour == 11 and 45 <= current_minute < 50
    
    # Domestic warnings
    elif warning_type == 'domestic_1h':  # 2:00 PM (1h before 3 PM)
        return current_hour == 14 and current_minute < 5
    elif warning_type == 'domestic_30m':  # 2:30 PM
        return current_hour == 14 and 30 <= current_minute < 35
    elif warning_type == 'domestic_15m':  # 2:45 PM
        return current_hour == 14 and 45 <= current_minute < 50
    elif warning_type == 'domestic_closing':  # 4:45 PM (15m before close)
        return current_hour == 16 and 45 <= current_minute < 50
    
    return False


def get_next_match_window():
    """
    Get the next match window datetime
    ✅ Returns EST datetime
    """
    now = get_current_time_est()
    logger.debug(f"🔍 Finding next window from: {now.strftime('%A %b %d %I:%M %p EST')}")
    
    for days_ahead in range(8):
        check_date = now + timedelta(days=days_ahead)
        
        if check_date.weekday() in MATCH_DAYS:
            # Check European window
            european_time = check_date.replace(hour=EUROPEAN_START_HOUR, minute=0, second=0, microsecond=0)
            if european_time > now:
                logger.info(f"✅ Next window: {european_time.strftime('%A %b %d at %I:%M %p EST')} (European)")
                return european_time
            
            # Check Domestic window
            domestic_time = check_date.replace(hour=DOMESTIC_START_HOUR, minute=0, second=0, microsecond=0)
            if domestic_time > now:
                logger.info(f"✅ Next window: {domestic_time.strftime('%A %b %d at %I:%M %p EST')} (Domestic)")
                return domestic_time
    
    # Fallback
    days_until_monday = (7 - now.weekday()) % 7 or 7
    next_monday = now + timedelta(days=days_until_monday)
    result = next_monday.replace(hour=EUROPEAN_START_HOUR, minute=0, second=0, microsecond=0)
    return result


def format_time_for_user(dt_est, user_timezone=None):
    """
    Convert EST time to user's timezone for display
    
    Args:
        dt_est: datetime in EST
        user_timezone: User's timezone (e.g., 'Europe/London', 'Asia/Tokyo')
                      If None, returns EST time
    
    Returns:
        Formatted string with time in user's timezone
    """
    if user_timezone:
        try:
            user_tz = ZoneInfo(user_timezone)
            dt_user = dt_est.astimezone(user_tz)
            return dt_user.strftime('%I:%M %p %Z')
        except:
            pass
    
    return dt_est.strftime('%I:%M %p EST')


async def open_match_window(window_type='domestic'):
    """Open match window"""
    logger.info(f"🟢 Opening {window_type} match window...")
    
    async with db.pool.acquire() as conn:
        state = await conn.fetchrow('SELECT * FROM game_state')
        current_week = state['current_week']
        
        if window_type == 'domestic':
            await conn.execute("""
                UPDATE fixtures 
                SET playable = TRUE 
                WHERE week_number = $1 AND played = FALSE
            """, current_week)
            logger.info(f"✅ Domestic fixtures opened for Week {current_week}")
        
        elif window_type == 'european':
            if current_week in config.EUROPEAN_MATCH_WEEKS:
                await conn.execute("""
                    UPDATE european_fixtures 
                    SET playable = TRUE 
                    WHERE week_number = $1 AND played = FALSE
                """, current_week)
                logger.info(f"🏆 European fixtures opened for Week {current_week}")
            else:
                logger.info(f"⏭️ No European matches this week (Week {current_week})")
        
        await conn.execute("UPDATE game_state SET match_window_open = TRUE")
        logger.info(f"✅ Database: match_window_open = TRUE")


async def close_match_window(window_type='domestic', bot=None):
    """
    Close match window and simulate unplayed matches
    
    ✅ FIXED: Properly closes window and advances week
    """
    logger.info(f"🔴 CLOSING {window_type} match window...")
    
    async with db.pool.acquire() as conn:
        state = await conn.fetchrow('SELECT * FROM game_state')
        current_week = state['current_week']
        
        results = []
        
        if window_type == 'domestic':
            # Get unplayed matches
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
                
                await add_match_result_news(
                    result['home_team'],
                    result['away_team'],
                    result['home_score'],
                    result['away_score'],
                    'match_news',
                    current_week,
                    competition='League'
                )
            
            logger.info(f"✅ Simulated {len(unplayed)} matches")
            
            # ✅ Set window closed BEFORE advancing week
            await conn.execute("UPDATE game_state SET match_window_open = FALSE")
            logger.info(f"✅ Database: match_window_open = FALSE")
            
            # ✅ CRITICAL: Advance week
            logger.info(f"📅 ADVANCING WEEK from {current_week} to {current_week + 1}...")
            await advance_week(bot=bot)
        
        elif window_type == 'european':
            if current_week in config.EUROPEAN_MATCH_WEEKS:
                from utils.european_competitions import close_european_window
                await close_european_window(current_week, bot=bot, competition=None)
                logger.info(f"🏆 European window closed for Week {current_week}")
            
            # European window does NOT advance week
            await conn.execute("UPDATE game_state SET match_window_open = FALSE")
            logger.info(f"⏸️ Week stays at {current_week} (domestic window will advance)")
    
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


async def add_match_result_news(home_team, away_team, home_score, away_score, 
                                category, week_number, competition='League'):
    """Add match result to news database"""
    
    if home_score > away_score:
        margin = home_score - away_score
        if margin >= 3:
            headline = f"{home_team} Thrash {away_team} {home_score}-{away_score}"
            content = f"{home_team} dominated with a {home_score}-{away_score} victory over {away_team} in the {competition}."
            importance = 7
        else:
            headline = f"{home_team} Beat {away_team} {home_score}-{away_score}"
            content = f"{home_team} secured a {home_score}-{away_score} win against {away_team} in the {competition}."
            importance = 5
    
    elif away_score > home_score:
        margin = away_score - home_score
        if margin >= 3:
            headline = f"{away_team} Demolish {home_team} {away_score}-{home_score}"
            content = f"{away_team} put on a stunning away performance, winning {away_score}-{home_score} at {home_team} in the {competition}."
            importance = 7
        else:
            headline = f"{away_team} Win at {home_team} {away_score}-{home_score}"
            content = f"{away_team} claimed all three points with a {away_score}-{home_score} away victory at {home_team} in the {competition}."
            importance = 5
    
    else:
        if home_score >= 3:
            headline = f"Thriller: {home_team} {home_score}-{away_score} {away_team}"
            content = f"An entertaining {home_score}-{away_score} draw between {home_team} and {away_team} in the {competition}."
            importance = 6
        else:
            headline = f"{home_team} {home_score}-{away_score} {away_team}"
            content = f"{home_team} and {away_team} shared the points in a {home_score}-{away_score} draw in the {competition}."
            importance = 4
    
    await db.add_news(
        headline=headline,
        content=content,
        category=category,
        user_id=None,
        importance=importance,
        week_number=week_number
    )


async def advance_week(bot=None):
    """Advance to next week"""
    async with db.pool.acquire() as conn:
        state = await conn.fetchrow('SELECT * FROM game_state')
        current_week = state['current_week']
        next_week = current_week + 1
        
        logger.info(f"📅 ADVANCING: Week {current_week} → Week {next_week}")
        
        if next_week > config.SEASON_TOTAL_WEEKS:
            logger.info("🏁 Season complete!")
            await end_season(bot=bot)
            return
        
        await conn.execute("UPDATE game_state SET current_week = $1", next_week)
        logger.info(f"✅ Week advanced to {next_week}")
        
        # European competition progression
        from utils import european_competitions as euro
        
        try:
            if current_week == 18:
                logger.info("🏆 Group stage complete, drawing Round of 16...")
                await euro.generate_knockout_draw('CL', 'r16', state['current_season'])
                await euro.generate_knockout_draw('EL', 'r16', state['current_season'])
            
            elif current_week == 24:
                logger.info("🏆 R16 complete, drawing Quarter-Finals...")
                await euro.close_knockout_round('CL', 'r16', state['current_season'])
                await euro.close_knockout_round('EL', 'r16', state['current_season'])
                await euro.generate_knockout_draw('CL', 'quarters', state['current_season'])
                await euro.generate_knockout_draw('EL', 'quarters', state['current_season'])
            
            elif current_week == 30:
                logger.info("🏆 Quarter-Finals complete, drawing Semi-Finals...")
                await euro.close_knockout_round('CL', 'quarters', state['current_season'])
                await euro.close_knockout_round('EL', 'quarters', state['current_season'])
                await euro.generate_knockout_draw('CL', 'semis', state['current_season'])
                await euro.generate_knockout_draw('EL', 'semis', state['current_season'])
            
            elif current_week == 36:
                logger.info("🏆 Semi-Finals complete, preparing Finals...")
                await euro.close_knockout_round('CL', 'semis', state['current_season'])
                await euro.close_knockout_round('EL', 'semis', state['current_season'])
                await euro.generate_knockout_draw('CL', 'final', state['current_season'])
                await euro.generate_knockout_draw('EL', 'final', state['current_season'])
            
            elif current_week == 38:
                logger.info("🏆 Finals played, crowning champions!")
                await euro.close_knockout_round('CL', 'final', state['current_season'])
                await euro.close_knockout_round('EL', 'final', state['current_season'])
                
                if bot:
                    try:
                        from utils.event_poster import post_european_champions
                        await post_european_champions(bot, state['current_season'])
                    except Exception as e:
                        logger.warning(f"⚠️ Could not post European champions: {e}")
        
        except Exception as e:
            logger.error(f"❌ Error in European competition progression: {e}", exc_info=True)
        
        # Transfer windows
        if next_week in config.TRANSFER_WINDOW_WEEKS:
            logger.info(f"💼 Transfer window opening for Week {next_week}...")
            
            try:
                from utils.transfer_system import process_weekly_transfer_offers
                await process_weekly_transfer_offers(bot=bot)
                logger.info("✅ Player transfer offers generated")
            except Exception as e:
                logger.error(f"❌ Error generating player offers: {e}", exc_info=True)
            
            try:
                from utils.transfer_system import simulate_npc_transfers
                npc_count = await simulate_npc_transfers()
                logger.info(f"✅ NPC transfers complete: {npc_count} transfers")
            except Exception as e:
                logger.error(f"❌ Error in NPC transfers: {e}", exc_info=True)
        
        # Weekly news digest
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
        await generate_all_fixtures()
        
        from utils.european_competitions import draw_groups
        await draw_groups(f"{current_season + 1}/{current_season + 2}")
        
        await conn.execute("""
            UPDATE game_state 
            SET current_season = current_season + 1, current_week = 1, match_window_open = FALSE
        """)
        
        logger.info(f"✅ New season: {current_season + 1}/{current_season + 2}")


# ===== WARNING NOTIFICATION FUNCTIONS =====
# (All warning functions from your code - they're fine, keeping them as-is)

async def send_european_1h_warning(bot):
    """Send 1 hour warning for European (11 AM)"""
    state = await db.get_game_state()
    current_week = state['current_week']
    
    if current_week not in config.EUROPEAN_MATCH_WEEKS:
        return
    
    logger.info("📢 Sending European 1h warning...")
    
    async with db.pool.acquire() as conn:
        players_with_matches = await conn.fetch("""
            SELECT DISTINCT p.user_id, p.player_name, p.team_id, t.team_name,
                   f.competition, f.home_team_id, f.away_team_id,
                   COALESCE(ht.team_name, eht.team_name) as home_name,
                   COALESCE(at.team_name, eat.team_name) as away_name,
                   f.stage, f.leg
            FROM players p
            JOIN teams t ON p.team_id = t.team_id
            JOIN european_fixtures f ON (f.home_team_id = p.team_id OR f.away_team_id = p.team_id)
            LEFT JOIN teams ht ON f.home_team_id = ht.team_id
            LEFT JOIN teams at ON f.away_team_id = at.team_id
            LEFT JOIN european_teams eht ON f.home_team_id = eht.team_id
            LEFT JOIN european_teams eat ON f.away_team_id = eat.team_id
            WHERE p.retired = FALSE
              AND p.team_id != 'free_agent'
              AND f.week_number = $1
              AND f.played = FALSE
        """, current_week)
    
    for player_info in players_with_matches:
        try:
            user = await bot.fetch_user(player_info['user_id'])
            
            comp_name = "🏆 Champions League" if player_info['competition'] == 'CL' else "🏆 Europa League"
            
            stage_info = f"{player_info['stage'].title()}"
            if player_info['leg'] and player_info['leg'] > 1:
                stage_info += f" (Leg {player_info['leg']})"
            
            embed = discord.Embed(
                title=f"⏰ {comp_name} - 1 HOUR WARNING",
                description=f"Your European match starts in **1 hour** (12:00 PM EST)!",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="⚽ Your Match",
                value=f"**{player_info['home_name']}** vs **{player_info['away_name']}**\n"
                      f"{stage_info} • Week {current_week}",
                inline=False
            )
            
            embed.add_field(
                name="🕐 Window (EST)",
                value="**12:00 PM - 2:00 PM EST**\n2 hour window",
                inline=True
            )
            
            embed.add_field(
                name="🎮 Ready to Play",
                value="`/play_match` when window opens",
                inline=True
            )
            
            embed.set_footer(text=f"🏆 {comp_name} • Times shown in EST")
            
            await user.send(embed=embed)
            logger.info(f"  ✅ Sent European 1h warning to {player_info['player_name']}")
        except Exception as e:
            logger.warning(f"  ⚠️ Could not send warning: {e}")


async def send_european_30m_warning(bot):
    """Send 30m warning for European (11:30 AM)"""
    state = await db.get_game_state()
    current_week = state['current_week']
    
    if current_week not in config.EUROPEAN_MATCH_WEEKS:
        return
    
    logger.info("📢 Sending European 30m warning...")
    
    async with db.pool.acquire() as conn:
        players_with_matches = await conn.fetch("""
            SELECT DISTINCT p.user_id, p.player_name,
                   f.competition,
                   COALESCE(ht.team_name, eht.team_name) as home_name,
                   COALESCE(at.team_name, eat.team_name) as away_name
            FROM players p
            JOIN teams t ON p.team_id = t.team_id
            JOIN european_fixtures f ON (f.home_team_id = p.team_id OR f.away_team_id = p.team_id)
            LEFT JOIN teams ht ON f.home_team_id = ht.team_id
            LEFT JOIN teams at ON f.away_team_id = at.team_id
            LEFT JOIN european_teams eht ON f.home_team_id = eht.team_id
            LEFT JOIN european_teams eat ON f.away_team_id = eat.team_id
            WHERE p.retired = FALSE
              AND p.team_id != 'free_agent'
              AND f.week_number = $1
              AND f.played = FALSE
        """, current_week)

    for player_info in players_with_matches:
        try:
            user = await bot.fetch_user(player_info['user_id'])
            
            comp_name = "🏆 Champions League" if player_info['competition'] == 'CL' else "🏆 Europa League"
            
            embed = discord.Embed(
                title=f"🚨 {comp_name} - 15 MINUTES!",
                description=f"European window opens in **15 minutes**!",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="⚽ Your Match",
                value=f"**{player_info['home_name']}** vs **{player_info['away_name']}**",
                inline=False
            )
            
            embed.add_field(
                name="⏰ Final Reminder",
                value="Be ready at **12:00 PM EST**!",
                inline=False
            )
            
            embed.set_footer(text=f"🏆 {comp_name} • Big European night!")
            
            await user.send(embed=embed)
            logger.info(f"  ✅ Sent European 15m warning to {player_info['player_name']}")
        except Exception as e:
            logger.warning(f"  ⚠️ Could not send warning: {e}")


async def send_1h_warning(bot):
    """Send 1 hour warning for domestic (2 PM)"""
    state = await db.get_game_state()
    current_week = state['current_week']
    
    logger.info("📢 Sending domestic 1h warning...")
    
    async with db.pool.acquire() as conn:
        players_with_matches = await conn.fetch("""
            SELECT DISTINCT p.user_id, p.player_name, p.team_id, t.team_name,
                   f.home_team_id, f.away_team_id,
                   ht.team_name as home_name,
                   at.team_name as away_name
            FROM players p
            JOIN teams t ON p.team_id = t.team_id
            JOIN fixtures f ON (f.home_team_id = p.team_id OR f.away_team_id = p.team_id)
            JOIN teams ht ON f.home_team_id = ht.team_id
            JOIN teams at ON f.away_team_id = at.team_id
            WHERE p.retired = FALSE
              AND p.team_id != 'free_agent'
              AND f.week_number = $1
              AND f.played = FALSE
        """, current_week)
    
    for player_info in players_with_matches:
        try:
            user = await bot.fetch_user(player_info['user_id'])
            
            embed = discord.Embed(
                title="⏰ LEAGUE MATCH - 1 HOUR WARNING",
                description=f"Your league match starts in **1 hour** (3:00 PM EST)!",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="⚽ Your Match",
                value=f"**{player_info['home_name']}** vs **{player_info['away_name']}**\n"
                      f"Week {current_week}",
                inline=False
            )
            
            embed.add_field(
                name="🕐 Window (EST)",
                value="**3:00 PM - 5:00 PM EST**\n2 hour window",
                inline=True
            )
            
            embed.add_field(
                name="🎮 Ready to Play",
                value="`/play_match` when window opens",
                inline=True
            )
            
            embed.set_footer(text=f"⚽ League Match • Week {current_week}")
            
            await user.send(embed=embed)
            logger.info(f"  ✅ Sent domestic 1h warning to {player_info['player_name']}")
        except Exception as e:
            logger.warning(f"  ⚠️ Could not send warning: {e}")


async def send_30m_warning(bot):
    """Send 30 minute warning for domestic (2:30 PM)"""
    state = await db.get_game_state()
    current_week = state['current_week']
    
    logger.info("📢 Sending domestic 30m warning...")
    
    async with db.pool.acquire() as conn:
        players_with_matches = await conn.fetch("""
            SELECT DISTINCT p.user_id, p.player_name,
                   ht.team_name as home_name,
                   at.team_name as away_name
            FROM players p
            JOIN teams t ON p.team_id = t.team_id
            JOIN fixtures f ON (f.home_team_id = p.team_id OR f.away_team_id = p.team_id)
            JOIN teams ht ON f.home_team_id = ht.team_id
            JOIN teams at ON f.away_team_id = at.team_id
            WHERE p.retired = FALSE
              AND p.team_id != 'free_agent'
              AND f.week_number = $1
              AND f.played = FALSE
        """, current_week)
    
    for player_info in players_with_matches:
        try:
            user = await bot.fetch_user(player_info['user_id'])
            
            embed = discord.Embed(
                title="⏰ LEAGUE MATCH - 30 MINUTES!",
                description=f"Your league match window opens in **30 minutes**!",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="⚽ Match",
                value=f"**{player_info['home_name']}** vs **{player_info['away_name']}**",
                inline=False
            )
            
            embed.add_field(
                name="🕐 Opens At (EST)",
                value="**3:00 PM EST**",
                inline=True
            )
            
            embed.set_footer(text="⚽ Get ready!")
            
            await user.send(embed=embed)
            logger.info(f"  ✅ Sent domestic 30m warning to {player_info['player_name']}")
        except Exception as e:
            logger.warning(f"  ⚠️ Could not send warning: {e}")


async def send_15m_warning(bot):
    """Send 15 minute warning for domestic (2:45 PM)"""
    state = await db.get_game_state()
    current_week = state['current_week']
    
    logger.info("📢 Sending domestic 15m warning...")
    
    async with db.pool.acquire() as conn:
        players_with_matches = await conn.fetch("""
            SELECT DISTINCT p.user_id, p.player_name,
                   ht.team_name as home_name,
                   at.team_name as away_name
            FROM players p
            JOIN teams t ON p.team_id = t.team_id
            JOIN fixtures f ON (f.home_team_id = p.team_id OR f.away_team_id = p.team_id)
            JOIN teams ht ON f.home_team_id = ht.team_id
            JOIN teams at ON f.away_team_id = at.team_id
            WHERE p.retired = FALSE
              AND p.team_id != 'free_agent'
              AND f.week_number = $1
              AND f.played = FALSE
        """, current_week)
    
    for player_info in players_with_matches:
        try:
            user = await bot.fetch_user(player_info['user_id'])
            
            embed = discord.Embed(
                title="🚨 LEAGUE MATCH - 15 MINUTES!",
                description=f"Window opens in **15 minutes**!",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="⚽ Your Match",
                value=f"**{player_info['home_name']}** vs **{player_info['away_name']}**",
                inline=False
            )
            
            embed.add_field(
                name="⏰ Final Reminder",
                value="Be ready at **3:00 PM EST**!",
                inline=False
            )
            
            embed.set_footer(text="⚽ Almost time!")
            
            await user.send(embed=embed)
            logger.info(f"  ✅ Sent domestic 15m warning to {player_info['player_name']}")
        except Exception as e:
            logger.warning(f"  ⚠️ Could not send warning: {e}")


async def send_closing_warning(bot):
    """Send closing warning (4:45 PM)"""
    state = await db.get_game_state()
    current_week = state['current_week']
    
    logger.info("📢 Sending closing warning...")
    
    async with db.pool.acquire() as conn:
        players_with_matches = await conn.fetch("""
            SELECT DISTINCT p.user_id, p.player_name
            FROM players p
            JOIN fixtures f ON (f.home_team_id = p.team_id OR f.away_team_id = p.team_id)
            WHERE p.retired = FALSE
              AND p.team_id != 'free_agent'
              AND f.week_number = $1
              AND f.played = FALSE
        """, current_week)
    
    for player_info in players_with_matches:
        try:
            user = await bot.fetch_user(player_info['user_id'])
            
            embed = discord.Embed(
                title="🚨 WINDOW CLOSING - 15 MINUTES!",
                description=f"**Last chance to play your match!**",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="⏰ Time Left",
                value="**15 minutes** until window closes!",
                inline=False
            )
            
            embed.add_field(
                name="⚡ Action Required",
                value="Use `/play_match` NOW or your match will be simulated!",
                inline=False
            )
            
            embed.set_footer(text="⏰ Window closes at 5:00 PM EST!")
            
            await user.send(embed=embed)
            logger.info(f"  ✅ Sent closing warning to {player_info['player_name']}")
        except Exception as e:
            logger.warning(f"  ⚠️ Could not send warning: {e}")
                   COALESCE(at.team_name, eat.team_name) as away_name
            FROM players p
            JOIN teams t ON p.team_id = t.team_id
            JOIN european_fixtures f ON (f.home_team_id = p.team_id OR f.away_team_id = p.team_id)
            LEFT JOIN teams ht ON f.home_team_id = ht.team_id
            LEFT JOIN teams at ON f.away_team_id = at.team_id
            LEFT JOIN european_teams eht ON f.home_team_id = eht.team_id
            LEFT JOIN european_teams eat ON f.away_team_id = eat.team_id
            WHERE p.retired = FALSE
              AND p.team_id != 'free_agent'
              AND f.week_number = $1
              AND f.played = FALSE
        """, current_week)
    
    for player_info in players_with_matches:
        try:
            user = await bot.fetch_user(player_info['user_id'])
            
            comp_name = "🏆 Champions League" if player_info['competition'] == 'CL' else "🏆 Europa League"
            
            embed = discord.Embed(
                title=f"⏰ {comp_name} - 30 MINUTES!",
                description=f"Your European match window opens in **30 minutes**!",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="⚽ Match",
                value=f"**{player_info['home_name']}** vs **{player_info['away_name']}**",
                inline=False
            )
            
            embed.add_field(
                name="🕐 Opens At (EST)",
                value="**12:00 PM EST** (Noon)",
                inline=True
            )
            
            embed.set_footer(text=f"🏆 {comp_name}")
            
            await user.send(embed=embed)
            logger.info(f"  ✅ Sent European 30m warning to {player_info['player_name']}")
        except Exception as e:
            logger.warning(f"  ⚠️ Could not send warning: {e}")


async def send_european_15m_warning(bot):
    """Send 15m warning for European (11:45 AM)"""
    state = await db.get_game_state()
    current_week = state['current_week']
    
    if current_week not in config.EUROPEAN_MATCH_WEEKS:
        return
    
    logger.info("📢 Sending European 15m warning...")
    
    async with db.pool.acquire() as conn:
        players_with_matches = await conn.fetch("""
            SELECT DISTINCT p.user_id, p.player_name,
                   f.competition,
                   COALESCE(ht.team_name, eht.team_name) as home_name,
