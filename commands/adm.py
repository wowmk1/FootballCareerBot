"""
Admin Commands - Simple Group (No Cog)
Loaded directly in bot.py
GUILD-SPECIFIC version for instant updates
"""
import discord
from discord import app_commands
from database import db
import config
import asyncio


# Create the admin group with a DIFFERENT name to avoid Discord's cache
admin_group = app_commands.Group(name="adm", description="Administrator commands")


@admin_group.command(name="advance_week", description="⏩ Advance to next week")
@app_commands.checks.has_permissions(administrator=True)
async def advance_week(interaction: discord.Interaction):
    """Advance to the next week"""
    await interaction.response.defer()
    
    from utils.season_manager import advance_week as adv_week
    await adv_week()
    
    state = await db.get_game_state()
    
    embed = discord.Embed(
        title="✅ Week Advanced",
        description=f"Now on Week {state['current_week']}/{config.SEASON_TOTAL_WEEKS}",
        color=discord.Color.green()
    )
    
    await interaction.followup.send(embed=embed)


@admin_group.command(name="advance_weeks", description="⏩ Advance multiple weeks")
@app_commands.describe(weeks="Number of weeks to advance")
@app_commands.checks.has_permissions(administrator=True)
async def advance_weeks(interaction: discord.Interaction, weeks: int):
    """Advance multiple weeks"""
    if weeks < 1 or weeks > 10:
        await interaction.response.send_message("❌ Please advance between 1-10 weeks", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    from utils.season_manager import advance_week as adv_week
    for _ in range(weeks):
        await adv_week()
        await asyncio.sleep(1)
    
    state = await db.get_game_state()
    
    embed = discord.Embed(
        title=f"✅ Advanced {weeks} Weeks",
        description=f"Now on Week {state['current_week']}/{config.SEASON_TOTAL_WEEKS}",
        color=discord.Color.green()
    )
    
    await interaction.followup.send(embed=embed)


@admin_group.command(name="open_window", description="🟢 Open match window")
@app_commands.checks.has_permissions(administrator=True)
async def open_window(interaction: discord.Interaction):
    """Open match window"""
    await interaction.response.defer()
    
    from utils.season_manager import open_match_window
    bot = interaction.client
    await open_match_window(bot=bot)
    
    embed = discord.Embed(
        title="✅ Match Window Opened",
        description=f"Window open for {config.MATCH_WINDOW_HOURS} hours",
        color=discord.Color.green()
    )
    
    await interaction.followup.send(embed=embed)


@admin_group.command(name="close_window", description="🔴 Close match window")
@app_commands.checks.has_permissions(administrator=True)
async def close_window(interaction: discord.Interaction):
    """Close match window"""
    await interaction.response.defer()
    
    from utils.season_manager import close_match_window
    await close_match_window()
    
    embed = discord.Embed(
        title="✅ Match Window Closed",
        description="Unplayed matches auto-simulated",
        color=discord.Color.green()
    )
    
    await interaction.followup.send(embed=embed)


@admin_group.command(name="assign_team", description="👤 Assign player to team")
@app_commands.describe(user="User to assign", team_id="Team ID (e.g., man_city)")
@app_commands.checks.has_permissions(administrator=True)
async def assign_team(interaction: discord.Interaction, user: discord.User, team_id: str):
    """Assign player to team"""
    player = await db.get_player(user.id)
    if not player:
        await interaction.response.send_message(f"❌ {user.mention} hasn't created a player!", ephemeral=True)
        return
    
    team = await db.get_team(team_id)
    if not team:
        await interaction.response.send_message(f"❌ Team '{team_id}' not found!", ephemeral=True)
        return
    
    wage = (player['overall_rating'] ** 2) * 10
    
    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE players SET team_id = $1, league = $2, contract_wage = $3, contract_years = $4 WHERE user_id = $5",
            team_id, team['league'], wage, 3, user.id
        )
    
    embed = discord.Embed(
        title="✅ Player Assigned",
        description=f"{user.mention} → **{team['team_name']}**",
        color=discord.Color.green()
    )
    
    await interaction.response.send_message(embed=embed)


