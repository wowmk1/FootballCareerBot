"""
Admin Command - Single command with all admin actions in dropdown
FIXED VERSION - Now passes bot instance to season manager functions
ENHANCED VERSION - Added European competition admin controls
SAFEGUARDED VERSION - Prevents duplicate starts and allows clean restarts
DIAGNOSTIC VERSION - Added NPC stats diagnostic
MATCH ENGINE TEST - Added sandbox match engine testing with REAL engine logic
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
        app_commands.Choice(name="🏆 Start European Now", value="start_european_now"),
        app_commands.Choice(name="🏆 Simulate European to End", value="simulate_european_to_end"),
        app_commands.Choice(name="🗑️ Wipe & Restart European", value="wipe_european"),
        app_commands.Choice(name="🔍 Diagnose NPC Stats", value="diagnose_npcs"),
        app_commands.Choice(name="🎮 Test Match Engine", value="test_match_engine"),
        app_commands.Choice(name="🔄 Recalculate Tables", value="recalculate_tables"),
        app_commands.Choice(name="🔍 Debug Fixtures", value="debug_fixtures"),
        app_commands.Choice(name="🔄 Restart Bot", value="restart"),
        app_commands.Choice(name="🧪 Test Training System", value="test_training"),
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
        elif action == "start_european_now":
            await self._start_european_now(interaction)
        elif action == "simulate_european_to_end":
            await self._simulate_european_to_end(interaction)
        elif action == "wipe_european":
            await self._wipe_european(interaction)
        elif action == "diagnose_npcs":
            await self._diagnose_npcs(interaction)
        elif action == "test_match_engine":
            await self._test_match_engine(interaction)
        elif action == "restart":
            await self._restart(interaction)
        elif action == "test_training":
            await self._test_training(interaction)
        elif action == "recalculate_tables":  # ← ADD THIS
            await self._recalculate_tables(interaction)
        elif action == "debug_fixtures":
            await self._debug_fixtures(interaction)
    
    async def _advance_week(self, interaction: discord.Interaction):
        """Advance to the next week"""
        await interaction.response.defer()
        
        from utils.season_manager import advance_week as adv_week
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
    
    async def _debug_fixtures(self, interaction: discord.Interaction):
        """Debug fixture counts"""
        await interaction.response.defer()
    
        async with db.pool.acquire() as conn:
            # Count by week
            by_week = await conn.fetch("""
                SELECT week_number, COUNT(*) as count
                FROM fixtures 
                WHERE played = true
                GROUP BY week_number
                ORDER BY week_number
            """)
        
            # Total count
            total = await conn.fetchval("SELECT COUNT(*) FROM fixtures WHERE played = true")
        
            # Week 11 details
            week11 = await conn.fetch("""
                SELECT fixture_id, home_team_id, away_team_id, home_score, away_score, played
                FROM fixtures 
                WHERE week_number = 11
                LIMIT 5
            """)
    
        result = f"**Total played fixtures: {total}**\n\n"
        result += "**By week:**\n"
        for w in by_week:
            result += f"Week {w['week_number']}: {w['count']} fixtures\n"
    
        result += f"\n**Week 11 sample:**\n"
        for f in week11:
            result += f"{f['home_team_id']} {f['home_score']}-{f['away_score']} {f['away_team_id']} (played={f['played']})\n"
    
        await interaction.followup.send(result)
    
    async def _open_window(self, interaction: discord.Interaction):
        """Open match window with notifications"""
        await interaction.response.defer(ephemeral=True)
        
        from utils.season_manager import open_match_window
        
        await open_match_window()
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

    async def _recalculate_tables(self, interaction: discord.Interaction):
        """Recalculate all team statistics from played fixtures"""
    
        await interaction.response.defer()
    
        async with db.pool.acquire() as conn:
            # Reset all team stats
            await conn.execute("""
                UPDATE teams SET 
                    played = 0, won = 0, drawn = 0, lost = 0,
                    goals_for = 0, goals_against = 0, points = 0
            """)
        
            # Get all played fixtures
            fixtures = await conn.fetch("""
                SELECT fixture_id, home_team_id, away_team_id, home_score, away_score
                FROM fixtures 
                WHERE played = true 
                ORDER BY week_number, fixture_id
            """)
        
            # Recalculate for each fixture
            for fixture in fixtures:
                # Home team stats
                if fixture['home_score'] > fixture['away_score']:
                    h_won, h_drawn, h_lost, h_points = 1, 0, 0, 3
                elif fixture['home_score'] == fixture['away_score']:
                    h_won, h_drawn, h_lost, h_points = 0, 1, 0, 1
                else:
                    h_won, h_drawn, h_lost, h_points = 0, 0, 1, 0
            
                await conn.execute("""
                    UPDATE teams SET
                        played = played + 1,
                        won = won + $1,
                        drawn = drawn + $2,
                        lost = lost + $3,
                        goals_for = goals_for + $4,
                        goals_against = goals_against + $5,
                        points = points + $6
                    WHERE team_id = $7
                """, h_won, h_drawn, h_lost, fixture['home_score'], 
                     fixture['away_score'], h_points, fixture['home_team_id'])
            
                # Away team stats
                if fixture['away_score'] > fixture['home_score']:
                    a_won, a_drawn, a_lost, a_points = 1, 0, 0, 3
                elif fixture['away_score'] == fixture['home_score']:
                    a_won, a_drawn, a_lost, a_points = 0, 1, 0, 1
                else:
                    a_won, a_drawn, a_lost, a_points = 0, 0, 1, 0
            
                await conn.execute("""
                    UPDATE teams SET
                        played = played + 1,
                        won = won + $1,
                        drawn = drawn + $2,
                        lost = lost + $3,
                        goals_for = goals_for + $4,
                        goals_against = goals_against + $5,
                        points = points + $6
                    WHERE team_id = $7
                """, a_won, a_drawn, a_lost, fixture['away_score'], 
                     fixture['home_score'], a_points, fixture['away_team_id'])
        
            # Get summary
            teams = await conn.fetch("""
                SELECT team_name, league, played, points 
                FROM teams 
                ORDER BY league, points DESC, (goals_for - goals_against) DESC
            """)
    
        # Build summary by league
        pl_teams = [t for t in teams if t['league'] == 'Premier League']
        champ_teams = [t for t in teams if t['league'] == 'Championship']
        l1_teams = [t for t in teams if t['league'] == 'League One']
    
        embed = discord.Embed(
            title="✅ League Tables Recalculated",
            description=f"Recalculated stats for **{len(fixtures)} fixtures**",
            color=discord.Color.green()
        )
    
        if pl_teams:
            top5 = "\n".join([f"{i+1}. {t['team_name']}: {t['played']}P, {t['points']}pts" 
                             for i, t in enumerate(pl_teams[:5])])
            embed.add_field(name="⚽ Premier League (Top 5)", value=top5, inline=False)
    
        if champ_teams:
            top5 = "\n".join([f"{i+1}. {t['team_name']}: {t['played']}P, {t['points']}pts" 
                             for i, t in enumerate(champ_teams[:5])])
            embed.add_field(name="⚽ Championship (Top 5)", value=top5, inline=False)
    
        if l1_teams:
            top3 = "\n".join([f"{i+1}. {t['team_name']}: {t['played']}P, {t['points']}pts" 
                             for i, t in enumerate(l1_teams[:3])])
            embed.add_field(name="⚽ League One (Top 3)", value=top3, inline=False)
    
        embed.set_footer(text="Use /league table to view full standings")
    
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
    
    async def _start_european_now(self, interaction: discord.Interaction):
        """START EUROPEAN COMPETITIONS MID-SEASON"""
        await interaction.response.defer()
        
        try:
            state = await db.get_game_state()
            current_week = state['current_week']
            season = state['current_season']
            
            async with db.pool.acquire() as conn:
                existing_groups = await conn.fetchval(
                    "SELECT COUNT(*) FROM european_groups WHERE season = $1", 
                    season
                )
                
                if existing_groups > 0:
                    await interaction.followup.send(
                        f"❌ **European competitions already started for Season {season}!**\n\n"
                        f"Found {existing_groups} existing groups.\n\n"
                        f"Use `/european_standings` to view current state, or\n"
                        f"Use **🗑️ Wipe & Restart European** to start fresh.",
                        ephemeral=True
                    )
                    return
            
            await interaction.followup.send(
                f"🏆 Starting European competitions!\n"
                f"Week: {current_week} | Season: {season}\n\n"
                f"Processing...",
                ephemeral=True
            )
            
            from utils.european_competitions import draw_groups
            from utils.european_mid_season import simulate_missed_european_weeks
            
            await draw_groups(season=season)
            
            missed_weeks = [w for w in config.GROUP_STAGE_WEEKS if w < current_week]
            
            if missed_weeks:
                results = await simulate_missed_european_weeks(missed_weeks, season)
                
                next_week = min([w for w in config.EUROPEAN_MATCH_WEEKS if w >= current_week], default='Season End')
                
                await interaction.followup.send(
                    f"✅ European competitions started!\n\n"
                    f"**Simulated:**\n"
                    f"- {len(missed_weeks)} weeks\n"
                    f"- {results['matches_simulated']} matches\n\n"
                    f"**Next European Week:** {next_week}\n\n"
                    f"Use `/european_standings` to see current standings!",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "✅ Groups drawn! Waiting for Week 3.",
                    ephemeral=True
                )
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
            import traceback
            traceback.print_exc()
    
    async def _simulate_european_to_end(self, interaction: discord.Interaction):
        """SIMULATE ENTIRE EUROPEAN SEASON"""
        await interaction.response.defer()
        
        try:
            state = await db.get_game_state()
            current_week = state['current_week']
            season = state['current_season']
            
            async with db.pool.acquire() as conn:
                existing_groups = await conn.fetchval(
                    "SELECT COUNT(*) FROM european_groups WHERE season = $1", 
                    season
                )
                
                if existing_groups == 0:
                    await interaction.followup.send(
                        f"❌ **European competitions haven't started yet for Season {season}!**\n\n"
                        f"Use **🏆 Start European Now** first.",
                        ephemeral=True
                    )
                    return
            
            await interaction.followup.send(
                f"🏆 Simulating ENTIRE European season to completion!\n"
                f"Current Week: {current_week}\n\n"
                f"This will simulate:\n"
                f"- All remaining group matches\n"
                f"- All knockout rounds\n"
                f"- Determine champions\n\n"
                f"Processing... (may take 30-60 seconds)",
                ephemeral=True
            )
            
            from utils.european_mid_season import simulate_full_european_season
            
            results = await simulate_full_european_season(season, current_week)
            
            await interaction.followup.send(
                f"✅ European season simulated to completion!\n\n"
                f"**Results:**\n"
                f"- Group matches: {results['group_matches']}\n"
                f"- Knockout matches: {results['knockout_matches']}\n\n"
                f"**Champions:**\n"
                f"🏆 CL Winner: {results['cl_winner']}\n"
                f"🏆 EL Winner: {results['el_winner']}\n\n"
                f"Use `/knockout_bracket` to see full bracket!",
                ephemeral=True
            )
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
            import traceback
            traceback.print_exc()
    
    async def _wipe_european(self, interaction: discord.Interaction):
        """WIPE ALL EUROPEAN DATA"""
        
        view = ConfirmEuropeanWipeView()
        await interaction.response.send_message(
            "⚠️ **WARNING: WIPE ALL EUROPEAN COMPETITION DATA?**\n\n"
            "This will delete:\n"
            "- All groups\n"
            "- All group matches\n"
            "- All knockout brackets\n"
            "- All knockout matches\n\n"
            "You can then use **🏆 Start European Now** to restart from scratch.\n\n"
            "**This cannot be undone!**",
            view=view,
            ephemeral=True
        )
        
        await view.wait()
        
        if not view.confirmed:
            return
        
        try:
            state = await db.get_game_state()
            season = state['current_season']
            
            deleted_counts = {
                'groups': 0,
                'group_matches': 0,
                'knockout_brackets': 0,
                'knockout_matches': 0
            }
            
            async with db.pool.acquire() as conn:
                try:
                    result = await conn.execute(
                        "DELETE FROM european_knockout WHERE season = $1", 
                        season
                    )
                    deleted_counts['knockout_brackets'] = int(result.split()[-1]) if result else 0
                except Exception as e:
                    print(f"Could not delete from european_knockout: {e}")
                
                try:
                    result = await conn.execute(
                        "DELETE FROM european_fixtures WHERE season = $1", 
                        season
                    )
                    deleted_counts['knockout_matches'] = int(result.split()[-1]) if result else 0
                except Exception as e:
                    print(f"Could not delete from european_fixtures: {e}")
                
                try:
                    result = await conn.execute(
                        "DELETE FROM european_groups WHERE season = $1", 
                        season
                    )
                    deleted_counts['groups'] = int(result.split()[-1]) if result else 0
                except Exception as e:
                    print(f"Could not delete from european_groups: {e}")
                
                try:
                    await conn.execute(
                        "DELETE FROM player_european_stats WHERE season = $1", 
                        season
                    )
                except:
                    pass
                
                try:
                    await conn.execute(
                        "DELETE FROM european_npc_performance WHERE season = $1", 
                        season
                    )
                except:
                    pass
            
            total_deleted = sum(deleted_counts.values())
            
            await interaction.followup.send(
                f"✅ **All European data wiped for Season {season}!**\n\n"
                f"**Deleted:**\n"
                f"- {deleted_counts['groups']} groups\n"
                f"- {deleted_counts['group_matches']} group matches\n"
                f"- {deleted_counts['knockout_brackets']} knockout brackets\n"
                f"- {deleted_counts['knockout_matches']} knockout matches\n\n"
                f"**Total records deleted: {total_deleted}**\n\n"
                f"You can now use:\n"
                f"- **🏆 Start European Now** to restart competitions\n"
                f"- **🏆 Simulate European to End** to fast-forward after restarting",
                ephemeral=True
            )
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
            import traceback
            traceback.print_exc()
    
    async def _diagnose_npcs(self, interaction: discord.Interaction):
        """Diagnose NPC stat issues"""
        await interaction.response.defer(ephemeral=True)
        
        async with db.pool.acquire() as conn:
            npcs = await conn.fetch("""
                SELECT 
                    n.player_name,
                    n.position,
                    n.overall_rating,
                    n.pace,
                    n.shooting,
                    n.passing,
                    n.dribbling,
                    n.defending,
                    n.physical,
                    t.team_name
                FROM npc_players n
                JOIN teams t ON n.team_id = t.team_id
                WHERE t.league = 'Championship' 
                AND n.retired = FALSE
                LIMIT 5
            """)
        
        if not npcs:
            await interaction.followup.send("❌ No Championship NPCs found!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🔍 NPC Stats Diagnostic",
            description=f"Checking {len(npcs)} sample Championship NPCs",
            color=discord.Color.blue()
        )
        
        all_good = True
        issues = []
        
        for npc in npcs:
            stat_text = ""
            has_issue = False
            
            stats_to_check = {
                'Pace': npc['pace'],
                'Shooting': npc['shooting'],
                'Passing': npc['passing'],
                'Dribbling': npc['dribbling'],
                'Defending': npc['defending'],
                'Physical': npc['physical']
            }
            
            for stat_name, value in stats_to_check.items():
                if value is None:
                    stat_text += f"❌ {stat_name}: MISSING\n"
                    has_issue = True
                    all_good = False
                else:
                    stat_text += f"✅ {stat_name[:3]}: {value} "
            
            if has_issue:
                issues.append(npc['player_name'])
            
            embed.add_field(
                name=f"{npc['player_name']} ({npc['position']}) - OVR {npc['overall_rating']}",
                value=stat_text.strip(),
                inline=False
            )
        
        if all_good:
            embed.color = discord.Color.green()
            embed.set_footer(text="✅ All NPCs have complete stats!")
        else:
            embed.color = discord.Color.red()
            embed.set_footer(text=f"❌ {len(issues)} NPCs missing stats - need to run fix script!")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def _test_match_engine(self, interaction: discord.Interaction):
        """Test match engine with sandbox match using actual engine logic"""
        await interaction.response.defer()
        
        try:
            # Import actual match engine
            from utils.match_engine import match_engine
            
            if not match_engine:
                await interaction.followup.send("❌ Match engine not initialized!", ephemeral=True)
                return
            
            # Create sandbox fixture
            sandbox_fixture = {
                'fixture_id': 999999,
                'home_team_id': 'test_home',
                'away_team_id': 'test_away',
                'week_number': 99,
                'competition': 'Sandbox Test'
            }
            
            # Create temporary channel
            guild = interaction.guild
            category = discord.utils.get(guild.categories, name="⚽ ACTIVE MATCHES")
            if not category:
                category = await guild.create_category("⚽ ACTIVE MATCHES")
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            match_channel = await guild.create_text_channel(
                name="🧪-sandbox-test",
                category=category,
                overwrites=overwrites
            )
            
            await interaction.followup.send(
                f"✅ **Sandbox Match Started!**\n"
                f"Channel: {match_channel.mention}\n\n"
                f"⚠️ **This is a TEST** - No database changes\n"
                f"🎮 You'll get real interactive moments\n"
                f"⏱️ Channel auto-deletes after match",
                ephemeral=True
            )
            
            # Run actual sandbox match
            await self._run_sandbox_match_with_engine(
                match_channel, 
                interaction.user, 
                match_engine
            )
            
            # Cleanup
            await asyncio.sleep(30)
            try:
                await match_channel.delete()
            except:
                pass
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
            import traceback
            traceback.print_exc()
    
    async def _run_sandbox_match_with_engine(self, channel, player_user, engine):
        """Run sandbox match using ACTUAL match engine logic"""
        import random
        
        # Create sandbox teams (minimal info needed)
        home_team = {
            'team_id': 'sandbox_home',
            'team_name': 'Sandbox United',
            'league': 'Test League'
        }
        
        away_team = {
            'team_id': 'sandbox_away',
            'team_name': 'Test City FC',
            'league': 'Test League'
        }
        
        # Create sandbox player
        sandbox_player = {
            'user_id': player_user.id,
            'player_name': f"{player_user.name}'s Player",
            'position': 'ST',
            'pace': 82,
            'shooting': 85,
            'passing': 78,
            'dribbling': 83,
            'defending': 45,
            'physical': 79,
            'overall_rating': 80,
            'form': 85,
            'team_id': 'sandbox_home'
        }
        
        home_score = 0
        away_score = 0
        
        # Opening embed
        embed = discord.Embed(
            title="🧪 SANDBOX TEST MATCH",
            description=f"## {home_team['team_name']} 🆚 {away_team['team_name']}\n\n"
                       f"**Interactive Test** - Real match engine logic\n"
                       f"No database changes will be made!",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🎮 Test Player",
            value=f"**{sandbox_player['player_name']}**\n"
                  f"{sandbox_player['position']} | OVR {sandbox_player['overall_rating']}",
            inline=False
        )
        await channel.send(embed=embed)
        await asyncio.sleep(3)
        
        # Store goal actions for highlights
        goal_actions = []
        
        # Run 3 test moments using REAL engine logic
        minutes = [15, 45, 78]
        
        for minute in minutes:
            # Progress embed
            embed = discord.Embed(
                title=f"⚡ MOMENT {minutes.index(minute)+1}/3 — {minute}'",
                description=f"## {home_team['team_name']} {home_score} - {away_score} {away_team['team_name']}",
                color=discord.Color.blue()
            )
            await channel.send(embed=embed)
            await asyncio.sleep(1)
            
            # Use ACTUAL engine methods
            adjusted_stats = engine.apply_form_to_stats(sandbox_player)
            scenario_type, defender_positions, scenario_description = engine.get_position_scenario(
                sandbox_player['position']
            )
            available_actions = engine.get_actions_for_scenario(
                sandbox_player['position'], 
                scenario_type
            )
            
            # Create NPC defender
            defender = {
                'player_name': f'{away_team["team_name"]} Defender',
                'position': random.choice(defender_positions),
                'pace': 75,
                'shooting': 65,
                'passing': 70,
                'dribbling': 68,
                'defending': 80,
                'physical': 78
            }
            
            scenario_text = scenario_description.format(
                defender=f"**{defender['player_name']}** ({defender['position']})"
            )
            
            # Create interactive moment using REAL engine display
            embed = discord.Embed(
                title=f"🎯 {player_user.display_name}'S MOMENT!",
                description=f"## {sandbox_player['player_name']} ({sandbox_player['position']})\n"
                           f"**{minute}'** | Form: 🔥 Hot\n\n{scenario_text}",
                color=discord.Color.gold()
            )
            
            # Calculate REAL action chances using engine's system
            actions_data = []
            for action in available_actions:
                att_p, att_s, def_p, def_s = engine.get_action_stats(action)
                player_weighted = engine.calculate_weighted_stat(adjusted_stats, att_p, att_s)
                player_pos_bonus = engine.get_position_bonus(sandbox_player['position'], action)
                player_effective = player_weighted + player_pos_bonus
                
                defender_weighted = engine.calculate_weighted_stat(defender, def_p, def_s)
                defender_pos_bonus = engine.get_position_bonus(defender['position'], action)
                defender_effective = defender_weighted + defender_pos_bonus
                
                chance = engine.calculate_d20_success_probability(player_effective, defender_effective)
                chance = min(90, chance + 3)  # Home advantage
                
                actions_data.append({
                    'action': action,
                    'chance': int(chance),
                    'player_effective': player_effective,
                    'defender_effective': defender_effective
                })
            
            # Sort and highlight recommended (just like real engine)
            actions_data.sort(key=lambda x: x['chance'], reverse=True)
            recommended_action = actions_data[0]['action']
            
            actions_text = ""
            for data in actions_data:
                action = data['action']
                chance = data['chance']
                
                if chance >= 65:
                    emoji = "🟢"
                elif chance >= 50:
                    emoji = "🟡"
                else:
                    emoji = "🔴"
                
                if action == recommended_action:
                    emoji = "⭐" + emoji
                
                actions_text += f"{emoji} **{action.replace('_', ' ').title()}** — **{chance}%**\n"
            
            embed.add_field(name="⚡ CHOOSE YOUR ACTION", value=actions_text, inline=False)
            embed.set_footer(text="⭐ = Recommended | 🎲 = Die roll after | ⏱️ 20s")
            
            # Show buttons
            from utils.match_engine import EnhancedActionView
            view = EnhancedActionView(available_actions, player_user.id, timeout=20)
            
            msg = await channel.send(f"📢 {player_user.mention}", embed=embed, view=view)
            await view.wait()
            
            action = view.chosen_action or recommended_action
            if not view.chosen_action:
                await channel.send(f"⏰ Auto-selected: **{action.upper()}**")
            
            # Execute using REAL engine logic (simplified, no DB)
            att_p, att_s, def_p, def_s = engine.get_action_stats(action)
            player_stat = engine.calculate_weighted_stat(adjusted_stats, att_p, att_s)
            position_bonus = engine.get_position_bonus(sandbox_player['position'], action)
            
            player_roll = random.randint(1, 20)
            player_total = player_stat + player_roll + position_bonus + 3
            
            defender_stat = engine.calculate_weighted_stat(defender, def_p, def_s)
            defender_roll = random.randint(1, 20)
            defender_total = defender_stat + defender_roll
            
            success = player_total > defender_total
            
            # Result display WITH VISUALIZATION
            result_embed = discord.Embed(
                title=f"🎲 {action.replace('_', ' ').upper()}",
                color=discord.Color.green() if success else discord.Color.red()
            )
            
            result_embed.add_field(
                name="⚔️ Duel",
                value=f"**YOU**: {player_stat} + 🎲{player_roll} +{position_bonus} = **{player_total}**\n"
                      f"**THEM**: {defender_stat} + 🎲{defender_roll} = **{defender_total}**\n\n"
                      f"{'✅ **YOU WIN**' if success else '❌ **DEFENDER WINS**'}",
                inline=False
            )
            
            is_goal = False
            if action in ['shoot', 'header'] and success and player_roll >= 15:
                is_goal = True
                home_score += 1
                result_embed.add_field(name="⚽ GOAL!", value=f"**{sandbox_player['player_name']}** scores!", inline=False)
                result_embed.color = discord.Color.gold()
                
                # Store goal for highlights
                goal_actions.append({
                    'action': action,
                    'player': sandbox_player,
                    'defender': defender,
                    'minute': minute,
                    'start_pos': (random.randint(300, 500), random.randint(200, 400)),
                    'end_pos': (600, 300)
                })
            elif success:
                result_embed.add_field(name="✅ SUCCESS!", value=f"Great {action}!", inline=False)
            else:
                result_embed.add_field(name="❌ FAILED!", value="Unsuccessful!", inline=False)
            
            await channel.send(embed=result_embed)
            
            # ✅ ADD STATIC VISUALIZATION
            try:
                from match_visualizer import generate_action_visualization
                
                viz = await generate_action_visualization(
                    action=action,
                    player=sandbox_player,
                    defender=defender,
                    is_home=True,
                    success=success,
                    is_goal=is_goal,
                    animated=False  # Static PNG during match
                )
                
                await channel.send(file=discord.File(fp=viz, filename="action.png"))
            except Exception as e:
                print(f"⚠️ Visualization error: {e}")
            
            await asyncio.sleep(2)
        
        # Final score
        final_embed = discord.Embed(
            title="🏁 TEST COMPLETE!",
            description=f"## {home_team['team_name']} {home_score} - {away_score} {away_team['team_name']}",
            color=discord.Color.gold()
        )
        final_embed.add_field(
            name="✅ Sandbox Test Results",
            value="✓ Used real match engine logic\n"
                  "✓ Real stat calculations\n"
                  "✓ Real scenario system\n"
                  "✓ Real D20 mechanics\n"
                  "✓ No database changes",
            inline=False
        )
        await channel.send(embed=final_embed)
        
        # ✅ GENERATE ANIMATED HIGHLIGHTS
        if goal_actions:
            await channel.send("🎬 **Generating animated highlights...**")
            
            try:
                from match_visualizer import MatchVisualizer
                from PIL import Image
                import io
                
                all_frames = []
                
                for goal_action in goal_actions:
                    # Create 10 animated frames per goal
                    frames = await MatchVisualizer.create_action_animation(
                        action=goal_action['action'],
                        player_name=goal_action['player']['player_name'],
                        player_position=goal_action['player']['position'],
                        defender_name=goal_action['defender']['player_name'] if goal_action['defender'] else None,
                        start_pos=goal_action['start_pos'],
                        end_pos=goal_action['end_pos'],
                        is_home=True,
                        success=True,
                        is_goal=True,
                        frames=10
                    )
                    all_frames.extend(frames)
                
                # Resize and save as GIF
                resized_frames = []
                for frame in all_frames:
                    new_width = int(frame.width * 0.7)
                    new_height = int(frame.height * 0.7)
                    resized = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    resized_frames.append(resized)
                
                buffer = io.BytesIO()
                resized_frames[0].save(
                    buffer,
                    format='GIF',
                    save_all=True,
                    append_images=resized_frames[1:],
                    duration=70,
                    loop=0,
                    optimize=True,
                    quality=85
                )
                buffer.seek(0)
                
                await channel.send(
                    content=f"⚽ **Match Highlights!** ({len(goal_actions)} goal{'s' if len(goal_actions) != 1 else ''})",
                    file=discord.File(fp=buffer, filename='sandbox_highlights.gif')
                )
                
            except Exception as e:
                await channel.send(f"⚠️ Could not generate highlights: {e}")
                import traceback
                traceback.print_exc()
        else:
            await channel.send("ℹ️ No goals to show in highlights!")
        
        await asyncio.sleep(5)
        final_embed.set_footer(text="Channel deletes in 25 seconds...")
        await channel.send("⏱️ Channel deletes in 25 seconds...")

    async def _restart(self, interaction: discord.Interaction):
        """Restart the bot"""
        await interaction.response.send_message("🔄 Restarting bot...", ephemeral=True)
        await self.bot.close()

    async def _test_training(self, interaction: discord.Interaction):
        """Test training system in sandbox mode (no DB changes)"""
        await interaction.response.defer()
        
        try:
            # Import the sandbox tester
            from commands.training import test_training_sandbox
            
            await interaction.followup.send(
                "🧪 **Starting Training Sandbox Test**\n\n"
                "This will show you the complete training flow:\n"
                "✅ Stat selection screen\n"
                "✅ Preview with secondary stats\n"
                "✅ Detailed results screen\n"
                "✅ All GIFs and formatting\n\n"
                "⚠️ **No database changes will be made!**",
                ephemeral=True
            )
            
            # Run the sandbox test
            await test_training_sandbox(interaction)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
            import traceback
            traceback.print_exc()


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


class ConfirmEuropeanWipeView(discord.ui.View):
    """Separate confirmation for European data wipe"""
    def __init__(self):
        super().__init__(timeout=30)
        self.confirmed = False
    
    @discord.ui.button(label="⚠️ YES, WIPE EUROPEAN DATA", style=discord.ButtonStyle.danger)
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
