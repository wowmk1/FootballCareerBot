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
    
    # Calculate team strength using WEIGHTED average
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
    Calculate team strength using WEIGHTED average
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
    
    # Calculate WEIGHTED average (user players count 1.5x)
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
    # This is how elite teams are identified!
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
    """
    ✅ REBALANCED: More realistic scorelines (0-3 goals typical)
    Works for both domestic and European competitions
    
    Uses a probabilistic system where:
    - Each team gets multiple "chances" to score
    - Stronger teams have higher conversion rates
    - Strength difference affects both chances and conversion
    - Elite teams (85+ strength) naturally score more
    """
    
    # Calculate strength difference
    diff = home_strength - away_strength
    
    # ═══════════════════════════════════════════════════════════
    # STEP 1: Determine number of scoring chances (attacks)
    # ═══════════════════════════════════════════════════════════
    
    # Base chances (6-10 per team is realistic for 90 min match)
    # Elite teams (90+ strength) will get 9-10 chances
    # Weak teams (60 strength) will get 5-6 chances
    home_base_chances = 7 + (home_strength - 70) // 10  # 5-9 chances
    away_base_chances = 7 + (away_strength - 70) // 10
    
    # Adjust for strength difference (stronger team dominates possession)
    if diff > 15:
        home_base_chances += 2
        away_base_chances -= 1
    elif diff > 30:
        home_base_chances += 3
        away_base_chances -= 2
    elif diff < -15:
        away_base_chances += 2
        home_base_chances -= 1
    elif diff < -30:
        away_base_chances += 3
        home_base_chances -= 2
    
    # Add randomness (form/tactics variation)
    home_chances = max(4, home_base_chances + random.randint(-1, 1))
    away_chances = max(4, away_base_chances + random.randint(-1, 1))
    
    # ═══════════════════════════════════════════════════════════
    # STEP 2: Convert chances to goals (realistic conversion ~10-20%)
    # ═══════════════════════════════════════════════════════════
    
    home_score = 0
    away_score = 0
    
    # Home team conversion rate (higher strength = better finishing)
    # Elite teams (90 strength) get ~20% conversion
    # Weak teams (60 strength) get ~8% conversion
    home_conversion = min(25, 8 + (home_strength - 70) // 5)  # 8-25% range
    if diff > 20:  # Boost against weak opponents
        home_conversion += 5
    
    # Away team conversion (slight penalty for being away)
    away_conversion = min(25, 6 + (away_strength - 70) // 5)  # 6-25% range
    if diff < -20:  # Boost against weak opponents
        away_conversion += 5
    
    # Simulate each chance
    for _ in range(home_chances):
        if random.randint(1, 100) <= home_conversion:
            home_score += 1
    
    for _ in range(away_chances):
        if random.randint(1, 100) <= away_conversion:
            away_score += 1
    
    # ═══════════════════════════════════════════════════════════
    # STEP 3: Special scenarios (rare events)
    # ═══════════════════════════════════════════════════════════
    
    # Occasional upset bonus (10% chance if losing badly)
    if diff > 25 and random.random() < 0.10:
        away_score += random.randint(1, 2)  # Underdog fights back
    elif diff < -25 and random.random() < 0.10:
        home_score += random.randint(1, 2)
    
    # Very rare high-scoring thriller (3% chance)
    if random.random() < 0.03:
        home_score += random.randint(0, 1)
        away_score += random.randint(0, 1)
    
    # Rare defensive masterclass (5% chance - very low scoring)
    if random.random() < 0.05:
        home_score = min(home_score, 1)
        away_score = min(away_score, 1)
    
    # ═══════════════════════════════════════════════════════════
    # STEP 4: Cap scores for realism
    # ═══════════════════════════════════════════════════════════
    
    # Cap at 6 goals per team (extremely rare to score more)
    home_score = min(home_score, 6)
    away_score = min(away_score, 6)
    
    # Ensure non-negative
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
