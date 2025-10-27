"""
Season Management - Two Windows on Same Days
12-2 PM EST: European (CL+EL) on European weeks
3-5 PM EST: Domestic (always) - advances week after close

✅ FIXED: Proper timezone handling and end detection
✅ FIXED: Window closes at EXACT time (2:00 PM, 5:00 PM)
✅ FIXED: European window only shows on actual European weeks
✅ FIXED: Prevents duplicate window closes
✅ FIXED: Notification happens BEFORE week advances (correct week numbers)
"""
import asyncio
from datetime import datetime, timedelta, timezone
from database import db
import config
import logging
import discord

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

EST = ZoneInfo('America/New_York')
MATCH_DAYS = [0, 2, 5]
EUROPEAN_START_HOUR = 12
EUROPEAN_END_HOUR = 14
DOMESTIC_START_HOUR = 15
DOMESTIC_END_HOUR = 17


def get_current_time_est():
    return datetime.now(EST)


def is_match_window_time(current_week=None):
    """
    Check if we're in a match window
    
    Args:
        current_week: Current game week (required to detect European weeks)
    
    Returns:
        (is_window_time, is_start, is_end, window_type)
    """
    now = get_current_time_est()
    current_day = now.weekday()
    current_hour = now.hour
    current_minute = now.minute
    
    logger.info(f"Window check: {now.strftime('%A %I:%M %p EST')} (hour={current_hour}, min={current_minute})")
    
    if current_day not in MATCH_DAYS:
        return False, False, False, None
    
    # ✅ FIXED: Check European window time (12-2 PM) ONLY if it's a European week
    if EUROPEAN_START_HOUR <= current_hour < EUROPEAN_END_HOUR:
        is_start = (current_hour == EUROPEAN_START_HOUR and current_minute < 5)
        # Only return 'european' if current week is in EUROPEAN_MATCH_WEEKS
        if current_week and current_week in config.EUROPEAN_MATCH_WEEKS:
            logger.info(f"  Inside European window (is_start={is_start})")
            return True, is_start, False, 'european'
        else:
            # It's 12-2 PM but NOT a European week - no window open
            logger.info(f"  12-2 PM time but NOT a European week - no window")
            return False, False, False, None
    
    if current_hour == EUROPEAN_END_HOUR and current_minute < 5:
        # Only close European window if it's actually a European week
        if current_week and current_week in config.EUROPEAN_MATCH_WEEKS:
            logger.info(f"  European window CLOSING TIME")
            return False, False, True, 'european'
        else:
            return False, False, False, None
    
    if DOMESTIC_START_HOUR <= current_hour < DOMESTIC_END_HOUR:
        is_start = (current_hour == DOMESTIC_START_HOUR and current_minute < 5)
        logger.info(f"  Inside Domestic window (is_start={is_start})")
        return True, is_start, False, 'domestic'
    
    if current_hour == DOMESTIC_END_HOUR and current_minute < 5:
        logger.info(f"  Domestic window CLOSING TIME")
        return False, False, True, 'domestic'
    
    return False, False, False, None


def should_send_warning(warning_type, current_week=None):
    """
    Check if we should send a warning
    
    Args:
        warning_type: Type of warning to check
        current_week: Current game week (required for European warnings)
    """
    now = get_current_time_est()
    current_day = now.weekday()
    current_hour = now.hour
    current_minute = now.minute
    
    if current_day not in MATCH_DAYS:
        return False
    
    # European warnings - only if it's a European week
    if warning_type.startswith('european_'):
        if not current_week or current_week not in config.EUROPEAN_MATCH_WEEKS:
            return False
    
    if warning_type == 'european_1h':
        return current_hour == 11 and current_minute < 5
    elif warning_type == 'european_30m':
        return current_hour == 11 and 30 <= current_minute < 35
    elif warning_type == 'european_15m':
        return current_hour == 11 and 45 <= current_minute < 50
    elif warning_type == 'domestic_1h':
        return current_hour == 14 and current_minute < 5
    elif warning_type == 'domestic_30m':
        return current_hour == 14 and 30 <= current_minute < 35
    elif warning_type == 'domestic_15m':
        return current_hour == 14 and 45 <= current_minute < 50
    elif warning_type == 'domestic_closing':
        return current_hour == 16 and 45 <= current_minute < 50
    
    return False


