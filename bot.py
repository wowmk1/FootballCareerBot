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
        print("📄 Setting up bot...")

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

        await self.tree.sync()
        print(f"✅ Synced {len(self.tree.get_commands())} slash commands")

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
            "ACTIVE MATCHES": [],
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

    await interaction.response.send_message(embed=embed)


# Admin command group
@bot.tree.command(name="admin", description="[ADMIN] Admin control panel")
@app_commands.describe(
    action="Choose admin action",
    user="User (for assign_team/transfer_test)",
    team_id="Team ID (for assign_team)",
    weeks="Weeks to advance (for advance_weeks)"
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
    app_commands.Choice(name="🏗️ Setup Channels", value="setup_channels"),
])
async def admin_command(
        interaction: discord.Interaction,
        action: str,
        user: discord.User = None,
        team_id: str = None,
        weeks: int = 1
):
    """Unified admin command"""

    # Check if command is being used in a guild
    if not interaction.guild:
        await interaction.response.send_message(
            "❌ This command can only be used in a server, not in DMs.",
            ephemeral=True
        )
        return

    # Check for administrator permissions
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Administrator permissions required!",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    if action == "advance_week":
        from utils.season_manager import advance_week
        await advance_week()
        state = await db.get_game_state()

        embed = discord.Embed(
            title="✅ Week Advanced",
            description=f"Now on Week {state['current_week']}/{config.SEASON_TOTAL_WEEKS}",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)

    elif action == "advance_weeks":
        from utils.season_manager import advance_week
        for _ in range(weeks):
            await advance_week()
            await asyncio.sleep(1)

        state = await db.get_game_state()
        embed = discord.Embed(
            title=f"✅ Advanced {weeks} Weeks",
            description=f"Now on Week {state['current_week']}/{config.SEASON_TOTAL_WEEKS}",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)

    elif action == "open_window":
        from utils.season_manager import open_match_window
        await open_match_window(bot=bot)

        embed = discord.Embed(
            title="✅ Match Window Opened",
            description=f"Window open for {config.MATCH_WINDOW_HOURS} hours",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)

    elif action == "close_window":
        from utils.season_manager import close_match_window
        await close_match_window()

        embed = discord.Embed(
            title="✅ Match Window Closed",
            description="Unplayed matches auto-simulated",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)

    elif action == "assign_team":
        if not user or not team_id:
            await interaction.followup.send("❌ Need both user and team_id!", ephemeral=True)
            return

        player = await db.get_player(user.id)
        if not player:
            await interaction.followup.send(f"❌ {user.mention} hasn't created a player!", ephemeral=True)
            return

        team = await db.get_team(team_id)
        if not team:
            await interaction.followup.send(f"❌ Team '{team_id}' not found!", ephemeral=True)
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
        await interaction.followup.send(embed=embed)

    elif action == "wipe_players":
        view = ConfirmWipeView()
        await interaction.followup.send(
            "⚠️ **WARNING: DELETE ALL PLAYERS?**\nThis cannot be undone!",
            view=view,
            ephemeral=True
        )

        await view.wait()

        if view.confirmed:
            await db.wipe_all_user_players()
            await interaction.followup.send("✅ All players wiped!", ephemeral=True)

    elif action == "check_retirements":
        retirements = await db.retire_old_players()

        embed = discord.Embed(
            title="✅ Retirement Check Complete",
            description=f"Processed {retirements} retirements",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)

    elif action == "check_squads":
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

    elif action == "transfer_test":
        if not user:
            await interaction.followup.send("❌ Need to specify a user!", ephemeral=True)
            return

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

        # Send DM to user
        try:
            dm_embed = discord.Embed(
                title="📬 TEST: Transfer Offers",
                description=f"Admin generated test offers for you!\nUse `/offers` to view.",
                color=discord.Color.gold()
            )
            await user.send(embed=dm_embed)
        except:
            pass

    elif action == "setup_channels":
        await bot.setup_server_channels(interaction.guild)

        embed = discord.Embed(
            title="✅ Channels Setup Complete",
            description="Created organized channel structure",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)


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


# Run bot
if __name__ == "__main__":
    try:
        bot.run(config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("\n⚠️ Bot shutdown requested")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
