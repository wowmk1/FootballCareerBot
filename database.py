import aiosqlite
import config
import json
from datetime import datetime

class Database:
    def __init__(self):
        self.db = None
    
    async def connect(self):
        """Connect to SQLite database"""
        self.db = await aiosqlite.connect(config.DATABASE_PATH)
        self.db.row_factory = aiosqlite.Row
        await self.create_tables()
        print("✅ Database connected")
    
    async def create_tables(self):
        """Create all necessary tables"""
        
        # Game state table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS game_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                season_started BOOLEAN DEFAULT 0,
                current_season TEXT DEFAULT '2027/28',
                current_week INTEGER DEFAULT 0,
                current_year INTEGER DEFAULT 2027,
                season_start_date TEXT,
                last_match_day TEXT,
                next_match_day TEXT,
                match_window_open BOOLEAN DEFAULT 0,
                match_window_closes TEXT,
                fixtures_generated BOOLEAN DEFAULT 0
            )
        ''')
        
        await self.db.execute('''
            INSERT OR IGNORE INTO game_state (id) VALUES (1)
        ''')
        
        # Players table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
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
                career_goals INTEGER DEFAULT 0,
                career_assists INTEGER DEFAULT 0,
                career_apps INTEGER DEFAULT 0,
                injury_weeks INTEGER DEFAULT 0,
                injury_type TEXT,
                retired BOOLEAN DEFAULT 0,
                retirement_date TEXT,
                joined_week INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Teams table
        await self.db.execute('''
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
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS npc_players (
                npc_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                retired BOOLEAN DEFAULT 0,
                is_regen BOOLEAN DEFAULT 0,
                FOREIGN KEY (team_id) REFERENCES teams(team_id)
            )
        ''')
        
        # Fixtures table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS fixtures (
                fixture_id INTEGER PRIMARY KEY AUTOINCREMENT,
                home_team_id TEXT,
                away_team_id TEXT,
                competition TEXT DEFAULT 'Premier League',
                league TEXT NOT NULL,
                week_number INTEGER,
                season TEXT DEFAULT '2027/28',
                home_score INTEGER,
                away_score INTEGER,
                played BOOLEAN DEFAULT 0,
                playable BOOLEAN DEFAULT 0,
                match_date TEXT,
                FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
                FOREIGN KEY (away_team_id) REFERENCES teams(team_id)
            )
        ''')
        
        # Match events table (enhanced for DnD)
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS match_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                fixture_id INTEGER,
                user_id INTEGER,
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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fixture_id) REFERENCES fixtures(fixture_id),
                FOREIGN KEY (user_id) REFERENCES players(user_id),
                FOREIGN KEY (npc_id) REFERENCES npc_players(npc_id)
            )
        ''')
        
        # Active matches table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS active_matches (
                match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                fixture_id INTEGER UNIQUE,
                home_team_id TEXT,
                away_team_id TEXT,
                home_score INTEGER DEFAULT 0,
                away_score INTEGER DEFAULT 0,
                current_minute INTEGER DEFAULT 0,
                events_completed INTEGER DEFAULT 0,
                match_state TEXT DEFAULT 'waiting',
                channel_id INTEGER,
                message_id INTEGER,
                last_event_time TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fixture_id) REFERENCES fixtures(fixture_id)
            )
        ''')
        
        # Match participants table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS match_participants (
                participant_id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER,
                user_id INTEGER,
                team_id TEXT,
                match_rating REAL DEFAULT 5.0,
                actions_taken INTEGER DEFAULT 0,
                goals_scored INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                joined BOOLEAN DEFAULT 0,
                FOREIGN KEY (match_id) REFERENCES active_matches(match_id),
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        ''')
        
        # Training history
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS training_history (
                training_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                training_date TEXT DEFAULT CURRENT_TIMESTAMP,
                stat_gains TEXT,
                streak_bonus BOOLEAN DEFAULT 0,
                overall_before INTEGER,
                overall_after INTEGER,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        ''')
        
        # Transfers table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS transfers (
                transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                npc_id INTEGER,
                from_team TEXT,
                to_team TEXT,
                fee INTEGER,
                wage INTEGER,
                contract_length INTEGER,
                season TEXT DEFAULT '2027/28',
                transfer_date TEXT DEFAULT CURRENT_TIMESTAMP,
                transfer_type TEXT DEFAULT 'permanent',
                FOREIGN KEY (user_id) REFERENCES players(user_id),
                FOREIGN KEY (npc_id) REFERENCES npc_players(npc_id)
            )
        ''')
        
        # News table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS news (
                news_id INTEGER PRIMARY KEY AUTOINCREMENT,
                headline TEXT NOT NULL,
                content TEXT,
                category TEXT,
                user_id INTEGER,
                importance INTEGER DEFAULT 5,
                week_number INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        ''')
        
        # Notifications table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                notif_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT NOT NULL,
                notif_type TEXT,
                read BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        ''')
        
        # Settings table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                notify_matches BOOLEAN DEFAULT 1,
                notify_training BOOLEAN DEFAULT 1,
                notify_transfers BOOLEAN DEFAULT 1,
                notify_news BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        ''')
        
        await self.db.commit()
        print("✅ Database tables created")
    
    async def get_game_state(self):
        """Get current game state"""
        async with self.db.execute("SELECT * FROM game_state WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def update_game_state(self, **kwargs):
        """Update game state"""
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values())
        
        await self.db.execute(
            f"UPDATE game_state SET {set_clause} WHERE id = 1",
            values
        )
        await self.db.commit()
    
    async def get_player(self, user_id: int):
        """Get player by user ID"""
        async with self.db.execute(
            "SELECT * FROM players WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_team(self, team_id: str):
        """Get team by team ID"""
        async with self.db.execute(
            "SELECT * FROM teams WHERE team_id = ?",
            (team_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_league_table(self, league: str):
        """Get league standings"""
        async with self.db.execute(
            """SELECT * FROM teams 
               WHERE league = ? 
               ORDER BY points DESC, (goals_for - goals_against) DESC, goals_for DESC""",
            (league,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_player_team_fixtures(self, user_id: int, limit: int = 5):
        """Get upcoming fixtures for player's team"""
        player = await self.get_player(user_id)
        if not player or player['team_id'] == 'free_agent':
            return []
        
        async with self.db.execute(
            """SELECT * FROM fixtures 
               WHERE (home_team_id = ? OR away_team_id = ?) 
               AND played = 0 
               ORDER BY week_number ASC 
               LIMIT ?""",
            (player['team_id'], player['team_id'], limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def add_news(self, headline: str, content: str, category: str, user_id: int = None, importance: int = 5, week_number: int = None):
        """Add news article"""
        if week_number is None:
            state = await self.get_game_state()
            week_number = state['current_week'] if state else 0
        
        await self.db.execute(
            """INSERT INTO news (headline, content, category, user_id, importance, week_number)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (headline, content, category, user_id, importance, week_number)
        )
        await self.db.commit()
    
    async def get_recent_news(self, user_id: int = None, limit: int = 10):
        """Get recent news"""
        if user_id:
            query = """SELECT * FROM news 
                       WHERE user_id = ? OR user_id IS NULL 
                       ORDER BY created_at DESC 
                       LIMIT ?"""
            params = (user_id, limit)
        else:
            query = """SELECT * FROM news 
                       ORDER BY created_at DESC 
                       LIMIT ?"""
            params = (limit,)
        
        async with self.db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def add_notification(self, user_id: int, message: str, notif_type: str):
        """Add notification for user"""
        await self.db.execute(
            """INSERT INTO notifications (user_id, message, notif_type)
               VALUES (?, ?, ?)""",
            (user_id, message, notif_type)
        )
        await self.db.commit()
    
    async def age_all_players(self):
        """Age all players by 1 year"""
        await self.db.execute("UPDATE players SET age = age + 1 WHERE retired = 0")
        await self.db.execute("UPDATE npc_players SET age = age + 1 WHERE retired = 0")
        await self.db.commit()
        print("✅ All players aged by 1 year")
    
    async def retire_old_players(self):
        """Retire players who reach retirement age"""
        from datetime import datetime
        
        # Retire user players
        async with self.db.execute(
            "SELECT * FROM players WHERE age >= ? AND retired = 0",
            (config.RETIREMENT_AGE,)
        ) as cursor:
            old_players = await cursor.fetchall()
        
        for player in old_players:
            await self.db.execute(
                """UPDATE players 
                   SET retired = 1, retirement_date = ?, team_id = 'retired'
                   WHERE user_id = ?""",
                (datetime.now().isoformat(), player['user_id'])
            )
            
            await self.add_news(
                f"Legend Retires: {player['player_name']}",
                f"{player['player_name']} has announced retirement at age {player['age']}. "
                f"Career: {player['career_goals']} goals, {player['career_assists']} assists in {player['career_apps']} apps.",
                "player_news",
                player['user_id'],
                10
            )
        
        # Retire NPC players
        async with self.db.execute(
            "SELECT * FROM npc_players WHERE age >= ? AND retired = 0",
            (config.RETIREMENT_AGE,)
        ) as cursor:
            old_npcs = await cursor.fetchall()
        
        for npc in old_npcs:
            await self.db.execute(
                "UPDATE npc_players SET retired = 1 WHERE npc_id = ?",
                (npc['npc_id'],)
            )
            
            await self.create_regen_player(npc['team_id'], npc['position'])
            
            await self.add_news(
                f"{npc['player_name']} Retires",
                f"Veteran {npc['player_name']} ({npc['age']}) has retired from {npc['team_id']}.",
                "league_news",
                None,
                3
            )
        
        await self.db.commit()
        
        if old_players or old_npcs:
            print(f"✅ Retired {len(old_players)} user + {len(old_npcs)} NPC players")
        
        return len(old_players) + len(old_npcs)
    
    async def create_regen_player(self, team_id: str, position: str):
        """Create regenerated player"""
        from utils.player_generator import generate_random_player_name, calculate_regen_rating
        
        team = await self.get_team(team_id)
        if not team:
            return
        
        name = generate_random_player_name()
        rating = calculate_regen_rating(team['league'], position)
        age = 18
        
        base = rating
        pace = max(50, min(95, base + (5 if position in ['W', 'FB'] else -5)))
        shooting = max(50, min(95, base + (5 if position in ['ST', 'W'] else -5)))
        passing = max(50, min(95, base + (5 if position in ['CM', 'CAM'] else -5)))
        dribbling = max(50, min(95, base + (5 if position in ['W', 'CAM'] else -5)))
        defending = max(50, min(95, base + (10 if position in ['CB', 'CDM'] else -10)))
        physical = max(50, min(95, base + (5 if position in ['CB', 'ST'] else -5)))
        
        await self.db.execute('''
            INSERT INTO npc_players 
            (player_name, team_id, position, age, overall_rating, pace, shooting, passing, dribbling, defending, physical, is_regen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (name, team_id, position, age, rating, pace, shooting, passing, dribbling, defending, physical))
        
        await self.db.commit()
    
    async def wipe_all_user_players(self):
        """ADMIN: Delete all user-created players and reset game state"""
        await self.db.execute("DELETE FROM players")
        await self.db.execute("DELETE FROM training_history")
        await self.db.execute("DELETE FROM match_events WHERE user_id IS NOT NULL")
        await self.db.execute("DELETE FROM active_matches")
        await self.db.execute("DELETE FROM match_participants")
        await self.db.execute("DELETE FROM notifications")
        await self.db.execute("DELETE FROM user_settings")
        await self.db.execute("DELETE FROM news WHERE user_id IS NOT NULL")
        
        # Reset game state
        await self.db.execute("""
            UPDATE game_state SET
            season_started = 0,
            current_week = 0,
            match_window_open = 0,
            fixtures_generated = 0,
            next_match_day = NULL,
            last_match_day = NULL,
            match_window_closes = NULL
        """)
        
        # Reset fixtures
        await self.db.execute("UPDATE fixtures SET played = 0, playable = 0, home_score = NULL, away_score = NULL")
        
        # Reset team stats
        await self.db.execute("""
            UPDATE teams SET
            played = 0, won = 0, drawn = 0, lost = 0,
            goals_for = 0, goals_against = 0, points = 0, form = ''
        """)
        
        # Reset NPC stats
        await self.db.execute("""
            UPDATE npc_players SET
            season_goals = 0, season_assists = 0, season_apps = 0
        """)
        
        await self.db.commit()
        print("✅ All user players wiped and game reset to Day 1")
    
    async def close(self):
        """Close database connection"""
        if self.db:
            await self.db.close()
            print("✅ Database closed")

# Global database instance
db = Database()
