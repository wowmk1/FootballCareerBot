"""
Data Initializer - Sets up teams, fixtures, and NPC players
"""

from database import db
import random

async def initialize_game_data():
    """Initialize all game data - teams, players, fixtures"""
    
    # Check if already initialized
    async with db.pool.acquire() as conn:
        team_count = await conn.fetchval("SELECT COUNT(*) FROM teams")
    
    if team_count > 0:
        print("✅ Game data already initialized")
        return
    
    print("🎮 Initializing game data...")
    
    # Initialize teams
    await initialize_teams()
    
    # Initialize NPC players
    await initialize_npc_players()
    
    # Generate fixtures
    await generate_season_fixtures()
    
    print("✅ Game data initialization complete!")


async def initialize_teams():
    """Initialize all teams in the database"""
    from data.teams import ALL_TEAMS
    
    print("📊 Initializing teams...")
    
    async with db.pool.acquire() as conn:
        for team in ALL_TEAMS:
            # Set budgets based on league
            if team['league'] == 'Premier League':
                budget = 150000000
                wage_budget = 200000
            elif team['league'] == 'Championship':
                budget = 50000000
                wage_budget = 80000
            else:  # League One
                budget = 10000000
                wage_budget = 30000
            
            await conn.execute('''
                INSERT INTO teams (team_id, team_name, league, budget, wage_budget)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (team_id) DO NOTHING
            ''',
                team['team_id'],
                team['team_name'],
                team['league'],
                budget,
                wage_budget
            )
    
    print(f"✅ Initialized {len(ALL_TEAMS)} teams")


async def initialize_npc_players():
    """Initialize NPC players for all teams"""
    
    print("⚽ Initializing NPC players...")
    
    # Check if real players already exist
    async with db.pool.acquire() as conn:
        existing_count = await conn.fetchval("SELECT COUNT(*) FROM npc_players")
    
    if existing_count > 0:
        print(f"✅ {existing_count} NPC players already exist")
        return
    
    # Try to load real players first
    try:
        await load_real_players()
    except Exception as e:
        print(f"⚠️ Could not load real players: {e}")
    
    # Fill remaining squads with generated players
    await generate_missing_squads()
    
    async with db.pool.acquire() as conn:
        total_npcs = await conn.fetchval("SELECT COUNT(*) FROM npc_players")
    
    print(f"✅ Initialized {total_npcs} NPC players")


async def load_real_players():
    """Load real Premier League and Championship players"""
    
    try:
        from data.players import PREMIER_LEAGUE_PLAYERS
        print("  Loading Premier League players...")
        await insert_real_players(PREMIER_LEAGUE_PLAYERS)
        print(f"  ✅ Loaded {len(PREMIER_LEAGUE_PLAYERS)} PL players")
    except ImportError:
        print("  ⚠️ Premier League player data not found")
    
    try:
        from data.championship_players import CHAMPIONSHIP_PLAYERS
        print("  Loading Championship players...")
        await insert_real_players(CHAMPIONSHIP_PLAYERS)
        print(f"  ✅ Loaded {len(CHAMPIONSHIP_PLAYERS)} Championship players")
    except ImportError:
        print("  ⚠️ Championship player data not found")


