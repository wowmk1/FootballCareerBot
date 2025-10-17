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
