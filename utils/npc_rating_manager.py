"""
NPC Rating Manager - Keeps NPC players competitive with user players
Automatically maintains balance over time
"""
from database import db
import random


async def weekly_npc_maintenance(week_number: int):
    """
    Call this at the end of each week to maintain NPC balance
    
    Every 5 weeks: Improve ~30% of NPCs
    Every 10 weeks: Balance teams with user players
    """
    print(f"🔧 Running NPC maintenance for Week {week_number}...")
    
    # Every 5 weeks, improve some NPCs
    if week_number % 5 == 0:
        await auto_update_npc_stats_periodically()
    
    # Every 10 weeks, check team balance
    if week_number % 10 == 0:
        async with db.pool.acquire() as conn:
            teams_with_users = await conn.fetch("""
                SELECT DISTINCT team_id 
                FROM players 
                WHERE retired = FALSE
            """)
            
            for team in teams_with_users:
                await balance_team_strength(team['team_id'])
    
    print(f"✅ NPC maintenance complete for Week {week_number}")


async def auto_update_npc_stats_periodically():
    """
    Automatically update individual NPC stats to keep pace with training
    Randomly improves ~30% of NPCs to simulate their "training"
    """
    async with db.pool.acquire() as conn:
        # Randomly improve some domestic NPCs
        result = await conn.execute("""
            UPDATE npc_players
            SET 
                pace = LEAST(99, pace + FLOOR(RANDOM() * 2)),
                shooting = LEAST(99, shooting + FLOOR(RANDOM() * 2)),
                passing = LEAST(99, passing + FLOOR(RANDOM() * 2)),
                dribbling = LEAST(99, dribbling + FLOOR(RANDOM() * 2)),
                defending = LEAST(99, defending + FLOOR(RANDOM() * 2)),
                physical = LEAST(99, physical + FLOOR(RANDOM() * 2)),
                overall_rating = LEAST(99, overall_rating + 1)
            WHERE retired = FALSE
            AND RANDOM() < 0.3
        """)
        
        # Also update European NPCs
        await conn.execute("""
            UPDATE european_npc_players
            SET 
                pace = LEAST(99, pace + FLOOR(RANDOM() * 2)),
                shooting = LEAST(99, shooting + FLOOR(RANDOM() * 2)),
                passing = LEAST(99, passing + FLOOR(RANDOM() * 2)),
                dribbling = LEAST(99, dribbling + FLOOR(RANDOM() * 2)),
                defending = LEAST(99, defending + FLOOR(RANDOM() * 2)),
                physical = LEAST(99, physical + FLOOR(RANDOM() * 2)),
                overall_rating = LEAST(99, overall_rating + 1)
            WHERE retired = FALSE
            AND RANDOM() < 0.3
        """)
        
        print("✅ Auto-updated ~30% of NPC players")


async def balance_team_strength(team_id: str):
    """
    Balance a specific team's NPC ratings based on user player strength
    Prevents huge gaps between star players and their NPC teammates
    """
    async with db.pool.acquire() as conn:
        # Get user players on this team
        user_players = await conn.fetch("""
            SELECT overall_rating 
            FROM players 
            WHERE team_id = $1 AND retired = FALSE
        """, team_id)
        
        if not user_players:
            return  # No user players, no need to balance
        
        avg_user_rating = sum(p['overall_rating'] for p in user_players) / len(user_players)
        
        # Get NPC players
        npc_players = await conn.fetch("""
            SELECT npc_id, overall_rating, position
            FROM npc_players
            WHERE team_id = $1 AND retired = FALSE
        """, team_id)
        
        if not npc_players:
            return
        
        avg_npc_rating = sum(p['overall_rating'] for p in npc_players) / len(npc_players)
        
        # If NPCs are more than 8 points behind users, boost them gradually
        if avg_user_rating - avg_npc_rating > 8:
            boost_amount = min(3, int((avg_user_rating - avg_npc_rating) * 0.3))
            
            await conn.execute("""
                UPDATE npc_players
                SET overall_rating = LEAST(99, overall_rating + $1),
                    pace = LEAST(99, pace + $1),
                    shooting = LEAST(99, shooting + $1),
                    passing = LEAST(99, passing + $1),
                    dribbling = LEAST(99, dribbling + $1),
                    defending = LEAST(99, defending + $1),
                    physical = LEAST(99, physical + $1)
                WHERE team_id = $2 AND retired = FALSE
            """, boost_amount, team_id)
            
            print(f"✅ Boosted NPCs on {team_id} by +{boost_amount} (user avg: {avg_user_rating:.1f})")


