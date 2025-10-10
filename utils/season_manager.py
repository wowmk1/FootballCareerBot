import discord
from database import db
from datetime import datetime, timedelta
import config
import random

async def start_season():
    """Start the season and schedule first match"""
    state = await db.get_game_state()
    
    if state['season_started']:
        print("⚠️ Season already started")
        return False
    
    # Find next Mon/Wed/Sat at 3 PM
    now = datetime.now()
    
    # Days of week: 0=Mon, 2=Wed, 5=Sat
    target_days = [0, 2, 5]
    
    # Find next match day
    days_ahead = None
    for target_day in target_days:
        days_until = (target_day - now.weekday()) % 7
        if days_until == 0:  # Today
            if now.hour < config.MATCH_START_HOUR:
                days_ahead = 0
                break
        elif days_ahead is None or days_until < days_ahead:
            days_ahead = days_until
    
    if days_ahead is None:
        days_ahead = (target_days[0] - now.weekday()) % 7
    
    first_match_day = now + timedelta(days=days_ahead)
    first_match_day = first_match_day.replace(
        hour=config.MATCH_START_HOUR,
        minute=0,
        second=0,
        microsecond=0
    )
    
    await db.update_game_state(
        season_started=True,
        current_week=1,
        current_season='2027/28',
        season_start_date=now.isoformat(),
        next_match_day=first_match_day.isoformat(),
        current_match_of_week=0
    )
    
    # Generate fixtures for all teams
    await generate_season_fixtures()
    
    print(f"✅ Season started! First match: {first_match_day.strftime('%A, %B %d at %I:%M %p')}")
    return True


async def generate_season_fixtures():
    """Generate fixtures for all leagues"""
    from utils.fixture_generator import generate_league_fixtures
    
    leagues = ['Premier League', 'Championship', 'League One']
    
    for league in leagues:
        teams = await db.get_league_table(league)
        team_ids = [t['team_id'] for t in teams]
        
        await generate_league_fixtures(
            team_ids=team_ids,
            league=league,
            season='2027/28',
            total_weeks=config.SEASON_TOTAL_WEEKS
        )
    
    await db.update_game_state(fixtures_generated=True)
    print(f"✅ Generated {config.SEASON_TOTAL_WEEKS} weeks of fixtures for all leagues")


async def open_match_window():
    """Open the match window for current week"""
    state = await db.get_game_state()
    current_week = state['current_week']
    
    # Make this week's fixtures playable
    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE fixtures SET playable = TRUE WHERE week_number = $1 AND played = FALSE",
            current_week
        )
    
    # Set closing time
    closes = datetime.now() + timedelta(hours=config.MATCH_WINDOW_HOURS)
    
    await db.update_game_state(
        match_window_open=True,
        match_window_closes=closes.isoformat()
    )
    
    print(f"✅ Match window opened for Week {current_week}")
    print(f"   Closes at: {closes.strftime('%I:%M %p')}")


async def close_match_window():
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
    
    for fixture in unplayed:
        await simulate_match(dict(fixture))
    
    if unplayed:
        print(f"⚽ Simulated {len(unplayed)} unplayed matches")
    
    # Close window
    await db.update_game_state(
        match_window_open=False,
        match_window_closes=None
    )
    
    # Advance to next week
    await advance_week()
    
    print(f"✅ Match window closed for Week {current_week}")


async def advance_week():
    """Advance to next week and schedule next match"""
    state = await db.get_game_state()
    current_week = state['current_week']
    next_week = current_week + 1
    
    # Check if season ended
    if next_week > config.SEASON_TOTAL_WEEKS:
        await end_season()
        return

# Calculate next match day (Mon/Wed/Sat at 3 PM)
    now = datetime.now()
    target_days = [0, 2, 5]  # Mon, Wed, Sat
    current_match = state.get('current_match_of_week', 0)
    
    # Cycle through match days
    next_match_index = (current_match + 1) % len(target_days)
    target_day = target_days[next_match_index]
    
    # Calculate days until next target day
    days_until = (target_day - now.weekday()) % 7
    if days_until == 0:
        days_until = 7  # If today, schedule for next week
    
    next_match_day = now + timedelta(days=days_until)
    next_match_day = next_match_day.replace(
        hour=config.MATCH_START_HOUR,
        minute=0,
        second=0,
        microsecond=0
    )
    
    # Update game state
    await db.update_game_state(
        current_week=next_week,
        next_match_day=next_match_day.isoformat(),
        current_match_of_week=next_match_index
    )
    
    # Check if transfer window should open
    if next_week in config.TRANSFER_WINDOW_WEEKS:
        await open_transfer_window()
    
    # Check if transfer window should close
    if current_week in config.TRANSFER_WINDOW_WEEKS and next_week not in config.TRANSFER_WINDOW_WEEKS:
        await close_transfer_window()
    
    print(f"📅 Advanced to Week {next_week}")
    print(f"   Next match: {next_match_day.strftime('%A, %B %d at %I:%M %p')}")


