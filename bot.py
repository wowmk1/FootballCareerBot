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

    async def setup_hook(self):
        """Called when bot is starting up"""
        print("🔄 Setting up bot...")

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
        # END AUTO-MIGRATE
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
            print("🔄 Syncing commands with Discord...")
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} slash commands globally")
        except discord.HTTPException as e:
            if e.status == 429:
                print("⚠️ Rate limited by Discord. Commands will sync eventually.")
                print("💡 Tip: Avoid frequent bot restarts to prevent rate limits.")
            else:
                print(f"❌ Error syncing commands: {e}")

        if not self.season_task_started:
            self.check_match_day.start()
            self.check_retirements.start()
            self.check_training_reminders.start()
            self.check_match_warnings.start()
            self.season_task_started = True
            print("✅ Background tasks started")

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
            for guild in self.guilds:
                channel = discord.utils.get(guild.text_channels, name="match-results")
                if not channel:
                    channel = discord.utils.get(guild.text_channels, name="general")
                
                if channel:
                    state = await db.get_game_state()
                    embed = discord.Embed(
                        title="🟢 MATCH WINDOW OPEN!",
                        description=f"**Week {state['current_week']}** matches are now playable!\n\n"
                                   f"Use `/play_match` to play your match!",
                        color=discord.Color.green()
                    )
                    
                    from datetime import datetime
                    closes = datetime.fromisoformat(state['match_window_closes'])
                    timestamp = int(closes.timestamp())
                    
                    embed.add_field(
                        name="⏰ Window Closes",
                        value=f"<t:{timestamp}:R>\n<t:{timestamp}:t>",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="⚡ Quick Commands",
                        value="`/play_match` - Play your match\n`/season` - Check schedule",
                        inline=True
                    )
                    
                    embed.set_footer(text="Don't miss your match!")
                    
                    await channel.send(embed=embed)
                    print(f"✅ Posted match window notification to {guild.name}")
        except Exception as e:
            print(f"⚠️ Could not post match window notification: {e}")

    @tasks.loop(minutes=15)
    async def check_match_day(self):
        """Check if it's time to open/close match windows"""
        try:
            from utils.season_manager import check_match_day_trigger
            triggered = await check_match_day_trigger(bot=self)
            if triggered:
                print("⚽ Match window state changed")
        except Exception as e:
            print(f"❌ Error in match day check: {e}")

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

    @tasks.loop(minutes=5)
    async def check_match_warnings(self):
        """Check for upcoming match windows and send warnings"""
        try:
            state = await db.get_game_state()
            
            if not state['season_started'] or state['match_window_open']:
                return
            
            if not state['next_match_day']:
                return
            
            from datetime import datetime
            
            now = datetime.now()
            next_match = datetime.fromisoformat(state['next_match_day'])
            time_until = (next_match - now).total_seconds()
            
            # Send warnings at specific intervals
            if 3300 <= time_until <= 3600:  # 55-60 minutes before
                await self.send_match_warning_1hour()
            elif 1500 <= time_until <= 1800:  # 25-30 minutes before
                await self.send_match_warning_30min()
            elif 600 <= time_until <= 900:  # 10-15 minutes before
                await self.send_match_warning_15min()
                
        except Exception as e:
            print(f"❌ Error in match warning check: {e}")

    async def send_match_warning_1hour(self):
        """Send 1 hour warning to all servers"""
        state = await db.get_game_state()
        
        for guild in self.guilds:
            try:
                channel = discord.utils.get(guild.text_channels, name="match-results")
                if not channel:
                    channel = discord.utils.get(guild.text_channels, name="general")
                
                if channel:
                    from datetime import datetime
                    next_match = datetime.fromisoformat(state['next_match_day'])
                    timestamp = int(next_match.timestamp())
                    
                    embed = discord.Embed(
                        title="⏰ Match Window Opening Soon!",
                        description=f"**Week {state['current_week']}** matches start in **1 hour**!",
                        color=discord.Color.orange()
                    )
                    
                    embed.add_field(
                        name="🕐 Opens At",
                        value=f"<t:{timestamp}:t> (<t:{timestamp}:R>)",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="⚡ Get Ready",
                        value="Use `/play_match` when the window opens!",
                        inline=True
                    )
                    
                    embed.set_footer(text="Don't miss your match!")
                    
                    await channel.send(embed=embed)
                    print(f"✅ Sent 1h warning to {guild.name}")
            except Exception as e:
                print(f"⚠️ Could not send 1h warning to {guild.name}: {e}")

    async def send_match_warning_30min(self):
        """Send 30 minute warning via DM"""
        state = await db.get_game_state()
        
        async with db.pool.acquire() as conn:
            players = await conn.fetch("""
                SELECT user_id, player_name 
                FROM players 
                WHERE retired = FALSE AND team_id != 'free_agent'
            """)
        
        from datetime import datetime
        next_match = datetime.fromisoformat(state['next_match_day'])
        timestamp = int(next_match.timestamp())
        
        for player in players:
            try:
                user = await self.fetch_user(player['user_id'])
                
                embed = discord.Embed(
                    title="⏰ Match Starting Soon!",
                    description=f"**Week {state['current_week']}** match window opens in **30 minutes**!",
                    color=discord.Color.orange()
                )
                
                embed.add_field(
                    name="🕐 Opens At",
                    value=f"<t:{timestamp}:t> (<t:{timestamp}:R>)",
                    inline=False
                )
                
                embed.add_field(
                    name="⚡ Quick Tip",
                    value="Be ready to use `/play_match` when the window opens!",
                    inline=False
                )
                
                await user.send(embed=embed)
            except:
                pass
        
        print(f"✅ Sent 30min warnings to {len(players)} players")

    async def send_match_warning_15min(self):
        """Send 15 minute final warning"""
        state = await db.get_game_state()
        
        for guild in self.guilds:
            try:
                channel = discord.utils.get(guild.text_channels, name="match-results")
                if not channel:
                    channel = discord.utils.get(guild.text_channels, name="general")
                
                if channel:
                    from datetime import datetime
                    next_match = datetime.fromisoformat(state['next_match_day'])
                    timestamp = int(next_match.timestamp())
                    
                    embed = discord.Embed(
                        title="🚨 Match Window Opening VERY Soon!",
                        description=f"**Week {state['current_week']}** matches start in **15 minutes**!",
                        color=discord.Color.red()
                    )
                    
                    embed.add_field(
                        name="🕐 Opens At",
                        value=f"<t:{timestamp}:t> (<t:{timestamp}:R>)",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="⚡ Final Reminder",
                        value="Get ready to use `/play_match`!\nWindow will be open for 2 hours.",
                        inline=False
                    )
                    
                    await channel.send(embed=embed)
                    print(f"✅ Sent 15min warning to {guild.name}")
            except Exception as e:
                print(f"⚠️ Could not send 15min warning to {guild.name}: {e}")

    @check_match_day.before_loop
    async def before_check_match_day(self):
        await self.wait_until_ready()

    @check_retirements.before_loop
    async def before_check_retirements(self):
        await self.wait_until_ready()

    @check_training_reminders.before_loop
    async def before_check_training_reminders(self):
        await self.wait_until_ready()

    @check_match_warnings.before_loop
    async def before_check_match_warnings(self):
        await self.wait_until_ready()

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

        print("=" * 50 + "\n")

        await self.change_presence(
            activity=discord.Game(name="⚽ /start to begin | /help for commands"),
            status=discord.Status.online
        )


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
