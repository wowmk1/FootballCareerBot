```python
"""
Populate European teams with real player rosters
"""

from database import db
from data.european_players import TEAM_ROSTERS
import random

def calculate_attributes(position, rating):
    """Calculate position-specific stats"""
    if position == 'GK':
        return {
            'pace': max(40, rating - random.randint(20, 30)),
            'shooting': max(30, rating - random.randint(35, 45)),
            'passing': max(50, rating - random.randint(10, 20)),
            'dribbling': max(40, rating - random.randint(25, 35)),
            'defending': min(99, rating + random.randint(5, 15)),
            'physical': min(99, rating + random.randint(0, 10))
        }
    elif position in ['ST', 'W']:
        return {
            'pace': min(99, rating + random.randint(5, 15)),
            'shooting': min(99, rating + random.randint(5, 15)),
            'passing': max(60, rating - random.randint(0, 10)),
            'dribbling': min(99, rating + random.randint(0, 10)),
            'defending': max(30, rating - random.randint(30, 40)),
            'physical': max(55, rating - random.randint(0, 10))
        }
    elif position in ['CAM', 'CM']:
        return {
            'pace': max(60, rating - random.randint(0, 10)),
            'shooting': max(65, rating - random.randint(0, 10)),
            'passing': min(99, rating + random.randint(5, 15)),
            'dribbling': min(99, rating + random.randint(0, 10)),
            'defending': max(50, rating - random.randint(10, 20)),
            'physical': max(60, rating - random.randint(0, 10))
        }
    elif position == 'CDM':
        return {
            'pace': max(50, rating - random.randint(5, 10)),
            'shooting': max(50, rating - random.randint(10, 15)),
            'passing': min(99, rating + random.randint(0, 10)),
            'dribbling': max(55, rating - random.randint(5, 10)),
            'defending': min(99, rating + random.randint(5, 15)),
            'physical': min(99, rating + random.randint(5, 10))
        }
    elif position in ['CB', 'FB']:
        pace = min(99, rating + random.randint(0, 5)) if position == 'FB' else max(50, rating - random.randint(5, 10))
        return {
            'pace': pace,
            'shooting': max(35, rating - random.randint(20, 30)),
            'passing': max(55, rating - random.randint(5, 10)),
            'dribbling': max(45, rating - random.randint(10, 20)),
            'defending': min(99, rating + random.randint(5, 15)),
            'physical': min(99, rating + random.randint(5, 10))
        }
    else:
        return {
            'pace': rating, 'shooting': rating, 'passing': rating,
            'dribbling': rating, 'defending': rating, 'physical': rating
        }

async def populate_european_teams():
    """Populate all European teams and players"""
    print("🌍 Starting European team population...")
    
    async with db.pool.acquire() as conn:
        teams_added = 0
        players_added = 0
        
        for team_id, team_data in TEAM_ROSTERS.items():
            # Insert team
            await conn.execute("""
                INSERT INTO european_teams (team_id, team_name, country, league, reputation)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (team_id) DO NOTHING
            """, team_id, team_data['name'], team_data['country'], 
                 team_data['league'], 85)
            
            teams_added += 1
            
            # Insert players
            for player in team_data['players']:
                stats = calculate_attributes(player['pos'], player['rating'])
                
                # Calculate value
                base_value = player['rating'] * 1000000
                if player['age'] < 24:
                    value = int(base_value * 1.5)
                elif player['age'] > 30:
                    value = int(base_value * 0.7)
                else:
                    value = base_value
                
                wage = player['rating'] * 10000
                
                await conn.execute("""
                    INSERT INTO european_npc_players 
                    (player_name, team_id, position, overall_rating, age, nationality,
                     pace, shooting, passing, dribbling, defending, physical, value, wage)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                """, player['name'], team_id, player['pos'], player['rating'],
                     player['age'], player['nat'], stats['pace'], stats['shooting'],
                     stats['passing'], stats['dribbling'], stats['defending'], 
                     stats['physical'], value, wage)
                
                players_added += 1
            
            print(f"  ✅ {team_data['name']}: {len(team_data['players'])} players")
    
    print(f"🎉 Populated {teams_added} teams with {players_added} players!")
    return teams_added, players_added
```

---
