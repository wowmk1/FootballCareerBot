"""
NPC Squad Generator - Creates complete squads for all teams
Ensures every team has players in all positions
"""
from database import db
import random

def generate_random_player_name():
    """Generate a random player name"""
    first_names = [
        "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
        "Thomas", "Charles", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven",
        "Paul", "Andrew", "Joshua", "Kenneth", "Kevin", "Brian", "George", "Edward",
        "Ronald", "Timothy", "Jason", "Jeffrey", "Ryan", "Jacob", "Gary", "Nicholas",
        "Eric", "Jonathan", "Stephen", "Larry", "Justin", "Scott", "Brandon", "Benjamin",
        "Samuel", "Raymond", "Gregory", "Frank", "Alexander", "Patrick", "Jack", "Dennis",
        "Jerry", "Tyler", "Aaron", "Jose", "Adam", "Henry", "Nathan", "Douglas", "Zachary",
        "Peter", "Kyle", "Walter", "Ethan", "Jeremy", "Harold", "Keith", "Christian", "Roger",
        "Noah", "Gerald", "Carl", "Terry", "Sean", "Austin", "Arthur", "Lawrence", "Jesse",
        "Dylan", "Bryan", "Joe", "Jordan", "Billy", "Bruce", "Albert", "Willie", "Gabriel",
        "Logan", "Alan", "Juan", "Wayne", "Roy", "Ralph", "Randy", "Eugene", "Vincent",
        "Russell", "Elijah", "Louis", "Bobby", "Philip", "Johnny"
    ]
    
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
        "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
        "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
        "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
        "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
        "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
        "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey",
        "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson", "Watson",
        "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza", "Ruiz", "Hughes",
        "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers", "Long", "Ross", "Foster",
        "Jimenez"
    ]
    
    return f"{random.choice(first_names)} {random.choice(last_names)}"

async def generate_squad_for_team(team_id: str, league: str):
    """Generate a complete squad for a team"""
    
    # Determine rating range based on league
    if league == 'Premier League':
        rating_range = (72, 85)
    elif league == 'Championship':
        rating_range = (65, 75)
    else:  # League One
        rating_range = (58, 68)
    
    # Squad composition: 25 players total
    squad_composition = {
        'GK': 3,   # 3 goalkeepers
        'CB': 5,   # 5 center backs
        'FB': 4,   # 4 full backs
        'CDM': 3,  # 3 defensive mids
        'CM': 4,   # 4 central mids
        'CAM': 2,  # 2 attacking mids
        'W': 3,    # 3 wingers
        'ST': 3    # 3 strikers
    }
    
    players = []
    
    for position, count in squad_composition.items():
        for i in range(count):
            name = generate_random_player_name()
            age = random.randint(18, 35)
            
            # Adjust rating based on age (prime years 24-29)
            age_modifier = 0
            if 24 <= age <= 29:
                age_modifier = random.randint(0, 3)
            elif age < 24:
                age_modifier = random.randint(-3, 0)
            else:  # age > 29
                age_modifier = random.randint(-5, -2)
            
            overall = random.randint(rating_range[0], rating_range[1]) + age_modifier
            overall = max(50, min(90, overall))
            
            # Calculate individual stats based on position
            if position == 'GK':
                pace = max(40, overall - random.randint(10, 15))
                shooting = max(40, overall - random.randint(15, 20))
                passing = max(50, overall - random.randint(5, 10))
                dribbling = max(45, overall - random.randint(10, 15))
                defending = min(99, overall + random.randint(5, 15))
                physical = max(60, overall + random.randint(-5, 5))
            
            elif position in ['ST', 'W']:
                pace = min(99, overall + random.randint(0, 10))
                shooting = min(99, overall + random.randint(5, 10))
                passing = max(50, overall - random.randint(0, 10))
                dribbling = min(99, overall + random.randint(0, 10))
                defending = max(30, overall - random.randint(20, 30))
                physical = max(50, overall - random.randint(0, 10))
            
            elif position in ['CAM', 'CM']:
                pace = max(50, overall - random.randint(0, 5))
                shooting = max(55, overall - random.randint(0, 10))
                passing = min(99, overall + random.randint(5, 10))
                dribbling = min(99, overall + random.randint(0, 10))
                defending = max(45, overall - random.randint(10, 20))
                physical = max(55, overall - random.randint(0, 10))
            
            elif position == 'CDM':
                pace = max(50, overall - random.randint(5, 10))
                shooting = max(50, overall - random.randint(10, 15))
                passing = min(99, overall + random.randint(0, 10))
                dribbling = max(55, overall - random.randint(5, 10))
                defending = min(99, overall + random.randint(5, 15))
                physical = min(99, overall + random.randint(5, 10))
            
            elif position in ['CB', 'FB']:
                if position == 'FB':
                    pace = min(99, overall + random.randint(0, 5))
                else:
                    pace = max(50, overall - random.randint(5, 10))
                shooting = max(35, overall - random.randint(20, 30))
                passing = max(55, overall - random.randint(5, 10))
                dribbling = max(45, overall - random.randint(10, 20))
                defending = min(99, overall + random.randint(5, 15))
                physical = min(99, overall + random.randint(5, 10))
            
            else:
                pace = overall
                shooting = overall
                passing = overall
                dribbling = overall
                defending = overall
                physical = overall
            
            players.append({
                'name': name,
                'position': position,
                'age': age,
                'overall': overall,
                'pace': pace,
                'shooting': shooting,
                'passing': passing,
                'dribbling': dribbling,
                'defending': defending,
                'physical': physical
            })
    
    # Insert all players into database
    async with db.pool.acquire() as conn:
        for player in players:
            await conn.execute('''
                INSERT INTO npc_players (
                    player_name, team_id, position, age, overall_rating,
                    pace, shooting, passing, dribbling, defending, physical, is_regen
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, FALSE)
            ''',
                player['name'],
                team_id,
                player['position'],
                player['age'],
                player['overall'],
                player['pace'],
                player['shooting'],
                player['passing'],
                player['dribbling'],
                player['defending'],
                player['physical']
            )
    
    return len(players)

async def populate_all_teams():
    """Populate all teams with complete squads"""
    from data.teams import ALL_TEAMS
    
    total_players = 0
    
    for team in ALL_TEAMS:
        # Check if team already has players
        async with db.pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT COUNT(*) as count FROM npc_players WHERE team_id = $1",
                team['team_id']
            )
            count = result['count']
        
        if count == 0:
            players_added = await generate_squad_for_team(team['team_id'], team['league'])
            total_players += players_added
            print(f"✅ Generated {players_added} players for {team['team_name']}")
    
    print(f"✅ Total NPC players created: {total_players}")
    return total_players
