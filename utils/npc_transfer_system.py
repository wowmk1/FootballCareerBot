"""
NPC Transfer System - NPCs move between teams realistically
Runs during transfer windows
FIXED: Only executes during transfer windows (failsafe protection)
ENHANCED: Supports European player transfers and team rating compatibility
"""

from database import db
import random
import config


async def get_team_minimum_rating(team_id: str) -> int:
    """Get minimum player rating a team will accept"""
    
    async with db.pool.acquire() as conn:
        # Get team's current player ratings (domestic)
        user_players = await conn.fetch(
            "SELECT overall_rating FROM players WHERE team_id = $1 AND retired = FALSE",
            team_id
        )
        npc_players = await conn.fetch(
            "SELECT overall_rating FROM npc_players WHERE team_id = $1 AND retired = FALSE",
            team_id
        )
        
        # Check if this is a European team
        european_players = await conn.fetch(
            "SELECT overall_rating FROM european_npc_players WHERE team_id = $1 AND retired = FALSE",
            team_id
        )
        
        team_row = await conn.fetchrow("SELECT league FROM teams WHERE team_id = $1", team_id)
        if not team_row:
            # Check European teams
            team_row = await conn.fetchrow("SELECT league FROM european_teams WHERE team_id = $1", team_id)
    
    # Combine all ratings
    all_ratings = (
        [p['overall_rating'] for p in user_players] + 
        [p['overall_rating'] for p in npc_players] +
        [p['overall_rating'] for p in european_players]
    )
    
    if not all_ratings:
        # Default minimums by league
        league_defaults = {
            'Premier League': 70,
            'Champions League': 78,
            'Europa League': 75,
            'Championship': 60,
            'League One': 50
        }
        return league_defaults.get(team_row['league'], 50) if team_row else 50
    
    # Team will accept players within 8 rating points below their average
    avg_rating = sum(all_ratings) / len(all_ratings)
    return max(50, int(avg_rating - 8))


async def get_team_maximum_rating(team_id: str) -> int:
    """Get maximum player rating a team can attract (affordability)"""
    
    async with db.pool.acquire() as conn:
        # Get domestic players
        user_players = await conn.fetch(
            "SELECT overall_rating FROM players WHERE team_id = $1 AND retired = FALSE",
            team_id
        )
        npc_players = await conn.fetch(
            "SELECT overall_rating FROM npc_players WHERE team_id = $1 AND retired = FALSE",
            team_id
        )
        
        # Check European players
        european_players = await conn.fetch(
            "SELECT overall_rating FROM european_npc_players WHERE team_id = $1 AND retired = FALSE",
            team_id
        )
        
        team_row = await conn.fetchrow("SELECT league FROM teams WHERE team_id = $1", team_id)
        if not team_row:
            team_row = await conn.fetchrow("SELECT league FROM european_teams WHERE team_id = $1", team_id)
    
    # Combine all ratings
    all_ratings = (
        [p['overall_rating'] for p in user_players] + 
        [p['overall_rating'] for p in npc_players] +
        [p['overall_rating'] for p in european_players]
    )
    
    if not all_ratings:
        # Default maximums by league
        league_defaults = {
            'Premier League': 90,
            'Champions League': 95,
            'Europa League': 88,
            'Championship': 78,
            'League One': 70
        }
        return league_defaults.get(team_row['league'], 90) if team_row else 90
    
    # Team can attract players up to 10 rating points above their average
    avg_rating = sum(all_ratings) / len(all_ratings)
    return min(95, int(avg_rating + 10))


