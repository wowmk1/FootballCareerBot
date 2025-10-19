"""
European Competition Management System
Groups, Knockout Stages, Fixtures, Standings

✅ UPDATED: Now adds match results to news database
✅ FIXED: Creates 12 fixtures per group (full round-robin)
"""

import random
from datetime import datetime
from database import db
import config

async def draw_groups(season='2027/28'):
    """Draw Champions League and Europa League groups"""
    print("🏆 Drawing European groups...")
    
    async with db.pool.acquire() as conn:
        # Get qualified English teams based on current standings
        standings = await conn.fetch("""
            SELECT team_id, position
            FROM teams
            WHERE league = 'Premier League'
            ORDER BY points DESC, (goals_for - goals_against) DESC, goals_for DESC
        """)
        
        cl_teams = []
        el_teams = []
        
        for i, row in enumerate(standings, 1):
            # Update position field for accuracy
            await conn.execute(
                "UPDATE teams SET position = $1 WHERE team_id = $2",
                i, row['team_id']
            )
            
            if i in config.CL_QUALIFICATION_POSITIONS['Premier League']:
                cl_teams.append(row['team_id'])
            elif i in config.EL_QUALIFICATION_POSITIONS['Premier League']:
                el_teams.append(row['team_id'])
        
        # Get all European teams
        all_euro = await conn.fetch("SELECT team_id FROM european_teams")
        euro_ids = [t['team_id'] for t in all_euro]
        
        # Champions League: 28 European + up to 4 English
        cl_pool = random.sample(euro_ids, min(28, len(euro_ids))) + cl_teams
        random.shuffle(cl_pool)
        cl_pool = cl_pool[:32]
        
        # Europa League: remaining European + up to 2 English
        remaining = [t for t in euro_ids if t not in cl_pool]
        el_pool = random.sample(remaining, min(30, len(remaining))) + el_teams
        random.shuffle(el_pool)
        el_pool = el_pool[:32]
        
        # Create groups
        await create_groups(conn, 'CL', cl_pool, season)
        await create_groups(conn, 'EL', el_pool, season)
        
        print("✅ Groups drawn!")

async def create_groups(conn, competition, teams, season):
    """Create groups and fixtures"""
    groups = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    
    for i, group_name in enumerate(groups):
        group_teams = teams[i*4:(i+1)*4]
        
        for team_id in group_teams:
            await conn.execute("""
                INSERT INTO european_groups 
                (competition, group_name, team_id, season)
                VALUES ($1, $2, $3, $4)
            """, competition, group_name, team_id, season)
        
        await create_group_fixtures(conn, competition, group_name, group_teams, season)

