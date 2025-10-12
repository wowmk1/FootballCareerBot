"""
Admin Command - Single command with all admin actions in dropdown
FIXED VERSION - Now passes bot instance to season manager functions
"""
import discord
from discord import app_commands
from discord.ext import commands
from database import db
import config
import asyncio


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="adm", description="🔧 Admin tools")
    @app_commands.describe(
        action="What admin action to perform",
        weeks="Number of weeks (for advance_weeks)",
        user="User to target (for assign_team/transfer_test)",
        team_id="Team ID (for assign_team/debug_crests)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="⏩ Advance Week", value="advance_week"),
        app_commands.Choice(name="⏩ Advance Multiple Weeks", value="advance_weeks"),
        app_commands.Choice(name="🟢 Open Match Window", value="open_window"),
        app_commands.Choice(name="🔴 Close Match Window", value="close_window"),
        app_commands.Choice(name="👤 Assign Player to Team", value="assign_team"),
        app_commands.Choice(name="🗑️ Wipe All Players", value="wipe_players"),
        app_commands.Choice(name="👴 Check Retirements", value="check_retirements"),
        app_commands.Choice(name="📊 Check Squad Counts", value="check_squads"),
        app_commands.Choice(name="💼 Test Transfer System", value="transfer_test"),
        app_commands.Choice(name="🔍 Debug Crests", value="debug_crests"),
        app_commands.Choice(name="🗂️ Setup Channels", value="setup_channels"),
        app_commands.Choice(name="🎮 View Game State", value="game_state"),
        app_commands.Choice(name="🔧 Sync to This Server", value="sync_guild"),
        app_commands.Choice(name="🔍 Debug Commands", value="debug_commands"),
        app_commands.Choice(name="🔄 Rebuild All Commands", value="rebuild_commands"),
        app_commands.Choice(name="🔧 Fix MOTM Columns", value="fix_motm"),
        app_commands.Choice(name="🔄 Restart Bot", value="restart"),
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def adm(
        self, 
        interaction: discord.Interaction, 
        action: str,
        weeks: int = None,
        user: discord.User = None,
        team_id: str = None
    ):
        """Admin command with multiple actions"""
        
        if action == "advance_week":
            await self._advance_week(interaction)
        elif action == "advance_weeks":
            await self._advance_weeks(interaction, weeks)
        elif action == "open_window":
            await self._open_window(interaction)
        elif action == "close_window":
            await self._close_window(interaction)
        elif action == "assign_team":
            await self._assign_team(interaction, user, team_id)
        elif action == "wipe_players":
            await self._wipe_players(interaction)
        elif action == "check_retirements":
            await self._check_retirements(interaction)
        elif action == "check_squads":
            await self._check_squads(interaction)
        elif action == "transfer_test":
            await self._transfer_test(interaction, user)
        elif action == "debug_crests":
            await self._debug_crests(interaction, team_id or "man_city")
        elif action == "setup_channels":
            await self._setup_channels(interaction)
        elif action == "game_state":
            await self._game_state(interaction)
        elif action == "sync_guild":
            await self._sync_guild(interaction)
        elif action == "debug_commands":
            await self._debug_commands(interaction)
        elif action == "rebuild_commands":
            await self._rebuild_commands(interaction)
        elif action == "fix_motm":
            await self._fix_motm(interaction)
        elif action == "restart":
            await self._restart(interaction)
    
    async def _advance_week(self, interaction: discord.Interaction):
        """Advance to the next week"""
        await interaction.response.defer()
        
        from utils.season_manager import advance_week as adv_week
        # CRITICAL FIX: Pass bot instance so DMs can be sent
        await adv_week(bot=self.bot)
        
        state = await db.get_game_state()
        
        embed = discord.Embed(
            title="✅ Week Advanced",
            description=f"Now on Week {state['current_week']}/{config.SEASON_TOTAL_WEEKS}",
            color=discord.Color.green()
        )
        
        await interaction.followup.send(embed=embed)
    
    async def _advance_weeks(self, interaction: discord.Interaction, weeks: int):
        """Advance multiple weeks"""
        if not weeks or weeks < 1 or weeks > 10:
            await interaction.response.send_message("❌ Please specify between 1-10 weeks", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        from utils.season_manager import advance_week as adv_week
        for i in range(weeks):
            # CRITICAL FIX: Pass bot instance so DMs can be sent
            await adv_week(bot=self.bot)
            await asyncio.sleep(1)
            print(f"  Advanced week {i+1}/{weeks}")
        
        state = await db.get_game_state()
        
        embed = discord.Embed(
            title=f"✅ Advanced {weeks} Weeks",
            description=f"Now on Week {state['current_week']}/{config.SEASON_TOTAL_WEEKS}",
            color=discord.Color.green()
        )
        
        await interaction.followup.send(embed=embed)
    
    async def _open_window(self, interaction: discord.Interaction):
        """Open match window with notifications"""
        await interaction.response.defer(ephemeral=True)
        
        from utils.season_manager import open_match_window
        
        # Open the window
        await open_match_window()
        
        # CRITICAL: Send notifications to all servers
        await self.bot.notify_match_window_open()
        
        state = await db.get_game_state()
        
        embed = discord.Embed(
            title="✅ Match Window Force Opened",
            description=f"**Week {state['current_week']}** matches are now playable!\n\n"
                       f"Notifications sent to all servers.",
            color=discord.Color.green()
        )
        
        from datetime import datetime
        if state['match_window_closes']:
            closes = datetime.fromisoformat(state['match_window_closes'])
            timestamp = int(closes.timestamp())
            
            embed.add_field(
                name="⏰ Closes At",
                value=f"<t:{timestamp}:t> (<t:{timestamp}:R>)",
                inline=True
            )
        
        embed.add_field(
            name="📢 Notifications",
            value=f"✅ Posted to {len(self.bot.guilds)} server(s)",
            inline=True
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def _close_window(self, interaction: discord.Interaction):
        """Close match window"""
        await interaction.response.defer()
        
        from utils.season_manager import close_match_window
        await close_match_window(bot=self.bot)
        
        embed = discord.Embed(
            title="✅ Match Window Closed",
            description="Unplayed matches auto-simulated",
            color=discord.Color.green()
        )
        
        await interaction.followup.send(embed=embed)
    
    async def _assign_team(self, interaction: discord.Interaction, user: discord.User, team_id: str):
        """Assign player to team"""
        if not user or not team_id:
            await interaction.response.send_message("❌ Please specify both user and team_id", ephemeral=True)
            return
        
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
    
    async def _wipe_players(self, interaction: discord.Interaction):
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
    
    async def _check_retirements(self, interaction: discord.Interaction):
        """Check retirements"""
        await interaction.response.defer()
        
        retirements = await db.retire_old_players(bot=self.bot)
        
        embed = discord.Embed(
            title="✅ Retirement Check Complete",
            description=f"Processed {retirements} retirements",
            color=discord.Color.green()
        )
        
        await interaction.followup.send(embed=embed)
    
    async def _check_squads(self, interaction: discord.Interaction):
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
    
    async def _transfer_test(self, interaction: discord.Interaction, user: discord.User):
        """Test transfer system"""
        if not user:
            await interaction.response.send_message("❌ Please specify a user", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        player = await db.get_player(user.id)
        if not player:
            await interaction.followup.send(f"❌ {user.mention} hasn't created a player!", ephemeral=True)
            return
        
        from utils.transfer_window_manager import generate_offers_for_player
        state = await db.get_game_state()
        
        # CRITICAL FIX: Pass bot instance so notifications can be sent
        offers = await generate_offers_for_player(player, state['current_week'], num_offers=5, bot=self.bot)
        
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
            print(f"✅ Sent DM notification to {user.name}")
        except Exception as e:
            print(f"⚠️ Could not send DM to {user.name}: {e}")
    
    async def _debug_crests(self, interaction: discord.Interaction, team_id: str):
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
    
    async def _setup_channels(self, interaction: discord.Interaction):
        """Setup server channels"""
        await interaction.response.defer()
        
        await self.bot.setup_server_channels(interaction.guild)
        
        embed = discord.Embed(
            title="✅ Channels Setup Complete",
            description="Created organized channel structure",
            color=discord.Color.green()
        )
        
        await interaction.followup.send(embed=embed)
    
    async def _game_state(self, interaction: discord.Interaction):
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
    
    async def _sync_guild(self, interaction: discord.Interaction):
        """Sync commands to this guild only"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            synced = await self.bot.tree.sync(guild=interaction.guild)
            await interaction.followup.send(
                f"✅ **Synced {len(synced)} commands to {interaction.guild.name}!**\n\n"
                f"Commands should appear immediately (no restart needed).\n"
                f"This bypasses Discord's global rate limit.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
    
    async def _debug_commands(self, interaction: discord.Interaction):
        """Debug commands"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            local_commands = self.bot.tree.get_commands()
            global_commands = await self.bot.tree.fetch_commands()
            
            local_list = "**Local:**\n" + "\n".join([f"• `/{cmd.name}`" for cmd in local_commands[:20]])
            global_list = "**Global:**\n" + "\n".join([f"• `/{cmd.name}`" for cmd in global_commands[:20]])
            
            await interaction.followup.send(
                f"🔍 **Command Registry**\n\n{local_list}\n\n{global_list}\n\n"
                f"📊 Local: {len(local_commands)} | Global: {len(global_commands)}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
    
    async def _rebuild_commands(self, interaction: discord.Interaction):
        """Rebuild all commands"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            self.bot.tree.clear_commands(guild=None)
            await self.bot.tree.sync()
            await interaction.followup.send("🧹 Cleared commands", ephemeral=True)
            
            cogs = ['commands.start', 'commands.player', 'commands.training', 'commands.season', 
                   'commands.matches', 'commands.leagues', 'commands.transfers', 
                   'commands.news', 'commands.interactive_match', 'commands.adm', 'commands.organized']
            
            for cog in cogs:
                try:
                    await self.bot.reload_extension(cog)
                except:
                    await self.bot.load_extension(cog)
            
            synced = await self.bot.tree.sync()
            
            await interaction.followup.send(
                f"✅ **Rebuild Complete!**\n🎯 {len(synced)} commands\n"
                f"⚠️ Restart Discord to see changes!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
    
    async def _fix_motm(self, interaction: discord.Interaction):
        """Fix MOTM columns"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with db.pool.acquire() as conn:
                # Add MOTM columns if missing
                await conn.execute("""
                    ALTER TABLE players 
                    ADD COLUMN IF NOT EXISTS season_motm INTEGER DEFAULT 0
                """)
                await conn.execute("""
                    ALTER TABLE players 
                    ADD COLUMN IF NOT EXISTS career_motm INTEGER DEFAULT 0
                """)
            
            await interaction.followup.send("✅ MOTM columns fixed!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
    
    async def _restart(self, interaction: discord.Interaction):
        """Restart the bot"""
        await interaction.response.send_message("🔄 Restarting bot...", ephemeral=True)
        await self.bot.close()


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


async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
