"""
Inter-European Transfer System - NPC ONLY
"""

import random
from database import db

async def simulate_european_transfers():
    """Simulate transfers between European NPCs"""
    print("🌍 Simulating inter-European transfers (NPC only)...")
    
    transfers_made = 0
    
    async with db.pool.acquire() as conn:
        elite_players = await conn.fetch("""
            SELECT * FROM european_npc_players
            WHERE overall_rating >= 88
            AND retired = FALSE
            ORDER BY RANDOM()
            LIMIT 5
        """)
        
        for player in elite_players:
            if random.random() > 0.3:
                continue
            
            top_clubs = ['real_madrid', 'barcelona', 'bayern', 'man_city', 'psg', 'liverpool']
            available_clubs = [c for c in top_clubs if c != player['team_id']]
            
            if not available_clubs:
                continue
            
            new_club = random.choice(available_clubs)
            fee = player['value'] * random.uniform(1.0, 1.5)
            
            await conn.execute("""
                UPDATE european_npc_players
                SET team_id = $1, value = $2
                WHERE npc_id = $3
            """, new_club, int(fee), player['npc_id'])
            
            transfers_made += 1
            
            from_team = await conn.fetchval("SELECT team_name FROM european_teams WHERE team_id = $1", player['team_id'])
            to_team = await conn.fetchval("SELECT team_name FROM european_teams WHERE team_id = $1", new_club)
            
            print(f"  💼 {player['player_name']} ({player['overall_rating']} OVR): {from_team} → {to_team} (£{int(fee/1000000)}M)")
    
    print(f"✅ {transfers_made} inter-European NPC transfers completed!")
    return transfers_made

async def simulate_european_to_english_transfers():
    """European NPCs to English teams"""
    print("🌍 Simulating European NPC → English team transfers...")
    
    transfers_made = 0
    
    async with db.pool.acquire() as conn:
        elite_european = await conn.fetch("""
            SELECT * FROM european_npc_players
            WHERE overall_rating >= 85
            AND retired = FALSE
            ORDER BY RANDOM()
            LIMIT 5
        """)
        
        for player in elite_european:
            if random.random() > 0.15:
                continue
            
            if player['overall_rating'] >= 88:
                english_clubs = await conn.fetch("""
                    SELECT team_id, team_name FROM teams
                    WHERE league = 'Premier League'
                    AND team_id IN (
                        SELECT team_id FROM league_table 
                        WHERE position <= 8 AND league = 'Premier League'
                    )
                    ORDER BY RANDOM()
                    LIMIT 1
                """)
            else:
                english_clubs = await conn.fetch("""
                    SELECT team_id, team_name FROM teams
                    WHERE league = 'Premier League'
                    ORDER BY RANDOM()
                    LIMIT 1
                """)
            
            if not english_clubs:
                continue
            
            new_club = english_clubs[0]
            fee = player['value'] * random.uniform(1.2, 1.8)
            
            await conn.execute("""
                INSERT INTO npc_players 
                (player_name, team_id, position, overall_rating, age,
                 pace, shooting, passing, dribbling, defending, physical, value, wage)
                SELECT player_name, $1, position, overall_rating, age,
                       pace, shooting, passing, dribbling, defending, physical, $2, wage
                FROM european_npc_players
                WHERE npc_id = $3
            """, new_club['team_id'], int(fee), player['npc_id'])
            
            await conn.execute("""
                DELETE FROM european_npc_players WHERE npc_id = $1
            """, player['npc_id'])
            
            transfers_made += 1
            
            from_team = await conn.fetchval("SELECT team_name FROM european_teams WHERE team_id = $1", player['team_id'])
            
            print(f"  🏴󠁧󠁢󠁥󠁮󠁧󠁿 {player['player_name']} ({player['overall_rating']} OVR): {from_team} → {new_club['team_name']} (£{int(fee/1000000)}M)")
    
    print(f"✅ {transfers_made} European → English NPC transfers completed!")
    return transfers_made

async def simulate_english_to_european_transfers():
    """English NPCs to European teams - NPC ONLY!"""
    print("🌍 Simulating English NPC → European transfers...")
    
    transfers_made = 0
    
    async with db.pool.acquire() as conn:
        # CRITICAL: Only NPCs, exclude human players
        elite_english = await conn.fetch("""
            SELECT n.* FROM npc_players n
            WHERE n.overall_rating >= 85
            AND n.retired = FALSE
            AND n.team_id IN (
                SELECT team_id FROM teams 
                WHERE league = 'Premier League'
            )
            AND NOT EXISTS (
                SELECT 1 FROM players p 
                WHERE p.player_name = n.player_name 
                AND p.team_id = n.team_id
            )
            ORDER BY RANDOM()
            LIMIT 3
        """)
        
        for player in elite_english:
            if random.random() > 0.2:
                continue
            
            if player['overall_rating'] >= 88:
                destinations = ['real_madrid', 'barcelona', 'bayern', 'psg']
            else:
                destinations = ['atletico', 'inter', 'ac_milan', 'dortmund', 'juventus']
            
            new_club = random.choice(destinations)
            fee = player['value'] * random.uniform(1.2, 1.8)
            
            await conn.execute("""
                INSERT INTO european_npc_players 
                (player_name, team_id, position, overall_rating, age, nationality,
                 pace, shooting, passing, dribbling, defending, physical, value, wage)
                SELECT player_name, $1, position, overall_rating, age, 'England',
                       pace, shooting, passing, dribbling, defending, physical, $2, wage
                FROM npc_players
                WHERE npc_id = $3
            """, new_club, int(fee), player['npc_id'])
            
            await conn.execute("""
                DELETE FROM npc_players WHERE npc_id = $1
            """, player['npc_id'])
            
            transfers_made += 1
            
            from_team = await conn.fetchval("SELECT team_name FROM teams WHERE team_id = $1", player['team_id'])
            to_team = await conn.fetchval("SELECT team_name FROM european_teams WHERE team_id = $1", new_club)
            
            print(f"  🌍 {player['player_name']} ({player['overall_rating']} OVR): {from_team} → {to_team} (£{int(fee/1000000)}M)")
    
    print(f"✅ {transfers_made} English NPC → European transfers completed!")
    return transfers_made
