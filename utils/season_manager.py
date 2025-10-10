"""
SIMPLIFIED Season Manager - Fixed Schedule System
Match windows: Mon/Wed/Sat 3-5 PM EST
WITH AUTOMATIC TRANSFER OFFER GENERATION
"""
import discord
from database import db
from datetime import datetime, timedelta
import pytz
import config

# Timezone setup
EST = pytz.timezone('America/New_York')

# Fixed schedule
MATCH_DAYS = [0, 2, 5]  # Monday=0, Wednesday=2, Saturday=5
MATCH_START_HOUR = 15  # 3 PM
MATCH_END_HOUR = 17    # 5 PM

def is_match_window_time():
    """
    Simple check: Is it Mon/Wed/Sat between 3-5 PM EST?
    Returns: (is_window_time, is_start_time, is_end_time)
    """
    now = datetime.now(EST)
    
    # Check if it's a match day
    is_match_day = now.weekday() in MATCH_DAYS
    
    # Check if it's within match hours
    is_match_hours = MATCH_START_HOUR <= now.hour < MATCH_END_HOUR
    
    # Check if it's exactly start time (within 5 min window for opening)
    is_start = (now.hour == MATCH_START_HOUR and now.minute < 5)
    
    # Check if it's exactly end time (within 5 min window for closing)
    is_end = (now.hour == MATCH_END_HOUR and now.minute < 5)
    
    return (is_match_day and is_match_hours), is_start, is_end


def get_next_match_window():
    """
    Get next match window time (for display purposes)
    Returns: datetime of next Mon/Wed/Sat 3 PM EST
    """
    now = datetime.now(EST)
    
    # Find next match day
    current_day = now.weekday()
    days_ahead = None
    
    for match_day in MATCH_DAYS:
        days_until = (match_day - current_day) % 7
        
        # If it's today but before 3 PM, use today
        if days_until == 0 and now.hour < MATCH_START_HOUR:
            days_ahead = 0
            break
        # If it's a future day this week
        elif days_until > 0:
            if days_ahead is None or days_until < days_ahead:
                days_ahead = days_until
    
    # If no day found, use next week's first match day
    if days_ahead is None:
        days_ahead = (MATCH_DAYS[0] - current_day) % 7
        if days_ahead == 0:
            days_ahead = 7
    
    next_match = now + timedelta(days=days_ahead)
    next_match = next_match.replace(hour=MATCH_START_HOUR, minute=0, second=0, microsecond=0)
    
    return next_match


def should_send_warning(warning_type):
    """
    Check if we should send a warning right now
    warning_type: 'pre_1h', 'pre_30m', 'pre_15m', 'closing_soon'
    Returns: True if we should send this warning now
    """
    now = datetime.now(EST)
    
    # Only send warnings on match days
    if now.weekday() not in MATCH_DAYS:
        return False
    
    if warning_type == 'pre_1h':
        # 2:00-2:05 PM (1 hour before)
        return now.hour == 14 and now.minute < 5
    
    elif warning_type == 'pre_30m':
        # 2:30-2:35 PM (30 min before)
        return now.hour == 14 and 30 <= now.minute < 35
    
    elif warning_type == 'pre_15m':
        # 2:45-2:50 PM (15 min before)
        return now.hour == 14 and 45 <= now.minute < 50
    
    elif warning_type == 'closing_soon':
        # 4:45-4:50 PM (15 min before close)
        return now.hour == 16 and 45 <= now.minute < 50
    
    return False


async def start_season():
    """Start the season - simplified"""
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
    
    # Generate fixtures for all teams
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
    """Open the match window - no date calculations needed"""
    state = await db.get_game_state()
    current_week = state['current_week']
    
    # Make this week's fixtures playable
    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE fixtures SET playable = TRUE WHERE week_number = $1 AND played = FALSE",
            current_week
        )
    
    await db.update_game_state(match_window_open=True)
    
    print(f"✅ Match window OPENED for Week {current_week}")
    print(f"   Time: {datetime.now(EST).strftime('%A %I:%M %p EST')}")
    return True


async def close_match_window(bot=None):
    """Close match window and simulate unplayed matches"""
    state = await db.get_game_state()
    current_week = state['current_week']
    
    # Simulate all unplayed matches
    async with db.pool.acquire() as conn:
        unplayed = await conn.fetch(
            """SELECT * FROM fixtures 
               WHERE week_number = $1 AND played = FALSE AND playable = TRUE""",
            current_week
        )
    
    from utils.match_simulator import simulate_match
    
    simulated_count = 0
    for fixture in unplayed:
        await simulate_match(dict(fixture))
        simulated_count += 1
    
    if simulated_count > 0:
        print(f"⚽ Simulated {simulated_count} unplayed matches")
    
    # Close window
    await db.update_game_state(match_window_open=False)
    
    print(f"✅ Match window CLOSED for Week {current_week}")
    print(f"   Time: {datetime.now(EST).strftime('%A %I:%M %p EST')}")
    
    # Advance to next week
    await advance_week(bot=bot)


