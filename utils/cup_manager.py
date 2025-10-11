"""
Cup Competition Manager
Handles FA Cup, League Cup, and European competitions
"""
from database import db
import random
import config

CUP_COMPETITIONS = {
    'fa_cup': {
        'name': 'FA Cup',
        'rounds': ['R64', 'R32', 'R16', 'QF', 'SF', 'F'],
        'eligible_leagues': ['Premier League', 'Championship', 'League One'],
        'is_two_legged': False,
        'start_week': 10,
        'weeks_between_rounds': 3
    },
    'league_cup': {
        'name': 'League Cup',
        'rounds': ['R32', 'R16', 'QF', 'SF', 'F'],
        'eligible_leagues': ['Premier League', 'Championship'],
        'is_two_legged': False,  # Except SF
        'start_week': 8,
        'weeks_between_rounds': 4
    },
    'europa': {
        'name': 'Europa League',
        'rounds': ['Group', 'R16', 'QF', 'SF', 'F'],
        'eligible_leagues': ['Premier League'],
        'is_two_legged': True,
        'qualification_positions': [5, 6, 7],  # PL positions
        'start_week': 6,
        'weeks_between_rounds': 3
    },
    'champions': {
        'name': 'Champions League',
        'rounds': ['Group', 'R16', 'QF', 'SF', 'F'],
        'eligible_leagues': ['Premier League'],
        'is_two_legged': True,
        'qualification_positions': [1, 2, 3, 4],  # Top 4
        'start_week': 6,
        'weeks_between_rounds': 3
    }
}

async def initialize_cup_season(season: str):
    """Initialize all cup competitions for the season"""
    
    async with db.pool.acquire() as conn:
        for cup_id, cup_data in CUP_COMPETITIONS.items():
            # Create competition entry
            result = await conn.fetchrow("""
                INSERT INTO cup_competitions (
                    competition_name, competition_type, season, 
                    current_round, is_active
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING competition_id
            """, cup_data['name'], cup_id, season, 
                 cup_data['rounds'][0], False)
            
            competition_id = result['competition_id']
            
            # Generate first round fixtures
            await generate_cup_round(competition_id, cup_data, cup_data['rounds'][0])
    
    print(f"✅ Initialized {len(CUP_COMPETITIONS)} cup competitions")