async def execute_npc_transfers(week: int):
    """Execute NPC transfers during transfer windows (domestic + European)"""
    
    # Only run during transfer windows
    if week not in config.TRANSFER_WINDOW_WEEKS:
        return 0
    
    print(f"🔄 Processing NPC transfers for Week {week}...")
    
    # Get transfer candidates from BOTH domestic and European leagues
    async with db.pool.acquire() as conn:
        # Domestic transfer candidates
        domestic_candidates = await conn.fetch("""
            SELECT n.*, t.league 
            FROM npc_players n
            LEFT JOIN teams t ON n.team_id = t.team_id
            WHERE n.retired = FALSE 
            AND n.age BETWEEN 20 AND 32
            AND n.overall_rating BETWEEN 60 AND 85
            AND n.team_id IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 15
        """)
        
        # European transfer candidates
        european_candidates = await conn.fetch("""
            SELECT n.*, t.league 
            FROM european_npc_players n
            LEFT JOIN european_teams t ON n.team_id = t.team_id
            WHERE n.retired = FALSE 
            AND n.age BETWEEN 20 AND 32
            AND n.overall_rating BETWEEN 60 AND 90
            AND n.team_id IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 10
        """)
    
    # Combine candidates
    all_candidates = list(domestic_candidates) + list(european_candidates)
    transfers_made = 0
    
    for candidate in all_candidates:
        # 25% chance to transfer
        if random.random() > 0.25:
            continue
        
        candidate = dict(candidate)
        current_league = candidate.get('league')
        rating = candidate['overall_rating']
        
        # Determine if this is a European player
        is_european = 'european_npc_players' in str(type(candidate)) or current_league in ['Champions League', 'Europa League']
        
        # Determine potential target leagues
        potential_leagues = []
        
        # High-rated players can move to top leagues
        if rating >= 78:
            potential_leagues.extend(['Premier League', 'Champions League', 'Europa League'])
        if rating >= 68:
            potential_leagues.extend(['Championship', 'Europa League'])
        if rating >= 58:
            potential_leagues.append('League One')
        
        # 60% lateral moves, 40% up/down
        if random.random() < 0.6 and current_league in potential_leagues:
            target_league = current_league
        else:
            if current_league in potential_leagues:
                potential_leagues.remove(current_league)
            if not potential_leagues:
                continue
            target_league = random.choice(potential_leagues)
        
        # Find suitable teams in target league (check BOTH domestic and European)
        async with db.pool.acquire() as conn:
            if target_league in ['Champions League', 'Europa League']:
                # Search European teams
                potential_teams = await conn.fetch("""
                    SELECT team_id, team_name, league
                    FROM european_teams
                    WHERE league = $1 AND team_id != $2
                    ORDER BY RANDOM()
                    LIMIT 10
                """, target_league, candidate['team_id'])
            else:
                # Search domestic teams
                potential_teams = await conn.fetch("""
                    SELECT team_id, team_name, league
                    FROM teams
                    WHERE league = $1 AND team_id != $2
                    ORDER BY RANDOM()
                    LIMIT 10
                """, target_league, candidate['team_id'])
        
        if not potential_teams:
            continue
        
        # Filter teams by rating compatibility
        suitable_team = None
        for team in potential_teams:
            team = dict(team)
            min_rating = await get_team_minimum_rating(team['team_id'])
            max_rating = await get_team_maximum_rating(team['team_id'])
            
            if min_rating <= rating <= max_rating:
                suitable_team = team
                break
        
        if not suitable_team:
            continue
        
        new_team = suitable_team
        
        # Calculate transfer fee
        base_fee = rating * 100000
        age_modifier = 1.0
        if candidate['age'] < 23:
            age_modifier = 1.5
        elif candidate['age'] > 29:
            age_modifier = 0.7
        
        fee = int(base_fee * age_modifier * random.uniform(0.7, 1.3))
        
        # Execute transfer
        async with db.pool.acquire() as conn:
            # Get old team name
            if is_european or current_league in ['Champions League', 'Europa League']:
                old_team = await conn.fetchrow(
                    "SELECT team_name FROM european_teams WHERE team_id = $1",
                    candidate['team_id']
                )
            else:
                old_team = await conn.fetchrow(
                    "SELECT team_name FROM teams WHERE team_id = $1",
                    candidate['team_id']
                )
            
            # Update player based on source table
            if 'npc_id' in candidate:
                # Domestic NPC - check if moving to European league
                if new_team['league'] in ['Champions League', 'Europa League']:
                    # Move from domestic to European
                    await conn.execute("""
                        DELETE FROM npc_players WHERE npc_id = $1
                    """, candidate['npc_id'])
                    
                    await conn.execute("""
                        INSERT INTO european_npc_players
                        (player_name, team_id, position, overall_rating, age, nationality,
                         pace, shooting, passing, dribbling, defending, physical, value, wage)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    """, candidate['player_name'], new_team['team_id'], candidate['position'],
                         candidate['overall_rating'], candidate['age'], 'Unknown',
                         candidate.get('pace', 70), candidate.get('shooting', 70),
                         candidate.get('passing', 70), candidate.get('dribbling', 70),
                         candidate.get('defending', 70), candidate.get('physical', 70),
                         fee, rating * 1000)
                else:
                    # Domestic to domestic
                    await conn.execute("""
                        UPDATE npc_players
                        SET team_id = $1
                        WHERE npc_id = $2
                    """, new_team['team_id'], candidate['npc_id'])
            else:
                # European NPC - check if moving to domestic league
                if new_team['league'] not in ['Champions League', 'Europa League']:
                    # Move from European to domestic
                    await conn.execute("""
                        DELETE FROM european_npc_players WHERE player_name = $1 AND team_id = $2
                    """, candidate['player_name'], candidate['team_id'])
                    
                    await conn.execute("""
                        INSERT INTO npc_players
                        (player_name, team_id, position, age, overall_rating,
                         pace, shooting, passing, dribbling, defending, physical, potential)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    """, candidate['player_name'], new_team['team_id'], candidate['position'],
                         candidate['age'], candidate['overall_rating'],
                         candidate.get('pace', 70), candidate.get('shooting', 70),
                         candidate.get('passing', 70), candidate.get('dribbling', 70),
                         candidate.get('defending', 70), candidate.get('physical', 70),
                         min(95, rating + 10))
                else:
                    # European to European
                    await conn.execute("""
                        UPDATE european_npc_players
                        SET team_id = $1
                        WHERE player_name = $2 AND team_id = $3
                    """, new_team['team_id'], candidate['player_name'], candidate['team_id'])
            
            # Record in transfers table (optional - for history)
            await conn.execute("""
                INSERT INTO transfers (
                    from_team, to_team, fee, wage, 
                    contract_length, transfer_type, season
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, 
                candidate['team_id'],
                new_team['team_id'],
                fee,
                rating * 1000,
                random.randint(2, 4),
                'transfer',
                config.CURRENT_SEASON
            )
        
        # Add news for notable transfers (75+ rated or big fees)
        if rating >= 75 or fee >= 10000000:
            old_team_name = old_team['team_name'] if old_team else 'Unknown'
            await db.add_news(
                f"TRANSFER: {candidate['player_name']} joins {new_team['team_name']}",
                f"{candidate['player_name']} ({rating} OVR, {candidate['position']}) transfers from "
                f"{old_team_name} to {new_team['team_name']} for £{fee:,}. {candidate['age']} years old.",
                "transfer_news",
                None,
                6,
                week
            )
            print(f"  📰 {candidate['player_name']} ({old_team_name} → {new_team['team_name']}) £{fee:,}")
        
        transfers_made += 1
    
    print(f"✅ Completed {transfers_made} NPC transfers")
    return transfers_made


async def balance_team_squads():
    """Balance squad sizes - move players from large squads to small ones
    
    ✅ CRITICAL FIX: ONLY RUNS DURING TRANSFER WINDOWS (Failsafe Protection)
    """
    
    # ✅ FAILSAFE: Only run during transfer windows
    state = await db.get_game_state()
    if state['current_week'] not in config.TRANSFER_WINDOW_WEEKS:
        print(f"⚠️ Week {state['current_week']}: Not a transfer window - skipping squad balancing")
        return 0
    
    print(f"⚖️ Week {state['current_week']}: Balancing squad sizes (transfer window active)...")
    
    async with db.pool.acquire() as conn:
        # Find teams with too many players (30+)
        large_squads = await conn.fetch("""
            SELECT t.team_id, t.team_name, t.league, COUNT(n.npc_id) as player_count
            FROM teams t
            LEFT JOIN npc_players n ON t.team_id = n.team_id AND n.retired = FALSE
            GROUP BY t.team_id, t.team_name, t.league
            HAVING COUNT(n.npc_id) > 30
        """)
        
        # Find teams with too few players (< 15)
        small_squads = await conn.fetch("""
            SELECT t.team_id, t.team_name, t.league, COUNT(n.npc_id) as player_count
            FROM teams t
            LEFT JOIN npc_players n ON t.team_id = n.team_id AND n.retired = FALSE
            GROUP BY t.team_id, t.team_name, t.league
            HAVING COUNT(n.npc_id) < 15
        """)
    
    if not large_squads or not small_squads:
        print("  ✅ No squad balancing needed")
        return 0
    
    transfers = 0
    
    for small_team in small_squads:
        small_team = dict(small_team)
        needed = 20 - small_team['player_count']
        
        # Find large team in same league
        same_league_large = [t for t in large_squads if dict(t)['league'] == small_team['league']]
        
        if not same_league_large:
            continue
        
        large_team = dict(random.choice(same_league_large))
        
        # Move players from large to small squad
        async with db.pool.acquire() as conn:
            excess_players = await conn.fetch("""
                SELECT npc_id, player_name, position, overall_rating
                FROM npc_players
                WHERE team_id = $1 AND retired = FALSE
                ORDER BY RANDOM()
                LIMIT $2
            """, large_team['team_id'], min(needed, 3))
            
            for player in excess_players:
                player = dict(player)
                
                await conn.execute("""
                    UPDATE npc_players
                    SET team_id = $1
                    WHERE npc_id = $2
                """, small_team['team_id'], player['npc_id'])
                
                transfers += 1
                print(f"  🔄 Balanced: {player['player_name']} ({large_team['team_name']} → {small_team['team_name']})")
    
    if transfers > 0:
        print(f"✅ Balanced {transfers} players across squads")
    
    return transfers


async def get_npc_transfer_summary(week: int):
    """Get summary of NPC transfers this week"""
    
    async with db.pool.acquire() as conn:
        transfers = await conn.fetch("""
            SELECT t.*, n.player_name, n.position, n.overall_rating,
                   t1.team_name as from_team_name, t2.team_name as to_team_name
            FROM transfers t
            LEFT JOIN npc_players n ON t.npc_id = n.npc_id
            LEFT JOIN teams t1 ON t.from_team = t1.team_id
            LEFT JOIN teams t2 ON t.to_team = t2.team_id
            WHERE t.transfer_date >= NOW() - INTERVAL '7 days'
            AND t.npc_id IS NOT NULL
            ORDER BY t.fee DESC
            LIMIT 10
        """)
    
    return [dict(t) for t in transfers]