@admin_group.command(name="wipe_players", description="🗑️ Delete all user players")
@app_commands.checks.has_permissions(administrator=True)
async def wipe_players(interaction: discord.Interaction):
    """Wipe all user players"""
    view = ConfirmWipeView()
    await interaction.response.send_message(
        "⚠️ **WARNING: DELETE ALL PLAYERS?**\nThis cannot be undone!",
        view=view,
        ephemeral=True
    )
    
    await view.wait()
    
    if view.confirmed:
        await db.wipe_all_user_players()
        await interaction.followup.send("✅ All players wiped!", ephemeral=True)


@admin_group.command(name="check_retirements", description="👴 Check retirement system")
@app_commands.checks.has_permissions(administrator=True)
async def check_retirements(interaction: discord.Interaction):
    """Check retirements"""
    await interaction.response.defer()
    
    retirements = await db.retire_old_players()
    
    embed = discord.Embed(
        title="✅ Retirement Check Complete",
        description=f"Processed {retirements} retirements",
        color=discord.Color.green()
    )
    
    await interaction.followup.send(embed=embed)


@admin_group.command(name="check_squads", description="📊 Check squad counts")
@app_commands.checks.has_permissions(administrator=True)
async def check_squads(interaction: discord.Interaction):
    """Check squad counts"""
    await interaction.response.defer()
    
    async with db.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT t.team_name, t.league, COUNT(n.npc_id) as players
            FROM teams t
            LEFT JOIN npc_players n ON t.team_id = n.team_id AND n.retired = FALSE
            GROUP BY t.team_name, t.league
            ORDER BY players DESC
        """)
    
    teams = [dict(row) for row in rows]
    
    embed = discord.Embed(
        title="NPC Squad Status",
        description=f"Total teams: {len(teams)}",
        color=discord.Color.blue()
    )
    
    pl_teams = [t for t in teams if t['league'] == 'Premier League']
    champ_teams = [t for t in teams if t['league'] == 'Championship']
    
    if pl_teams:
        pl_text = "\n".join([f"{t['team_name']}: {t['players']} players" for t in pl_teams[:10]])
        embed.add_field(name="Premier League (sample)", value=pl_text, inline=False)
    
    if champ_teams:
        champ_text = "\n".join([f"{t['team_name']}: {t['players']} players" for t in champ_teams[:10]])
        embed.add_field(name="Championship (sample)", value=champ_text, inline=False)
    
    total_npcs = sum(t['players'] for t in teams)
    embed.set_footer(text=f"Total NPC players: {total_npcs}")
    
    await interaction.followup.send(embed=embed)


@admin_group.command(name="transfer_test", description="💼 Test transfer system")
@app_commands.describe(user="User to generate test offers for")
@app_commands.checks.has_permissions(administrator=True)
async def transfer_test(interaction: discord.Interaction, user: discord.User):
    """Test transfer system"""
    await interaction.response.defer()
    
    player = await db.get_player(user.id)
    if not player:
        await interaction.followup.send(f"❌ {user.mention} hasn't created a player!", ephemeral=True)
        return
    
    from utils.transfer_window_manager import generate_offers_for_player
    state = await db.get_game_state()
    
    offers = await generate_offers_for_player(player, state['current_week'], num_offers=5)
    
    embed = discord.Embed(
        title="✅ Test Offers Generated",
        description=f"Created {len(offers)} offers for {player['player_name']}",
        color=discord.Color.green()
    )
    
    for i, offer in enumerate(offers[:5], 1):
        embed.add_field(
            name=f"Offer #{i}",
            value=f"{offer['team_name']}\n£{offer['wage_offer']:,}/wk | {offer['contract_length']}y",
            inline=True
        )
    
    await interaction.followup.send(embed=embed)
    
    try:
        dm_embed = discord.Embed(
            title="📬 TEST: Transfer Offers",
            description=f"Admin generated test offers for you!\nUse `/offers` to view.",
            color=discord.Color.gold()
        )
        await user.send(embed=dm_embed)
    except:
        pass


@admin_group.command(name="debug_crests", description="🔍 Debug team crests")
@app_commands.describe(team_id="Team ID to test")
@app_commands.checks.has_permissions(administrator=True)
async def debug_crests(interaction: discord.Interaction, team_id: str = "man_city"):
    """Debug crests"""
    await interaction.response.defer()
    
    from utils.football_data_api import get_team_crest_url, get_competition_logo
    
    crest_url = get_team_crest_url(team_id)
    logo_url = get_competition_logo('Premier League')
    
    embed = discord.Embed(
        title="🔍 Crest System Debug",
        description=f"Testing: `{team_id}`",
        color=discord.Color.blue()
    )
    
    if crest_url:
        embed.add_field(name="✅ Crest Found", value=f"```{crest_url}```", inline=False)
        embed.set_thumbnail(url=crest_url)
    else:
        embed.add_field(name="❌ Not Found", value=f"No URL for: {team_id}", inline=False)
    
    if logo_url:
        embed.set_footer(text="Premier League", icon_url=logo_url)
    
    await interaction.followup.send(embed=embed)


@admin_group.command(name="setup_channels", description="🗂️ Setup server channels")
@app_commands.checks.has_permissions(administrator=True)
async def setup_channels(interaction: discord.Interaction):
    """Setup server channels"""
    await interaction.response.defer()
    
    bot = interaction.client
    await bot.setup_server_channels(interaction.guild)
    
    embed = discord.Embed(
        title="✅ Channels Setup Complete",
        description="Created organized channel structure",
        color=discord.Color.green()
    )
    
    await interaction.followup.send(embed=embed)


@admin_group.command(name="game_state", description="🎮 View current game state")
@app_commands.checks.has_permissions(administrator=True)
async def game_state(interaction: discord.Interaction):
    """View game state"""
    state = await db.get_game_state()
    
    embed = discord.Embed(title="🎮 Game State", color=discord.Color.blue())
    
    embed.add_field(
        name="Season Info",
        value=f"Started: {state['season_started']}\n"
              f"Season: {state['current_season']}\n"
              f"Week: {state['current_week']}/{config.SEASON_TOTAL_WEEKS}",
        inline=False
    )
    
    embed.add_field(
        name="Match Window",
        value=f"Open: {state['match_window_open']}\n"
              f"Closes: {state.get('match_window_closes', 'N/A')}",
        inline=False
    )
    
    embed.add_field(
        name="Transfer Window",
        value=f"Active: {state.get('transfer_window_active', False)}",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)


@admin_group.command(name="debug_commands", description="🔍 See all registered commands")
@app_commands.checks.has_permissions(administrator=True)
async def debug_commands_admin(interaction: discord.Interaction):
    """Debug what commands are registered"""
    await interaction.response.defer(ephemeral=True)
    
    try:
        from discord import app_commands as ac
        
        # Check what's in the bot's tree
        bot = interaction.client
        local_commands = bot.tree.get_commands()
        
        # Check what Discord knows about
        global_commands = await bot.tree.fetch_commands()
        
        local_list = "**Local (in bot code):**\n"
        for cmd in local_commands:
            if isinstance(cmd, ac.Group):
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


@admin_group.command(name="rebuild_commands", description="🔧 Completely rebuild all slash commands")
@app_commands.checks.has_permissions(administrator=True)
async def rebuild_commands_admin(interaction: discord.Interaction):
    """Completely wipe and rebuild all commands"""
    await interaction.response.defer(ephemeral=True)
    
    try:
        bot = interaction.client
        
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
        
        await interaction.followup.send(f"✅ Step 4: Reloaded all modules", ephemeral=True)
        
        # Step 4: Sync everything fresh
        synced = await bot.tree.sync()
        
        result_msg = f"✅ **REBUILD COMPLETE!**\n\n"
        result_msg += f"🎯 Registered {len(synced)} commands with Discord\n"
        result_msg += f"\n⚠️ **FULLY CLOSE AND REOPEN DISCORD** to see changes!"
        
        await interaction.followup.send(result_msg, ephemeral=True)
        
    except Exception as e:
        import traceback
        await interaction.followup.send(f"❌ Error: {e}\n```{traceback.format_exc()[:1000]}```", ephemeral=True)


class ConfirmWipeView(discord.ui.View):
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


# NO setup function - this is loaded directly in bot.py
