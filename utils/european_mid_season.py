"""
Mid-Season European Start - Simulates Missed Weeks
"""

from database import db
import config

async def simulate_missed_european_weeks(missed_weeks, season):
    """Simulate all missed European weeks to catch up"""
    print(f"🏆 Simulating {len(missed_weeks)} missed weeks...")
    
    matches_simulated = 0
    
    async with db.pool.acquire() as conn:
        for week in missed_weeks:
            fixtures = await conn.fetch("""
                SELECT * FROM european_fixtures
                WHERE week_number = $1 AND season = $2 AND stage = 'group'
            """, week, season)
            
            for fixture in fixtures:
                from utils.match_engine import simulate_npc_match
                
                result = await simulate_npc_match(
                    fixture['home_team_id'],
                    fixture['away_team_id'],
                    is_european=True
                )
                
                await conn.execute("""
                    UPDATE european_fixtures
                    SET home_score = $1, away_score = $2, played = TRUE
                    WHERE fixture_id = $3
                """, result['home_score'], result['away_score'], fixture['fixture_id'])
                
                await update_standings(
                    conn, fixture['competition'], fixture['group_name'],
                    fixture['home_team_id'], fixture['away_team_id'],
                    result['home_score'], result['away_score']
                )
                
                matches_simulated += 1
            
            print(f"  ✅ Week {week}: {len(fixtures)} matches")
    
    print(f"🎉 Done! {matches_simulated} matches simulated")
    
    return {
        'matches_simulated': matches_simulated,
        'weeks_simulated': len(missed_weeks)
    }

async def update_standings(conn, comp, group, home, away, home_score, away_score):
    """Update group standings after simulated match"""
    
    if home_score > away_score:
        await conn.execute("""
            UPDATE european_groups
            SET played = played + 1, won = won + 1, 
                goals_for = goals_for + $1, goals_against = goals_against + $2,
                points = points + 3
            WHERE competition = $3 AND group_name = $4 AND team_id = $5
        """, home_score, away_score, comp, group, home)
        
        await conn.execute("""
            UPDATE european_groups
            SET played = played + 1, lost = lost + 1,
                goals_for = goals_for + $1, goals_against = goals_against + $2
            WHERE competition = $3 AND group_name = $4 AND team_id = $5
        """, away_score, home_score, comp, group, away)
    
    elif away_score > home_score:
        await conn.execute("""
            UPDATE european_groups
            SET played = played + 1, lost = lost + 1,
                goals_for = goals_for + $1, goals_against = goals_against + $2
            WHERE competition = $3 AND group_name = $4 AND team_id = $5
        """, home_score, away_score, comp, group, home)
        
        await conn.execute("""
            UPDATE european_groups
            SET played = played + 1, won = won + 1,
                goals_for = goals_for + $1, goals_against = goals_against + $2,
                points = points + 3
            WHERE competition = $3 AND group_name = $4 AND team_id = $5
        """, away_score, home_score, comp, group, away)
    else:
        for team in [home, away]:
            await conn.execute("""
                UPDATE european_groups
                SET played = played + 1, drawn = drawn + 1,
                    goals_for = goals_for + $1, goals_against = goals_against + $2,
                    points = points + 1
                WHERE competition = $3 AND group_name = $4 AND team_id = $5
            """, home_score, away_score, comp, group, team)


async def simulate_full_european_season(season, current_week):
    """Simulate ENTIRE European season to completion"""
    print(f"🏆 Simulating FULL European season...")
    
    group_matches = 0
    knockout_matches = 0
    
    async with db.pool.acquire() as conn:
        # Use transaction for data consistency
        async with conn.transaction():
            # Simulate all remaining group stage matches
            remaining_group_weeks = [w for w in config.GROUP_STAGE_WEEKS if w >= current_week]
            
            if remaining_group_weeks:
                group_results = await simulate_missed_european_weeks(remaining_group_weeks, season)
                group_matches = group_results['matches_simulated']
            
            # Simulate all knockout stages
            from utils.european_competitions import (
                generate_knockout_draw,
                close_knockout_round
            )
            
            # R16
            await generate_knockout_draw('CL', 'r16', season)
            await generate_knockout_draw('EL', 'r16', season)
            knockout_matches += await simulate_knockout_stage('CL', 'r16', season, conn)
            knockout_matches += await simulate_knockout_stage('EL', 'r16', season, conn)
            await close_knockout_round('CL', 'r16', season)
            await close_knockout_round('EL', 'r16', season)
            
            # Quarters
            await generate_knockout_draw('CL', 'quarters', season)
            await generate_knockout_draw('EL', 'quarters', season)
            knockout_matches += await simulate_knockout_stage('CL', 'quarters', season, conn)
            knockout_matches += await simulate_knockout_stage('EL', 'quarters', season, conn)
            await close_knockout_round('CL', 'quarters', season)
            await close_knockout_round('EL', 'quarters', season)
            
            # Semis
            await generate_knockout_draw('CL', 'semis', season)
            await generate_knockout_draw('EL', 'semis', season)
            knockout_matches += await simulate_knockout_stage('CL', 'semis', season, conn)
            knockout_matches += await simulate_knockout_stage('EL', 'semis', season, conn)
            await close_knockout_round('CL', 'semis', season)
            await close_knockout_round('EL', 'semis', season)
            
            # Finals
            await generate_knockout_draw('CL', 'final', season)
            await generate_knockout_draw('EL', 'final', season)
            knockout_matches += await simulate_knockout_stage('CL', 'final', season, conn)
            knockout_matches += await simulate_knockout_stage('EL', 'final', season, conn)
            await close_knockout_round('CL', 'final', season)
            await close_knockout_round('EL', 'final', season)
            
            # Get winners
            cl_winner = await conn.fetchrow("""
                SELECT k.winner_team_id,
                       COALESCE(t.team_name, et.team_name) as team_name
                FROM european_knockout k
                LEFT JOIN teams t ON k.winner_team_id = t.team_id
                LEFT JOIN european_teams et ON k.winner_team_id = et.team_id
                WHERE k.competition = 'CL' AND k.stage = 'final' AND k.season = $1
                  AND k.winner_team_id IS NOT NULL
            """, season)
            
            el_winner = await conn.fetchrow("""
                SELECT k.winner_team_id,
                       COALESCE(t.team_name, et.team_name) as team_name
                FROM european_knockout k
                LEFT JOIN teams t ON k.winner_team_id = t.team_id
                LEFT JOIN european_teams et ON k.winner_team_id = et.team_id
                WHERE k.competition = 'EL' AND k.stage = 'final' AND k.season = $1
                  AND k.winner_team_id IS NOT NULL
            """, season)
    
    print(f"🎉 Full season simulated!")
    print(f"🏆 CL Winner: {cl_winner['team_name'] if cl_winner else 'N/A'}")
    print(f"🏆 EL Winner: {el_winner['team_name'] if el_winner else 'N/A'}")
    
    return {
        'group_matches': group_matches,
        'knockout_matches': knockout_matches,
        'cl_winner': cl_winner['team_name'] if cl_winner else 'Unknown',
        'el_winner': el_winner['team_name'] if el_winner else 'Unknown'
    }


