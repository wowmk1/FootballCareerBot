import discord
from discord import app_commands
from discord.ext import commands, tasks
import config
from database import db
import asyncio
from datetime import datetime, timedelta
import logging

# ============================================
# LOGGING CONFIGURATION
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True


class FootballBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=config.BOT_PREFIX,
            intents=intents,
            help_command=None
        )
        self.season_task_started = False
        self.match_window_lock = asyncio.Lock()

    async def setup_hook(self):
        """Called when bot is starting up"""
        logger.info("📄 Setting up bot...")

        await db.connect()

        # ============================================
        # AUTO-MIGRATE: Add fractional stat columns
        # ============================================
        try:
            async with db.pool.acquire() as conn:
                # Check if fractional columns exist
                result = await conn.fetchrow("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'players'
                      AND column_name = 'pace_fractional'
                """)

                if not result:
                    logger.info("📋 Adding fractional stat tracking columns...")
            
                    # Add all 6 fractional columns
                    await conn.execute("""
                        ALTER TABLE players
                        ADD COLUMN pace_fractional DECIMAL(5, 2) DEFAULT 0.0,
                        ADD COLUMN shooting_fractional DECIMAL(5, 2) DEFAULT 0.0,
                        ADD COLUMN passing_fractional DECIMAL(5, 2) DEFAULT 0.0,
                        ADD COLUMN dribbling_fractional DECIMAL(5, 2) DEFAULT 0.0,
                        ADD COLUMN defending_fractional DECIMAL(5, 2) DEFAULT 0.0,
                        ADD COLUMN physical_fractional DECIMAL(5, 2) DEFAULT 0.0
                    """)
            
                    # Initialize existing players to 0.0
                    await conn.execute("""
                        UPDATE players
                        SET pace_fractional = 0.0,
                            shooting_fractional = 0.0,
                            passing_fractional = 0.0,
                            dribbling_fractional = 0.0,
                            defending_fractional = 0.0,
                            physical_fractional = 0.0
                        WHERE pace_fractional IS NULL
                    """)
            
                    logger.info("✅ Fractional stat columns added!")
                else:
                    logger.info("✅ Fractional stat columns already exist")
            
        except Exception as e:
            logger.warning(f"⚠️ Fractional stats migration warning: {e}")
        
        # ============================================
        # AUTO-MIGRATE: Add missing column if needed
        # ============================================
        try:
            async with db.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'game_state'
                      AND column_name = 'current_match_of_week'
                """)

                if not result:
                    logger.info("📋 Auto-migration: Adding current_match_of_week column...")
                    await conn.execute("""
                        ALTER TABLE game_state
                        ADD COLUMN current_match_of_week INTEGER DEFAULT 0
                    """)
                    await conn.execute("""
                        UPDATE game_state
                        SET current_match_of_week = 0
                        WHERE current_match_of_week IS NULL
                    """)
                    logger.info("✅ Auto-migration complete!")
                else:
                    logger.info("✅ current_match_of_week column already exists")
        except Exception as e:
            logger.warning(f"⚠️ Auto-migration warning: {e}")

        # ============================================
        # AUTO-MIGRATE: Add last_reminded column
        # ============================================
        try:
            async with db.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'players'
                      AND column_name = 'last_reminded'
                """)

                if not result:
                    logger.info("📋 Adding last_reminded column for training notifications...")
                    await conn.execute("""
                        ALTER TABLE players
                        ADD COLUMN last_reminded TEXT
                    """)
                    logger.info("✅ last_reminded column added")
                else:
                    logger.info("✅ last_reminded column already exists")
        except Exception as e:
            logger.warning(f"⚠️ Migration warning: {e}")

        # ============================================
        # AUTO-MIGRATE: Add season_motm column
        # ============================================
        try:
            async with db.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'players'
                      AND column_name = 'season_motm'
                """)

                if not result:
                    logger.info("📋 Adding season_motm column...")
                    await conn.execute("""
                        ALTER TABLE players
                        ADD COLUMN season_motm INTEGER DEFAULT 0
                    """)
                    await conn.execute("""
                        UPDATE players
                        SET season_motm = 0
                        WHERE season_motm IS NULL
                    """)
                    logger.info("✅ season_motm column added")
                else:
                    logger.info("✅ season_motm column already exists")
        except Exception as e:
            logger.warning(f"⚠️ Migration warning: {e}")

        # ============================================
        # AUTO-MIGRATE: Add career_motm column
        # ============================================
        try:
            async with db.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'players'
                      AND column_name = 'career_motm'
                """)

                if not result:
                    logger.info("📋 Adding career_motm column...")
                    await conn.execute("""
                        ALTER TABLE players
                        ADD COLUMN career_motm INTEGER DEFAULT 0
                    """)
                    await conn.execute("""
                        UPDATE players
                        SET career_motm = 0
                        WHERE career_motm IS NULL
                    """)
                    logger.info("✅ career_motm column added")
                else:
                    logger.info("✅ career_motm column already exists")
        except Exception as e:
            logger.warning(f"⚠️ Migration warning: {e}")

        # ============================================
        # AUTO-MIGRATE: Add motm column to match_participants  <-- ADD THIS NEW BLOCK
        # ============================================
        try:
            async with db.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'match_participants'
                      AND column_name = 'motm'
                """)

                if not result:
                    logger.info("📋 Adding motm column to match_participants...")
                    await conn.execute("""
                        ALTER TABLE match_participants
                        ADD COLUMN motm BOOLEAN DEFAULT FALSE
                    """)
                    await conn.execute("""
                        UPDATE match_participants
                        SET motm = FALSE
                        WHERE motm IS NULL
                    """)
                    logger.info("✅ motm column added to match_participants")
                else:
                    logger.info("✅ motm column already exists in match_participants")
        except Exception as e:
            logger.warning(f"⚠️ Migration warning: {e}")
        
        # Add this to bot.py in the setup_hook method, after the other migrations

        # ============================================
        # AUTO-SETUP: Image Cache for Visualizations
        # ============================================
        try:
            async with db.pool.acquire() as conn:
                # Check if image_cache table exists
                result = await conn.fetchrow("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'image_cache'
                    )
                """)
        
                # FIX: Check count BEFORE using it in the condition
                count = 0
                if result['exists']:
                    count = await conn.fetchval("SELECT COUNT(*) FROM image_cache")
        
                # FORCE RELOAD if table empty OR doesn't exist
                if not result['exists'] or count == 0:
                    logger.info("📋 Creating/reloading image_cache table...")
            
                    # Create table
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS image_cache (
                            image_key VARCHAR(50) PRIMARY KEY,
                            image_data BYTEA NOT NULL,
                            image_format VARCHAR(10) NOT NULL,
                            width INTEGER NOT NULL,
                            height INTEGER NOT NULL,
                            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            file_size INTEGER NOT NULL
                        )
                    """)
            
                    await conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_image_cache_last_accessed 
                        ON image_cache(last_accessed)
                    """)
            
                    logger.info("✅ image_cache table created")
        
                # CHECK FOR MISSING IMAGES (always runs)
                logger.info("🔍 Checking for missing images...")
        
                import requests
                from PIL import Image
                import io
        
                IMAGE_URLS = {
                    'stadium': 'https://raw.githubusercontent.com/wowmk1/FootballCareerBot/main/assets/stadium.jpg',
                    'player_home': 'https://raw.githubusercontent.com/wowmk1/FootballCareerBot/main/assets/player_home.png',
                    'player_away': 'https://raw.githubusercontent.com/wowmk1/FootballCareerBot/main/assets/player_away.png',
                    'defender_home': 'https://raw.githubusercontent.com/wowmk1/FootballCareerBot/main/assets/defender_home.png',
                    'defender_away': 'https://raw.githubusercontent.com/wowmk1/FootballCareerBot/main/assets/defender_away.png',
                    'goalie_home': 'https://raw.githubusercontent.com/wowmk1/FootballCareerBot/main/assets/goalie_home.png',
                    'goalie_away': 'https://raw.githubusercontent.com/wowmk1/FootballCareerBot/main/assets/goalie_away.png',
                    'ball': 'https://raw.githubusercontent.com/wowmk1/FootballCareerBot/main/assets/ball.png'
                }
        
                for key, url in IMAGE_URLS.items():
                    # Check if this specific image exists
                    exists = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM image_cache WHERE image_key = $1)", key
                    )
            
                    if not exists:
                        logger.info(f"  📥 Downloading missing image: {key}")
                        try:
                            # Download image
                            response = requests.get(url, timeout=30)
                            response.raise_for_status()
                    
                            # Load with PIL
                            img = Image.open(io.BytesIO(response.content))
                    
                            # Convert to bytes
                            buffer = io.BytesIO()
                            img_format = img.format or 'PNG'
                            img.save(buffer, format=img_format)
                            image_bytes = buffer.getvalue()
                    
                            # Insert into database
                            await conn.execute("""
                                INSERT INTO image_cache 
                                (image_key, image_data, image_format, width, height, file_size)
                                VALUES ($1, $2, $3, $4, $5, $6)
                            """, key, image_bytes, img_format, img.width, img.height, len(image_bytes))
                    
                            logger.info(f"    ✅ Cached '{key}' ({len(image_bytes) // 1024} KB)")
                    
                        except Exception as e:
                            logger.error(f"    ❌ Failed to cache '{key}': {e}")
        
                final_count = await conn.fetchval("SELECT COUNT(*) FROM image_cache")
                logger.info(f"✅ Image cache ready! ({final_count}/8 images)")
                
        except Exception as e:
            logger.warning(f"⚠️ Image cache setup warning: {e}")
        
                # ============================================
                # END AUTO-MIGRATE
                # ============================================

        await self.initialize_data()
        await self.load_cogs()

        # Initialize match engine
        from utils.match_engine import MatchEngine
        from utils import match_engine as me_module
        me_module.match_engine = MatchEngine(self)
        logger.info("✅ Match engine initialized")

        # Cache team crests
        from utils.football_data_api import cache_all_crests
        await cache_all_crests()
        logger.info("✅ Team crests cached")

        # Sync commands (with rate limit protection)
        try:
            logger.info("📄 Syncing commands with Discord...")
            synced = await self.tree.sync()
            logger.info(f"✅ Synced {len(synced)} slash commands globally")
        except discord.HTTPException as e:
            if e.status == 429:
                logger.warning("⚠️ Rate limited by Discord. Commands will sync eventually.")
                logger.warning("💡 Tip: Avoid frequent bot restarts to prevent rate limits.")
            else:
                logger.error(f"❌ Error syncing commands: {e}")

        # START SIMPLIFIED BACKGROUND TASKS WITH HEALTH MONITORING
        if not self.season_task_started:
            self.check_match_windows.start()
            self.check_warnings.start()
            self.check_retirements.start()
            self.check_training_reminders.start()
            self.cleanup_old_data.start()
            self.check_database_health.start()
            self.monitor_task_health.start()
            self.season_task_started = True
            logger.info("✅ Background tasks started (simplified system with health monitoring)")

    async def load_cogs(self):
        """Load all command modules"""
        cogs = [
            'commands.start',
            'commands.player',
            'commands.training',
            'commands.season',
            'commands.matches',
            'commands.leagues',
            'commands.transfers',
            'commands.news',
            'commands.interactive_match',
            'commands.adm',
            'commands.organized',
            'commands.achievements',
            'commands.european',
            'commands.viz_test_cog',
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"✅ Loaded {cog}")
            except Exception as e:
                logger.error(f"❌ Failed to load {cog}: {e}")

    async def initialize_data(self):
        """Initialize database with teams and complete squads"""
        from data.teams import ALL_TEAMS
        from data.players import PREMIER_LEAGUE_PLAYERS
        from data.championship_players import CHAMPIONSHIP_PLAYERS
        from data.league_one_players import LEAGUE_ONE_PLAYERS
        from utils.npc_squad_generator import populate_all_teams

        async with db.pool.acquire() as conn:
            result = await conn.fetchrow("SELECT COUNT(*) as count FROM teams")
            team_count = result['count']

        if team_count == 0:
            logger.info("📊 Initializing teams...")
            async with db.pool.acquire() as conn:
                for team in ALL_TEAMS:
                    if team['league'] == 'Premier League':
                        budget = 150000000
                        wage_budget = 200000
                    elif team['league'] == 'Championship':
                        budget = 50000000
                        wage_budget = 80000
                    else:
                        budget = 10000000
                        wage_budget = 30000

                    await conn.execute('''
                        INSERT INTO teams (team_id, team_name, league, budget, wage_budget)
                        VALUES ($1, $2, $3, $4, $5)
                    ''', team['team_id'], team['team_name'], team['league'], budget, wage_budget)
            logger.info(f"✅ Added {len(ALL_TEAMS)} teams")

        async with db.pool.acquire() as conn:
            result = await conn.fetchrow("SELECT COUNT(*) as count FROM npc_players WHERE is_regen = FALSE")
            real_player_count = result['count']

        if real_player_count == 0:
            await self.populate_real_players(
                PREMIER_LEAGUE_PLAYERS,
                CHAMPIONSHIP_PLAYERS,
                LEAGUE_ONE_PLAYERS
            )

        async with db.pool.acquire() as conn:
            result = await conn.fetchrow("SELECT COUNT(*) as count FROM npc_players")
            npc_count = result['count']

        if npc_count < 1000:
            logger.info("⚽ Generating squads for remaining teams...")
            await populate_all_teams()
            logger.info("✅ All teams now have complete squads!")

        await db.retire_old_players(bot=self)

        # Initialize European teams
        async with db.pool.acquire() as conn:
            euro_count = await conn.fetchval("SELECT COUNT(*) FROM european_teams")

        if euro_count == 0:
            logger.info("🌍 Populating European teams...")
            from utils.european_npc_populator import populate_european_teams
            teams, players = await populate_european_teams()
            logger.info(f"✅ European teams populated! {teams} teams, {players} players")

    async def populate_real_players(self, pl_players, champ_players, l1_players):
        """Populate real players with proper stats"""
        import random

        logger.info("⚽ Adding real Premier League players...")
        async with db.pool.acquire() as conn:
            for p in pl_players:
                stats = self.calculate_player_stats(p['overall_rating'], p['position'])
                await conn.execute('''
                    INSERT INTO npc_players (player_name, team_id, position, age, overall_rating,
                                            pace, shooting, passing, dribbling, defending, physical,
                                            is_regen)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, FALSE)
                ''', p['player_name'], p['team_id'], p['position'], p['age'], p['overall_rating'],
                                   stats['pace'], stats['shooting'], stats['passing'], stats['dribbling'],
                                   stats['defending'], stats['physical'])

        logger.info(f"✅ Added {len(pl_players)} Premier League players")

        logger.info("⚽ Adding real Championship players...")
        async with db.pool.acquire() as conn:
            for p in champ_players:
                stats = self.calculate_player_stats(p['overall_rating'], p['position'])
                await conn.execute('''
                    INSERT INTO npc_players (player_name, team_id, position, age, overall_rating,
                                            pace, shooting, passing, dribbling, defending, physical,
                                            is_regen)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, FALSE)
                ''', p['player_name'], p['team_id'], p['position'], p['age'], p['overall_rating'],
                                   stats['pace'], stats['shooting'], stats['passing'], stats['dribbling'],
                                   stats['defending'], stats['physical'])

        logger.info(f"✅ Added {len(champ_players)} Championship players")

        logger.info("⚽ Adding real League One players...")
        async with db.pool.acquire() as conn:
            for p in l1_players:
                stats = self.calculate_player_stats(p['overall_rating'], p['position'])
                await conn.execute('''
                    INSERT INTO npc_players (player_name, team_id, position, age, overall_rating,
                                            pace, shooting, passing, dribbling, defending, physical,
                                            is_regen)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, FALSE)
                ''', p['player_name'], p['team_id'], p['position'], p['age'], p['overall_rating'],
                                   stats['pace'], stats['shooting'], stats['passing'], stats['dribbling'],
                                   stats['defending'], stats['physical'])

        logger.info(f"✅ Added {len(l1_players)} League One players")

    def calculate_player_stats(self, base, position):
        """Calculate individual stats based on position"""
        import random

        if position == 'GK':
            return {
                'pace': max(40, base - random.randint(10, 15)),
                'shooting': max(40, base - random.randint(15, 20)),
                'passing': max(50, base - random.randint(5, 10)),
                'dribbling': max(45, base - random.randint(10, 15)),
                'defending': min(99, base + random.randint(5, 15)),
                'physical': min(99, base + random.randint(-5, 5))
            }
        elif position in ['ST', 'W']:
            return {
                'pace': min(99, base + random.randint(0, 10)),
                'shooting': min(99, base + random.randint(5, 10)),
                'passing': max(50, base - random.randint(0, 10)),
                'dribbling': min(99, base + random.randint(0, 10)),
                'defending': max(30, base - random.randint(20, 30)),
                'physical': max(50, base - random.randint(0, 10))
            }
        elif position in ['CAM', 'CM']:
            return {
                'pace': max(50, base - random.randint(0, 5)),
                'shooting': max(55, base - random.randint(0, 10)),
                'passing': min(99, base + random.randint(5, 10)),
                'dribbling': min(99, base + random.randint(0, 10)),
                'defending': max(45, base - random.randint(10, 20)),
                'physical': max(55, base - random.randint(0, 10))
            }
        elif position == 'CDM':
            return {
                'pace': max(50, base - random.randint(5, 10)),
                'shooting': max(50, base - random.randint(10, 15)),
                'passing': min(99, base + random.randint(0, 10)),
                'dribbling': max(55, base - random.randint(5, 10)),
                'defending': min(99, base + random.randint(5, 15)),
                'physical': min(99, base + random.randint(5, 10))
            }
        elif position in ['CB', 'FB']:
            return {
                'pace': min(99, base + random.randint(0, 5)) if position == 'FB' else max(50, base - random.randint(5, 10)),
                'shooting': max(35, base - random.randint(20, 30)),
                'passing': max(55, base - random.randint(5, 10)),
                'dribbling': max(45, base - random.randint(10, 20)),
                'defending': min(99, base + random.randint(5, 15)),
                'physical': min(99, base + random.randint(5, 10))
            }
        else:
            return {'pace': base, 'shooting': base, 'passing': base,
                    'dribbling': base, 'defending': base, 'physical': base}

    async def notify_match_window_open(self):
        """Notify all guilds that match window is open"""
        try:
            state = await db.get_game_state()

            for guild in self.guilds:
                channel = discord.utils.get(guild.text_channels, name="match-results")
                if not channel:
                    channel = discord.utils.get(guild.text_channels, name="general")

                if channel:
                    embed = discord.Embed(
                        title="🟢 MATCH WINDOW OPEN!",
                        description=f"**Week {state['current_week']}** matches are now playable!\n\n"
                                    f"Use `/play_match` to play your match!",
                        color=discord.Color.green()
                    )

                    embed.add_field(
                        name="⏰ Window Open",
                        value="**3:00 PM - 5:00 PM EST**\n2 hour window",
                        inline=True
                    )

                    embed.add_field(
                        name="⚡ Quick Commands",
                        value="`/play_match` - Play your match\n`/season` - Check schedule",
                        inline=True
                    )

                    async with db.pool.acquire() as conn:
                        players = await conn.fetch("""
                            SELECT DISTINCT p.user_id, p.player_name, t.team_name
                            FROM players p
                            JOIN teams t ON p.team_id = t.team_id
                            WHERE p.retired = FALSE
                              AND p.team_id != 'free_agent'
                              AND EXISTS (
                                SELECT 1 FROM fixtures f
                                WHERE (f.home_team_id = p.team_id OR f.away_team_id = p.team_id)
                                AND f.week_number = $1
                                AND f.played = FALSE
                              )
                        """, state['current_week'])

                    player_mentions = []
                    for p in players:
                        member = guild.get_member(p['user_id'])
                        if member:
                            player_mentions.append(f"{member.mention} ({p['team_name']})")

                    if player_mentions:
                        mentions_text = "\n".join(player_mentions[:10])
                        if len(player_mentions) > 10:
                            mentions_text += f"\n*...and {len(player_mentions) - 10} more*"

                        embed.add_field(
                            name="👥 Players with Matches",
                            value=mentions_text,
                            inline=False
                        )

                    embed.set_footer(text="Window closes at 5:00 PM EST!")

                    await channel.send(embed=embed)
                    logger.info(f"✅ Posted match window notification to {guild.name}")
        except Exception as e:
            logger.warning(f"⚠️ Could not post match window notification: {e}")

    async def notify_european_window_open(self):
        """Notify guilds that European window is open (12 PM)"""
        try:
            state = await db.get_game_state()

            for guild in self.guilds:
                channel = discord.utils.get(guild.text_channels, name="match-results")
                if not channel:
                    channel = discord.utils.get(guild.text_channels, name="general")

                if channel:
                    embed = discord.Embed(
                        title="🟢 EUROPEAN WINDOW OPEN!",
                        description=f"**Week {state['current_week']}** Champions League & Europa League matches are now playable!\n\n"
                                    f"Use `/play_match` to play your European match!",
                        color=discord.Color.blue()
                    )

                    embed.add_field(
                        name="🏆 Window Open",
                        value="**12:00 PM - 2:00 PM EST**\n2 hour window",
                        inline=True
                    )

                    embed.add_field(
                        name="⚡ Quick Commands",
                        value="`/play_match` - Play your match\n`/european` - Check fixtures",
                        inline=True
                    )

                    # Find players with European matches
                    async with db.pool.acquire() as conn:
                        players = await conn.fetch("""
                            SELECT DISTINCT p.user_id, p.player_name, t.team_name, f.competition
                            FROM players p
                            JOIN teams t ON p.team_id = t.team_id
                            JOIN european_fixtures f ON (f.home_team_id = p.team_id OR f.away_team_id = p.team_id)
                            WHERE p.retired = FALSE
                              AND p.team_id != 'free_agent'
                              AND f.week_number = $1
                              AND f.played = FALSE
                        """, state['current_week'])

                    player_mentions = []
                    for p in players:
                        member = guild.get_member(p['user_id'])
                        if member:
                            comp_emoji = "🏆" if p['competition'] == 'CL' else "🌟"
                            player_mentions.append(f"{comp_emoji} {member.mention} ({p['team_name']})")

                    if player_mentions:
                        mentions_text = "\n".join(player_mentions[:10])
                        if len(player_mentions) > 10:
                            mentions_text += f"\n*...and {len(player_mentions) - 10} more*"

                        embed.add_field(
                            name="👥 Players with European Matches",
                            value=mentions_text,
                            inline=False
                        )

                    embed.add_field(
                        name="ℹ️ Domestic Matches",
                        value="League matches open later at **3:00 PM EST**",
                        inline=False
                    )

                    embed.set_footer(text="European window closes at 2:00 PM EST • Domestic opens at 3:00 PM!")

                    await channel.send(embed=embed)
                    logger.info(f"✅ Posted European window open notification to {guild.name}")
        except Exception as e:
            logger.warning(f"⚠️ Could not post European window notification: {e}")

    async def notify_match_window_closed(self, week_results):
        """Notify all guilds that match window has closed with results"""
        try:
            state = await db.get_game_state()

            for guild in self.guilds:
                channel = discord.utils.get(guild.text_channels, name="match-results")
                if not channel:
                    channel = discord.utils.get(guild.text_channels, name="general")

                if channel:
                    embed = discord.Embed(
                        title="🔴 MATCH WINDOW CLOSED",
                        description=f"**Week {state['current_week']}** is complete! Advancing to Week {state['current_week'] + 1}...",
                        color=discord.Color.red()
                    )

                    if week_results:
                        results_text = ""
                        for result in week_results[:5]:
                            results_text += f"**{result['home_team_name']}** {result['home_score']} - {result['away_score']} **{result['away_team_name']}**\n"

                        embed.add_field(
                            name="📊 Recent Results",
                            value=results_text,
                            inline=False
                        )

                    embed.add_field(
                        name="📅 Next Match Window",
                        value="Check `/season` for schedule",
                        inline=False
                    )

                    embed.set_footer(text="Use /league table to see updated standings!")

                    await channel.send(embed=embed)
                    logger.info(f"✅ Posted window closed notification to {guild.name}")
        except Exception as e:
            logger.warning(f"⚠️ Could not post window closed notification: {e}")

    async def notify_european_window_closed(self):
        """Notify guilds that European window has closed (2 PM)"""
        try:
            state = await db.get_game_state()

            for guild in self.guilds:
                channel = discord.utils.get(guild.text_channels, name="match-results")
                if not channel:
                    channel = discord.utils.get(guild.text_channels, name="general")

                if channel:
                    embed = discord.Embed(
                        title="🔴 EUROPEAN WINDOW CLOSED",
                        description=f"**Week {state['current_week']}** European matches (12-2 PM) are complete!",
                        color=discord.Color.blue()
                    )

                    # Get European results from this window
                    async with db.pool.acquire() as conn:
                        results = await conn.fetch("""
                            SELECT 
                                COALESCE(ht.team_name, eht.team_name) as home_team,
                                COALESCE(at.team_name, eat.team_name) as away_team,
                                f.home_score, f.away_score, f.competition
                            FROM european_fixtures f
                            LEFT JOIN teams ht ON f.home_team_id = ht.team_id
                            LEFT JOIN teams at ON f.away_team_id = at.team_id
                            LEFT JOIN european_teams eht ON f.home_team_id = eht.team_id
                            LEFT JOIN european_teams eat ON f.away_team_id = eat.team_id
                            WHERE f.week_number = $1 AND f.played = TRUE
                            ORDER BY f.fixture_id DESC
                            LIMIT 5
                        """, state['current_week'])

                    if results:
                        results_text = ""
                        for r in results:
                            comp_emoji = "🏆" if r['competition'] == 'CL' else "🌟"
                            results_text += f"{comp_emoji} **{r['home_team']}** {r['home_score']} - {r['away_score']} **{r['away_team']}**\n"

                        embed.add_field(
                            name="📊 European Results",
                            value=results_text,
                            inline=False
                        )

                    embed.add_field(
                        name="⏰ Domestic Window Opens Soon",
                        value=f"League matches open at **3:00 PM EST** (in 1 hour)\nUse `/season` to check your match!",
                        inline=False
                    )

                    embed.set_footer(text="Domestic league matches open at 3:00 PM EST!")

                    await channel.send(embed=embed)
                    logger.info(f"✅ Posted European window closed notification to {guild.name}")
        except Exception as e:
            logger.warning(f"⚠️ Could not post European window closed notification: {e}")

    async def notify_domestic_window_closed(self, completing_week):
        """Notify guilds that Domestic window has closed and week is advancing (5 PM)"""
        try:
            # ✅ FIX: Calculate new week from parameter (don't read database!)
            new_week = completing_week + 1

            for guild in self.guilds:
                channel = discord.utils.get(guild.text_channels, name="match-results")
                if not channel:
                    channel = discord.utils.get(guild.text_channels, name="general")

                if channel:
                    embed = discord.Embed(
                        title="🔴 DOMESTIC WINDOW CLOSED",
                        description=f"**Week {completing_week}** is complete!\n\n⏭️ Advancing to **Week {new_week}**...",
                        color=discord.Color.red()
                    )

                    # Get recent domestic results
                    async with db.pool.acquire() as conn:
                        results = await conn.fetch("""
                            SELECT 
                                ht.team_name as home_team,
                                at.team_name as away_team,
                                f.home_score, f.away_score
                            FROM fixtures f
                            JOIN teams ht ON f.home_team_id = ht.team_id
                            JOIN teams at ON f.away_team_id = at.team_id
                            WHERE f.week_number = $1 AND f.played = TRUE
                            ORDER BY f.fixture_id DESC
                            LIMIT 5
                        """, completing_week)

                    if results:
                        results_text = ""
                        for r in results:
                            results_text += f"⚽ **{r['home_team']}** {r['home_score']} - {r['away_score']} **{r['away_team']}**\n"

                        embed.add_field(
                            name="📊 Recent League Results",
                            value=results_text,
                            inline=False
                        )

                    embed.add_field(
                        name=f"📅 Week {new_week} Begins",
                        value=f"Use `/season` to see when your next match is!\nUse `/league table` for updated standings!",
                        inline=False
                    )

                    embed.set_footer(text=f"Week {completing_week} complete • Week {new_week} starts now!")

                    await channel.send(embed=embed)
                    logger.info(f"✅ Posted domestic window closed notification to {guild.name}")
        except Exception as e:
            logger.error(f"❌ Could not post domestic window closed notification: {e}", exc_info=True)

    # ============================================
    # SELF-HEALING BACKGROUND TASKS (FIXED)
    # ============================================

    @tasks.loop(hours=168)
    async def cleanup_old_data(self):
        """Weekly cleanup of old data"""
        try:
            await db.cleanup_old_retired_players()
            logger.info("✅ Weekly data cleanup complete")
        except Exception as e:
            logger.error(f"❌ ERROR in cleanup_old_data: {e}", exc_info=True)

    @cleanup_old_data.before_loop
    async def before_cleanup_old_data(self):
        await self.wait_until_ready()

    @tasks.loop(minutes=5)
    async def check_match_windows(self):
        """
        Check BOTH windows:
        - 12-2 PM: European (on European weeks)
        - 3-5 PM: Domestic (always, advances week)

        ✅ FIXED: Enhanced logging to debug window issues
        ✅ FIXED: Proper handling of 4-value return from is_match_window_time()
        ✅ FIXED: Passes current_week to is_match_window_time()
        """
        try:
            from utils.season_manager import (
                is_match_window_time,
                open_match_window,
                close_match_window
            )

            state = await db.get_game_state()

            if not state['season_started']:
                logger.debug("⏸️ Season not started, skipping window check")
                return

            # ✅ FIXED: Get window status (returns 4 values) - PASS current_week
            current_week = state['current_week']
            is_window_time, is_start_time, is_end_time, window_type = is_match_window_time(current_week=current_week)
            window_open = state['match_window_open']

            logger.info(
                f"🔍 WINDOW CHECK: window_time={is_window_time}, start={is_start_time}, end={is_end_time}, type={window_type}, db_open={window_open}")

            # ===== OPEN WINDOW =====
            if is_start_time and not window_open and window_type:
                logger.info(f"🟢 OPENING {window_type.upper()} WINDOW NOW")
                await open_match_window(window_type=window_type)

                # ✅ Send notifications for both window types
                if window_type == 'domestic':
                    await self.notify_match_window_open()
                elif window_type == 'european':
                    await self.notify_european_window_open()

                time_text = "12-2 PM" if window_type == 'european' else "3-5 PM"
                await self.change_presence(
                    activity=discord.Game(name=f"🟢 {window_type.upper()} {time_text} | Week {state['current_week']}"),
                    status=discord.Status.online
                )

            # ===== CLOSE WINDOW =====
            elif is_end_time and window_open and window_type:
                logger.info(f"🔴 CLOSING {window_type.upper()} WINDOW NOW")
    
                # ✅ Notification now handled INSIDE close_match_window() to ensure correct timing
                await close_match_window(window_type=window_type, bot=self)

                # ✅ Send European notification (domestic notification is now inside close_match_window)
                if window_type == 'european':
                    await self.notify_european_window_closed()

                # Update status after closing
                state = await db.get_game_state()
                from utils.season_manager import get_next_match_window
                try:
                    next_window = get_next_match_window()
                    time_str = next_window.strftime('%I:%M %p')
                    day = next_window.strftime('%a')
                    await self.change_presence(
                        activity=discord.Game(name=f"Next: {day} {time_str} | Week {state['current_week']}"),
                        status=discord.Status.online
                    )
                except:
                    await self.change_presence(
                        activity=discord.Game(name=f"⚽ Week {state['current_week']} | /season"),
                        status=discord.Status.online
                    )

            # ===== SAFETY CHECK: Window open but shouldn't be =====
            elif window_open and not is_window_time:
                logger.warning("⚠️ SAFETY: Window is open outside of match hours - FORCE CLOSING")
                await close_match_window(window_type='domestic', bot=self)

                state = await db.get_game_state()
                await self.change_presence(
                    activity=discord.Game(name=f"⚽ Week {state['current_week']} | /season"),
                    status=discord.Status.online
                )

            else:
                logger.debug(f"✅ Window check OK - No action needed")

        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in check_match_windows: {e}", exc_info=True)

    @tasks.loop(minutes=5)
    async def check_warnings(self):
        """
        Check if we should send warnings
        Times:
        - European: 11:00 AM, 11:30 AM, 11:45 AM (before 12 PM open)
        - Domestic: 2:00 PM, 2:30 PM, 2:45 PM (before 3 PM open), 4:45 PM (before close)
        SELF-HEALING: Errors logged but task continues
        ✅ FIXED: Passes current_week to all should_send_warning() calls
        """
        try:
            from utils.season_manager import (
                should_send_warning,
                send_1h_warning,
                send_30m_warning,
                send_15m_warning,
                send_closing_warning,
                send_european_1h_warning,
                send_european_30m_warning,
                send_european_15m_warning
            )

            state = await db.get_game_state()

            if not state['season_started']:
                return

            current_week = state['current_week']

            # ✅ FIXED: European warnings (11 AM, 11:30 AM, 11:45 AM) - pass current_week
            if should_send_warning('european_1h', current_week=current_week):
                await send_european_1h_warning(self)

            elif should_send_warning('european_30m', current_week=current_week):
                await send_european_30m_warning(self)

            elif should_send_warning('european_15m', current_week=current_week):
                await send_european_15m_warning(self)

            # ✅ FIXED: Domestic warnings (2 PM, 2:30 PM, 2:45 PM, 4:45 PM) - pass current_week
            elif should_send_warning('domestic_1h', current_week=current_week):
                await send_1h_warning(self)

            elif should_send_warning('domestic_30m', current_week=current_week):
                await send_30m_warning(self)

            elif should_send_warning('domestic_15m', current_week=current_week):
                await send_15m_warning(self)

            elif should_send_warning('domestic_closing', current_week=current_week):
                await send_closing_warning(self)

        except Exception as e:
            logger.error(f"❌ ERROR in check_warnings: {e}", exc_info=True)

    @tasks.loop(hours=24)
    async def check_retirements(self):
        """
        Daily retirement check
        SELF-HEALING: Errors logged but task continues
        """
        try:
            await db.retire_old_players(bot=self)
        except Exception as e:
            logger.error(f"❌ ERROR in check_retirements: {e}", exc_info=True)

    @tasks.loop(minutes=5)
    async def check_training_reminders(self):
        """
        Check for players whose training is ready and send reminders
        """
        try:
            cooldown_threshold = datetime.now() - timedelta(hours=config.TRAINING_COOLDOWN_HOURS)

            logger.info(f"🔍 Checking training reminders at {datetime.now()}")
            logger.info(f"   Cooldown threshold: {cooldown_threshold}")

            async with db.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT user_id, player_name, last_training, last_reminded
                    FROM players
                    WHERE retired = FALSE
                      AND last_training IS NOT NULL
                      AND last_training::timestamp <= $1
                      AND (last_reminded IS NULL 
                           OR last_reminded::timestamp <= last_training::timestamp)
                """, cooldown_threshold)

                logger.info(f"   Found {len(rows)} players ready for reminder")
                for row in rows:
                    logger.info(f"   - {row['player_name']}: last_training={row['last_training']}, last_reminded={row.get('last_reminded', 'NULL')}")

                for row in rows:
                    success = await self.send_training_reminder(row['user_id'])

                    if success:
                        await conn.execute("""
                            UPDATE players
                            SET last_reminded = $1
                            WHERE user_id = $2
                        """, datetime.now().isoformat(), row['user_id'])

                        logger.info(f"✅ Sent training reminder to user {row['user_id']}")

        except Exception as e:
            logger.error(f"❌ ERROR in check_training_reminders: {e}", exc_info=True)

    async def send_training_reminder(self, user_id: int):
        """Send DM when training is available"""
        try:
            player = await db.get_player(user_id)
            if not player or not player['last_training']:
                return False

            last_train = datetime.fromisoformat(player['last_training'])
            time_since = datetime.now() - last_train

            if time_since < timedelta(hours=config.TRAINING_COOLDOWN_HOURS):
                logger.warning(f"⚠️ Skipped premature reminder for user {user_id}")
                return False

            user = await self.fetch_user(user_id)
            embed = discord.Embed(
                title="💪 Training Available!",
                description="Your training cooldown is over!\n\nUse `/train` to improve your stats.",
                color=discord.Color.green()
            )

            embed.add_field(
                name="🔥 Reminder",
                value=f"Training daily maintains your streak!\n"
                      f"Current streak: **{player['training_streak']} days**\n"
                      f"30-day streak = +3 potential",
                inline=False
            )

            hours_since = int(time_since.total_seconds() // 3600)
            embed.add_field(
                name="⏱️ Cooldown Info",
                value=f"Last trained: **{hours_since}h ago**\nYou're ready to train again!",
                inline=False
            )

            await user.send(embed=embed)
            logger.info(f"✅ Sent training reminder to user {user_id}")
            return True

        except Exception as e:
            logger.warning(f"⚠️ Could not send training reminder to {user_id}: {e}")
            return False

    @tasks.loop(minutes=5)
    async def check_database_health(self):
        """Monitor database connection health"""
        try:
            is_healthy = await db.health_check()
            if not is_healthy:
                logger.critical("🚨 Database unhealthy - connection issues detected!")
        except Exception as e:
            logger.critical(f"❌ Database health check failed: {e}", exc_info=True)

    @check_database_health.before_loop
    async def before_check_database_health(self):
        await self.wait_until_ready()

    @tasks.loop(hours=1)
    async def monitor_task_health(self):
        """Check if background tasks are still running and restart if needed"""
        try:
            tasks_status = {
                'match_windows': self.check_match_windows.is_running(),
                'warnings': self.check_warnings.is_running(),
                'retirements': self.check_retirements.is_running(),
                'training_reminders': self.check_training_reminders.is_running(),
                'cleanup': self.cleanup_old_data.is_running(),
                'database_health': self.check_database_health.is_running()
            }

            failed_tasks = [name for name, running in tasks_status.items() if not running]

            if failed_tasks:
                logger.critical(f"🚨 TASKS STOPPED: {failed_tasks} - Attempting restart...")

                for task_name in failed_tasks:
                    try:
                        if task_name == 'match_windows' and not self.check_match_windows.is_running():
                            self.check_match_windows.start()
                            logger.info("✅ Restarted check_match_windows")

                        elif task_name == 'warnings' and not self.check_warnings.is_running():
                            self.check_warnings.start()
                            logger.info("✅ Restarted check_warnings")

                        elif task_name == 'retirements' and not self.check_retirements.is_running():
                            self.check_retirements.start()
                            logger.info("✅ Restarted check_retirements")

                        elif task_name == 'training_reminders' and not self.check_training_reminders.is_running():
                            self.check_training_reminders.start()
                            logger.info("✅ Restarted check_training_reminders")

                        elif task_name == 'cleanup' and not self.cleanup_old_data.is_running():
                            self.cleanup_old_data.start()
                            logger.info("✅ Restarted cleanup_old_data")

                        elif task_name == 'database_health' and not self.check_database_health.is_running():
                            self.check_database_health.start()
                            logger.info("✅ Restarted check_database_health")

                    except Exception as restart_error:
                        logger.error(f"❌ Failed to restart {task_name}: {restart_error}", exc_info=True)
            else:
                logger.info("✅ All background tasks healthy")

        except Exception as e:
            logger.error(f"❌ ERROR in monitor_task_health: {e}", exc_info=True)

    @monitor_task_health.before_loop
    async def before_monitor_task_health(self):
        await self.wait_until_ready()

    @check_match_windows.before_loop
    async def before_check_match_windows(self):
        await self.wait_until_ready()

    @check_warnings.before_loop
    async def before_check_warnings(self):
        await self.wait_until_ready()

    @check_retirements.before_loop
    async def before_check_retirements(self):
        await self.wait_until_ready()

    @check_training_reminders.before_loop
    async def before_check_training_reminders(self):
        await self.wait_until_ready()

    async def on_ready(self):
        """Called when bot is fully ready"""
        state = await db.get_game_state()

        logger.info("\n" + "=" * 50)
        logger.info(f'✅ Bot logged in as {self.user.name}')
        logger.info(f'✅ Connected to {len(self.guilds)} server(s)')

        if state['season_started']:
            logger.info(
                f'📅 Season: {state["current_season"]} - Week {state["current_week"]}/{config.SEASON_TOTAL_WEEKS}')
        else:
            logger.info(f'⏳ Season not started')

        from utils.season_manager import get_next_match_window, EST
        try:
            next_window = get_next_match_window()
            logger.info(f'⏰ Next match window: {next_window.strftime("%A, %B %d at %I:%M %p EST")}')
        except:
            pass

        logger.info("=" * 50 + "\n")

        if state['season_started']:
            if state['match_window_open']:
                status_text = f"🟢 WINDOW OPEN | Week {state['current_week']}"
            else:
                try:
                    next_window = get_next_match_window()
                    time_str = next_window.strftime('%I:%M %p')
                    day = next_window.strftime('%a')
                    status_text = f"Next: {day} {time_str} | Week {state['current_week']}"
                except:
                    status_text = f"⚽ Week {state['current_week']} | /season"
        else:
            status_text = "⚽ /start to begin"

        await self.change_presence(
            activity=discord.Game(name=status_text),
            status=discord.Status.online
        )

    async def on_guild_join(self, guild):
        """When bot joins a new server, auto-setup channels"""
        logger.info(f"📥 Joined new server: {guild.name}")

        from utils.channel_setup import setup_server_channels
        try:
            await setup_server_channels(guild)
            logger.info(f"✅ Auto-setup complete for {guild.name}")
        except Exception as e:
            logger.warning(f"⚠️ Could not auto-setup channels: {e}")


# Create bot instance
bot = FootballBot()


# Help command
@bot.tree.command(name="help", description="View all available commands")
async def help_command(interaction: discord.Interaction):
    """Show help information"""

    embed = discord.Embed(
        title="⚽ Football Career Bot - Guide",
        description="Build your player from 18 to 38 with interactive matches!",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="🎮 Getting Started",
        value="`/start` - Create player\n`/profile` - View stats\n`/player` - Player info menu",
        inline=False
    )

    embed.add_field(
        name="💼 Transfers",
        value="`/offers` - View offers (transfer windows)\n`/player contract` - Current deal\n`/player history` - Past moves",
        inline=False
    )

    embed.add_field(
        name="📈 Training",
        value="`/train` - Train daily (2+ points per session!)\n30-day streak = +3 permanent potential!",
        inline=False
    )

    embed.add_field(
        name="🎲 Matches",
        value="`/play_match` - Play your match!\nPosition-specific events\nD20 duels vs opponents",
        inline=False
    )

    embed.add_field(
        name="📅 Season",
        value="`/season` - Current week\n`/league fixtures` - Your schedule\n`/league table` - League tables",
        inline=False
    )

    if interaction.user.guild_permissions.administrator:
        embed.add_field(
            name="🔧 Admin Commands",
            value="Type `/adm` to see all admin commands\nAll admin tools are in the `/adm` dropdown menu",
            inline=False
        )

    await interaction.response.send_message(embed=embed)


# Run bot
if __name__ == "__main__":
    try:
        bot.run(config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Bot shutdown requested")
    except Exception as e:
        logger.critical(f"❌ Fatal error: {e}", exc_info=True)
