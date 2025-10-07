import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from database import db
import config
from datetime import datetime
import asyncio

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online!")
    
    # Connect to database
    await db.connect()
    
    # Initialize data
    from utils.data_initializer import initialize_game_data
    await initialize_game_data()
    
    # Cache team crests
    from utils.football_data_api import cache_all_crests
    await cache_all_crests()
    print("✅ Team crests cached")
    
    # Load cogs
    await load_cogs()
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

async def load_cogs():
    """Load all cog files"""
    cogs = [
        'cogs.player_commands',
        'cogs.admin_commands',
        'cogs.match_commands',
        'cogs.training_commands',
        'cogs.info_commands',
        'cogs.transfer_commands'
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded {cog}")
        except Exception as e:
            print(f"❌ Failed to load {cog}: {e}")

# ============================================================================
# ADMIN COMMANDS - Grouped Together
# ============================================================================

@bot.tree.command(name="admin_help", description="[ADMIN] Show all admin commands")
async def admin_help(interaction: discord.Interaction):
    """Show all available admin commands"""
    if interaction.user.id not in config.ADMIN_USER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🛠️ Admin Command Panel",
        description="All available admin commands for managing the bot",
        color=discord.Color.red()
    )
    
    embed.add_field(
        name="⏰ Time & Season Management",
        value="`/advance_week` - Move to next week\n"
              "`/open_match_window` - Open match window\n"
              "`/close_match_window` - Close match window\n"
              "`/end_season` - End current season\n"
              "`/skip_to_week <week>` - Skip to specific week",
        inline=False
    )
    
    embed.add_field(
        name="🔄 Transfer Management",
        value="`/open_transfer_window` - Open transfer window\n"
              "`/close_transfer_window` - Close transfer window\n"
              "`/force_transfer <user> <team>` - Force player transfer",
        inline=False
    )
    
    embed.add_field(
        name="📊 Data Management",
        value="`/initialize_data` - Initialize/reset all game data\n"
              "`/wipe_players` - Delete all user players (DANGER)\n"
              "`/simulate_week` - Simulate week results\n"
              "`/fix_fixtures` - Fix fixture issues",
        inline=False
    )
    
    embed.add_field(
        name="👥 Player Management",
        value="`/set_player_stat <user> <stat> <value>` - Edit player stat\n"
              "`/set_player_team <user> <team>` - Change player team\n"
              "`/retire_player <user>` - Force retire player\n"
              "`/heal_player <user>` - Remove injury",
        inline=False
    )
    
    embed.add_field(
        name="🏆 Team Management",
        value="`/set_team_points <team> <points>` - Set team points\n"
              "`/reset_league_table <league>` - Reset league standings",
        inline=False
    )
    
    embed.add_field(
        name="📰 System Management",
        value="`/create_news <headline> <content>` - Create news article\n"
              "`/check_game_state` - View current game state\n"
              "`/admin_help` - Show this help menu",
        inline=False
    )
    
    embed.set_footer(text="⚠️ Use admin commands carefully! | Use /admin_help anytime")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="check_game_state", description="[ADMIN] Check current game state")
