import discord
from discord import app_commands
from discord.ext import commands, tasks
import config
from database import db
import asyncio
from datetime import datetime

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
        self.match_window_lock = asyncio.Lock()  # Race condition prevention

    async def setup_hook(self):
        """Called when bot is starting up"""
        print("📄 Setting up bot...")

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
                    print("📋 Auto-migration: Adding current_match_of_week column...")
                    await conn.execute("""
                        ALTER TABLE game_state
                        ADD COLUMN current_match_of_week INTEGER DEFAULT 0
                    """)
                    await conn.execute("""
                        UPDATE game_state
                        SET current_match_of_week = 0
                        WHERE current_match_of_week IS NULL
                    """)
                    print("✅ Auto-migration complete!")
                else:
                    print("✅ current_match_of_week column already exists")
        except Exception as e:
            print(f"⚠️ Auto-migration warning: {e}")
        
        # ============================================
        # AUTO-MIGRATE: Add last_reminded column
        # ============================================
        try:
            async with db.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'players' AND column_name = 'last_reminded'
                """)
                
                if not result:
                    print("📋 Adding last_reminded column for training notifications...")
                    await conn.execute("""
                        ALTER TABLE players 
                        ADD COLUMN last_reminded TEXT
                    """)
                    print("✅ last_reminded column added")
                else:
                    print("✅ last_reminded column already exists")
        except Exception as e:
            print(f"⚠️ Migration warning: {e}")
        
        # ============================================
        # AUTO-MIGRATE: Add season_motm column
        # ============================================
        try:
            async with db.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'players' AND column_name = 'season_motm'
                """)
                
                if not result:
                    print("📋 Adding season_motm column...")
                    await conn.execute("""
                        ALTER TABLE players 
                        ADD COLUMN season_motm INTEGER DEFAULT 0
                    """)
                    await conn.execute("""
                        UPDATE players 
                        SET season_motm = 0 
                        WHERE season_motm IS NULL
                    """)
                    print("✅ season_motm column added")
                else:
                    print("✅ season_motm column already exists")
        except Exception as e:
            print(f"⚠️ Migration warning: {e}")
        
        # ============================================
        # AUTO-MIGRATE: Add career_motm column
        # ============================================
        try:
            async with db.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'players' AND column_name = 'career_motm'
                """)
                
                if not result:
                    print("📋 Adding career_motm column...")
                    await conn.execute("""
                        ALTER TABLE players 
                        ADD COLUMN career_motm INTEGER DEFAULT 0
                    """)
                    await conn.execute("""
                        UPDATE players 
                        SET career_motm = 0 
                        WHERE career_motm IS NULL
                    """)
                    print("✅ career_motm column added")
                else:
                    print("✅ career_motm column already exists")
        except Exception as e:
            print(f"⚠️ Migration warning: {e}")
        # ============================================
        # END AUTO-MIGRATE
        # ============================================

        try:
            from utils.cup_manager import initialize_cup_season
            state = await db.get_game_state()

            if state['season_started']:
                # Check if cups exist for current season
                async with db.pool.acquire() as conn:
                    result = await conn.fetchrow("""
                                                 SELECT COUNT(*) as count
                                                 FROM cup_competitions
                                                 WHERE season = $1
                                                 """, state['current_season'])

                    if result['count'] == 0:
                        print("🏆 Initializing cup competitions...")
                        await initialize_cup_season(state['current_season'])
                        print("✅ Cup competitions initialized")
                    else:
                        print("✅ Cup competitions already initialized")
        except Exception as e:
            print(f"⚠️ Cup initialization warning: {e}")
        # ============================================
        # END CUP INITIALIZATION
        # ============================================

        await self.initialize_data()
        await self.load_cogs()

        # Initialize match engine
        from utils.match_engine import MatchEngine
        from utils import match_engine as me_module
        me_module.match_engine = MatchEngine(self)
        print("✅ Match engine initialized")

        # Cache team crests
        from utils.football_data_api import cache_all_crests
        await cache_all_crests()
        print("✅ Team crests cached")

        # Sync commands (with rate limit protection)
        try:
            print("📄 Syncing commands with Discord...")
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} slash commands globally")
        except discord.HTTPException as e:
            if e.status == 429:
                print("⚠️ Rate limited by Discord. Commands will sync eventually.")
                print("💡 Tip: Avoid frequent bot restarts to prevent rate limits.")
            else:
                print(f"❌ Error syncing commands: {e}")

        # START SIMPLIFIED BACKGROUND TASKS
        if not self.season_task_started:
            self.check_match_windows.start()
            self.check_warnings.start()
            self.check_retirements.start()
            self.check_training_reminders.start()
            self.cleanup_old_data.start()  # Weekly cleanup
            self.season_task_started = True
            print("✅ Background tasks started (simplified system)")

    async def load_cogs(self):
        """Load all command modules"""
        cogs = [
            'commands.start',  # Player creation
            'commands.player',
            'commands.training',
            'commands.season',
            'commands.matches',
            'commands.leagues',
            'commands.transfers',
            'commands.news',
            'commands.interactive_match',
            'commands.adm',  # Admin commands
            'commands.organized',  # Organized player/league commands
            'commands.achievements',  # Achievement system
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅ Loaded {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")

    async def initialize_data(self):
        """Initialize database with teams and complete squads"""
        from data.teams import ALL_TEAMS
        from data.players import PREMIER_LEAGUE_PLAYERS
        from data.championship_players import CHAMPIONSHIP_PLAYERS
        from utils.npc_squad_generator import populate_all_teams

        async with db.pool.acquire() as conn:
            result = await conn.fetchrow("SELECT COUNT(*) as count FROM teams")
            team_count = result['count']

        if team_count == 0:
            print("📊 Initializing teams...")
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
            print(f"✅ Added {len(ALL_TEAMS)} teams")

        async with db.pool.acquire() as conn:
            result = await conn.fetchrow("SELECT COUNT(*) as count FROM npc_players WHERE is_regen = FALSE")
            real_player_count = result['count']

        if real_player_count == 0:
            await self.populate_real_players(PREMIER_LEAGUE_PLAYERS, CHAMPIONSHIP_PLAYERS)

        async with db.pool.acquire() as conn:
            result = await conn.fetchrow("SELECT COUNT(*) as count FROM npc_players")
            npc_count = result['count']

        if npc_count < 1000:
            print("⚽ Generating squads for remaining teams...")
            await populate_all_teams()
            print("✅ All teams now have complete squads!")

        await db.retire_old_players()

    async def populate_real_players(self, pl_players, champ_players):
        """Populate real players with proper stats"""
        import random

        print("⚽ Adding real Premier League players...")
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

        print(f"✅ Added {len(pl_players)} Premier League players")

        print("⚽ Adding real Championship players...")
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

        print(f"✅ Added {len(champ_players)} Championship players")

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
                'physical': max(60, base + random.randint(-5, 5))
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

                    # Get players in this server who have matches
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

                    # Mention players who need to play
                    player_mentions = []
                    for p in players:
                        member = guild.get_member(p['user_id'])
                        if member:
                            player_mentions.append(f"{member.mention} ({p['team_name']})")

                    if player_mentions:
                        mentions_text = "\n".join(player_mentions[:10])  # Max 10
                        if len(player_mentions) > 10:
                            mentions_text += f"\n*...and {len(player_mentions) - 10} more*"

                        embed.add_field(
                            name="👥 Players with Matches",
                            value=mentions_text,
                            inline=False
                        )

                    embed.set_footer(text="Window closes at 5:00 PM EST!")

                    await channel.send(embed=embed)
                    print(f"✅ Posted match window notification to {guild.name}")
        except Exception as e:
            print(f"⚠️ Could not post match window notification: {e}")

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

                    # Show match summary
                    if week_results:
                        results_text = ""
                        for result in week_results[:5]:  # Show top 5
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
                    print(f"✅ Posted window closed notification to {guild.name}")
        except Exception as e:
            print(f"⚠️ Could not post window closed notification: {e}")

    # ============================================
    # SIMPLIFIED BACKGROUND TASKS
    # ============================================

    @tasks.loop(hours=168)  # Weekly (7 days)
    async def cleanup_old_data(self):
        """Weekly cleanup of old data"""
        try:
            await db.cleanup_old_retired_players()
            print("✅ Weekly data cleanup complete")
        except Exception as e:
            print(f"❌ Error in cleanup: {e}")

    @cleanup_old_data.before_loop
    async def before_cleanup_old_data(self):
        await self.wait_until_ready()

    @tasks.loop(minutes=5)
    async def check_match_windows(self):
        """
        Simple 5-minute check: Is it time to open/close windows?
        Checks: Mon/Wed/Sat 3-5 PM EST
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
            
            # Check: Is it match window time RIGHT NOW?
            is_window_time, is_start_time, is_end_time = is_match_window_time()
            
            window_open = state['match_window_open']
            
            # OPEN WINDOW: If it's start time and window is closed
            if is_start_time and not window_open:
                print("🟢 Opening match window (fixed schedule)")
                await open_match_window()
                await self.notify_match_window_open()
            
            # CLOSE WINDOW: If it's end time and window is open
            elif is_end_time and window_open:
                print("🔴 Closing match window (fixed schedule)")
                await close_match_window(bot=self)
            
            # AUTO-CLOSE: If window is open but it's NOT window time (safety check)
            elif window_open and not is_window_time:
                print("⚠️ Window is open outside of match hours - auto-closing")
                await close_match_window(bot=self)
                
        except Exception as e:
            print(f"❌ Error in match window check: {e}")
            import traceback
            traceback.print_exc()

    @tasks.loop(minutes=5)
    async def check_warnings(self):
        """
        Check if we should send warnings
        Times: 2:00 PM, 2:30 PM, 2:45 PM (before open), 4:45 PM (before close)
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
            
            # Check each warning type
            if should_send_warning('pre_1h'):
                await send_1h_warning(self)
            
            elif should_send_warning('pre_30m'):
                await send_30m_warning(self)
            
            elif should_send_warning('pre_15m'):
                await send_15m_warning(self)
            
            elif should_send_warning('closing_soon'):
                await send_closing_warning(self)
                
        except Exception as e:
            print(f"❌ Error in warning check: {e}")

    @tasks.loop(hours=24)
    async def check_retirements(self):
        """Daily retirement check"""
        try:
            await db.retire_old_players()
        except Exception as e:
            print(f"❌ Error in retirement check: {e}")

    @tasks.loop(hours=1)
    async def check_training_reminders(self):
        """Check for players whose training is ready and send reminders"""
        try:
            async with db.pool.acquire() as conn:
                # Get players who can train now (24h+ since last training)
                # AND haven't been reminded in the last 12 hours
                rows = await conn.fetch("""
                    SELECT user_id, player_name, last_training
                    FROM players
                    WHERE retired = FALSE
                      AND last_training IS NOT NULL
                      AND last_training::timestamp <= NOW() - INTERVAL '24 hours'
                      AND (last_reminded IS NULL OR last_reminded::timestamp < NOW() - INTERVAL '12 hours')
                """)

                for row in rows:
                    # Send reminder
                    success = await self.send_training_reminder(row['user_id'])
                    
                    if success:
                        # Update last_reminded to avoid spam
                        await conn.execute("""
                            UPDATE players 
                            SET last_reminded = $1 
                            WHERE user_id = $2
                        """, datetime.now().isoformat(), row['user_id'])
                        
        except Exception as e:
            print(f"❌ Error in training reminder check: {e}")

    async def send_training_reminder(self, user_id: int):
        """Send DM when training is available"""
        try:
            user = await self.fetch_user(user_id)
            embed = discord.Embed(
                title="💪 Training Available!",
                description="Your training cooldown is over!\n\nUse `/train` to improve your stats.",
                color=discord.Color.green()
            )
            embed.add_field(
                name="🔥 Reminder",
                value="Training daily maintains your streak!\n30-day streak = +3 potential",
                inline=False
            )
            await user.send(embed=embed)
            print(f"✅ Sent training reminder to user {user_id}")
            return True
        except Exception as e:
            print(f"⚠️ Could not send training reminder to {user_id}: {e}")
            return False

    # Wait until ready methods
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

    # ============================================
    # END SIMPLIFIED BACKGROUND TASKS
    # ============================================

    async def on_ready(self):
        """Called when bot is fully ready"""
        state = await db.get_game_state()

        print("\n" + "=" * 50)
        print(f'✅ Bot logged in as {self.user.name}')
        print(f'✅ Connected to {len(self.guilds)} server(s)')

        if state['season_started']:
            print(f'📅 Season: {state["current_season"]} - Week {state["current_week"]}/{config.SEASON_TOTAL_WEEKS}')
        else:
            print(f'⏳ Season not started')

        # Show next match window
        from utils.season_manager import get_next_match_window, EST
        try:
            next_window = get_next_match_window()
            print(f'⏰ Next match window: {next_window.strftime("%A, %B %d at %I:%M %p EST")}')
        except:
            pass

        print("=" * 50 + "\n")

        # Dynamic bot presence based on window status
        if state['season_started']:
            if state['match_window_open']:
                # Window is OPEN - show green status
                status_text = f"🟢 WINDOW OPEN | Week {state['current_week']}"
            else:
                # Window is CLOSED - show next window time
                try:
                    next_window = get_next_match_window()
                    day = next_window.strftime('%a')  # Mon, Wed, Sat
                    status_text = f"Next: {day} 3PM EST | Week {state['current_week']}"
                except:
                    status_text = f"⚽ Week {state['current_week']} | /season"
        else:
            # Season not started
            status_text = "⚽ /start to begin"
        
        await self.change_presence(
            activity=discord.Game(name=status_text),
            status=discord.Status.online
        )

    # ============================================
    # HIGH #4: AUTO-SETUP CHANNELS ON NEW SERVERS
    # ============================================
    
    async def on_guild_join(self, guild):
        """When bot joins a new server, auto-setup channels"""
        print(f"📥 Joined new server: {guild.name}")
        
        from utils.channel_setup import setup_server_channels
        try:
            await setup_server_channels(guild)
            print(f"✅ Auto-setup complete for {guild.name}")
        except Exception as e:
            print(f"⚠️ Could not auto-setup channels: {e}")


# Create bot instance
bot = FootballBot()


# Help command (ONLY non-admin standalone command)
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

    # Only show admin info to administrators
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
        print("\n⚠️ Bot shutdown requested")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