async def season_start_npc_update():
    """
    Major NPC update at season start
    Brings all NPCs closer to league average user ratings
    """
    print("🔄 Starting season NPC update...")
    
    async with db.pool.acquire() as conn:
        # Get average user player rating by league
        league_averages = await conn.fetch("""
            SELECT 
                p.league,
                AVG(p.overall_rating) as avg_rating,
                COUNT(*) as user_count
            FROM players p
            WHERE p.retired = FALSE
            GROUP BY p.league
        """)
        
        for league_data in league_averages:
            league = league_data['league']
            avg_user_rating = float(league_data['avg_rating'])
            
            # Update NPCs in this league to stay within reasonable distance
            await conn.execute("""
                UPDATE npc_players
                SET overall_rating = LEAST(99, GREATEST(60, 
                    overall_rating + FLOOR(($1 - overall_rating) * 0.3)
                ))
                WHERE team_id IN (
                    SELECT team_id FROM teams WHERE league = $2
                )
                AND retired = FALSE
            """, avg_user_rating, league)
            
            print(f"✅ Updated NPC ratings in {league} (target: {avg_user_rating:.1f})")
        
        # Boost elite teams
        await boost_elite_npcs()
        
        print("✅ Season NPC update complete!")


async def boost_elite_npcs():
    """
    Boost ratings for NPCs on top teams to maintain realism
    Elite teams should have 80+ rated players
    """
    async with db.pool.acquire() as conn:
        # Premier League elite teams
        elite_teams = [
            'man_city', 'arsenal', 'liverpool', 'chelsea', 
            'man_united', 'tottenham', 'newcastle'
        ]
        
        for team_id in elite_teams:
            await conn.execute("""
                UPDATE npc_players
                SET overall_rating = LEAST(99, overall_rating + 3),
                    pace = LEAST(99, pace + 2),
                    shooting = LEAST(99, shooting + 2),
                    passing = LEAST(99, passing + 2),
                    dribbling = LEAST(99, dribbling + 2),
                    defending = LEAST(99, defending + 2),
                    physical = LEAST(99, physical + 2)
                WHERE team_id = $1
                AND retired = FALSE
                AND overall_rating < 85
            """, team_id)
        
        print(f"✅ Boosted {len(elite_teams)} elite teams")


async def get_accurate_team_strength(team_id: str, is_home: bool = False) -> int:
    """
    Calculate team strength using WEIGHTED average
    User players count 1.5x more than NPCs
    This is used by match_engine for NPC simulations
    """
    async with db.pool.acquire() as conn:
        # User players (weight: 1.5x)
        user_players = await conn.fetch("""
            SELECT overall_rating FROM players 
            WHERE team_id = $1 AND retired = FALSE
        """, team_id)
        
        # NPC players (weight: 1.0x)
        npc_players = await conn.fetch("""
            SELECT overall_rating FROM npc_players 
            WHERE team_id = $1 AND retired = FALSE
        """, team_id)
        
        # European players (weight: 1.0x)
        european_players = await conn.fetch("""
            SELECT overall_rating FROM european_npc_players 
            WHERE team_id = $1 AND retired = FALSE
        """, team_id)
    
    # Calculate WEIGHTED average
    total_weight = 0
    total_rating = 0
    
    # User players count 1.5x
    for player in user_players:
        total_rating += player['overall_rating'] * 1.5
        total_weight += 1.5
    
    # NPCs count 1.0x
    for player in npc_players:
        total_rating += player['overall_rating']
        total_weight += 1.0
    
    for player in european_players:
        total_rating += player['overall_rating']
        total_weight += 1.0
    
    if total_weight == 0:
        return 50  # Default for empty teams
    
    avg_rating = total_rating / total_weight
    
    # Team quality modifier
    if avg_rating >= 85:
        team_modifier = 25
    elif avg_rating >= 80:
        team_modifier = 20
    elif avg_rating >= 75:
        team_modifier = 15
    elif avg_rating >= 70:
        team_modifier = 10
    elif avg_rating >= 65:
        team_modifier = 5
    else:
        team_modifier = 0
    
    # Home advantage
    home_bonus = 5 if is_home else 0
    
    strength = int(avg_rating + team_modifier + home_bonus)
    return min(strength, 95)