def get_next_match_window():
    now = get_current_time_est()
    
    for days_ahead in range(8):
        check_date = now + timedelta(days=days_ahead)
        
        if check_date.weekday() in MATCH_DAYS:
            european_time = check_date.replace(hour=EUROPEAN_START_HOUR, minute=0, second=0, microsecond=0)
            if european_time > now:
                return european_time
            
            domestic_time = check_date.replace(hour=DOMESTIC_START_HOUR, minute=0, second=0, microsecond=0)
            if domestic_time > now:
                return domestic_time
    
    days_until_monday = (7 - now.weekday()) % 7 or 7
    next_monday = now + timedelta(days=days_until_monday)
    return next_monday.replace(hour=EUROPEAN_START_HOUR, minute=0, second=0, microsecond=0)


def format_time_for_user(dt_est, user_timezone=None):
    if user_timezone:
        try:
            user_tz = ZoneInfo(user_timezone)
            dt_user = dt_est.astimezone(user_tz)
            return dt_user.strftime('%I:%M %p %Z')
        except:
            pass
    return dt_est.strftime('%I:%M %p EST')


async def open_match_window(window_type='domestic'):
    logger.info(f"Opening {window_type} match window...")
    
    async with db.pool.acquire() as conn:
        state = await conn.fetchrow('SELECT * FROM game_state')
        current_week = state['current_week']
        
        if window_type == 'domestic':
            await conn.execute("""
                UPDATE fixtures 
                SET playable = TRUE 
                WHERE week_number = $1 AND played = FALSE
            """, current_week)
            logger.info(f"Domestic fixtures opened for Week {current_week}")
        
        elif window_type == 'european':
            if current_week in config.EUROPEAN_MATCH_WEEKS:
                await conn.execute("""
                    UPDATE european_fixtures 
                    SET playable = TRUE 
                    WHERE week_number = $1 AND played = FALSE
                """, current_week)
                logger.info(f"European fixtures opened for Week {current_week}")
        
        await conn.execute("UPDATE game_state SET match_window_open = TRUE")


async def close_match_window(window_type='domestic', bot=None):
    """
    ✅ FIXED: Now sends notification BEFORE advancing week
    This ensures correct week numbers in the notification
    """
    logger.info(f"CLOSING {window_type} match window...")
    
    async with db.pool.acquire() as conn:
        state = await conn.fetchrow('SELECT * FROM game_state')
        current_week = state['current_week']
        
        # ✅ CRITICAL FIX: Prevent duplicate closes
        if not state['match_window_open']:
            logger.warning(f"⚠️ Window already closed for week {current_week}, skipping duplicate close")
            return []
        
        # ✅ CRITICAL: Mark window as closed IMMEDIATELY to prevent race conditions
        await conn.execute("UPDATE game_state SET match_window_open = FALSE")
        logger.info(f"✅ Window marked as closed in database")
        
        results = []
        
        if window_type == 'domestic':
            # ✅ NEW: Send notification BEFORE simulating matches and advancing week
            # This ensures notification shows correct week numbers
            if bot:
                try:
                    logger.info(f"📢 Sending domestic window closed notification for Week {current_week}")
                    # Import here to avoid circular dependency
                    from bot import FootballBot
                    if isinstance(bot, FootballBot):
                        await bot.notify_domestic_window_closed(current_week)
                        logger.info(f"✅ Notification sent for Week {current_week}")
                except Exception as e:
                    logger.error(f"❌ Error sending notification: {e}")
            
            # Now simulate matches
            unplayed = await conn.fetch("""
                SELECT * FROM fixtures 
                WHERE week_number = $1 AND played = FALSE AND playable = TRUE
            """, current_week)
            
            logger.info(f"Simulating {len(unplayed)} unplayed matches...")
            
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
            
            # Now advance week AFTER notification and match simulation
            logger.info(f"ADVANCING WEEK from {current_week} to {current_week + 1}")
            await advance_week(bot=bot)
        
        elif window_type == 'european':
            if current_week in config.EUROPEAN_MATCH_WEEKS:
                from utils.european_competitions import close_european_window
                await close_european_window(current_week, bot=bot, competition=None)
    
    return results


async def update_team_stats(conn, team_id, goals_for, goals_against):
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