async def insert_real_players(players_list):
    """Insert real players into database"""
    
    async with db.pool.acquire() as conn:
        for p in players_list:
            base = p['overall_rating']
            position = p['position']
            
            # Calculate position-based stats
            if position == 'GK':
                pace = max(40, base - random.randint(10, 15))
                shooting = max(40, base - random.randint(15, 20))
                passing = max(50, base - random.randint(5, 10))
                dribbling = max(45, base - random.randint(10, 15))
                defending = min(99, base + random.randint(5, 15))
                physical = max(60, base + random.randint(-5, 5))
            elif position in ['ST', 'W']:
                pace = min(99, base + random.randint(0, 10))
                shooting = min(99, base + random.randint(5, 10))
                passing = max(50, base - random.randint(0, 10))
                dribbling = min(99, base + random.randint(0, 10))
                defending = max(30, base - random.randint(20, 30))
                physical = max(50, base - random.randint(0, 10))
            elif position in ['CAM', 'CM']:
                pace = max(50, base - random.randint(0, 5))
                shooting = max(55, base - random.randint(0, 10))
                passing = min(99, base + random.randint(5, 10))
                dribbling = min(99, base + random.randint(0, 10))
                defending = max(45, base - random.randint(10, 20))
                physical = max(55, base - random.randint(0, 10))
            elif position == 'CDM':
                pace = max(50, base - random.randint(5, 10))
                shooting = max(50, base - random.randint(10, 15))
                passing = min(99, base + random.randint(0, 10))
                dribbling = max(55, base - random.randint(5, 10))
                defending = min(99, base + random.randint(5, 15))
                physical = min(99, base + random.randint(5, 10))
            elif position in ['CB', 'FB']:
                if position == 'FB':
                    pace = min(99, base + random.randint(0, 5))
                else:
                    pace = max(50, base - random.randint(5, 10))
                shooting = max(35, base - random.randint(20, 30))
                passing = max(55, base - random.randint(5, 10))
                dribbling = max(45, base - random.randint(10, 20))
                defending = min(99, base + random.randint(5, 15))
                physical = min(99, base + random.randint(5, 10))
            else:
                pace = base
                shooting = base
                passing = base
                dribbling = base
                defending = base
                physical = base
            
            await conn.execute('''
                INSERT INTO npc_players (
                    player_name, team_id, position, age, overall_rating,
                    pace, shooting, passing, dribbling, defending, physical, is_regen
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, FALSE)
                ON CONFLICT DO NOTHING
            ''',
                p['player_name'],
                p['team_id'],
                p['position'],
                p['age'],
                p['overall_rating'],
                pace, shooting, passing, dribbling, defending, physical
            )


async def generate_missing_squads():
    """Generate NPC players for teams that don't have full squads"""
    
    from data.teams import ALL_TEAMS
    from data.player_names import get_random_player_name
    
    print("  Generating missing squad players...")
    
    required_positions = {
        'GK': 2,
        'CB': 4,
        'FB': 4,
        'CDM': 2,
        'CM': 4,
        'CAM': 2,
        'W': 4,
        'ST': 3
    }
    
    for team in ALL_TEAMS:
        async with db.pool.acquire() as conn:
            # Check current squad size
            current_count = await conn.fetchval(
                "SELECT COUNT(*) FROM npc_players WHERE team_id = $1 AND retired = FALSE",
                team['team_id']
            )
            
            if current_count >= 25:
                continue  # Team already has full squad
            
            # Get position counts
            position_counts = {}
            for pos in required_positions:
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM npc_players WHERE team_id = $1 AND position = $2 AND retired = FALSE",
                    team['team_id'], pos
                )
                position_counts[pos] = count
            
            # Generate missing players
            for position, required in required_positions.items():
                needed = required - position_counts.get(position, 0)
                
                for _ in range(needed):
                    player_name = get_random_player_name()
                    age = random.randint(18, 32)
                    
                    # Rating based on league
                    if team['league'] == 'Premier League':
                        base_rating = random.randint(70, 85)
                    elif team['league'] == 'Championship':
                        base_rating = random.randint(60, 75)
                    else:  # League One
                        base_rating = random.randint(50, 65)
                    
                    # Age adjustment
                    if age <= 21:
                        base_rating = max(50, base_rating - 5)
                    elif age >= 30:
                        base_rating = min(85, base_rating + 3)
                    
                    # Calculate stats based on position
                    stats = calculate_position_stats(position, base_rating)
                    
                    await conn.execute('''
                        INSERT INTO npc_players (
                            player_name, team_id, position, age, overall_rating,
                            pace, shooting, passing, dribbling, defending, physical, is_regen
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, FALSE)
                    ''',
                        player_name, team['team_id'], position, age, base_rating,
                        stats['pace'], stats['shooting'], stats['passing'],
                        stats['dribbling'], stats['defending'], stats['physical']
                    )


