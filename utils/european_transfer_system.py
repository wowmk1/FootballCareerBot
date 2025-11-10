"""
Inter-European Transfer System - NPC ONLY
Enhanced to use ALL European teams realistically
"""

import random
from database import db

# Define club tiers for realistic transfer patterns
CLUB_TIERS = {
    'elite': [
        'real_madrid', 'barcelona', 'bayern_munich', 'paris_saint_germain',
        'man_city', 'liverpool', 'inter_milan', 'ac_milan', 'juventus'
    ],
    'top': [
        'atletico_madrid', 'sevilla', 'borussia_dortmund', 'rb_leipzig',
        'bayer_leverkusen', 'napoli', 'as_roma', 'lazio', 'atalanta',
        'porto', 'benfica', 'sporting_cp', 'ajax', 'psv_eindhoven'
    ],
    'mid': [
        'real_sociedad', 'villarreal', 'real_betis', 'athletic_bilbao',
        'eintracht_frankfurt', 'union_berlin', 'freiburg', 'hoffenheim',
        'fiorentina', 'lille', 'nice', 'rennes', 'lens', 'marseille',
        'monaco', 'lyon', 'braga', 'vitoria_guimaraes', 'feyenoord',
        'az_alkmaar', 'fc_twente', 'fc_utrecht', 'club_brugge', 'genk'
    ],
    'lower': [
        'anderlecht', 'royal_antwerp', 'galatasaray', 'fenerbahce',
        'celtic', 'rangers', 'rb_salzburg', 'young_boys', 'shakhtar_donetsk',
        'red_star_belgrade', 'olympiacos', 'panathinaikos', 'slavia_prague',
        'dynamo_kyiv', 'copenhagen', 'bodo_glimt', 'maccabi_haifa', 'apoel',
        'rio_ave'
    ]
}

def get_appropriate_destinations(player_rating, current_tier):
    """Get realistic transfer destinations based on player rating and current club tier"""
    
    # World-class players (88+) can move to elite clubs
    if player_rating >= 88:
        return CLUB_TIERS['elite'] + CLUB_TIERS['top']
    
    # Great players (85-87) can move to top/elite clubs
    elif player_rating >= 85:
        return CLUB_TIERS['top'] + CLUB_TIERS['elite'][:4]  # Some elite clubs
    
    # Good players (82-84) move to top/mid clubs
    elif player_rating >= 82:
        return CLUB_TIERS['top'] + CLUB_TIERS['mid']
    
    # Decent players (78-81) move to mid/lower clubs
    elif player_rating >= 78:
        return CLUB_TIERS['mid'] + CLUB_TIERS['lower']
    
    # Lower rated players stay in lower tiers
    else:
        return CLUB_TIERS['lower'] + CLUB_TIERS['mid'][:10]

def get_club_tier(team_id):
    """Get the tier of a club"""
    for tier, clubs in CLUB_TIERS.items():
        if team_id in clubs:
            return tier
    return 'lower'