async def add_match_result_news(home_team, away_team, home_score, away_score, category, week_number, competition='League'):
    if home_score > away_score:
        margin = home_score - away_score
        if margin >= 3:
            headline = f"{home_team} Thrash {away_team} {home_score}-{away_score}"
            importance = 7
        else:
            headline = f"{home_team} Beat {away_team} {home_score}-{away_score}"
            importance = 5
        content = f"{home_team} won {home_score}-{away_score} against {away_team}."
    elif away_score > home_score:
        margin = away_score - home_score
        if margin >= 3:
            headline = f"{away_team} Demolish {home_team} {away_score}-{home_score}"
            importance = 7
        else:
            headline = f"{away_team} Win at {home_team} {away_score}-{home_score}"
            importance = 5
        content = f"{away_team} won {away_score}-{home_score} at {home_team}."
    else:
        headline = f"{home_team} {home_score}-{away_score} {away_team}"
        importance = 4
        content = f"{home_team} and {away_team} drew {home_score}-{away_score}."
    
    await db.add_news(headline=headline, content=content, category=category, user_id=None, importance=importance, week_number=week_number)


async def advance_week(bot=None):
    async with db.pool.acquire() as conn:
        state = await conn.fetchrow('SELECT * FROM game_state')
        current_week = state['current_week']
        next_week = current_week + 1
        
        logger.info(f"ADVANCING: Week {current_week} to {next_week}")
        
        if next_week > config.SEASON_TOTAL_WEEKS:
            await end_season(bot=bot)
            return
        
        await conn.execute("UPDATE game_state SET current_week = $1", next_week)
        
        from utils import european_competitions as euro
        
        try:
            if current_week == 18:
                await euro.generate_knockout_draw('CL', 'r16', state['current_season'])
                await euro.generate_knockout_draw('EL', 'r16', state['current_season'])
            elif current_week == 24:
                await euro.close_knockout_round('CL', 'r16', state['current_season'])
                await euro.close_knockout_round('EL', 'r16', state['current_season'])
                await euro.generate_knockout_draw('CL', 'quarters', state['current_season'])
                await euro.generate_knockout_draw('EL', 'quarters', state['current_season'])
            elif current_week == 30:
                await euro.close_knockout_round('CL', 'quarters', state['current_season'])
                await euro.close_knockout_round('EL', 'quarters', state['current_season'])
                await euro.generate_knockout_draw('CL', 'semis', state['current_season'])
                await euro.generate_knockout_draw('EL', 'semis', state['current_season'])
            elif current_week == 36:
                await euro.close_knockout_round('CL', 'semis', state['current_season'])
                await euro.close_knockout_round('EL', 'semis', state['current_season'])
                await euro.generate_knockout_draw('CL', 'final', state['current_season'])
                await euro.generate_knockout_draw('EL', 'final', state['current_season'])
            elif current_week == 38:
                await euro.close_knockout_round('CL', 'final', state['current_season'])
                await euro.close_knockout_round('EL', 'final', state['current_season'])
        except Exception as e:
            logger.error(f"Error in European progression: {e}")
        
        if next_week in config.TRANSFER_WINDOW_WEEKS:
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"🔄 TRANSFER WINDOW ACTIVE - Week {next_week}")
                logger.info(f"{'='*60}")
        
                # ✅ FIXED: Correct import path
                from utils.transfer_window_manager import (
                    process_weekly_transfer_offers, 
                    simulate_npc_transfers
                )
        
                # 1. Generate player transfer offers (human players)
                logger.info("📬 Generating transfer offers for players...")
                await process_weekly_transfer_offers(bot=bot)
        
                # 2. Simulate domestic NPC transfers
                logger.info("🔄 Simulating domestic NPC transfers...")
                await simulate_npc_transfers()
        
                # ✅ NEW: European transfer system
                logger.info("🌍 Processing European transfers...")
                from utils.european_transfer_system import (
                    simulate_european_transfers,
                    simulate_european_to_english_transfers,
                    simulate_english_to_european_transfers
                )
        
                # 3. Inter-European transfers (Real Madrid ↔ Bayern, etc.)
                euro_count = await simulate_european_transfers()
                logger.info(f"  ✅ {euro_count} inter-European transfers")
        
                # 4. European → English transfers (Mbappe → Man City, etc.)
                euro_to_eng = await simulate_european_to_english_transfers()
                logger.info(f"  ✅ {euro_to_eng} European → English transfers")
        
                # 5. English → European transfers (Kane → Bayern, etc.)
                eng_to_euro = await simulate_english_to_european_transfers()
                logger.info(f"  ✅ {eng_to_euro} English → European transfers")
        
                # ✅ BONUS: Balance squad sizes (optional but recommended)
                try:
                    from utils.npc_transfer_system import balance_team_squads
                    balanced = await balance_team_squads()
                    if balanced:
                        logger.info(f"  ⚖️ {balanced} players balanced across squads")
                except Exception as e:
                    logger.warning(f"Squad balancing skipped: {e}")
        
                logger.info(f"{'='*60}")
                logger.info(f"✅ TRANSFER WINDOW COMPLETE")
                logger.info(f"{'='*60}\n")
        
            except Exception as e:
                logger.error(f"❌ CRITICAL: Error in transfer window processing: {e}", exc_info=True)


