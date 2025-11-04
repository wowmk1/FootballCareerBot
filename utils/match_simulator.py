from database import db
import random

async def simulate_all_matches(week: int):
    """Simulate all matches for a given week across all leagues"""
    
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM fixtures WHERE week_number = $1 AND played = FALSE",
            week
        )
        fixtures = [dict(row) for row in rows]
    
    results = []
    
    for fixture in fixtures:
        result = await simulate_match(fixture)
        results.append(result)
    
    print(f"✅ Simulated {len(results)} matches for Week {week}")
    
    return results

async def simulate_match(fixture: dict):
    """Simulate a single match using actual team strength from player ratings"""
    
    home_team = await db.get_team(fixture['home_team_id'])
    away_team = await db.get_team(fixture['away_team_id'])
    
    # Check for user players
    async with db.pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT COUNT(*) as count FROM players WHERE (team_id = $1 OR team_id = $2) AND retired = FALSE",
            fixture['home_team_id'], fixture['away_team_id']
        )
        has_user_players = result['count'] > 0
    
    # ✅ FIX: Calculate team strength using WEIGHTED average
    home_strength = await calculate_team_strength(fixture['home_team_id'], is_home=True)
    away_strength = await calculate_team_strength(fixture['away_team_id'], is_home=False)
    
    # Simulate match based on strength difference
    home_score, away_score = simulate_score(home_strength, away_strength)
    
    async with db.pool.acquire() as conn:
        await conn.execute('''
            UPDATE fixtures 
            SET home_score = $1, away_score = $2, played = TRUE, playable = FALSE
            WHERE fixture_id = $3
        ''', home_score, away_score, fixture['fixture_id'])
    
    await update_team_stats(fixture['home_team_id'], home_score, away_score, is_home=True)
    await update_team_stats(fixture['away_team_id'], away_score, home_score, is_home=False)
    
    return {
        'home_team': fixture['home_team_id'],
        'away_team': fixture['away_team_id'],
        'home_team_name': home_team['team_name'],
        'away_team_name': away_team['team_name'],
        'home_score': home_score,
        'away_score': away_score,
        'has_user_players': has_user_players
    }

async def calculate_team_strength(team_id: str, is_home: bool = False) -> int:
    """
    ✅ FIX: Calculate team strength using WEIGHTED average
    User players count 1.5x more than NPCs to reflect their training/growth
    
    This prevents teams with one 90-rated user + ten 65-rated NPCs
    from having their strength calculated as only 67
    """
    
    async with db.pool.acquire() as conn:
        # Get domestic players (both user and NPC)
        user_players = await conn.fetch(
            "SELECT overall_rating FROM players WHERE team_id = $1 AND retired = FALSE",
            team_id
        )
        npc_players = await conn.fetch(
            "SELECT overall_rating FROM npc_players WHERE team_id = $1 AND retired = FALSE",
            team_id
        )
        
        # Get European players (if this is a European team)
        european_players = await conn.fetch(
            "SELECT overall_rating FROM european_npc_players WHERE team_id = $1 AND retired = FALSE",
            team_id
        )
    
    # ✅ FIX: Calculate WEIGHTED average (user players count 1.5x)
    total_weight = 0
    total_rating = 0
    
    # User players are worth 1.5x (they train and improve)
    for player in user_players:
        total_rating += player['overall_rating'] * 1.5
        total_weight += 1.5
    
    # NPCs are worth 1.0x
    for player in npc_players:
        total_rating += player['overall_rating']
        total_weight += 1.0
    
    for player in european_players:
        total_rating += player['overall_rating']
        total_weight += 1.0
    
    if total_weight == 0:
        return 50  # Default for teams with no players
    
    # Calculate weighted average
    avg_rating = total_rating / total_weight
    
    # Team quality modifier based on average rating
    if avg_rating >= 85:
        team_modifier = 25  # Elite teams (Man City, Real Madrid, Bayern)
    elif avg_rating >= 80:
        team_modifier = 20  # Top teams (Liverpool, Arsenal, Juventus)
    elif avg_rating >= 75:
        team_modifier = 15  # Good teams (Aston Villa, Roma)
    elif avg_rating >= 70:
        team_modifier = 10  # Mid-table (Brentford, Fulham)
    elif avg_rating >= 65:
        team_modifier = 5   # Lower teams (Luton, Southampton)
    else:
        team_modifier = 0   # Weak teams (League One clubs)
    
    # Home advantage
    home_bonus = 5 if is_home else 0
    
    # Calculate total strength
    strength = int(avg_rating + team_modifier + home_bonus)
    
    # Cap at 95 to prevent unrealistic scorelines
    return min(strength, 95)

def simulate_score(home_strength: int, away_strength: int) -> tuple:
    """Simulate match score based on team strengths"""
    
    # Calculate strength difference
    diff = home_strength - away_strength
    
    # Base goals from strength (stronger teams score more)
    home_base = max(0, (home_strength - 50) // 15)
    away_base = max(0, (away_strength - 50) // 15)
    
    # Add randomness (luck factor)
    home_score = home_base + random.randint(0, 2)
    away_score = away_base + random.randint(0, 2)
    
    # Apply strength difference bonuses
    if diff > 20:
        home_score += 1
    elif diff > 30:
        home_score += 2
    elif diff < -20:
        away_score += 1
    elif diff < -30:
        away_score += 2
    
    # Occasional upsets (10% chance - this is the "luck" factor)
    if random.random() < 0.1:
        if diff > 0:
            away_score += random.randint(1, 2)
        else:
            home_score += random.randint(1, 2)
    
    # Ensure scores are non-negative
    home_score = max(0, home_score)
    away_score = max(0, away_score)
    
    return home_score, away_score

async def update_team_stats(team_id: str, goals_for: int, goals_against: int, is_home: bool):
    """Update team statistics after a match"""
    
    if goals_for > goals_against:
        won = 1
        drawn = 0
        lost = 0
        points = 3
    elif goals_for == goals_against:
        won = 0
        drawn = 1
        lost = 0
        points = 1
    else:
        won = 0
        drawn = 0
        lost = 1
        points = 0
    
    async with db.pool.acquire() as conn:
        await conn.execute('''
            UPDATE teams SET
            played = played + 1,
            won = won + $1,
            drawn = drawn + $2,
            lost = lost + $3,
            goals_for = goals_for + $4,
            goals_against = goals_against + $5,
            points = points + $6
            WHERE team_id = $7
        ''', won, drawn, lost, goals_for, goals_against, points, team_id)