async def simulate_knockout_stage(competition, stage, season, conn):
    """Simulate all matches in a knockout stage and determine winners"""
    from utils.match_engine import simulate_npc_match
    import random
    
    matches = 0
    is_final = (stage == 'final')
    
    # Get all fixtures for this stage
    fixtures = await conn.fetch("""
        SELECT * FROM european_fixtures
        WHERE competition = $1 AND stage = $2 AND season = $3 AND played = FALSE
        ORDER BY knockout_id, leg
    """, competition, stage, season)
    
    # Simulate all matches
    for fixture in fixtures:
        result = await simulate_npc_match(
            fixture['home_team_id'],
            fixture['away_team_id'],
            is_european=True
        )
        
        await conn.execute("""
            UPDATE european_fixtures
            SET home_score = $1, away_score = $2, played = TRUE
            WHERE fixture_id = $3
        """, result['home_score'], result['away_score'], fixture['fixture_id'])
        
        matches += 1
    
    # Determine winners for each tie
    if is_final:
        # Finals are single leg
        for fixture in fixtures:
            fixture_updated = await conn.fetchrow("""
                SELECT * FROM european_fixtures
                WHERE fixture_id = $1
            """, fixture['fixture_id'])
            
            winner_id = determine_single_leg_winner(
                fixture_updated['home_team_id'],
                fixture_updated['away_team_id'],
                fixture_updated['home_score'],
                fixture_updated['away_score']
            )
            
            await conn.execute("""
                UPDATE european_knockout
                SET winner_team_id = $1
                WHERE knockout_id = $2
            """, winner_id, fixture_updated['knockout_id'])
    else:
        # Two-legged ties - group by knockout_id
        knockout_ids = set(f['knockout_id'] for f in fixtures)
        
        for ko_id in knockout_ids:
            legs = await conn.fetch("""
                SELECT * FROM european_fixtures
                WHERE knockout_id = $1 AND played = TRUE
                ORDER BY leg
            """, ko_id)
            
            if len(legs) == 2:
                winner_id = determine_two_leg_winner(legs[0], legs[1])
                
                await conn.execute("""
                    UPDATE european_knockout
                    SET winner_team_id = $1
                    WHERE knockout_id = $2
                """, winner_id, ko_id)
    
    return matches


def determine_single_leg_winner(home_id, away_id, home_score, away_score):
    """Determine winner of single-leg match (with ET/penalties if needed)"""
    import random
    
    if home_score > away_score:
        return home_id
    elif away_score > home_score:
        return away_id
    else:
        # Simulate extra time
        et_home = random.randint(0, 2)
        et_away = random.randint(0, 2)
        
        if et_home > et_away:
            return home_id
        elif et_away > et_home:
            return away_id
        else:
            # Penalties - 50/50
            return random.choice([home_id, away_id])


def determine_two_leg_winner(leg1, leg2):
    """Determine winner of two-legged tie with away goals rule"""
    import random
    
    # leg1: first leg, leg2: second leg (return leg)
    # Aggregate scores
    team1_id = leg1['home_team_id']
    team2_id = leg1['away_team_id']
    
    team1_goals = leg1['home_score'] + leg2['away_score']
    team2_goals = leg1['away_score'] + leg2['home_score']
    
    if team1_goals > team2_goals:
        return team1_id
    elif team2_goals > team1_goals:
        return team2_id
    else:
        # Check away goals
        team1_away = leg2['away_score']
        team2_away = leg1['away_score']
        
        if team1_away > team2_away:
            return team1_id
        elif team2_away > team1_away:
            return team2_id
        else:
            # Extra time in second leg (simplified - just add random goals)
            et_home = random.randint(0, 2)
            et_away = random.randint(0, 2)
            
            if et_home > et_away:
                return leg2['home_team_id']
            elif et_away > et_home:
                return leg2['away_team_id']
            else:
                # Penalties
                return random.choice([team1_id, team2_id])
