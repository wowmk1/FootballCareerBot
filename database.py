import asyncpg
import config
import json
import random
from datetime import datetime

class Database:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        """Connect to PostgreSQL database"""
        self.pool = await asyncpg.create_pool(
            config.DATABASE_URL,
            min_size=1,
            max_size=10
        )
        await self.create_tables()
        
        # Run transfer window migration
        await self.migrate_transfer_windows()
        
        # Add performance indexes
        await self.add_performance_indexes()
        
        print("✅ Database connected")
    
    async def add_performance_indexes(self):
        """Add performance indexes to database"""
        try:
            async with self.pool.acquire() as conn:
                indexes = [
                    'CREATE INDEX IF NOT EXISTS idx_players_team_id ON players(team_id)',
                    'CREATE INDEX IF NOT EXISTS idx_fixtures_week ON fixtures(week_number)',
                    'CREATE INDEX IF NOT EXISTS idx_fixtures_playable ON fixtures(playable, played)',
                    'CREATE INDEX IF NOT EXISTS idx_match_participants_user ON match_participants(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_match_participants_match ON match_participants(match_id)',
                    'CREATE INDEX IF NOT EXISTS idx_news_user_created ON news(user_id, created_at DESC)',
                    'CREATE INDEX IF NOT EXISTS idx_training_user_date ON training_history(user_id, training_date DESC)',
                    'CREATE INDEX IF NOT EXISTS idx_players_retired ON players(retired, age)',
                    'CREATE INDEX IF NOT EXISTS idx_npc_players_team ON npc_players(team_id, retired)',
                    'CREATE INDEX IF NOT EXISTS idx_transfer_offers_user ON transfer_offers(user_id, status)',
                    'CREATE INDEX IF NOT EXISTS idx_match_events_fixture ON match_events(fixture_id, minute)'
                    'CREATE INDEX IF NOT EXISTS idx_players_last_reminded ON players(last_reminded)',
                    'CREATE INDEX IF NOT EXISTS idx_transfer_offers_week ON transfer_offers(offer_week)',
                    'CREATE INDEX IF NOT EXISTS idx_fixtures_week_playable ON fixtures(week_number, playable, played)',
                ]
                
                for index_sql in indexes:
                    await conn.execute(index_sql)
                
                print("✅ Performance indexes verified")
        except Exception as e:
            print(f"⚠️ Index creation warning: {e}")
    
    async def migrate_transfer_windows(self):
        """Migrate database for transfer window system"""
        try:
            async with self.pool.acquire() as conn:
                # Check if migration already ran
                result = await conn.fetchrow("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'transfer_offers'
                    )
                """)
                
                if result['exists']:
                    print("✅ Transfer window tables already exist")
                    return
                
                print("🔄 Running transfer window migration...")
                
                # Add new columns to players table
                await conn.execute("""
                    ALTER TABLE players 
                    ADD COLUMN IF NOT EXISTS last_transfer_window INTEGER
                """)
                print("  ✅ Added last_transfer_window column")
                
                await conn.execute("""
                    ALTER TABLE players 
                    ADD COLUMN IF NOT EXISTS transfers_this_season INTEGER DEFAULT 0
                """)
                print("  ✅ Added transfers_this_season column")
                
                # Create transfer_offers table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS transfer_offers (
                        offer_id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        team_id TEXT NOT NULL,
                        wage_offer INTEGER NOT NULL,
                        contract_length INTEGER NOT NULL,
                        offer_week INTEGER NOT NULL,
                        expires_week INTEGER NOT NULL,
                        offer_type TEXT DEFAULT 'standard',
                        previous_offer_id INTEGER,
                        performance_bonus INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("  ✅ Created transfer_offers table")
                
                # Create indexes
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_transfer_offers_user_status 
                    ON transfer_offers(user_id, status)
                """)
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_transfer_offers_week 
                    ON transfer_offers(offer_week)
                """)
                print("  ✅ Created indexes")
                
                # Add column to game_state
                await conn.execute("""
                    ALTER TABLE game_state 
                    ADD COLUMN IF NOT EXISTS transfer_window_active BOOLEAN DEFAULT FALSE
                """)
                print("  ✅ Added transfer_window_active column")
                
                print("✅ Transfer window migration completed successfully!")
        except Exception as e:
            print(f"⚠️ Migration warning: {e}")
    
    async def create_tables(self):
        """Create all necessary tables"""
        
        async with self.pool.acquire() as conn:
            # Game state table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS game_state (
                    id INTEGER PRIMARY KEY,
                    season_started BOOLEAN DEFAULT FALSE,
                    current_season TEXT DEFAULT '2027/28',
                    current_week INTEGER DEFAULT 0,
                    current_year INTEGER DEFAULT 2027,
                    season_start_date TEXT,
                    last_match_day TEXT,
                    next_match_day TEXT,
                    match_window_open BOOLEAN DEFAULT FALSE,
                    match_window_closes TEXT,
                    fixtures_generated BOOLEAN DEFAULT FALSE,
                    CONSTRAINT game_state_check CHECK (id = 1)
                )
            ''')
            
            await conn.execute('''
                INSERT INTO game_state (id) VALUES (1) ON CONFLICT (id) DO NOTHING
            ''')
            
            # Players table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    user_id BIGINT PRIMARY KEY,
                    discord_username TEXT,
                    player_name TEXT NOT NULL,
                    position TEXT NOT NULL,
                    age INTEGER DEFAULT 18,
                    overall_rating INTEGER DEFAULT 60,
                    pace INTEGER DEFAULT 60,
                    shooting INTEGER DEFAULT 60,
                    passing INTEGER DEFAULT 60,
                    dribbling INTEGER DEFAULT 60,
                    defending INTEGER DEFAULT 40,
                    physical INTEGER DEFAULT 60,
                    potential INTEGER DEFAULT 75,
                    team_id TEXT DEFAULT 'free_agent',
                    league TEXT DEFAULT NULL,
                    contract_wage INTEGER DEFAULT 5000,
                    contract_years INTEGER DEFAULT 0,
                    form INTEGER DEFAULT 50,
                    morale INTEGER DEFAULT 75,
                    training_streak INTEGER DEFAULT 0,
                    last_training TEXT,
                    season_goals INTEGER DEFAULT 0,
                    season_assists INTEGER DEFAULT 0,
                    season_apps INTEGER DEFAULT 0,
                    season_rating REAL DEFAULT 0.0,
                    season_motm INTEGER DEFAULT 0,
                    career_goals INTEGER DEFAULT 0,
                    career_assists INTEGER DEFAULT 0,
                    career_apps INTEGER DEFAULT 0,
                    career_motm INTEGER DEFAULT 0,
                    injury_weeks INTEGER DEFAULT 0,
                    injury_type TEXT,
                    retired BOOLEAN DEFAULT FALSE,
                    retirement_date TEXT,
                    joined_week INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Teams table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    team_id TEXT PRIMARY KEY,
                    team_name TEXT NOT NULL,
                    league TEXT NOT NULL,
                    position INTEGER DEFAULT 10,
                    played INTEGER DEFAULT 0,
                    won INTEGER DEFAULT 0,
                    drawn INTEGER DEFAULT 0,
                    lost INTEGER DEFAULT 0,
                    goals_for INTEGER DEFAULT 0,
                    goals_against INTEGER DEFAULT 0,
                    points INTEGER DEFAULT 0,
                    budget INTEGER DEFAULT 50000000,
                    wage_budget INTEGER DEFAULT 100000,
                    form TEXT DEFAULT ''
                )
            ''')
            
            # NPC Players table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS npc_players (
                    npc_id SERIAL PRIMARY KEY,
                    player_name TEXT NOT NULL,
                    team_id TEXT,
                    position TEXT NOT NULL,
                    age INTEGER DEFAULT 25,
                    overall_rating INTEGER DEFAULT 75,
                    pace INTEGER DEFAULT 70,
                    shooting INTEGER DEFAULT 70,
                    passing INTEGER DEFAULT 70,
                    dribbling INTEGER DEFAULT 70,
                    defending INTEGER DEFAULT 50,
                    physical INTEGER DEFAULT 70,
                    season_goals INTEGER DEFAULT 0,
                    season_assists INTEGER DEFAULT 0,
                    season_apps INTEGER DEFAULT 0,
                    market_value INTEGER DEFAULT 10000000,
                    retired BOOLEAN DEFAULT FALSE,
                    is_regen BOOLEAN DEFAULT FALSE,
                    potential INTEGER DEFAULT 75
                )
            ''')
            
            # Fixtures table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS fixtures (
                    fixture_id SERIAL PRIMARY KEY,
                    home_team_id TEXT,
                    away_team_id TEXT,
                    competition TEXT DEFAULT 'Premier League',
                    league TEXT NOT NULL,
                    week_number INTEGER,
                    season TEXT DEFAULT '2027/28',
                    home_score INTEGER,
                    away_score INTEGER,
                    played BOOLEAN DEFAULT FALSE,
                    playable BOOLEAN DEFAULT FALSE,
                    match_date TEXT
                )
            ''')
            
            # Match events table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS match_events (
                    event_id SERIAL PRIMARY KEY,
                    fixture_id INTEGER,
                    user_id BIGINT,
                    npc_id INTEGER,
                    event_type TEXT,
                    minute INTEGER,
                    description TEXT,
                    dice_roll INTEGER,
                    stat_modifier INTEGER,
                    total_roll INTEGER,
                    difficulty_class INTEGER,
                    success BOOLEAN,
                    rating_impact REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Active matches table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS active_matches (
                    match_id SERIAL PRIMARY KEY,
                    fixture_id INTEGER UNIQUE,
                    home_team_id TEXT,
                    away_team_id TEXT,
                    home_score INTEGER DEFAULT 0,
                    away_score INTEGER DEFAULT 0,
                    current_minute INTEGER DEFAULT 0,
                    events_completed INTEGER DEFAULT 0,
                    match_state TEXT DEFAULT 'waiting',
                    channel_id BIGINT,
                    message_id BIGINT,
                    last_event_time TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Match participants table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS match_participants (
                    participant_id SERIAL PRIMARY KEY,
                    match_id INTEGER,
                    user_id BIGINT,
                    team_id TEXT,
                    match_rating REAL DEFAULT 5.0,
                    actions_taken INTEGER DEFAULT 0,
                    goals_scored INTEGER DEFAULT 0,
                    assists INTEGER DEFAULT 0,
                    joined BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Training history
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS training_history (
                    training_id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    training_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    stat_gains TEXT,
                    streak_bonus BOOLEAN DEFAULT FALSE,
                    overall_before INTEGER,
                    overall_after INTEGER
                )
            ''')
            
            # Transfers table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS transfers (
                    transfer_id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    npc_id INTEGER,
                    from_team TEXT,
                    to_team TEXT,
                    fee INTEGER,
                    wage INTEGER,
                    contract_length INTEGER,
                    season TEXT DEFAULT '2027/28',
                    transfer_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    transfer_type TEXT DEFAULT 'permanent'
                )
            ''')
            
            # News table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS news (
                    news_id SERIAL PRIMARY KEY,
                    headline TEXT NOT NULL,
                    content TEXT,
                    category TEXT,
                    user_id BIGINT,
                    importance INTEGER DEFAULT 5,
                    week_number INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Notifications table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    notif_id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    message TEXT NOT NULL,
                    notif_type TEXT,
                    read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Player Traits table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS player_traits (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    trait_id TEXT NOT NULL,
                    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, trait_id)
                )
            ''')
            
            # Achievements table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS achievements (
                    achievement_id TEXT PRIMARY KEY,
                    achievement_name TEXT NOT NULL,
                    description TEXT,
                    icon TEXT,
                    category TEXT,
                    rarity TEXT DEFAULT 'common'
                )
            ''')
            
            # Player achievements table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS player_achievements (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    achievement_id TEXT NOT NULL,
                    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    progress INTEGER DEFAULT 0,
                    UNIQUE(user_id, achievement_id)
                )
            ''')
            
            # Settings table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id BIGINT PRIMARY KEY,
                    notify_matches BOOLEAN DEFAULT TRUE,
                    notify_training BOOLEAN DEFAULT TRUE,
                    notify_transfers BOOLEAN DEFAULT TRUE,
                    notify_news BOOLEAN DEFAULT TRUE
                )
            ''')
        
        print("✅ Database tables created")
    
    @staticmethod
    def clamp_value(value: int, min_val: int = 0, max_val: int = 100) -> int:
        """Clamp a value between min and max"""
        return max(min_val, min(max_val, value))
    
    async def get_game_state(self):
        """Get current game state"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM game_state WHERE id = 1")
            return dict(row) if row else None
    
    async def update_game_state(self, **kwargs):
        """Update game state"""
        set_clause = ", ".join([f"{key} = ${i+1}" for i, key in enumerate(kwargs.keys())])
        values = list(kwargs.values())
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                f"UPDATE game_state SET {set_clause} WHERE id = 1",
                *values
            )
    
    async def get_player(self, user_id: int):
        """Get player by user ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM players WHERE user_id = $1",
                user_id
            )
            return dict(row) if row else None
    
    async def get_team(self, team_id: str):
        """Get team by team ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM teams WHERE team_id = $1",
                team_id
            )
            return dict(row) if row else None
    
    async def get_league_table(self, league: str):
        """Get league standings"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM teams 
                   WHERE league = $1 
                   ORDER BY points DESC, (goals_for - goals_against) DESC, goals_for DESC""",
                league
            )
            return [dict(row) for row in rows]
    
    async def get_player_team_fixtures(self, user_id: int, limit: int = 5):
        """Get upcoming fixtures for player's team"""
        player = await self.get_player(user_id)
        if not player or player['team_id'] == 'free_agent':
            return []
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM fixtures 
                   WHERE (home_team_id = $1 OR away_team_id = $1) 
                   AND played = FALSE 
                   ORDER BY week_number ASC 
                   LIMIT $2""",
                player['team_id'], limit
            )
            return [dict(row) for row in rows]
    
    async def add_news(self, headline: str, content: str, category: str, user_id: int = None, importance: int = 5, week_number: int = None):
        """Add news article"""
        if week_number is None:
            state = await self.get_game_state()
            week_number = state['current_week'] if state else 0
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO news (headline, content, category, user_id, importance, week_number)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                headline, content, category, user_id, importance, week_number
            )
    
    async def get_recent_news(self, user_id: int = None, limit: int = 10):
        """Get recent news"""
        async with self.pool.acquire() as conn:
            if user_id:
                rows = await conn.fetch(
                    """SELECT * FROM news 
                       WHERE user_id = $1 OR user_id IS NULL 
                       ORDER BY created_at DESC 
                       LIMIT $2""",
                    user_id, limit
                )
            else:
                rows = await conn.fetch(
                    """SELECT * FROM news 
                       ORDER BY created_at DESC 
                       LIMIT $1""",
                    limit
                )
            return [dict(row) for row in rows]
    
    async def add_notification(self, user_id: int, message: str, notif_type: str):
        """Add notification for user"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO notifications (user_id, message, notif_type)
                   VALUES ($1, $2, $3)""",
                user_id, message, notif_type
            )
    
    async def age_all_players(self):
        """Age all players by 1 year"""
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE players SET age = age + 1 WHERE retired = FALSE")
            await conn.execute("UPDATE npc_players SET age = age + 1 WHERE retired = FALSE")
        print("✅ All players aged by 1 year")
    
    async def retire_old_players(self):
        """Retire players who reach retirement age and create regens"""
        from data.player_names import get_random_player_name
        
        async with self.pool.acquire() as conn:
            # Retire user players
            old_players = await conn.fetch(
                "SELECT * FROM players WHERE age >= $1 AND retired = FALSE",
                config.RETIREMENT_AGE
            )
            
            for player in old_players:
                await conn.execute(
                    """UPDATE players 
                       SET retired = TRUE, retirement_date = $1, team_id = 'retired'
                       WHERE user_id = $2""",
                    datetime.now().isoformat(), player['user_id']
                )
                
                await self.add_news(
                    f"Legend Retires: {player['player_name']}",
                    f"{player['player_name']} has announced retirement at age {player['age']}. "
                    f"Career: {player['career_goals']} goals, {player['career_assists']} assists in {player['career_apps']} apps.",
                    "player_news",
                    player['user_id'],
                    10
                )
            
            # Retire NPC players and create regens
            old_npcs = await conn.fetch(
                "SELECT * FROM npc_players WHERE age >= $1 AND retired = FALSE",
                config.RETIREMENT_AGE
            )
            
            for npc in old_npcs:
                # Mark as retired
                await conn.execute(
                    "UPDATE npc_players SET retired = TRUE, team_id = 'retired' WHERE npc_id = $1",
                    npc['npc_id']
                )
                
                # Create regen ONLY if they were on a team
                if npc['team_id'] and npc['team_id'] not in ['free_agent', 'retired']:
                    await self.create_regen_player(npc['team_id'], npc['position'], npc['overall_rating'])
                
                # News for notable retirements (80+ rated)
                if npc['overall_rating'] >= 80:
                    team = await self.get_team(npc['team_id'])
                    team_name = team['team_name'] if team else 'Unknown'
                    await self.add_news(
                        f"Star Retires: {npc['player_name']}",
                        f"Legendary {npc['player_name']} ({npc['overall_rating']} OVR) retires at {npc['age']} from {team_name}. "
                        f"An 18-year-old regen will take his place.",
                        "league_news",
                        None,
                        7
                    )
            
            if old_players or old_npcs:
                print(f"✅ Retired {len(old_players)} user + {len(old_npcs)} NPC players")
                print(f"✅ Created {len(old_npcs)} regen players")
            
            return len(old_players) + len(old_npcs)
    
    async def cleanup_old_retired_players(self):
        """Delete players retired for 2+ seasons"""
        async with self.pool.acquire() as conn:
            # Delete user players retired 2+ seasons ago
            await conn.execute("""
                DELETE FROM players 
                WHERE retired = TRUE 
                AND retirement_date IS NOT NULL
                AND retirement_date::date < NOW() - INTERVAL '2 years'
            """)
            
            # Delete NPC players retired 2+ seasons ago
            await conn.execute("""
                DELETE FROM npc_players
                WHERE retired = TRUE
                AND team_id = 'retired'
            """)
            
            # Delete old training history (>1 year)
            await conn.execute("""
                DELETE FROM training_history
                WHERE training_date < NOW() - INTERVAL '1 year'
            """)
            
            # Delete old match events (>6 months)
            await conn.execute("""
                DELETE FROM match_events
                WHERE created_at < NOW() - INTERVAL '6 months'
            """)
            
            print("✅ Cleaned up old retired players and historical data")
    
    async def create_regen_player(self, team_id: str, position: str, original_rating: int = None):
        """Create regenerated player to replace retired player"""
        from data.player_names import get_random_player_name
        
        team = await self.get_team(team_id)
        if not team:
            return
        
        name = get_random_player_name()
        
        # Regen rating is 70-85% of original player's rating
        if original_rating:
            rating_multiplier = random.uniform(0.70, 0.85)
            base_rating = int(original_rating * rating_multiplier)
        else:
            # Fallback if no original rating provided
            if team['league'] == 'Premier League':
                base_rating = random.randint(65, 75)
            elif team['league'] == 'Championship':
                base_rating = random.randint(58, 68)
            else:
                base_rating = random.randint(50, 60)
        
        # Apply league min/max
        if team['league'] == 'Premier League':
            base_rating = max(65, min(80, base_rating))
        elif team['league'] == 'Championship':
            base_rating = max(58, min(72, base_rating))
        else:
            base_rating = max(50, min(65, base_rating))
        
        # Young regen (18 years old)
        age = 18
        
        # High potential (10-20 points above current rating)
        potential = min(99, base_rating + random.randint(10, 20))
        
        # Calculate stats based on position and rating
        if position == 'GK':
            pace = max(40, base_rating - random.randint(10, 15))
            shooting = max(40, base_rating - random.randint(15, 20))
            passing = max(50, base_rating - random.randint(5, 10))
            dribbling = max(45, base_rating - random.randint(10, 15))
            defending = min(99, base_rating + random.randint(5, 15))
            physical = min(99, base_rating + random.randint(-5, 5))
        elif position in ['ST', 'W']:
            pace = min(99, base_rating + random.randint(0, 10))
            shooting = min(99, base_rating + random.randint(5, 10))
            passing = max(50, base_rating - random.randint(0, 10))
            dribbling = min(99, base_rating + random.randint(0, 10))
            defending = max(30, base_rating - random.randint(20, 30))
            physical = max(50, base_rating - random.randint(0, 10))
        elif position in ['CAM', 'CM']:
            pace = max(50, base_rating - random.randint(0, 5))
            shooting = max(55, base_rating - random.randint(0, 10))
            passing = min(99, base_rating + random.randint(5, 10))
            dribbling = min(99, base_rating + random.randint(0, 10))
            defending = max(45, base_rating - random.randint(10, 20))
            physical = max(55, base_rating - random.randint(0, 10))
        elif position == 'CDM':
            pace = max(50, base_rating - random.randint(5, 10))
            shooting = max(50, base_rating - random.randint(10, 15))
            passing = min(99, base_rating + random.randint(0, 10))
            dribbling = max(55, base_rating - random.randint(5, 10))
            defending = min(99, base_rating + random.randint(5, 15))
            physical = min(99, base_rating + random.randint(5, 10))
        elif position in ['CB', 'FB']:
            if position == 'FB':
                pace = min(99, base_rating + random.randint(0, 5))
            else:
                pace = max(50, base_rating - random.randint(5, 10))
            shooting = max(35, base_rating - random.randint(20, 30))
            passing = max(55, base_rating - random.randint(5, 10))
            dribbling = max(45, base_rating - random.randint(10, 20))
            defending = min(99, base_rating + random.randint(5, 15))
            physical = min(99, base_rating + random.randint(5, 10))
        else:
            pace = base_rating
            shooting = base_rating
            passing = base_rating
            dribbling = base_rating
            defending = base_rating
            physical = base_rating
        
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO npc_players 
                (player_name, team_id, position, age, overall_rating, pace, shooting, passing, dribbling, defending, physical, potential, is_regen)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, TRUE)
            ''', name, team_id, position, age, base_rating, pace, shooting, passing, dribbling, defending, physical, potential)
        
        if team:
            print(f"  🆕 Regen: {name} ({position}, {base_rating} OVR, {potential} POT) joins {team['team_name']}")
    
    async def wipe_all_user_players(self):
        """ADMIN: Delete all user-created players and reset game state"""
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM players")
            await conn.execute("DELETE FROM training_history")
            await conn.execute("DELETE FROM match_events WHERE user_id IS NOT NULL")
            await conn.execute("DELETE FROM active_matches")
            await conn.execute("DELETE FROM match_participants")
            await conn.execute("DELETE FROM notifications")
            await conn.execute("DELETE FROM user_settings")
            await conn.execute("DELETE FROM news WHERE user_id IS NOT NULL")
            await conn.execute("DELETE FROM transfers")
            await conn.execute("DELETE FROM transfer_offers")
            
            await conn.execute("""
                UPDATE game_state SET
                season_started = FALSE,
                current_week = 0,
                match_window_open = FALSE,
                fixtures_generated = FALSE,
                next_match_day = NULL,
                last_match_day = NULL,
                match_window_closes = NULL,
                transfer_window_active = FALSE
            """)
            
            await conn.execute("DELETE FROM fixtures")
            
            await conn.execute("""
                UPDATE teams SET
                played = 0, won = 0, drawn = 0, lost = 0,
                goals_for = 0, goals_against = 0, points = 0, form = ''
            """)
            
            await conn.execute("""
                UPDATE npc_players SET
                season_goals = 0, season_assists = 0, season_apps = 0
            """)
        
        print("✅ All user players wiped and game reset to Day 1")
    
    async def close(self):
        """Close database connection"""
        if self.pool:
            await self.pool.close()
            print("✅ Database closed")

# Global database instance
db = Database()
