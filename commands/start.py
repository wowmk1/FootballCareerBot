"""
Enhanced /start command with club selection
FIXED VERSION - Auto-opens match window for first player
"""

import discord
from discord import app_commands
from discord.ext import commands
from database import db
import random


class StartCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="start", description="⚽ Create your player and start your career")
    @app_commands.describe(
        name="Your player's name",
        position="Your position"
    )
    @app_commands.choices(position=[
        app_commands.Choice(name="⚽ Striker (ST)", value="ST"),
        app_commands.Choice(name="🏃 Winger (W)", value="W"),
        app_commands.Choice(name="🎯 Attacking Mid (CAM)", value="CAM"),
        app_commands.Choice(name="⚙️ Central Mid (CM)", value="CM"),
        app_commands.Choice(name="🛡️ Defensive Mid (CDM)", value="CDM"),
        app_commands.Choice(name="📙 Full Back (FB)", value="FB"),
        app_commands.Choice(name="🧱 Center Back (CB)", value="CB"),
        app_commands.Choice(name="🧤 Goalkeeper (GK)", value="GK"),
    ])
    async def start(self, interaction: discord.Interaction, name: str, position: str):
        """Create a new player"""
        
        # Check if player already exists
        existing = await db.get_player(interaction.user.id)
        if existing and not existing['retired']:
            await interaction.response.send_message(
                f"❌ You already have an active player: **{existing['player_name']}**\n"
                f"Your player must retire (age 38) before creating a new one.",
                ephemeral=True
            )
            return
        
        # Step 1: Create the view first to get club data
        view = ClubSelectionView(name, position, interaction.user, self.bot)
        
        embed = discord.Embed(
            title="🏟️ Choose Your Starting Club",
            description=f"**{name}** ({position})\n\nYou have **3 contract offers** from Championship clubs:",
            color=discord.Color.blue()
        )
        
        # Show all 3 offers with full details
        for i, club in enumerate(view.clubs, 1):
            league_emoji = "🔵"
            
            embed.add_field(
                name=f"{league_emoji} Option {i}: {club['team_name']}",
                value=f"**League:** {club['league']}\n"
                      f"**Your Stats:** {club['starting_overall']} OVR → ⭐ {club['starting_potential']} POT\n"
                      f"**Wage:** £{club['wage']:,}/week (~£{club['wage']*52:,}/year)\n"
                      f"**Contract:** 3 years\n"
                      f"**Style:** {club['offer_type']}",
                inline=False
            )
        
        embed.add_field(
            name="💡 Choose Your Path",
            value="**All 3 options are Championship-ready!**\n"
                  "Each offer is unique - pick the club and stats you like best!\n"
                  "Everyone gets different random offers for variety.",
            inline=False
        )
        
        embed.set_footer(text="Click a button below to sign with that club")
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class ClubSelectionView(discord.ui.View):
    def __init__(self, player_name: str, position: str, user: discord.User, bot):
        super().__init__(timeout=180)
        self.player_name = player_name
        self.position = position
        self.user = user
        self.bot = bot
        
        # Generate 3 club options from different leagues
        self.clubs = self.generate_club_options()
        
        # Create buttons for each club
        for i, club in enumerate(self.clubs):
            button = ClubButton(club, i, self)
            self.add_item(button)
    
    def generate_club_options(self):
        """Generate 3 club offers - ALL FROM CHAMPIONSHIP with random but viable stats"""
        from data.teams import ALL_TEAMS
        import random
        
        # Get Championship teams only for fair starts
        championship_teams = [t for t in ALL_TEAMS if t['league'] == 'Championship']
        
        # Select 3 random Championship teams
        selected_teams = random.sample(championship_teams, 3)
        clubs = [team.copy() for team in selected_teams]
        
        # Each player gets 3 RANDOM but viable options
        for club in clubs:
            # Random wages (Championship range)
            club['wage'] = random.randint(9000, 14000)
            
            # Random starting overall (Championship-ready: 62-70)
            club['starting_overall'] = random.randint(62, 70)
            
            # Random ELITE potential (future superstars: 82-98)
            club['starting_potential'] = random.randint(82, 98)
            
            # Determine offer type based on stats
            stat_diff = club['starting_potential'] - club['starting_overall']
            if stat_diff >= 25:
                club['offer_type'] = "🌟 Superstar Path"
            elif stat_diff >= 18:
                club['offer_type'] = "⚖️ Elite Growth"
            else:
                club['offer_type'] = "💪 Strong Foundation"
        
        return clubs


