"""
NPC Transfer System - NPCs move between teams realistically
Runs during transfer windows
FIXED: Only executes during transfer windows (failsafe protection)
"""

from database import db
import random
import config

async def execute_npc_transfers(week: int):
    """Execute NPC transfers during transfer windows"""
    
    # Only run during transfer windows
    if week not in config.TRANSFER_WINDOW_WEEKS:
        return 0
    
    print(f"🔄 Processing NPC transfers for Week {week}...")
    
    # Get transfer candidates (aged 20-32, not top stars)
    async with db.pool.acquire() as conn:
        transfer_candidates = await conn.fetch("""
            SELECT n.*, t.league 
            FROM npc_players n
            LEFT JOIN teams t ON n.team_id = t.team_id
            WHERE n.retired = FALSE 
            AND n.age BETWEEN 20 AND 32
            AND n.overall_rating BETWEEN 60 AND 85
            AND n.team_id IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 20
        """)
    
    transfers_made = 0
    
    for candidate in transfer_candidates:
        # 25% chance to transfer (more realistic than 20%)
        if random.random() > 0.25:
            continue
        
        candidate = dict(candidate)
        current_league = candidate['league']
        rating = candidate['overall_rating']
        
        # Determine potential new leagues based on rating
        potential_leagues = []
        if rating >= 78:
            potential_leagues.append('Premier League')
        if rating >= 68:
            potential_leagues.append('Championship')
        if rating >= 58:
            potential_leagues.append('League One')
        
        # 60% lateral moves, 40% up/down
        if random.random() < 0.6 and current_league in potential_leagues:
            # Stay in same league
            target_league = current_league
        else:
            # Move up or down
            if current_league in potential_leagues:
                potential_leagues.remove(current_league)
            if not potential_leagues:
                continue
            target_league = random.choice(potential_leagues)
        
        # Find a random team in target league (not current team)
        async with db.pool.acquire() as conn:
            new_team = await conn.fetchrow("""
                SELECT team_id, team_name, league
                FROM teams
                WHERE league = $1 AND team_id != $2
                ORDER BY RANDOM()
                LIMIT 1
            """, target_league, candidate['team_id'])
        
        if not new_team:
            continue
        
        new_team = dict(new_team)
        
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
            old_team = await conn.fetchrow(
                "SELECT team_name FROM teams WHERE team_id = $1",
                candidate['team_id']
            )
            
            # Update NPC player team
            await conn.execute("""
                UPDATE npc_players
                SET team_id = $1
                WHERE npc_id = $2
            """, new_team['team_id'], candidate['npc_id'])
            
            # Record in transfers table
            await conn.execute("""
                INSERT INTO transfers (
                    npc_id, from_team, to_team, fee, wage, 
                    contract_length, transfer_type, season
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, 
                candidate['npc_id'],
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
