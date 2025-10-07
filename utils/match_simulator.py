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
    """Simulate a single match (fallback for matches without user involvement)"""
    
    home_team = await db.get_team(fixture['home_team_id'])
    away_team = await db.get_team(fixture['away_team_id'])
    
    async with db.pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT COUNT(*) as count FROM players WHERE (team_id = $1 OR team_id = $2) AND retired = FALSE",
            fixture['home_team_id'], fixture['away_team_id']
        )
        has_user_players = result['count'] > 0
    
    home_strength = random.randint(0, 3) + 1
    away_strength = random.randint(0, 3)
    
    home_score = home_strength
    away_score = away_strength
    
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
