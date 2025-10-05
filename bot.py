import discord
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
        
        # Connect to database
        await db.connect()
        
        # Initialize teams and players if database is empty
        await self.initialize_data()
        
        # Load all command cogs
        await self.load_cogs()
        
        # Initialize match engine
        from utils.match_engine import MatchEngine
        from utils import match_engine as me_module
        me_module.match_engine = MatchEngine(self)
        print("✅ Match engine initialized")
        
        # Sync slash commands
        await self.tree.sync()
        print(f"✅ Synced {len(self.tree.get_commands())} slash commands")
        
        # Start background tasks
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
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅ Loaded {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")
    
    async def initialize_data(self):
        """Initialize database with teams and players if empty"""
        from data.teams import ALL_TEAMS
        from data.players import PREMIER_LEAGUE_PLAYERS
        
        # Check if teams exist
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
                    ''',
                        team['team_id'],
                        team['team_name'],
                        team['league'],
                        budget,
                        wage_budget
                    )
            print(f"✅ Added {len(ALL_TEAMS)} teams")
        
        # Check if NPC players exist
        async with db.pool.acquire() as conn:
            result = await conn.fetchrow("SELECT COUNT(*) as count FROM npc_players")
            npc_count = result['count']
        
        if npc_count == 0 and len(PREMIER_LEAGUE_PLAYERS) > 0:
            print("⚽ Initializing NPC players...")
            async with db.pool.acquire() as conn:
                for player in PREMIER_LEAGUE_PLAYERS:
                    overall = player['overall_rating']
                    
                    if player['position'] == 'GK':
                        pace = max(40, overall - 10)
                        shooting = max(40, overall - 15)
                        passing = max(50, overall - 5)
                        dribbling = max(45, overall - 10)
                        defending = max(70, overall + 10)
                        physical = max(60, overall)
                    elif player['position'] in ['ST', 'W']:
                        pace = max(60, overall + 5)
                        shooting = max(65, overall + 5)
                        passing = max(55, overall - 5)
                        dribbling = max(60, overall + 5)
                        defending = max(35, overall - 20)
                        physical = max(55, overall)
                    elif player['position'] in ['CAM', 'CM']:
                        pace = max(55, overall)
                        shooting = max(60, overall)
                        passing = max(70, overall + 5)
                        dribbling = max(65, overall + 5)
                        defending = max(50, overall - 10)
                        physical = max(60, overall)
                    elif player['position'] in ['CDM']:
                        pace = max(50, overall - 5)
                        shooting = max(55, overall - 5)
                        passing = max(70, overall + 5)
                        dribbling = max(55, overall)
                        defending = max(70, overall + 5)
                        physical = max(70, overall + 5)
                    elif player['position'] in ['CB', 'FB']:
                        pace = max(55, overall if player['position'] == 'FB' else overall - 5)
                        shooting = max(40, overall - 20)
                        passing = max(60, overall)
                        dribbling = max(50, overall - 10)
                        defending = max(75, overall + 5)
                        physical = max(75, overall + 5)
                    else:
                        pace = overall
                        shooting = overall
                        passing = overall
                        dribbling = overall
                        defending = overall
                        physical = overall
                    
                    await conn.execute('''
                        INSERT INTO npc_players (
                            player_name, team_id, position, age, overall_rating,
                            pace, shooting, passing, dribbling, defending, physical, is_regen
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, FALSE)
                    ''',
                        player['player_name'],
                        player['team_id'],
                        player['position'],
                        player['age'],
                        player['overall_rating'],
                        pace, shooting, passing, dribbling, defending, physical
                    )
            
            print(f"✅ Added {len(PREMIER_LEAGUE_PLAYERS)} NPC players")
            
            await db.retire_old_players()
    
    @tasks.loop(minutes=15)
    async def check_match_day(self):
        """Check if it's time to open/close match windows"""
        try:
            from utils.season_manager import check_match_day_trigger
            
            triggered = await check_match_day_trigger()
            
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
        """Wait until bot is ready"""
        await self.wait_until_ready()
    
    @check_retirements.before_loop
    async def before_check_retirements(self):
        """Wait until bot is ready"""
        await self.wait_until_ready()
    
    async def on_ready(self):
        """Called when bot is fully ready"""
        state = await db.get_game_state()
        
        print("\n" + "="*50)
        print(f'✅ Bot logged in as {self.user.name}')
        print(f'✅ Bot ID: {self.user.id}')
        print(f'✅ Connected to {len(self.guilds)} server(s)')
        print(f'✅ Latency: {round(self.latency * 1000)}ms')
        
        if state['season_started']:
            print(f'📅 Season: {state["current_season"]} - Week {state["current_week"]}/{config.SEASON_TOTAL_WEEKS}')
            if state['match_window_open']:
                print(f'🎮 Match window: OPEN')
            else:
                print(f'⏰ Match window: CLOSED')
        else:
            print(f'⏳ Season not started - waiting for first player')
        
        print("="*50 + "\n")
        
        # Set bot status
        await self.change_presence(
            activity=discord.Game(name="⚽ /start to begin | /help for commands"),
            status=discord.Status.online
        )
    
    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        print(f"❌ Error: {error}")

# Create bot instance
bot = FootballBot()

# Help command
@bot.tree.command(name="help", description="View all available commands and how to play")
async def help_command(interaction: discord.Interaction):
    """Show help information"""
    
    embed = discord.Embed(
        title="⚽ Football Career Bot - Complete Guide",
        description="Build your player from age 18 to 40 with **DnD-style interactive matches**!",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🎮 Getting Started",
        value=(
            "`/start` - Create your player (auto-assigned to team!)\n"
            "`/profile [@user]` - View stats\n"
            "`/compare @user` - Compare players"
        ),
        inline=False
    )
    
    embed.add_field(
        name="💼 Transfers & Contracts",
        value=(
            "`/transfer_market` - Browse clubs interested in you\n"
            "`/my_contract` - View your current deal\n"
            "`/transfer_history` - See all your moves"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📈 Daily Training",
        value=(
            "`/train` - Train once every 24h\n"
            "• Build streaks for bonuses\n"
            "• Veterans improve slower"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🎲 INTERACTIVE MATCHES",
        value=(
            "`/play_match` - Play your match!\n"
            "• **8 key moments** per game\n"
            "• **Choose: Shoot/Pass/Dribble**\n"
            "• **Roll d20 + stats vs DC**\n"
            "• **10 sec timer** (auto-rolls if AFK)\n"
            "• **Affect the score** with decisions!"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📅 Match Windows",
        value=(
            f"• **Match days at {config.MATCH_START_HOUR}:00**\n"
            f"• **{config.MATCH_WINDOW_HOURS}h window** to play\n"
            "• Use `/play_match` during windows\n"
            "• Auto-sim if you miss it"
        ),
        inline=False
    )
    
    embed.add_field(
        name="⚽ Other Commands",
        value=(
            "`/season` - Check current week\n"
            "`/fixtures` - See your schedule\n"
            "`/results` - Recent matches\n"
            "`/league` - League tables\n"
            "`/news` - Your news feed"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🎲 DnD Mechanics",
        value=(
            "**Roll d20 + stat modifier vs DC**\n"
            "• Shooting 82 = +8 modifier\n"
            "• DC 10 = Easy | 15 = Medium | 20 = Hard\n"
            "• Natural 20 = Critical success!\n"
            "• Natural 1 = Critical failure!"
        ),
        inline=False
    )
    
    embed.add_field(
        name="⏳ Career",
        value=(
            f"• Age {config.STARTING_AGE}-{config.RETIREMENT_AGE} ({config.RETIREMENT_AGE - config.STARTING_AGE} years)\n"
            "• Retire at 40, create new player\n"
            "• Build your legacy!"
        ),
        inline=False
    )
    
    embed.set_footer(text=f"Season: {config.CURRENT_SEASON} | Transfer system enabled!")
    
    await interaction.response.send_message(embed=embed)

# Admin commands
@bot.tree.command(name="admin_advance_week", description="[ADMIN] Manually advance to next week")
async def admin_advance_week(interaction: discord.Interaction):
    """Admin: Force advance week"""
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Administrator permissions required!",
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    
    from utils.season_manager import advance_week
    await advance_week()
    
    state = await db.get_game_state()
    
    embed = discord.Embed(
        title="✅ Week Advanced",
        description=f"Now on Week {state['current_week']}/{config.SEASON_TOTAL_WEEKS}",
        color=discord.Color.green()
    )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="admin_open_window", description="[ADMIN] Manually open match window")
async def admin_open_window(interaction: discord.Interaction):
    """Admin: Force open match window"""
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Administrator permissions required!",
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    
    from utils.season_manager import open_match_window
    await open_match_window()
    
    embed = discord.Embed(
        title="✅ Match Window Opened",
        description=f"Window open for {config.MATCH_WINDOW_HOURS} hours",
        color=discord.Color.green()
    )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="admin_close_window", description="[ADMIN] Manually close match window")
async def admin_close_window(interaction: discord.Interaction):
    """Admin: Force close match window"""
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Administrator permissions required!",
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    
    from utils.season_manager import close_match_window
    await close_match_window()
    
    embed = discord.Embed(
        title="✅ Match Window Closed",
        description="Unplayed matches auto-simulated",
        color=discord.Color.green()
    )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="admin_assign_team", description="[ADMIN] Manually assign a player to a team")
@app_commands.describe(
    user="Player to assign",
    team_id="Team ID (e.g., 'man_city', 'arsenal', 'leeds')"
)
async def admin_assign_team(interaction: discord.Interaction, user: discord.User, team_id: str):
    """Admin: Assign player to team"""
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Administrator permissions required!",
            ephemeral=True
        )
        return
    
    player = await db.get_player(user.id)
    
    if not player:
        await interaction.response.send_message(
            f"❌ {user.mention} hasn't created a player yet!",
            ephemeral=True
        )
        return
    
    team = await db.get_team(team_id)
    
    if not team:
        await interaction.response.send_message(
            f"❌ Team '{team_id}' not found!\n\n"
            f"💡 **Examples:** `man_city`, `arsenal`, `liverpool`, `chelsea`, `leeds`, `burnley`, `barnsley`",
            ephemeral=True
        )
        return
    
    wage = player['overall_rating'] * 1000
    
    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE players SET team_id = $1, league = $2, contract_wage = $3, contract_years = $4 WHERE user_id = $5",
            team_id, team['league'], wage, 3, user.id
        )
        
        await conn.execute('''
            INSERT INTO transfers (user_id, from_team, to_team, fee, wage, contract_length, transfer_type)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''', user.id, player['team_id'], team_id, 0, wage, 3, 'admin_assignment')
    
    embed = discord.Embed(
        title="✅ Player Assigned",
        description=f"{user.mention} → **{team['team_name']}**",
        color=discord.Color.green()
    )
    
    embed.add_field(name="🏆 League", value=team['league'], inline=True)
    embed.add_field(name="💰 Wage", value=f"£{wage:,}/week", inline=True)
    embed.add_field(name="⏳ Contract", value="3 years", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="admin_wipe_players", description="[ADMIN] ⚠️ DELETE ALL USER PLAYERS AND RESET TO DAY 1")
async def admin_wipe_players(interaction: discord.Interaction):
    """Admin: Wipe all user players and reset game"""
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Administrator permissions required!",
            ephemeral=True
        )
        return
    
    # Confirmation view
    class ConfirmView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30)
            self.confirmed = False
        
        @discord.ui.button(label="⚠️ YES, WIPE EVERYTHING", style=discord.ButtonStyle.danger)
        async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.confirmed = True
            self.stop()
            await interaction.response.defer()
        
        @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
        async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.confirmed = False
            self.stop()
            await interaction.response.defer()
    
    view = ConfirmView()
    
    await interaction.response.send_message(
        "⚠️ **WARNING: THIS WILL DELETE ALL USER PLAYERS AND RESET THE GAME TO DAY 1**\n\n"
        "This action will:\n"
        "• Delete all user-created players\n"
        "• Reset season to Week 0\n"
        "• Clear all fixtures and match history\n"
        "• Reset all team stats\n"
        "• Keep NPC players intact\n\n"
        "**ARE YOU ABSOLUTELY SURE?**",
        view=view,
        ephemeral=True
    )
    
    await view.wait()
    
    if view.confirmed:
        await db.wipe_all_user_players()
        
        await interaction.followup.send(
            "✅ **WIPE COMPLETE**\n\n"
            "• All user players deleted\n"
            "• Game reset to Day 1\n"
            "• Season will start when first player uses `/start`\n"
            "• Bot is ready for fresh start!",
            ephemeral=True
        )
    else:
        await interaction.followup.send(
            "❌ Wipe cancelled. No changes made.",
            ephemeral=True
        )

@bot.tree.command(name="admin_retire_check", description="[ADMIN] Check for retirements")
async def admin_retire(interaction: discord.Interaction):
    """Admin: Trigger retirement check"""
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Administrator permissions required!",
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    
    retirements = await db.retire_old_players()
    
    embed = discord.Embed(
        title="✅ Retirement Check Complete",
        description=f"Processed {retirements} retirements",
        color=discord.Color.green()
    )
    
    await interaction.followup.send(embed=embed)

# Run bot
if __name__ == "__main__":
    try:
        bot.run(config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("\n⚠️ Bot shutdown requested")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