async def generate_cup_round(competition_id: int, cup_data: dict, round_name: str):
    """Generate fixtures for a cup round"""
    
    # Get qualified teams
    if round_name == cup_data['rounds'][0]:
        # First round - get all eligible teams
        async with db.pool.acquire() as conn:
            teams = await conn.fetch("""
                SELECT team_id FROM teams
                WHERE league = ANY($1)
                ORDER BY RANDOM()
            """, cup_data['eligible_leagues'])
    else:
        # Later rounds - get winners from previous round
        prev_round_index = cup_data['rounds'].index(round_name) - 1
        prev_round = cup_data['rounds'][prev_round_index]
        
        async with db.pool.acquire() as conn:
            teams = await conn.fetch("""
                SELECT DISTINCT winner_team_id as team_id
                FROM cup_fixtures
                WHERE competition_id = $1 AND round = $2
                AND winner_team_id IS NOT NULL
            """, competition_id, prev_round)
    
    if not teams:
        print(f"⚠️ No teams for {round_name}")
        return
    
    # Shuffle teams
    team_ids = [t['team_id'] for t in teams]
    random.shuffle(team_ids)
    
    # Create fixtures
    async with db.pool.acquire() as conn:
        for i in range(0, len(team_ids), 2):
            if i + 1 < len(team_ids):
                home_team = team_ids[i]
                away_team = team_ids[i + 1]
                
                # Determine if two-legged
                is_two_legged = cup_data['is_two_legged']
                if round_name == 'SF' and cup_data['competition_type'] == 'league_cup':
                    is_two_legged = True
                
                await conn.execute("""
                    INSERT INTO cup_fixtures (
                        competition_id, round, home_team_id, away_team_id,
                        is_two_legged, leg_number, playable
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, competition_id, round_name, home_team, away_team,
                     is_two_legged, 1, False)
                
                # If two-legged, create second leg
                if is_two_legged:
                    await conn.execute("""
                        INSERT INTO cup_fixtures (
                            competition_id, round, home_team_id, away_team_id,
                            is_two_legged, leg_number, playable
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, competition_id, round_name, away_team, home_team,
                         is_two_legged, 2, False)
    
    print(f"✅ Generated {round_name} for competition {competition_id}")

async def make_cup_fixtures_playable(competition_id: int):
    """Make cup fixtures playable for current round"""
    
    async with db.pool.acquire() as conn:
        comp = await conn.fetchrow("""
            SELECT current_round FROM cup_competitions
            WHERE competition_id = $1
        """, competition_id)
        
        if not comp:
            return
        
        await conn.execute("""
            UPDATE cup_fixtures
            SET playable = TRUE
            WHERE competition_id = $1 
            AND round = $2 
            AND played = FALSE
        """, competition_id, comp['current_round'])
    
    print(f"✅ Cup fixtures now playable for competition {competition_id}")

async def process_cup_result(fixture_id: int, home_score: int, away_score: int):
    """Process cup match result and determine winner"""
    
    async with db.pool.acquire() as conn:
        fixture = await conn.fetchrow("""
            SELECT * FROM cup_fixtures WHERE fixture_id = $1
        """, fixture_id)
        
        if not fixture:
            return
        
        fixture = dict(fixture)
        
        # Update scores
        await conn.execute("""
            UPDATE cup_fixtures
            SET home_score = $1, away_score = $2, played = TRUE
            WHERE fixture_id = $3
        """, home_score, away_score, fixture_id)
        
        # Determine winner
        if not fixture['is_two_legged']:
            # Single leg - simple winner
            if home_score > away_score:
                winner = fixture['home_team_id']
            elif away_score > home_score:
                winner = fixture['away_team_id']
            else:
                # Extra time/penalties (random for now)
                winner = random.choice([fixture['home_team_id'], fixture['away_team_id']])
            
            await conn.execute("""
                UPDATE cup_fixtures
                SET winner_team_id = $1
                WHERE fixture_id = $2
            """, winner, fixture_id)
        
        else:
            # Two-legged tie
            if fixture['leg_number'] == 1:
                # First leg - just update aggregate
                await conn.execute("""
                    UPDATE cup_fixtures
                    SET aggregate_home = $1, aggregate_away = $2
                    WHERE fixture_id = $3
                """, home_score, away_score, fixture_id)
            
            else:
                # Second leg - determine winner on aggregate
                # Get first leg scores
                first_leg = await conn.fetchrow("""
                    SELECT home_score, away_score
                    FROM cup_fixtures
                    WHERE competition_id = $1 
                    AND round = $2
                    AND home_team_id = $3
                    AND away_team_id = $4
                    AND leg_number = 1
                """, fixture['competition_id'], fixture['round'],
                     fixture['away_team_id'], fixture['home_team_id'])
                
                if first_leg:
                    # Calculate aggregate
                    home_aggregate = home_score + first_leg['away_score']
                    away_aggregate = away_score + first_leg['home_score']
                    
                    if home_aggregate > away_aggregate:
                        winner = fixture['home_team_id']
                    elif away_aggregate > home_aggregate:
                        winner = fixture['away_team_id']
                    else:
                        # Away goals rule or penalties
                        winner = random.choice([fixture['home_team_id'], fixture['away_team_id']])
                    
                    await conn.execute("""
                        UPDATE cup_fixtures
                        SET aggregate_home = $1, aggregate_away = $2, winner_team_id = $3
                        WHERE fixture_id = $4
                    """, home_aggregate, away_aggregate, winner, fixture_id)
