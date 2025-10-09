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

        # Sync commands
        print("🔄 Syncing commands with Discord...")
        synced = await self.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands globally")

        if not self.season_task_started:
            self.check_match_day.start()
            self.check_retirements.start()
            self.season_task_started = True
            print("✅ Background tasks started")

    async def load_cogs(self):
        """Load all command modules"""
        cogs = [
            'commands.player',
            'commands.training',
            'commands.season',
            'commands.matches',
            'commands.leagues',
            'commands.transfers',
            'commands.news',
            'commands.interactive_match',
            # DON'T load admin.py as cog - we add the group manually below
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅ Loaded {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")
        
        # Load admin commands group from adm.py (not admin.py!)
        try:
            from commands.adm import admin_group
            self.tree.add_command(admin_group)
            print(f"✅ Loaded admin command group as /{admin_group.name}")
        except Exception as e:
            print(f"❌ Failed to load admin group: {e}")
            import traceback
            traceback.print_exc()

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

    @check_match_day.before_loop
    async def before_check_match_day(self):
        await self.wait_until_ready()

    @check_retirements.before_loop
    async def before_check_retirements(self):
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

    async def setup_server_channels(self, guild):
        """Setup organized channel structure"""
        categories_to_create = {
            "📰 NEWS & INFO": ["news-feed", "match-results", "transfer-news"],
            "⚽ ACTIVE MATCHES": [],
            "📊 COMMANDS": ["bot-commands"],
            "💬 DISCUSSION": ["general-chat", "tactics-talk"]
        }

        for category_name, channels in categories_to_create.items():
            category = discord.utils.get(guild.categories, name=category_name)

            if not category:
                category = await guild.create_category(category_name)
                print(f"✅ Created category: {category_name}")

            for channel_name in channels:
                existing_channel = discord.utils.get(guild.text_channels, name=channel_name)

                if not existing_channel:
                    await guild.create_text_channel(channel_name, category=category)
                    print(f"✅ Created channel: {channel_name}")

    async def post_weekly_news(self, guild):
        """Post weekly news digest"""
        news_channel = discord.utils.get(guild.text_channels, name="news-feed")
        if not news_channel:
            return

        state = await db.get_game_state()
        current_week = state['current_week']

        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT *
                   FROM news
                   WHERE week_number = $1
                   ORDER BY importance DESC, created_at DESC LIMIT 10""",
                current_week
            )
            news_items = [dict(row) for row in rows]

        if not news_items:
            return

        embed = discord.Embed(
            title=f"📰 Week {current_week} News Digest",
            description=f"Season {state['current_season']}",
            color=discord.Color.blue()
        )

        for news in news_items[:8]:
            emoji = {'player_news': '⭐', 'league_news': '🏆', 'match_news': '⚽',
                     'transfer_news': '💼'}.get(news['category'], '📌')

            embed.add_field(
                name=f"{emoji} {news['headline']}",
                value=news['content'][:200],
                inline=False
            )

        await news_channel.send(embed=embed)


# Create bot instance
bot = FootballBot()


# ADMIN: Restart bot to reload commands
@bot.command()
@commands.has_permissions(administrator=True)
async def restart(ctx):
    """Restart the bot to reload all commands"""
    await ctx.send("🔄 Restarting bot to reload commands...")
    await bot.close()


# ADMIN: Clear old admin commands from Discord's global cache
@bot.command()
@commands.has_permissions(administrator=True)
async def fix_admin(ctx):
    """Remove old /admin_* commands and register /admin group properly"""
    await ctx.send("🔄 Fixing admin commands...")
    
    try:
        old_commands = [
            'admin_advance_week', 'admin_advance_weeks', 'admin_open_window',
            'admin_close_window', 'admin_assign_team', 'admin_wipe_players',
            'admin_check_retirements', 'admin_check_squads', 'admin_transfer_test',
            'admin_debug_crests', 'admin_setup_channels', 'admin_game_state'
        ]
        
        # Get current global commands from Discord
        global_commands = await bot.tree.fetch_commands()
        
        removed = []
        for cmd in global_commands:
            if cmd.name in old_commands:
                await bot.tree.delete_command(cmd.id)
                removed.append(cmd.name)
        
        # Re-sync to push changes
        await bot.tree.sync()
        
        if removed:
            await ctx.send(f"✅ Removed {len(removed)} old admin commands: {', '.join(removed)}\n"
                           f"🔄 Re-synced commands. Restart Discord to see changes!")
        else:
            await ctx.send("✅ No old admin commands found. Your commands are already correct!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")


# SLASH COMMAND VERSION - This one will definitely work
@bot.tree.command(name="fix_admin_commands", description="🔧 [ADMIN] Remove old /admin_* commands")
@app_commands.checks.has_permissions(administrator=True)
async def fix_admin_commands(interaction: discord.Interaction):
    """Remove old /admin_* commands and register /admin group properly"""
    await interaction.response.defer(ephemeral=True)
    
    try:
        old_commands = [
            'admin_advance_week', 'admin_advance_weeks', 'admin_open_window',
            'admin_close_window', 'admin_assign_team', 'admin_wipe_players',
            'admin_check_retirements', 'admin_check_squads', 'admin_transfer_test',
            'admin_debug_crests', 'admin_setup_channels', 'admin_game_state'
        ]
        
        # Get current global commands from Discord
        global_commands = await bot.tree.fetch_commands()
        
        await interaction.followup.send(f"📊 Found {len(global_commands)} total global commands\n🔍 Checking for old admin commands...", ephemeral=True)
        
        removed = []
        for cmd in global_commands:
            if cmd.name in old_commands:
                await bot.tree.delete_command(cmd.id)
                removed.append(cmd.name)
        
        # Re-sync to push changes
        synced = await bot.tree.sync()
        
        if removed:
            await interaction.followup.send(
                f"✅ **Fixed Admin Commands!**\n\n"
                f"**Removed {len(removed)} old commands:**\n" + 
                "\n".join([f"• `/{cmd}`" for cmd in removed]) +
                f"\n\n**Total commands now:** {len(synced)}\n"
                f"⚠️ **Fully restart Discord to see changes!**",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"✅ No old admin commands found!\n"
                f"📊 Total global commands: {len(synced)}\n\n"
                f"Your `/admin` group should already be working correctly.",
                ephemeral=True
            )
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)


# DIAGNOSTIC: See what commands are actually registered
@bot.tree.command(name="debug_commands", description="🔍 [ADMIN] See all registered commands")
@app_commands.checks.has_permissions(administrator=True)
async def debug_commands(interaction: discord.Interaction):
    """Debug what commands are registered"""
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Check what's in the bot's tree
        local_commands = bot.tree.get_commands()
        
        # Check what Discord knows about
        global_commands = await bot.tree.fetch_commands()
        
        local_list = "**Local (in bot code):**\n"
        for cmd in local_commands:
            if isinstance(cmd, app_commands.Group):
                local_list += f"📁 `/{cmd.name}` (GROUP with {len(cmd.commands)} subcommands)\n"
                for subcmd in cmd.commands:
                    local_list += f"  └─ `{subcmd.name}`\n"
            else:
                local_list += f"📄 `/{cmd.name}`\n"
        
        global_list = "**Global (registered with Discord):**\n"
        for cmd in global_commands:
            global_list += f"• `/{cmd.name}`\n"
        
        await interaction.followup.send(
            f"🔍 **Command Registry Debug**\n\n"
            f"{local_list}\n"
            f"{global_list}\n"
            f"📊 Local: {len(local_commands)} | Global: {len(global_commands)}",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)


# NUCLEAR OPTION: Completely wipe and rebuild all commands
@bot.tree.command(name="rebuild_commands", description="🔧 [ADMIN] Completely rebuild all slash commands")
@app_commands.checks.has_permissions(administrator=True)
async def rebuild_commands(interaction: discord.Interaction):
    """Completely wipe and rebuild all commands"""
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Step 1: Clear the local tree
        bot.tree.clear_commands(guild=None)
        await interaction.followup.send(f"🧹 Step 1: Cleared local command tree", ephemeral=True)
        
        # Step 2: Sync empty tree to remove all commands from Discord
        await bot.tree.sync()
        await interaction.followup.send(f"🗑️ Step 2: Synced empty tree (removed all commands from Discord)", ephemeral=True)
        
        # Step 3: Reload all cogs to re-register commands
        await interaction.followup.send(f"🔄 Step 3: Reloading all command modules...", ephemeral=True)
        
        # Reload cogs
        cogs = [
            'commands.player',
            'commands.training',
            'commands.season',
            'commands.matches',
            'commands.leagues',
            'commands.transfers',
            'commands.news',
            'commands.interactive_match',
        ]
        
        for cog in cogs:
            try:
                await bot.reload_extension(cog)
            except:
                await bot.load_extension(cog)
        
        # Re-add admin group
        from commands.admin import admin_group
        bot.tree.add_command(admin_group)
        
        # Re-add utility commands
        bot.tree.add_command(help_command)
        bot.tree.add_command(fix_admin_commands)
        bot.tree.add_command(debug_commands)
        bot.tree.add_command(rebuild_commands)
        
        await interaction.followup.send(f"✅ Step 4: Reloaded all modules", ephemeral=True)
        
        # Step 4: Sync everything fresh
        synced = await bot.tree.sync()
        
        # Show what was registered
        local_commands = bot.tree.get_commands()
        admin_group_local = None
        for cmd in local_commands:
            if isinstance(cmd, app_commands.Group) and cmd.name == 'admin':
                admin_group_local = cmd
                break
        
        result_msg = f"✅ **REBUILD COMPLETE!**\n\n"
        result_msg += f"🎯 Registered {len(synced)} commands with Discord\n"
        
        if admin_group_local:
            result_msg += f"📁 `/admin` group has {len(admin_group_local.commands)} subcommands\n"
        
        result_msg += f"\n⚠️ **FULLY CLOSE AND REOPEN DISCORD** to see changes!\n"
        result_msg += f"The `/admin` command should now be a proper group."
        
        await interaction.followup.send(result_msg, ephemeral=True)
        
    except Exception as e:
        import traceback
        await interaction.followup.send(f"❌ Error: {e}\n```{traceback.format_exc()}```", ephemeral=True)


# Help command (ONLY ONE DEFINITION)
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
        value="`/start` - Create player\n`/profile` - View stats\n`/compare @user` - Compare players",
        inline=False
    )

    embed.add_field(
        name="💼 Transfers",
        value="`/offers` - View offers (transfer windows)\n`/my_contract` - Current deal\n`/transfer_history` - Past moves",
        inline=False
    )

    embed.add_field(
        name="📈 Training",
        value="`/train` - Train daily (6+ points per session!)\n30-day streak = +5 permanent potential!",
        inline=False
    )

    embed.add_field(
        name="🎲 Matches",
        value="`/play_match` - Play your match!\nPosition-specific events\nD20 duels vs opponents",
        inline=False
    )

    embed.add_field(
        name="📅 Season",
        value="`/season` - Current week\n`/fixtures` - Your schedule\n`/league` - League tables",
        inline=False
    )

    # Only show admin info to administrators
    if interaction.user.guild_permissions.administrator:
        embed.add_field(
            name="🔧 Admin Commands",
            value="Type `/admin` to see all admin commands\nAll admin tools are in the `/admin` group",
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