async def advance_week(bot=None):
    """
    Advance to next week - WITH AUTOMATIC TRANSFER GENERATION
    NOTE: bot parameter added to pass to transfer functions
    """
    state = await db.get_game_state()
    current_week = state['current_week']
    next_week = current_week + 1
    
    # Check if season ended
    if next_week > config.SEASON_TOTAL_WEEKS:
        await end_season()
        return
    
    # Update week
    await db.update_game_state(current_week=next_week)
    
    # ============================================
    # 🔥 TRANSFER WINDOW MANAGEMENT
    # ============================================
    
    # Check if transfer window should OPEN
    if next_week in config.TRANSFER_WINDOW_WEEKS:
        await open_transfer_window()
        
        # 🎯 GENERATE TRANSFER OFFERS FOR ALL PLAYERS
        from utils.transfer_window_manager import process_weekly_transfer_offers
        try:
            offers_generated = await process_weekly_transfer_offers(bot=bot)
            print(f"💼 Generated {offers_generated} transfer offers for players")
        except Exception as e:
            print(f"⚠️ Could not generate transfer offers: {e}")
            import traceback
            traceback.print_exc()
    
    # Check if transfer window should CLOSE
    elif current_week in config.TRANSFER_WINDOW_WEEKS and next_week not in config.TRANSFER_WINDOW_WEEKS:
        await close_transfer_window()
    
    # If we're IN a transfer window (but not opening/closing), still generate offers
    elif next_week in config.TRANSFER_WINDOW_WEEKS:
        # Generate weekly offers during active transfer windows
        from utils.transfer_window_manager import generate_offers_for_eligible_players
        try:
            offers_generated = await generate_offers_for_eligible_players(bot=bot)
            if offers_generated > 0:
                print(f"💼 Generated {offers_generated} new transfer offers (ongoing window)")
        except Exception as e:
            print(f"⚠️ Could not generate transfer offers: {e}")
    
    # ============================================
    # END TRANSFER WINDOW MANAGEMENT
    # ============================================
    
    print(f"📅 Advanced to Week {next_week}")
    next_window = get_next_match_window()
    print(f"   Next match: {next_window.strftime('%A, %B %d at %I:%M %p EST')}")


async def open_transfer_window():
    """Open transfer window"""
    await db.update_game_state(transfer_window_active=True)
    print("💼 Transfer window OPENED")


async def close_transfer_window():
    """Close transfer window and trigger NPC transfers"""
    
    # ============================================
    # 🔥 SIMULATE NPC TRANSFERS
    # ============================================
    from utils.transfer_window_manager import simulate_npc_transfers
    try:
        npc_transfers = await simulate_npc_transfers()
        print(f"💼 {npc_transfers} NPC transfers completed")
    except Exception as e:
        print(f"⚠️ Could not simulate NPC transfers: {e}")
        import traceback
        traceback.print_exc()
    
    # ============================================
    
    await db.update_game_state(transfer_window_active=False)
    
    # Expire all pending offers
    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE transfer_offers SET status = 'expired' WHERE status = 'pending'"
        )
    
    print("💼 Transfer window CLOSED")


async def end_season():
    """End the season"""
    state = await db.get_game_state()
    current_season = state['current_season']
    
    print(f"🏆 Season {current_season} complete!")
    
    # Age all players
    await db.age_all_players()
    
    # Retire old players
    retired_count = await db.retire_old_players()
    print(f"👴 {retired_count} players retired")
    
    # Reset season stats
    async with db.pool.acquire() as conn:
        await conn.execute("""
            UPDATE players SET 
            season_goals = 0, season_assists = 0, 
            season_apps = 0, season_rating = 0.0, season_motm = 0
        """)
        
        await conn.execute("""
            UPDATE npc_players SET 
            season_goals = 0, season_assists = 0, season_apps = 0
        """)
        
        await conn.execute("""
            UPDATE teams SET 
            played = 0, won = 0, drawn = 0, lost = 0,
            goals_for = 0, goals_against = 0, points = 0, form = ''
        """)
    
    # Start new season
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
# WARNING FUNCTIONS - Called by bot.py
# ============================================

async def send_1h_warning(bot):
    """Send 1 hour warning to all servers"""
    state = await db.get_game_state()
    
    if state['match_window_open']:
        return  # Already open, no warning needed
    
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
        return  # Already open
    
    async with db.pool.acquire() as conn:
        players = await conn.fetch("""
            SELECT user_id, player_name 
            FROM players 
            WHERE retired = FALSE AND team_id != 'free_agent'
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
        return  # Already open
    
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
        return  # Not open
    
    # Find players who haven't played
    async with db.pool.acquire() as conn:
        all_players = await conn.fetch("""
            SELECT user_id, player_name
            FROM players
            WHERE retired = FALSE AND team_id != 'free_agent'
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