async def check_game_state(interaction: discord.Interaction):
    """Check current game state and statistics"""
    if interaction.user.id not in config.ADMIN_USER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    state = await db.get_game_state()
    
    # Get player count
    async with db.pool.acquire() as conn:
        player_count = await conn.fetchval("SELECT COUNT(*) FROM players WHERE retired = FALSE")
        active_matches = await conn.fetchval("SELECT COUNT(*) FROM active_matches WHERE match_state = 'in_progress'")
        total_npcs = await conn.fetchval("SELECT COUNT(*) FROM npc_players WHERE retired = FALSE")
        regen_count = await conn.fetchval("SELECT COUNT(*) FROM npc_players WHERE is_regen = TRUE AND retired = FALSE")
    
    embed = discord.Embed(
        title="🎮 Game State Dashboard",
        description="Current state of the game",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="⏰ Season Info",
        value=f"**Season**: {state['current_season']}\n"
              f"**Week**: {state['current_week']}/38\n"
              f"**Year**: {state['current_year']}\n"
              f"**Season Started**: {'✅ Yes' if state['season_started'] else '❌ No'}",
        inline=True
    )
    
    embed.add_field(
        name="🎮 Match Status",
        value=f"**Match Window**: {'🟢 OPEN' if state['match_window_open'] else '🔴 CLOSED'}\n"
              f"**Active Matches**: {active_matches}\n"
              f"**Next Match Day**: {state['next_match_day'] or 'Not set'}\n"
              f"**Closes**: {state['match_window_closes'] or 'N/A'}",
        inline=True
    )
    
    embed.add_field(
        name="🔄 Transfer Window",
        value=f"**Status**: {'🟢 OPEN' if state.get('transfer_window_active') else '🔴 CLOSED'}\n"
              f"**Fixtures Generated**: {'✅ Yes' if state['fixtures_generated'] else '❌ No'}",
        inline=True
    )
    
    embed.add_field(
        name="👥 Player Statistics",
        value=f"**User Players**: {player_count}\n"
              f"**NPC Players**: {total_npcs}\n"
              f"**Regens**: {regen_count}\n"
              f"**Total**: {player_count + total_npcs}",
        inline=True
    )
    
    # Get league leaders
    async with db.pool.acquire() as conn:
        pl_leader = await conn.fetchrow(
            "SELECT team_name, points FROM teams WHERE league = 'Premier League' ORDER BY points DESC LIMIT 1"
        )
        champ_leader = await conn.fetchrow(
            "SELECT team_name, points FROM teams WHERE league = 'Championship' ORDER BY points DESC LIMIT 1"
        )
        l1_leader = await conn.fetchrow(
            "SELECT team_name, points FROM teams WHERE league = 'League One' ORDER BY points DESC LIMIT 1"
        )
    
    embed.add_field(
        name="🏆 League Leaders",
        value=f"**Premier League**: {pl_leader['team_name'] if pl_leader else 'N/A'} ({pl_leader['points'] if pl_leader else 0} pts)\n"
              f"**Championship**: {champ_leader['team_name'] if champ_leader else 'N/A'} ({champ_leader['points'] if champ_leader else 0} pts)\n"
              f"**League One**: {l1_leader['team_name'] if l1_leader else 'N/A'} ({l1_leader['points'] if l1_leader else 0} pts)",
        inline=True
    )
    
    embed.add_field(
        name="📅 Important Dates",
        value=f"**Season Started**: {state['season_start_date'] or 'Not started'}\n"
              f"**Last Match Day**: {state['last_match_day'] or 'None yet'}",
        inline=True
    )
    
    embed.set_footer(text=f"Checked at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="wipe_players", description="[ADMIN] DANGER: Delete all user players and reset game")
async def wipe_players(interaction: discord.Interaction):
    """ADMIN: Wipe all user-created players"""
    if interaction.user.id not in config.ADMIN_USER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    # Confirmation view
    class ConfirmWipeView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30)
            self.confirmed = False
        
        @discord.ui.button(label="⚠️ CONFIRM WIPE", style=discord.ButtonStyle.danger)
        async def confirm_button(self, button_interaction: discord.Interaction, button: discord.ui.Button):
            self.confirmed = True
            self.stop()
            await button_interaction.response.edit_message(content="⏳ Wiping all data...", view=None)
        
        @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
        async def cancel_button(self, button_interaction: discord.Interaction, button: discord.ui.Button):
            self.stop()
            await button_interaction.response.edit_message(content="✅ Wipe cancelled. No data was deleted.", view=None)
    
    view = ConfirmWipeView()
    
    await interaction.response.send_message(
        "⚠️ **DANGER ZONE** ⚠️\n\n"
        "This will **DELETE ALL USER PLAYERS** and reset the game to Day 1!\n"
        "This action cannot be undone!\n\n"
        "**What will be deleted:**\n"
        "• All user-created players\n"
        "• All training history\n"
        "• All match events\n"
        "• All active matches\n"
        "• All notifications\n"
        "• All user news\n"
        "• All transfer offers\n\n"
        "**What will be reset:**\n"
        "• Game state (back to Week 0)\n"
        "• All fixtures (unplayed)\n"
        "• All team stats (0-0-0)\n"
        "• All NPC stats (season stats)\n\n"
        "Are you absolutely sure?",
        view=view,
        ephemeral=True
    )
    
    await view.wait()
    
    if view.confirmed:
        await db.wipe_all_user_players()
        await interaction.followup.send(
            "✅ **WIPE COMPLETE**\n\n"
            "All user players have been deleted.\n"
            "Game has been reset to Day 1.\n"
            "Users can now create new players with `/create_player`",
            ephemeral=True
        )
    else:
        if not view.is_finished():
            await interaction.followup.send("⏰ Wipe timed out. No data was deleted.", ephemeral=True)

@bot.tree.command(name="initialize_data", description="[ADMIN] Initialize game data (teams, fixtures, NPCs)")
async def initialize_data(interaction: discord.Interaction):
    """ADMIN: Initialize or reset game data"""
    if interaction.user.id not in config.ADMIN_USER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    from utils.data_initializer import initialize_game_data
    await initialize_game_data()
    
    await interaction.followup.send(
        "✅ Game data initialized!\n\n"
        "Teams, fixtures, and NPC players have been set up.\n"
        "The game is ready for players to join!",
        ephemeral=True
    )