def calculate_position_stats(position, base_rating):
    """Calculate stats based on position"""
    
    if position == 'GK':
        return {
            'pace': max(40, base_rating - random.randint(10, 15)),
            'shooting': max(40, base_rating - random.randint(15, 20)),
            'passing': max(50, base_rating - random.randint(5, 10)),
            'dribbling': max(45, base_rating - random.randint(10, 15)),
            'defending': min(99, base_rating + random.randint(5, 15)),
            'physical': max(60, base_rating + random.randint(-5, 5))
        }
    elif position in ['ST', 'W']:
        return {
            'pace': min(99, base_rating + random.randint(0, 10)),
            'shooting': min(99, base_rating + random.randint(5, 10)),
            'passing': max(50, base_rating - random.randint(0, 10)),
            'dribbling': min(99, base_rating + random.randint(0, 10)),
            'defending': max(30, base_rating - random.randint(20, 30)),
            'physical': max(50, base_rating - random.randint(0, 10))
        }
    elif position in ['CAM', 'CM']:
        return {
            'pace': max(50, base_rating - random.randint(0, 5)),
            'shooting': max(55, base_rating - random.randint(0, 10)),
            'passing': min(99, base_rating + random.randint(5, 10)),
            'dribbling': min(99, base_rating + random.randint(0, 10)),
            'defending': max(45, base_rating - random.randint(10, 20)),
            'physical': max(55, base_rating - random.randint(0, 10))
        }
    elif position == 'CDM':
        return {
            'pace': max(50, base_rating - random.randint(5, 10)),
            'shooting': max(50, base_rating - random.randint(10, 15)),
            'passing': min(99, base_rating + random.randint(0, 10)),
            'dribbling': max(55, base_rating - random.randint(5, 10)),
            'defending': min(99, base_rating + random.randint(5, 15)),
            'physical': min(99, base_rating + random.randint(5, 10))
        }
    elif position in ['CB', 'FB']:
        if position == 'FB':
            pace = min(99, base_rating + random.randint(0, 5))
        else:
            pace = max(50, base_rating - random.randint(5, 10))
        
        return {
            'pace': pace,
            'shooting': max(35, base_rating - random.randint(20, 30)),
            'passing': max(55, base_rating - random.randint(5, 10)),
            'dribbling': max(45, base_rating - random.randint(10, 20)),
            'defending': min(99, base_rating + random.randint(5, 15)),
            'physical': min(99, base_rating + random.randint(5, 10))
        }
    else:
        return {
            'pace': base_rating,
            'shooting': base_rating,
            'passing': base_rating,
            'dribbling': base_rating,
            'defending': base_rating,
            'physical': base_rating
        }


async def generate_season_fixtures():
    """Generate fixtures for all leagues"""
    
    from data.teams import ALL_TEAMS
    import config
    
    print("📅 Generating season fixtures...")
    
    # Check if fixtures already exist
    async with db.pool.acquire() as conn:
        existing_fixtures = await conn.fetchval("SELECT COUNT(*) FROM fixtures")
    
    if existing_fixtures > 0:
        print(f"✅ {existing_fixtures} fixtures already exist")
        return
    
    # Get current season from game state
    state = await db.get_game_state()
    current_season = state['current_season'] if state else '2027/28'
    
    # Group teams by league
    leagues = {}
    for team in ALL_TEAMS:
        league = team['league']
        if league not in leagues:
            leagues[league] = []
        leagues[league].append(team['team_id'])
    
    # Generate fixtures for each league
    fixture_count = 0
    for league, teams in leagues.items():
        league_fixtures = generate_round_robin(teams, league, current_season)
        
        async with db.pool.acquire() as conn:
            for fixture in league_fixtures:
                await conn.execute('''
                    INSERT INTO fixtures (
                        home_team_id, away_team_id, competition, league,
                        week_number, season, played, playable
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, FALSE, FALSE)
                ''',
                    fixture['home'],
                    fixture['away'],
                    league,
                    league,
                    fixture['week'],
                    current_season
                )
                fixture_count += 1
    
    print(f"✅ Generated {fixture_count} fixtures across all leagues")


def generate_round_robin(teams, league, season):
    """Generate round-robin fixtures for a league"""
    
    fixtures = []
    n = len(teams)
    
    # If odd number of teams, add a "bye" team
    if n % 2 == 1:
        teams.append(None)
        n += 1
    
    # Generate fixtures using round-robin algorithm
    for week in range(n - 1):
        week_fixtures = []
        
        for i in range(n // 2):
            home = teams[i]
            away = teams[n - 1 - i]
            
            if home and away:  # Skip if bye week
                week_fixtures.append({
                    'home': home,
                    'away': away,
                    'week': week + 1
                })
        
        fixtures.extend(week_fixtures)
        
        # Rotate teams for next week (keep first team fixed)
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
    
    # Second half of season (reverse fixtures)
    first_half_count = len(fixtures)
    for i in range(first_half_count):
        fixture = fixtures[i]
        fixtures.append({
            'home': fixture['away'],
            'away': fixture['home'],
            'week': fixture['week'] + (n - 1)
        })
    
    return fixtures