class ClubButton(discord.ui.Button):
    def __init__(self, club: dict, index: int, parent_view):
        self.club = club
        self.parent_view = parent_view
        
        style = discord.ButtonStyle.primary
        emoji = "🔵"
        
        label = f"{club['team_name']}"
        
        super().__init__(
            label=label,
            style=style,
            emoji=emoji,
            custom_id=f"club_{index}"
        )
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.parent_view.user.id:
            await interaction.response.send_message("❌ This isn't your player creation!", ephemeral=True)
            return
        
        await self.create_player(interaction)
    
    async def create_player(self, interaction: discord.Interaction):
        """Create the player with selected club"""
        
        # Base stats (adjusted by position)
        base_stats = self.calculate_starting_stats(
            self.parent_view.position, 
            self.club['starting_overall']
        )
        
        overall = self.club['starting_overall']
        potential = self.club['starting_potential']
        
        # Create player in database
        async with db.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO players (
                    user_id, discord_username, player_name, position,
                    age, overall_rating, pace, shooting, passing, dribbling, defending, physical,
                    potential, team_id, league, contract_wage, contract_years,
                    form, morale, joined_week
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
            ''',
                interaction.user.id,
                interaction.user.name,
                self.parent_view.player_name,
                self.parent_view.position,
                18,
                overall,
                base_stats['pace'],
                base_stats['shooting'],
                base_stats['passing'],
                base_stats['dribbling'],
                base_stats['defending'],
                base_stats['physical'],
                potential,
                self.club['team_id'],
                self.club['league'],
                self.club['wage'],
                3,
                50,  # Starting form
                75,  # Starting morale
                (await db.get_game_state())['current_week']
            )
        
        # Add news
        await db.add_news(
            f"NEW SIGNING: {self.parent_view.player_name} joins {self.club['team_name']}",
            f"18-year-old {self.parent_view.position} {self.parent_view.player_name} has signed with {self.club['team_name']} "
            f"on a 3-year deal worth £{self.club['wage']:,} per week.",
            "player_news",
            interaction.user.id,
            7
        )
        
        # POST TO transfer-news CHANNEL
        transfer_info = {
            'player_name': self.parent_view.player_name,
            'from_team': 'Free Agent',
            'to_team': self.club['team_name'],
            'fee': 0,
            'wage': self.club['wage'],
            'contract_length': 3,
            'is_new_player': True,
            'user': interaction.user,
            'position': self.parent_view.position,
            'age': 18,
            'overall': overall,
            'potential': potential
        }
        
        from utils.event_poster import post_new_player_announcement
        for guild in self.parent_view.bot.guilds:
            try:
                await post_new_player_announcement(self.parent_view.bot, guild, transfer_info)
            except Exception as e:
                print(f"Could not post new player announcement to {guild.name}: {e}")

                # ============================================
                # AUTO-START SEASON (BUT DON'T OPEN WINDOW YET)
                # ============================================
                state = await db.get_game_state()
                if not state['season_started']:
                    print(f"🎬 First player created! Auto-starting season...")
                    from utils.season_manager import start_season
                    await start_season()

                    # DON'T open window yet - let it open on schedule
                    print(f"✅ Season auto-started! First match window will open at scheduled time.")
                # ============================================
                # END OF AUTO-START
                # ============================================

                # Success embed
                from utils.football_data_api import get_team_crest_url

                # Get next match window info
                state = await db.get_game_state()
                next_match_str = "Check /season for schedule"

                if state['next_match_day']:
                    from datetime import datetime
                    next_match = datetime.fromisoformat(state['next_match_day'])
                    next_match_str = next_match.strftime('%A, %B %d at %I:%M %p')

                embed = discord.Embed(
                    title="✅ CAREER STARTED!",
                    description=f"## {self.parent_view.player_name}\n**{self.club['team_name']}** • {self.club['league']}",
                    color=discord.Color.green()
                )

                crest = get_team_crest_url(self.club['team_id'])
                if crest:
                    embed.set_thumbnail(url=crest)

                embed.add_field(
                    name="📊 Starting Stats",
                    value=f"**{overall} OVR** • ⭐ {potential} POT\n"
                          f"Age: **18** • Position: **{self.parent_view.position}**\n\n"
                          f"*Championship-ready player!*",
                    inline=False
                )

                embed.add_field(
                    name="💼 Contract",
                    value=f"**£{self.club['wage']:,}/week**\n3 years",
                    inline=True
                )

                embed.add_field(
                    name="📅 First Match",
                    value=f"**{next_match_str}**\n\n*Everyone plays at the same time!*",
                    inline=True
                )

                embed.add_field(
                    name="📈 Next Steps",
                    value="• `/train` - Train daily to improve\n"
                          "• `/season` - Check match schedule\n"
                          "• `/profile` - View your stats",
                    inline=False
                )

                embed.set_footer(text="🕐 Matches open at scheduled times - no rush!")

                # Disable all buttons
                for item in self.parent_view.children:
                    item.disabled = True

                await interaction.response.edit_message(embed=embed, view=self.parent_view)
    
    def calculate_starting_stats(self, position: str, target_overall: int):
        """Calculate starting stats based on position and target overall"""
        if position == 'GK':
            weights = {
                'pace': 0.08,
                'shooting': 0.08,
                'passing': 0.12,
                'dribbling': 0.10,
                'defending': 0.30,
                'physical': 0.32
            }
        elif position in ['ST', 'W']:
            weights = {
                'pace': 0.22,
                'shooting': 0.25,
                'passing': 0.12,
                'dribbling': 0.20,
                'defending': 0.06,
                'physical': 0.15
            }
        elif position in ['CAM', 'CM']:
            weights = {
                'pace': 0.15,
                'shooting': 0.15,
                'passing': 0.25,
                'dribbling': 0.20,
                'defending': 0.10,
                'physical': 0.15
            }
        elif position == 'CDM':
            weights = {
                'pace': 0.12,
                'shooting': 0.08,
                'passing': 0.18,
                'dribbling': 0.12,
                'defending': 0.28,
                'physical': 0.22
            }
        else:  # CB, FB
            if position == 'FB':
                weights = {
                    'pace': 0.20,
                    'shooting': 0.05,
                    'passing': 0.15,
                    'dribbling': 0.12,
                    'defending': 0.28,
                    'physical': 0.20
                }
            else:
                weights = {
                    'pace': 0.10,
                    'shooting': 0.05,
                    'passing': 0.12,
                    'dribbling': 0.08,
                    'defending': 0.35,
                    'physical': 0.30
                }
        
        stats = {}
        
        for stat, weight in weights.items():
            base = target_overall + (weight * 20)
            stats[stat] = max(30, min(90, int(base + random.randint(-5, 5))))
        
        return stats


async def setup(bot):
    await bot.add_cog(StartCommands(bot))