async def simulate_european_transfers():
    """Simulate transfers between European NPCs - ALL clubs, realistic patterns"""
    print("🌍 Simulating inter-European transfers (NPC only)...")
    
    transfers_made = 0
    
    async with db.pool.acquire() as conn:
        # Get a broader range of players (not just 88+ rated)
        potential_movers = await conn.fetch("""
            SELECT * FROM european_npc_players
            WHERE overall_rating >= 75
            AND retired = FALSE
            AND age BETWEEN 20 AND 32
            ORDER BY RANDOM()
            LIMIT 15
        """)
        
        for player in potential_movers:
            # Transfer probability based on rating
            if player['overall_rating'] >= 88:
                transfer_chance = 0.4  # 40% chance for elite
            elif player['overall_rating'] >= 85:
                transfer_chance = 0.35
            elif player['overall_rating'] >= 82:
                transfer_chance = 0.25
            else:
                transfer_chance = 0.15
            
            if random.random() > transfer_chance:
                continue
            
            current_tier = get_club_tier(player['team_id'])
            possible_destinations = get_appropriate_destinations(
                player['overall_rating'], 
                current_tier
            )
            
            # Remove current club
            available_clubs = [c for c in possible_destinations if c != player['team_id']]
            
            if not available_clubs:
                continue
            
            new_club = random.choice(available_clubs)
            new_tier = get_club_tier(new_club)
            
            # Fee calculation based on tier movement
            if new_tier == 'elite' and current_tier != 'elite':
                fee = player['value'] * random.uniform(1.3, 1.8)  # Moving up costs more
            elif new_tier == current_tier:
                fee = player['value'] * random.uniform(0.9, 1.2)  # Similar level
            else:
                fee = player['value'] * random.uniform(0.8, 1.1)  # Moving down
            
            await conn.execute("""
                UPDATE european_npc_players
                SET team_id = $1, value = $2
                WHERE npc_id = $3
            """, new_club, int(fee), player['npc_id'])
            
            transfers_made += 1
            
            from_team = await conn.fetchval("SELECT team_name FROM european_teams WHERE team_id = $1", player['team_id'])
            to_team = await conn.fetchval("SELECT team_name FROM european_teams WHERE team_id = $1", new_club)
            
            # Add tier change indicator
            tier_indicator = ""
            if new_tier == 'elite' and current_tier != 'elite':
                tier_indicator = " ⬆️"
            elif new_tier in ['mid', 'lower'] and current_tier in ['elite', 'top']:
                tier_indicator = " ⬇️"
            
            print(f"  💼 {player['player_name']} ({player['overall_rating']} OVR): {from_team} → {to_team}{tier_indicator} (£{int(fee/1000000)}M)")
    
    print(f"✅ {transfers_made} inter-European NPC transfers completed!")
    return transfers_made

async def simulate_european_to_english_transfers():
    """European NPCs to English teams"""
    print("🌍 Simulating European NPC → English team transfers...")
    
    transfers_made = 0
    
    async with db.pool.acquire() as conn:
        # Wider range of European players
        elite_european = await conn.fetch("""
            SELECT * FROM european_npc_players
            WHERE overall_rating >= 80
            AND retired = FALSE
            AND age BETWEEN 20 AND 30
            ORDER BY RANDOM()
            LIMIT 10
        """)
        
        for player in elite_european:
            # Lower-rated players less likely to move to England
            if player['overall_rating'] >= 85:
                transfer_chance = 0.25
            elif player['overall_rating'] >= 82:
                transfer_chance = 0.15
            else:
                transfer_chance = 0.08
                
            if random.random() > transfer_chance:
                continue
            
            # Match player quality to English club quality
            if player['overall_rating'] >= 88:
                # Elite players to top PL clubs
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
            elif player['overall_rating'] >= 83:
                # Good players to mid-table PL clubs
                english_clubs = await conn.fetch("""
                    SELECT team_id, team_name FROM teams
                    WHERE league = 'Premier League'
                    AND team_id IN (
                        SELECT team_id FROM league_table 
                        WHERE position BETWEEN 7 AND 15 AND league = 'Premier League'
                    )
                    ORDER BY RANDOM()
                    LIMIT 1
                """)
            else:
                # Decent players anywhere in PL or Championship
                english_clubs = await conn.fetch("""
                    SELECT team_id, team_name FROM teams
                    WHERE league IN ('Premier League', 'Championship')
                    ORDER BY RANDOM()
                    LIMIT 1
                """)
            
            if not english_clubs:
                continue
            
            new_club = english_clubs[0]
            fee = player['value'] * random.uniform(1.2, 1.8)  # English premium
            
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
            WHERE n.overall_rating >= 80
            AND n.retired = FALSE
            AND n.age BETWEEN 20 AND 32
            AND n.team_id IN (
                SELECT team_id FROM teams 
                WHERE league IN ('Premier League', 'Championship')
            )
            AND NOT EXISTS (
                SELECT 1 FROM players p 
                WHERE p.player_name = n.player_name 
                AND p.team_id = n.team_id
            )
            ORDER BY RANDOM()
            LIMIT 8
        """)
        
        for player in elite_english:
            # Transfer probability
            if player['overall_rating'] >= 85:
                transfer_chance = 0.3
            elif player['overall_rating'] >= 82:
                transfer_chance = 0.2
            else:
                transfer_chance = 0.1
                
            if random.random() > transfer_chance:
                continue
            
            # Get appropriate destinations based on rating
            possible_destinations = get_appropriate_destinations(
                player['overall_rating'], 
                'top'  # English players valued highly
            )
            
            new_club = random.choice(possible_destinations)
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