async def end_season(bot=None):
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
        
        await conn.execute("UPDATE game_state SET current_season = current_season + 1, current_week = 1, match_window_open = FALSE")


async def send_european_1h_warning(bot):
    state = await db.get_game_state()
    current_week = state['current_week']
    
    if current_week not in config.EUROPEAN_MATCH_WEEKS:
        return
    
    async with db.pool.acquire() as conn:
        players = await conn.fetch("""
            SELECT DISTINCT p.user_id, p.player_name,
                   f.competition,
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
            WHERE p.retired = FALSE AND p.team_id != 'free_agent'
              AND f.week_number = $1 AND f.played = FALSE
        """, current_week)
    
    for p in players:
        try:
            user = await bot.fetch_user(p['user_id'])
            comp = "Champions League" if p['competition'] == 'CL' else "Europa League"
            stage = p['stage'].title()
            if p['leg'] and p['leg'] > 1:
                stage += f" (Leg {p['leg']})"
            
            embed = discord.Embed(
                title=f"{comp} - 1 HOUR WARNING",
                description=f"Your European match starts in 1 hour (12:00 PM EST)!",
                color=discord.Color.blue()
            )
            embed.add_field(name="Match", value=f"{p['home_name']} vs {p['away_name']}\n{stage}", inline=False)
            embed.add_field(name="Window", value="12:00 PM - 2:00 PM EST", inline=True)
            await user.send(embed=embed)
        except:
            pass


async def send_european_30m_warning(bot):
    state = await db.get_game_state()
    current_week = state['current_week']
    
    if current_week not in config.EUROPEAN_MATCH_WEEKS:
        return
    
    async with db.pool.acquire() as conn:
        players = await conn.fetch("""
            SELECT DISTINCT p.user_id,
                   COALESCE(ht.team_name, eht.team_name) as home_name,
                   COALESCE(at.team_name, eat.team_name) as away_name
            FROM players p
            JOIN european_fixtures f ON (f.home_team_id = p.team_id OR f.away_team_id = p.team_id)
            LEFT JOIN teams ht ON f.home_team_id = ht.team_id
            LEFT JOIN teams at ON f.away_team_id = at.team_id
            LEFT JOIN european_teams eht ON f.home_team_id = eht.team_id
            LEFT JOIN european_teams eat ON f.away_team_id = eat.team_id
            WHERE p.retired = FALSE AND f.week_number = $1 AND f.played = FALSE
        """, current_week)
    
    for p in players:
        try:
            user = await bot.fetch_user(p['user_id'])
            embed = discord.Embed(title="European Match - 30 MINUTES!", description="Window opens in 30 minutes!", color=discord.Color.orange())
            embed.add_field(name="Match", value=f"{p['home_name']} vs {p['away_name']}", inline=False)
            await user.send(embed=embed)
        except:
            pass


async def send_european_15m_warning(bot):
    state = await db.get_game_state()
    current_week = state['current_week']
    
    if current_week not in config.EUROPEAN_MATCH_WEEKS:
        return
    
    async with db.pool.acquire() as conn:
        players = await conn.fetch("""
            SELECT DISTINCT p.user_id,
                   COALESCE(ht.team_name, eht.team_name) as home_name,
                   COALESCE(at.team_name, eat.team_name) as away_name
            FROM players p
            JOIN european_fixtures f ON (f.home_team_id = p.team_id OR f.away_team_id = p.team_id)
            LEFT JOIN teams ht ON f.home_team_id = ht.team_id
            LEFT JOIN teams at ON f.away_team_id = at.team_id
            LEFT JOIN european_teams eht ON f.home_team_id = eht.team_id
            LEFT JOIN european_teams eat ON f.away_team_id = eat.team_id
            WHERE p.retired = FALSE AND f.week_number = $1 AND f.played = FALSE
        """, current_week)
    
    for p in players:
        try:
            user = await bot.fetch_user(p['user_id'])
            embed = discord.Embed(title="European Match - 15 MINUTES!", description="Be ready at 12:00 PM EST!", color=discord.Color.red())
            await user.send(embed=embed)
        except:
            pass