@bot.tree.command(name="set_player_stat", description="[ADMIN] Set a player's stat")
async def set_player_stat(
    interaction: discord.Interaction,
    user: discord.Member,
    stat: str,
    value: int
):
    """ADMIN: Set a specific player stat"""
    if interaction.user.id not in config.ADMIN_USER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    valid_stats = ['pace', 'shooting', 'passing', 'dribbling', 'defending', 'physical', 'overall_rating', 'potential', 'form', 'morale']
    
    if stat.lower() not in valid_stats:
        await interaction.response.send_message(
            f"❌ Invalid stat. Valid stats: {', '.join(valid_stats)}",
            ephemeral=True
        )
        return
    
    if value < 0 or value > 99:
        await interaction.response.send_message("❌ Value must be between 0 and 99", ephemeral=True)
        return
    
    player = await db.get_player(user.id)
    if not player:
        await interaction.response.send_message(f"❌ {user.mention} doesn't have a player.", ephemeral=True)
        return
    
    async with db.pool.acquire() as conn:
        await conn.execute(
            f"UPDATE players SET {stat} = $1 WHERE user_id = $2",
            value, user.id
        )
    
    await interaction.response.send_message(
        f"✅ Set **{player['player_name']}**'s {stat} to {value}",
        ephemeral=True
    )

@bot.tree.command(name="set_player_team", description="[ADMIN] Force a player to join a team")
async def set_player_team(
    interaction: discord.Interaction,
    user: discord.Member,
    team_id: str
):
    """ADMIN: Force transfer a player to a team"""
    if interaction.user.id not in config.ADMIN_USER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    player = await db.get_player(user.id)
    if not player:
        await interaction.response.send_message(f"❌ {user.mention} doesn't have a player.", ephemeral=True)
        return
    
    team = await db.get_team(team_id)
    if not team:
        await interaction.response.send_message(f"❌ Team '{team_id}' not found.", ephemeral=True)
        return
    
    old_team = player['team_id']
    
    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE players SET team_id = $1, league = $2 WHERE user_id = $3",
            team_id, team['league'], user.id
        )
    
    await interaction.response.send_message(
        f"✅ **{player['player_name']}** transferred from {old_team} to **{team['team_name']}**!",
        ephemeral=True
    )
    
    await db.add_news(
        f"Transfer: {player['player_name']} joins {team['team_name']}",
        f"Admin forced transfer from {old_team}",
        "transfer_news",
        user.id,
        5
    )

@bot.tree.command(name="create_news", description="[ADMIN] Create a custom news article")
async def create_news(
    interaction: discord.Interaction,
    headline: str,
    content: str,
    importance: int = 5
):
    """ADMIN: Create custom news"""
    if interaction.user.id not in config.ADMIN_USER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    await db.add_news(
        headline,
        content,
        "admin_news",
        None,
        importance
    )
    
    await interaction.response.send_message(
        f"✅ News article created!\n\n**{headline}**\n{content}",
        ephemeral=True
    )

@bot.tree.command(name="simulate_week", description="[ADMIN] Simulate all unplayed matches for current week")
async def simulate_week(interaction: discord.Interaction):
    """ADMIN: Simulate all fixtures for the week"""
    if interaction.user.id not in config.ADMIN_USER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    from utils.match_simulator import simulate_all_fixtures
    results = await simulate_all_fixtures()
    
    await interaction.followup.send(
        f"✅ Simulated {results} matches for this week!",
        ephemeral=True
    )

@bot.tree.command(name="skip_to_week", description="[ADMIN] Skip to a specific week")
async def skip_to_week(interaction: discord.Interaction, week: int):
    """ADMIN: Skip to specific week"""
    if interaction.user.id not in config.ADMIN_USER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    if week < 1 or week > 38:
        await interaction.response.send_message("❌ Week must be between 1 and 38", ephemeral=True)
        return
    
    await db.update_game_state(current_week=week)
    
    await interaction.response.send_message(
        f"✅ Skipped to Week {week}!",
        ephemeral=True
    )

# ============================================================================
# END ADMIN COMMANDS
# ============================================================================

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: {error.param}")
    else:
        print(f"Error: {error}")
        await ctx.send("❌ An error occurred while executing the command.")

@bot.event
async def on_app_command_error(interaction: discord.Interaction, error):
    """Handle slash command errors"""
    if isinstance(error, discord.app_commands.CommandInvokeError):
        error = error.original
    
    error_message = str(error)
    
    if "interaction has already been responded to" in error_message:
        return
    
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"❌ An error occurred: {error_message}",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"❌ An error occurred: {error_message}",
                ephemeral=True
            )
    except:
        print(f"❌ Error: {error}")

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN'))
