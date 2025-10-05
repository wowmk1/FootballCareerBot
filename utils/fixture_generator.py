from database import db
import random
import config

async def generate_all_fixtures():
    """Generate fixtures for all leagues"""
    
    leagues = ["Premier League", "Championship", "League One"]
    
    for league in leagues:
        await generate_league_fixtures(league)
    
    await db.update_game_state(fixtures_generated=True)
    
    print("✅ All fixtures generated for all leagues")

async def generate_league_fixtures(league: str):
    """Generate round-robin fixtures for a league"""
    
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT team_id, team_name FROM teams WHERE league = $1 ORDER BY team_name",
            league
        )
        teams = [dict(row) for row in rows]
    
    if not teams:
        return
    
    team_ids = [team['team_id'] for team in teams]
    num_teams = len(team_ids)
    
    if num_teams % 2 != 0:
        team_ids.append(None)
        num_teams += 1
    
    fixtures = []
    
    for week in range(num_teams - 1):
        week_fixtures = []
        
        for i in range(num_teams // 2):
            home = team_ids[i]
            away = team_ids[num_teams - 1 - i]
            
            if home is not None and away is not None:
                week_fixtures.append({
                    'home_team_id': home,
                    'away_team_id': away,
                    'week_number': week + 1
                })
        
        fixtures.extend(week_fixtures)
        
        team_ids = [team_ids[0]] + [team_ids[-1]] + team_ids[1:-1]
    
    first_half = fixtures.copy()
    for fixture in first_half:
        fixtures.append({
            'home_team_id': fixture['away_team_id'],
            'away_team_id': fixture['home_team_id'],
            'week_number': fixture['week_number'] + (num_teams - 1)
        })
    
    random.shuffle(fixtures)
    
    fixtures_per_week = len([t for t in teams if t['team_id'] is not None]) // 2
    for idx, fixture in enumerate(fixtures):
        fixture['week_number'] = (idx // fixtures_per_week) + 1
    
    async with db.pool.acquire() as conn:
        for fixture in fixtures:
            await conn.execute('''
                INSERT INTO fixtures (home_team_id, away_team_id, league, competition, week_number, season, played, playable)
                VALUES ($1, $2, $3, $4, $5, $6, FALSE, FALSE)
            ''',
                fixture['home_team_id'],
                fixture['away_team_id'],
                league,
                league,
                fixture['week_number'],
                config.CURRENT_SEASON
            )
    
    print(f"✅ Generated {len(fixtures)} fixtures for {league}")