async def create_group_fixtures(conn, competition, group_name, teams, season):
    """
    Create all fixtures for a group (FULL ROUND-ROBIN)
    
    ✅ FIXED: Now creates 12 fixtures per group (each team plays all others home & away)
    """
    match_weeks = config.GROUP_STAGE_WEEKS
    
    # Create FULL round-robin: each team plays every other team HOME and AWAY
    fixtures = []
    for i in range(len(teams)):
        for j in range(len(teams)):
            if i != j:  # Don't play yourself
                fixtures.append((teams[i], teams[j]))
    
    # Now we have 12 fixtures (4 teams: each plays 3 others × 2 = 12 total)
    random.shuffle(fixtures)
    
    # Distribute 12 fixtures across 6 matchdays (2 matches per matchday)
    for idx, (home, away) in enumerate(fixtures):
        match_day_num = (idx // 2) + 1  # Matchdays 1-6 (2 matches per day)
        week_idx = (idx // 2) % 6  # Cycle through 6 weeks
        week = match_weeks[week_idx]
        
        await conn.execute("""
            INSERT INTO european_fixtures
            (competition, stage, group_name, home_team_id, away_team_id, 
             week_number, season, match_day)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, competition, 'group', group_name, home, away, week, season, match_day_num)

async def generate_knockout_draw(competition, stage, season):
    """Generate knockout stage draw"""
    print(f"🏆 Drawing {stage} for {competition}...")
    
    async with db.pool.acquire() as conn:
        if stage == 'r16':
            winners = []
            runners_up = []
            
            groups = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
            for group in groups:
                standings = await conn.fetch("""
                    SELECT team_id, group_name, points, 
                           (goals_for - goals_against) as gd
                    FROM european_groups
                    WHERE competition = $1 AND group_name = $2 AND season = $3
                    ORDER BY points DESC, gd DESC, goals_for DESC
                    LIMIT 2
                """, competition, group, season)
                
                if len(standings) >= 2:
                    winners.append(dict(standings[0]))
                    runners_up.append(dict(standings[1]))
            
            random.shuffle(winners)
            random.shuffle(runners_up)
            
            for i in range(8):
                winner = winners[i]
                runner = runners_up[i]
                
                if winner['group_name'] == runner['group_name'] and i < 7:
                    runners_up[i], runners_up[i+1] = runners_up[i+1], runners_up[i]
                    runner = runners_up[i]
                
                await conn.execute("""
                    INSERT INTO european_knockout
                    (competition, stage, home_team_id, away_team_id, season)
                    VALUES ($1, $2, $3, $4, $5)
                """, competition, stage, winner['team_id'], runner['team_id'], season)
        
        else:
            prev_stage = {'quarters': 'r16', 'semis': 'quarters', 'final': 'semis'}[stage]
            
            winners = await conn.fetch("""
                SELECT winner_team_id
                FROM european_knockout
                WHERE competition = $1 AND stage = $2 AND season = $3
                AND winner_team_id IS NOT NULL
            """, competition, prev_stage, season)
            
            winner_ids = [w['winner_team_id'] for w in winners]
            random.shuffle(winner_ids)
            
            for i in range(0, len(winner_ids), 2):
                if i+1 < len(winner_ids):
                    await conn.execute("""
                        INSERT INTO european_knockout
                        (competition, stage, home_team_id, away_team_id, season)
                        VALUES ($1, $2, $3, $4, $5)
                    """, competition, stage, winner_ids[i], winner_ids[i+1], season)
        
        await create_knockout_fixtures(conn, competition, stage, season)
        print(f"✅ {stage.upper()} draw complete!")

async def create_knockout_fixtures(conn, competition, stage, season):
    """Create knockout fixtures"""
    if stage == 'r16':
        weeks = config.KNOCKOUT_R16_WEEKS
        match_day = 1  # R16 is match day 1 of knockouts
    elif stage == 'quarters':
        weeks = config.KNOCKOUT_QF_WEEKS
        match_day = 2  # QF is match day 2
    elif stage == 'semis':
        weeks = config.KNOCKOUT_SF_WEEKS
        match_day = 3  # SF is match day 3
    else:
        weeks = [config.KNOCKOUT_FINAL_WEEK]
        match_day = 4  # Final is match day 4
    
    ties = await conn.fetch("""
        SELECT tie_id, home_team_id, away_team_id
        FROM european_knockout
        WHERE competition = $1 AND stage = $2 AND season = $3
    """, competition, stage, season)
    
    for tie in ties:
        await conn.execute("""
            INSERT INTO european_fixtures
            (competition, stage, home_team_id, away_team_id, week_number, season, leg, tie_id, match_day)
            VALUES ($1, $2, $3, $4, $5, $6, 1, $7, $8)
        """, competition, stage, tie['home_team_id'], tie['away_team_id'], 
             weeks[0], season, tie['tie_id'], match_day)
        
        if stage != 'final':
            await conn.execute("""
                INSERT INTO european_fixtures
                (competition, stage, home_team_id, away_team_id, week_number, season, leg, tie_id, match_day)
                VALUES ($1, $2, $3, $4, $5, $6, 2, $7, $8)
            """, competition, stage, tie['away_team_id'], tie['home_team_id'], 
                 weeks[1], season, tie['tie_id'], match_day)

async def close_knockout_round(competition, stage, season):
    """Process knockout round results"""
    print(f"🏆 Processing {stage} results...")
    
    async with db.pool.acquire() as conn:
        ties = await conn.fetch("""
            SELECT * FROM european_knockout
            WHERE competition = $1 AND stage = $2 AND season = $3
        """, competition, stage, season)
        
        for tie in ties:
            if stage == 'final':
                fixture = await conn.fetchrow("""
                    SELECT * FROM european_fixtures
                    WHERE tie_id = $1 AND leg = 1
                """, tie['tie_id'])
                
                if fixture['home_score'] > fixture['away_score']:
                    winner = fixture['home_team_id']
                elif fixture['away_score'] > fixture['home_score']:
                    winner = fixture['away_team_id']
                else:
                    winner = random.choice([fixture['home_team_id'], fixture['away_team_id']])
                    await conn.execute("""
                        UPDATE european_knockout
                        SET penalties_taken = TRUE, penalty_winner = $1
                        WHERE tie_id = $2
                    """, winner, tie['tie_id'])
            else:
                fixtures = await conn.fetch("""
                    SELECT * FROM european_fixtures
                    WHERE tie_id = $1
                    ORDER BY leg
                """, tie['tie_id'])
                
                if len(fixtures) < 2:
                    continue
                
                agg_home = fixtures[0]['home_score'] + fixtures[1]['away_score']
                agg_away = fixtures[0]['away_score'] + fixtures[1]['home_score']
                
                if agg_home > agg_away:
                    winner = tie['home_team_id']
                elif agg_away > agg_home:
                    winner = tie['away_team_id']
                else:
                    winner = random.choice([tie['home_team_id'], tie['away_team_id']])
                    await conn.execute("""
                        UPDATE european_knockout
                        SET penalties_taken = TRUE, penalty_winner = $1
                        WHERE tie_id = $2
                    """, winner, tie['tie_id'])
                
                await conn.execute("""
                    UPDATE european_knockout
                    SET first_leg_home_score = $1, first_leg_away_score = $2,
                        second_leg_home_score = $3, second_leg_away_score = $4,
                        aggregate_home = $5, aggregate_away = $6, winner_team_id = $7,
                        first_leg_played = TRUE, second_leg_played = TRUE
                    WHERE tie_id = $8
                """, fixtures[0]['home_score'], fixtures[0]['away_score'],
                     fixtures[1]['home_score'], fixtures[1]['away_score'],
                     agg_home, agg_away, winner, tie['tie_id'])
            
            await conn.execute("""
                UPDATE european_knockout
                SET winner_team_id = $1
                WHERE tie_id = $2
            """, winner, tie['tie_id'])
        
        print(f"✅ {stage.upper()} complete!")

async def open_european_window(current_week):
    """Open European match window"""
    async with db.pool.acquire() as conn:
        if current_week not in config.EUROPEAN_MATCH_WEEKS:
            return False
        
        await conn.execute("""
            UPDATE european_fixtures
            SET playable = TRUE
            WHERE week_number = $1 AND played = FALSE
        """, current_week)
        
        print(f"🏆 European window OPENED for week {current_week}")
        return True

async def close_european_window(current_week, bot=None, competition=None):
    """
    Close European window and simulate matches
    competition: 'CL', 'EL', or None (simulates both)
    
    ✅ UPDATED: Now adds match results to news database
    """
    async with db.pool.acquire() as conn:
        if competition:
            # Close specific competition
            unplayed = await conn.fetch("""
                SELECT * FROM european_fixtures
                WHERE week_number = $1 AND played = FALSE AND competition = $2
            """, current_week, competition)
        else:
            # Close both CL and EL
            unplayed = await conn.fetch("""
                SELECT * FROM european_fixtures
                WHERE week_number = $1 AND played = FALSE
            """, current_week)
        
        from utils.match_engine import match_engine
        
        for fixture in unplayed:
            result = await match_engine.simulate_npc_match(
                fixture['home_team_id'],
                fixture['away_team_id'],
                is_european=True
            )
            
            await conn.execute("""
                UPDATE european_fixtures
                SET home_score = $1, away_score = $2, played = TRUE, playable = FALSE
                WHERE fixture_id = $3
            """, result['home_score'], result['away_score'], fixture['fixture_id'])
            
            if fixture['stage'] == 'group':
                await update_group_standings(
                    conn, fixture['competition'], fixture['group_name'],
                    fixture['home_team_id'], fixture['away_team_id'],
                    result['home_score'], result['away_score']
                )
            
            # ✅ NEW: Add European match result to news database
            comp_name = "Champions League" if fixture['competition'] == 'CL' else "Europa League"
            
            # Import the helper function from season_manager
            from utils.season_manager import add_match_result_news
            
            await add_match_result_news(
                result['home_team'],
                result['away_team'],
                result['home_score'],
                result['away_score'],
                'match_news',  # Same category as league matches
                current_week,
                competition=comp_name
            )
        
        print(f"🏆 European window CLOSED. Simulated {len(unplayed)} matches")
        
        # Post to Discord channels (existing functionality)
        if bot:
            from utils.event_poster import post_european_results
            if competition:
                await post_european_results(bot, competition, current_week)
            else:
                # Post results for both competitions
                competitions = set(f['competition'] for f in unplayed)
                for comp in competitions:
                    await post_european_results(bot, comp, current_week)

async def update_group_standings(conn, comp, group, home, away, home_score, away_score):
    """Update group standings"""
    
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

async def get_group_standings(competition, group_name):
    """Get group standings"""
    async with db.pool.acquire() as conn:
        standings = await conn.fetch("""
            SELECT g.*, 
                   COALESCE(t.team_name, et.team_name) as team_name,
                   (g.goals_for - g.goals_against) as goal_difference
            FROM european_groups g
            LEFT JOIN teams t ON g.team_id = t.team_id
            LEFT JOIN european_teams et ON g.team_id = et.team_id
            WHERE g.competition = $1 AND g.group_name = $2
            ORDER BY g.points DESC, goal_difference DESC, g.goals_for DESC
        """, competition, group_name)
        
        return [dict(row) for row in standings]