async def send_1h_warning(bot):
    state = await db.get_game_state()
    current_week = state['current_week']
    
    async with db.pool.acquire() as conn:
        players = await conn.fetch("""
            SELECT DISTINCT p.user_id, ht.team_name as home_name, at.team_name as away_name
            FROM players p
            JOIN fixtures f ON (f.home_team_id = p.team_id OR f.away_team_id = p.team_id)
            JOIN teams ht ON f.home_team_id = ht.team_id
            JOIN teams at ON f.away_team_id = at.team_id
            WHERE p.retired = FALSE AND p.team_id != 'free_agent'
              AND f.week_number = $1 AND f.played = FALSE
        """, current_week)
    
    for p in players:
        try:
            user = await bot.fetch_user(p['user_id'])
            embed = discord.Embed(title="LEAGUE MATCH - 1 HOUR WARNING", description="Your match starts in 1 hour (3:00 PM EST)!", color=discord.Color.orange())
            embed.add_field(name="Match", value=f"{p['home_name']} vs {p['away_name']}", inline=False)
            embed.add_field(name="Window", value="3:00 PM - 5:00 PM EST", inline=True)
            await user.send(embed=embed)
        except:
            pass


async def send_30m_warning(bot):
    state = await db.get_game_state()
    current_week = state['current_week']
    
    async with db.pool.acquire() as conn:
        players = await conn.fetch("""
            SELECT DISTINCT p.user_id, ht.team_name as home_name, at.team_name as away_name
            FROM players p
            JOIN fixtures f ON (f.home_team_id = p.team_id OR f.away_team_id = p.team_id)
            JOIN teams ht ON f.home_team_id = ht.team_id
            JOIN teams at ON f.away_team_id = at.team_id
            WHERE p.retired = FALSE AND f.week_number = $1 AND f.played = FALSE
        """, current_week)
    
    for p in players:
        try:
            user = await bot.fetch_user(p['user_id'])
            embed = discord.Embed(title="LEAGUE MATCH - 30 MINUTES!", description="Window opens in 30 minutes!", color=discord.Color.orange())
            await user.send(embed=embed)
        except:
            pass


async def send_15m_warning(bot):
    state = await db.get_game_state()
    current_week = state['current_week']
    
    async with db.pool.acquire() as conn:
        players = await conn.fetch("""
            SELECT DISTINCT p.user_id
            FROM players p
            JOIN fixtures f ON (f.home_team_id = p.team_id OR f.away_team_id = p.team_id)
            WHERE p.retired = FALSE AND f.week_number = $1 AND f.played = FALSE
        """, current_week)
    
    for p in players:
        try:
            user = await bot.fetch_user(p['user_id'])
            embed = discord.Embed(title="LEAGUE MATCH - 15 MINUTES!", description="Be ready at 3:00 PM EST!", color=discord.Color.red())
            await user.send(embed=embed)
        except:
            pass


async def send_closing_warning(bot):
    state = await db.get_game_state()
    current_week = state['current_week']
    
    async with db.pool.acquire() as conn:
        players = await conn.fetch("""
            SELECT DISTINCT p.user_id
            FROM players p
            JOIN fixtures f ON (f.home_team_id = p.team_id OR f.away_team_id = p.team_id)
            WHERE p.retired = FALSE AND f.week_number = $1 AND f.played = FALSE
        """, current_week)
    
    for p in players:
        try:
            user = await bot.fetch_user(p['user_id'])
            embed = discord.Embed(title="WINDOW CLOSING - 15 MINUTES!", description="Last chance to play!", color=discord.Color.red())
            embed.add_field(name="Action Required", value="Use /play_match NOW or match will be simulated!", inline=False)
            await user.send(embed=embed)
        except:
            pass
