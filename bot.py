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
                
                # Check count BEFORE using it in condition (FIX: moved before if statement)
                count = await conn.fetchval("SELECT COUNT(*) FROM image_cache") if result['exists'] else 0
                
                if not result['exists'] or count == 0:
                    logger.info("📋 Creating/reloading image_cache table...")
                    
                    # Create table if it doesn't exist
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS image_cache (
                            name TEXT PRIMARY KEY,
                            image_data BYTEA NOT NULL,
                            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Load images
                    from utils.visualizations import cache_all_images
                    await cache_all_images(conn)
                    logger.info("✅ Image cache ready!")
                else:
                    logger.info(f"✅ Image cache already loaded ({count} images)")
                    
        except Exception as e:
            logger.warning(f"⚠️ Image cache setup warning: {e}")

        # Load cogs
        from commands import start, train, profile, transfers, admin, season, player, league, matches
        await self.add_cog(start.StartCog(self))
        await self.add_cog(train.TrainCog(self))
        await self.add_cog(profile.ProfileCog(self))
        await self.add_cog(transfers.TransfersCog(self))
        await self.add_cog(admin.AdminCog(self))
        await self.add_cog(season.SeasonCog(self))
        await self.add_cog(player.PlayerCog(self))
        await self.add_cog(league.LeagueCog(self))
        await self.add_cog(matches.MatchesCog(self))

        await self.tree.sync()
        logger.info("✅ Bot setup complete")

        # Start background tasks
        self.check_match_windows.start()
        self.check_warnings.start()
        self.check_retirements.start()
        self.check_training_reminders.start()
        self.cleanup_old_data.start()
        self.check_database_health.start()
        self.monitor_task_health.start()

        logger.info("✅ Background tasks started")

    @tasks.loop(minutes=1)
    async def check_match_windows(self):
        """Check if it's time to open/close match windows"""
        from utils.season_manager import check_match_window, EST
        try:
            current_time = datetime.now(EST)
            hour = current_time.hour
            minute = current_time.minute
            day_of_week = current_time.weekday()

            # Match windows: Tue/Thu/Sat 5pm-10pm EST
            is_match_day = day_of_week in [1, 3, 5]
            is_opening_time = hour == 17 and minute == 0
            is_closing_time = hour == 22 and minute == 0

            state = await db.get_game_state()

            # Check if we need to start the season automatically
            if not state['season_started']:
                try:
                    async with self.match_window_lock:
                        latest_state = await db.get_game_state()
                        if not latest_state['season_started']:
                            player_count = await db.pool.fetchval("SELECT COUNT(*) FROM players")
                            if player_count > 0:
                                logger.info(f"🚀 Auto-starting season with {player_count} player(s)...")
                                await db.pool.execute(
                                    "UPDATE game_state SET season_started = TRUE, current_season = 1, current_week = 1")
                                from utils.season_manager import generate_season_schedule
                                await generate_season_schedule()
                                logger.info("✅ Season auto-started successfully")
                            else:
                                return
                except Exception as e:
                    logger.error(f"❌ Auto-start error: {e}", exc_info=True)

            state = await db.get_game_state()

            if not state['season_started']:
                return

            # Check if current week is complete and we should advance
            current_week = state['current_week']
            max_week = config.SEASON_TOTAL_WEEKS

            # Count players who have participated in any match this week
            players_participated = await db.pool.fetchval("""
                SELECT COUNT(DISTINCT player_id) 
                FROM match_participants mp
                JOIN matches m ON m.id = mp.match_id
                WHERE m.week = $1
            """, current_week)

            total_players = await db.pool.fetchval("SELECT COUNT(*) FROM players")

            # If all players have played this week and window is closed, advance week
            if players_participated >= total_players and not state['match_window_open']:
                if current_week < max_week:
                    logger.info(
                        f"📅 All {total_players} players completed week {current_week}. Advancing to week {current_week + 1}...")

                    # Advance week
                    from commands.admin import advance_week_logic
                    success = await advance_week_logic(self)

                    if success:
                        logger.info(f"✅ Advanced to week {current_week + 1}")

                        # Send announcement
                        try:
                            announcement_channel = await self.fetch_channel(config.ANNOUNCEMENT_CHANNEL_ID)
                            new_week = current_week + 1

                            embed = discord.Embed(
                                title=f"📅 Week {new_week} Has Begun!",
                                description=f"All players have completed week {current_week}. The season continues!",
                                color=discord.Color.green()
                            )

                            embed.add_field(
                                name="⏰ Next Match Window",
                                value=f"Match windows open:\n**Tuesday, Thursday, Saturday**\n**5:00 PM - 10:00 PM EST**",
                                inline=False
                            )

                            embed.add_field(
                                name="🎮 Ready to Play?",
                                value="Use `/play_match` during match windows!",
                                inline=False
                            )

                            await announcement_channel.send(embed=embed)
                        except Exception as e:
                            logger.warning(f"⚠️ Could not send week advance announcement: {e}")
                    else:
                        logger.error("❌ Week advance failed")

                elif current_week == max_week and players_participated >= total_players:
                    logger.info("🏆 Season complete - all players finished final week")
                    # Could trigger end-of-season logic here

            # Normal window opening/closing logic
            if is_match_day:
                if is_opening_time and not state['match_window_open']:
                    async with self.match_window_lock:
                        latest_state = await db.get_game_state()
                        if not latest_state['match_window_open']:
                            logger.info("🟢 Opening match window...")
                            try:
                                await db.pool.execute("UPDATE game_state SET match_window_open = TRUE")

                                try:
                                    announcement_channel = await self.fetch_channel(config.ANNOUNCEMENT_CHANNEL_ID)
                                    state = await db.get_game_state()

                                    embed = discord.Embed(
                                        title="🟢 MATCH WINDOW OPEN!",
                                        description=f"**Week {state['current_week']}** matches are now available!",
                                        color=discord.Color.green()
                                    )

                                    embed.add_field(
                                        name="⚽ Play Now",
                                        value="Use `/play_match` to play your match!",
                                        inline=False
                                    )

                                    embed.add_field(
                                        name="⏰ Window Closes",
                                        value="10:00 PM EST tonight",
                                        inline=False
                                    )

                                    await announcement_channel.send(embed=embed)
                                except Exception as e:
                                    logger.warning(f"⚠️ Could not send window opening announcement: {e}")

                                await self.change_presence(
                                    activity=discord.Game(name=f"🟢 WINDOW OPEN | Week {state['current_week']}"),
                                    status=discord.Status.online
                                )

                                logger.info("✅ Match window opened successfully")
                            except Exception as e:
                                logger.error(f"❌ Failed to open match window: {e}", exc_info=True)

                elif is_closing_time and state['match_window_open']:
                    async with self.match_window_lock:
                        latest_state = await db.get_game_state()
                        if latest_state['match_window_open']:
                            logger.info("🔴 Closing match window...")
                            try:
                                await db.pool.execute("UPDATE game_state SET match_window_open = FALSE")

                                try:
                                    announcement_channel = await self.fetch_channel(config.ANNOUNCEMENT_CHANNEL_ID)

                                    embed = discord.Embed(
                                        title="🔴 Match Window Closed",
                                        description="Today's match window has ended.",
                                        color=discord.Color.red()
                                    )

                                    embed.add_field(
                                        name="⏰ Next Window",
                                        value="Check `/season` for next match day",
                                        inline=False
                                    )

                                    await announcement_channel.send(embed=embed)
                                except Exception as e:
                                    logger.warning(f"⚠️ Could not send window closing announcement: {e}")

                                state = await db.get_game_state()
                                from utils.season_manager import get_next_match_window, EST
                                try:
                                    next_window = get_next_match_window()
                                    time_str = next_window.strftime('%I:%M %p')
                                    day = next_window.strftime('%a')
                                    status_text = f"Next: {day} {time_str} | Week {state['current_week']}"
                                except:
                                    status_text = f"⚽ Week {state['current_week']} | /season"

                                await self.change_presence(
                                    activity=discord.Game(name=status_text),
                                    status=discord.Status.online
                                )

                                logger.info("✅ Match window closed successfully")
                            except Exception as e:
                                logger.error(f"❌ Failed to close match window: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"❌ ERROR in check_match_windows: {e}", exc_info=True)

    @tasks.loop(hours=4)
    async def check_warnings(self):
        """Check for players who haven't trained in 48 hours"""
        try:
            players = await db.pool.fetch("""
                SELECT user_id, last_trained 
                FROM players 
                WHERE last_trained IS NOT NULL
            """)

            for player in players:
                last_trained = datetime.fromisoformat(player['last_trained'])
                hours_since = (datetime.now() - last_trained).total_seconds() / 3600

                if 48 <= hours_since < 52:
                    user = await self.fetch_user(player['user_id'])
                    if user:
                        try:
                            await user.send("⚠️ You haven't trained in 2 days! Train with `/train` to maintain your progress.")
                        except:
                            pass

        except Exception as e:
            logger.error(f"❌ ERROR in check_warnings: {e}", exc_info=True)

    @tasks.loop(hours=12)
    async def check_retirements(self):
        """Check for players who reach age 38"""
        try:
            retired_players = await db.pool.fetch("""
                SELECT user_id, first_name, last_name 
                FROM players 
                WHERE age = 38 AND retired = FALSE
            """)

            for player in retired_players:
                await db.pool.execute("UPDATE players SET retired = TRUE WHERE user_id = $1", player['user_id'])

                user = await self.fetch_user(player['user_id'])
                if user:
                    try:
                        embed = discord.Embed(
                            title="🏆 Career Complete",
                            description=f"{player['first_name']} {player['last_name']} has retired at age 38!",
                            color=discord.Color.gold()
                        )
                        await user.send(embed=embed)
                    except:
                        pass

        except Exception as e:
            logger.error(f"❌ ERROR in check_retirements: {e}", exc_info=True)

    @tasks.loop(hours=24)
    async def check_training_reminders(self):
        """Send daily training reminders to opted-in users"""
        try:
            from datetime import timezone

            # Get all players who want reminders and haven't been reminded today
            players = await db.pool.fetch("""
                SELECT user_id, first_name, last_name, last_reminded, last_trained
                FROM players
                WHERE training_reminders = TRUE
            """)

            now = datetime.now(timezone.utc)
            today_str = now.strftime('%Y-%m-%d')

            for player in players:
                # Check if already reminded today
                last_reminded = player['last_reminded']
                if last_reminded == today_str:
                    continue

                # Check if already trained today
                last_trained = player['last_trained']
                if last_trained:
                    last_trained_date = datetime.fromisoformat(last_trained).strftime('%Y-%m-%d')
                    if last_trained_date == today_str:
                        continue  # Already trained today

                # Send reminder
                try:
                    user = await self.fetch_user(player['user_id'])
                    if user:
                        embed = discord.Embed(
                            title="💪 Daily Training Reminder",
                            description=f"Hey {player['first_name']}! Don't forget to train today with `/train`",
                            color=discord.Color.blue()
                        )
                        embed.add_field(
                            name="🔥 Keep Your Streak!",
                            value="Train every day to build your 30-day streak for +3 potential!",
                            inline=False
                        )

                        await user.send(embed=embed)

                        # Update last_reminded
                        await db.pool.execute(
                            "UPDATE players SET last_reminded = $1 WHERE user_id = $2",
                            today_str, player['user_id']
                        )

                        logger.info(f"📬 Sent training reminder to {player['first_name']} {player['last_name']}")

                except Exception as e:
                    logger.warning(f"⚠️ Could not send reminder to user {player['user_id']}: {e}")

        except Exception as e:
            logger.error(f"❌ ERROR in check_training_reminders: {e}", exc_info=True)

    @tasks.loop(hours=168)
    async def cleanup_old_data(self):
        """Clean up old data older than 90 days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=90)
            deleted = await db.pool.execute("""
                DELETE FROM match_participants 
                WHERE match_id IN (
                    SELECT id FROM matches WHERE created_at < $1
                )
            """, cutoff_date)

            logger.info(f"🧹 Cleaned up {deleted} old match records")

        except Exception as e:
            logger.error(f"❌ ERROR in cleanup_old_data: {e}", exc_info=True)

    @cleanup_old_data.before_loop
    async def before_cleanup_old_data(self):
        await self.wait_until_ready()
        await asyncio.sleep(3600)

    async def wait_for_season(self):
        """Wait for season to start before beginning checks"""
        while True:
            state = await db.get_game_state()
            if state['season_started']:
                return True
            await asyncio.sleep(60)
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