async def check_match_day_trigger(bot=None):
    """Check if it's time to open or close match windows - with time tolerance"""
    state = await db.get_game_state()
    
    if not state['season_started']:
        return False
    
    now = datetime.now()
    triggered = False
    
    # ============================================
    # CHECK IF WE SHOULD OPEN MATCH WINDOW
    # ============================================
    if state['next_match_day'] and not state['match_window_open']:
        next_match = datetime.fromisoformat(state['next_match_day'])
        
        # Use time range instead of exact match (within 15 min after scheduled time)
        time_diff = (now - next_match).total_seconds()
        
        if 0 <= time_diff <= 900:  # 0 to 15 minutes after scheduled time
            print(f"⚽ Opening match window (scheduled: {next_match}, now: {now})")
            await open_match_window()
            
            if bot:
                await bot.notify_match_window_open()
            
            triggered = True
    
    # ============================================
    # CHECK IF WE SHOULD SEND CLOSING WARNING
    # ============================================
    if state['match_window_open'] and state['match_window_closes']:
        closes = datetime.fromisoformat(state['match_window_closes'])
        time_until_close = (closes - now).total_seconds()
        
        # Send warning 15 minutes before close (check if within 14-16 min window)
        if 840 <= time_until_close <= 960:  # 14-16 minutes before closing
            await send_closing_warning(bot)
    
    # ============================================
    # CHECK IF WE SHOULD CLOSE MATCH WINDOW
    # ============================================
    if state['match_window_open'] and state['match_window_closes']:
        closes = datetime.fromisoformat(state['match_window_closes'])
        
        # Use time range instead of exact match (within 15 min after closing time)
        time_diff = (now - closes).total_seconds()
        
        if 0 <= time_diff <= 900:  # 0 to 15 minutes after closing time
            print(f"⏰ Closing match window (scheduled: {closes}, now: {now})")
            await close_match_window()
            triggered = True
    
    return triggered


async def send_closing_warning(bot=None):
    """Warn players who haven't played 15min before close"""
    if not bot:
        return
        
    state = await db.get_game_state()
    current_week = state['current_week']
    
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
    
    from datetime import datetime
    closes = datetime.fromisoformat(state['match_window_closes'])
    timestamp = int(closes.timestamp())
    
    warned = 0
    for player in all_players:
        if player['user_id'] not in played_ids:
            try:
                user = await bot.fetch_user(player['user_id'])
                
                embed = discord.Embed(
                    title="⚠️ Match Window Closing Soon!",
                    description=f"**You haven't played your Week {current_week} match!**\n\n"
                               f"Window closes in **15 minutes**!",
                    color=discord.Color.red()
                )
                
                embed.add_field(
                    name="⏰ Closes At",
                    value=f"<t:{timestamp}:t> (<t:{timestamp}:R>)",
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
        print(f"⚠️ Sent closing warnings to {warned} players who haven't played")


async def open_transfer_window():
    """Open transfer window"""
    await db.update_game_state(transfer_window_active=True)
    print("💼 Transfer window opened")


async def close_transfer_window():
    """Close transfer window"""
    await db.update_game_state(transfer_window_active=False)
    
    # Expire all pending offers
    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE transfer_offers SET status = 'expired' WHERE status = 'pending'"
        )
    
    print("💼 Transfer window closed")


async def end_season():
    """End the season and handle promotion/relegation"""
    state = await db.get_game_state()
    current_season = state['current_season']
    
    print(f"🏆 Season {current_season} complete!")
    
    # Handle promotion/relegation
    await handle_promotion_relegation()
    
    # Age all players
    await db.age_all_players()
    
    # Retire old players
    retired_count = await db.retire_old_players()
    
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


async def handle_promotion_relegation():
    """Handle promotion and relegation between leagues"""
    
    # Premier League: Bottom 3 relegated
    pl_table = await db.get_league_table('Premier League')
    relegated_from_pl = [pl_table[-3]['team_id'], pl_table[-2]['team_id'], pl_table[-1]['team_id']]
    
    # Championship: Top 2 promoted, 3rd-6th playoff (auto-promote top 3 for simplicity)
    champ_table = await db.get_league_table('Championship')
    promoted_from_champ = [champ_table[0]['team_id'], champ_table[1]['team_id'], champ_table[2]['team_id']]
    relegated_from_champ = [champ_table[-3]['team_id'], champ_table[-2]['team_id'], champ_table[-1]['team_id']]
    
    # League One: Top 3 promoted
    l1_table = await db.get_league_table('League One')
    promoted_from_l1 = [l1_table[0]['team_id'], l1_table[1]['team_id'], l1_table[2]['team_id']]
    
    # Apply changes
    async with db.pool.acquire() as conn:
        for team_id in relegated_from_pl:
            await conn.execute("UPDATE teams SET league = 'Championship' WHERE team_id = $1", team_id)
            await conn.execute("UPDATE npc_players SET team_id = $1 WHERE team_id = $1", team_id)
            print(f"   ⬇️ {team_id} relegated to Championship")
        
        for team_id in promoted_from_champ:
            await conn.execute("UPDATE teams SET league = 'Premier League' WHERE team_id = $1", team_id)
            await conn.execute("UPDATE npc_players SET team_id = $1 WHERE team_id = $1", team_id)
            print(f"   ⬆️ {team_id} promoted to Premier League")
        
        for team_id in relegated_from_champ:
            await conn.execute("UPDATE teams SET league = 'League One' WHERE team_id = $1", team_id)
            await conn.execute("UPDATE npc_players SET team_id = $1 WHERE team_id = $1", team_id)
            print(f"   ⬇️ {team_id} relegated to League One")
        
        for team_id in promoted_from_l1:
            await conn.execute("UPDATE teams SET league = 'Championship' WHERE team_id = $1", team_id)
            await conn.execute("UPDATE npc_players SET team_id = $1 WHERE team_id = $1", team_id)
            print(f"   ⬆️ {team_id} promoted to Championship")
    
    print("✅ Promotion/relegation complete")
