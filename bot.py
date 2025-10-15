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
        self.match_window_lock = asyncio.Lock()  # CRITICAL FIX #3: Always initialize lock

    async def setup_hook(self):
        """Called when bot is starting up"""
        logger.info("📄 Setting up bot...")

        await db.connect()

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
                'pace': min(99, base + random.randint(0, 5)) if position == 'FB' else max(50,
                                                                                          base - random.randint(5, 10)),
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
        Simple 5-minute check: Is it time to open/close windows?
        Checks: Mon/Wed/Sat 3-5 PM EST
        SELF-HEALING: Errors logged but task continues
        """
        try:
            from utils.season_manager import (
                is_match_window_time,
                open_match_window,
                close_match_window
            )

            state = await db.get_game_state()

            if not state['season_started']:
                return

            is_window_time, is_start_time, is_end_time = is_match_window_time()
            window_open = state['match_window_open']

            if is_start_time and not window_open:
                logger.info("🟢 Opening match window (fixed schedule)")
                await open_match_window()
                await self.notify_match_window_open()

                await self.change_presence(
                    activity=discord.Game(name=f"🟢 WINDOW OPEN | Week {state['current_week']}"),
                    status=discord.Status.online
                )

            elif is_end_time and window_open:
                logger.info("🔴 Closing match window (fixed schedule)")
                await close_match_window(bot=self)

                state = await db.get_game_state()
                from utils.season_manager import get_next_match_window
                try:
                    next_window = get_next_match_window()
                    day = next_window.strftime('%a')
                    await self.change_presence(
                        activity=discord.Game(name=f"Next: {day} 3PM EST | Week {state['current_week']}"),
                        status=discord.Status.online
                    )
                except:
                    await self.change_presence(
                        activity=discord.Game(name=f"⚽ Week {state['current_week']} | /season"),
                        status=discord.Status.online
                    )

            elif window_open and not is_window_time:
                logger.warning("⚠️ Window is open outside of match hours - auto-closing")
                await close_match_window(bot=self)

                state = await db.get_game_state()
                await self.change_presence(
                    activity=discord.Game(name=f"⚽ Week {state['current_week']} | /season"),
                    status=discord.Status.online
                )

        except Exception as e:
            logger.error(f"❌ ERROR in check_match_windows: {e}", exc_info=True)

    @tasks.loop(minutes=5)
    async def check_warnings(self):
        """
        Check if we should send warnings
        Times: 2:00 PM, 2:30 PM, 2:45 PM (before open), 4:45 PM (before close)
        SELF-HEALING: Errors logged but task continues
        """
        try:
            from utils.season_manager import (
                should_send_warning,
                send_1h_warning,
                send_30m_warning,
                send_15m_warning,
                send_closing_warning
            )

            state = await db.get_game_state()

            if not state['season_started']:
                return

            if should_send_warning('pre_1h'):
                await send_1h_warning(self)

            elif should_send_warning('pre_30m'):
                await send_30m_warning(self)

            elif should_send_warning('pre_15m'):
                await send_15m_warning(self)

            elif should_send_warning('closing_soon'):
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
            # Calculate when training becomes available
            cooldown_threshold = datetime.now() - timedelta(hours=config.TRAINING_COOLDOWN_HOURS)
        
            # DEBUG LOGGING - ADD THIS
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
            
                # DEBUG LOGGING - ADD THIS
                logger.info(f"   Found {len(rows)} players ready for reminder")
                for row in rows:
                    logger.info(f"   - {row['player_name']}: last_training={row['last_training']}, last_reminded={row.get('last_reminded', 'NULL')}")
            
                for row in rows:
                    # Send notification
                    success = await self.send_training_reminder(row['user_id'])
                
                    if success:
                        # Mark as reminded
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
                    day = next_window.strftime('%a')
                    status_text = f"Next: {day} 3PM EST | Week {state['current_week']}"
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
