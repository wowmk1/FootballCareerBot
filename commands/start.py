"""
Enhanced /start command with club selection
Add this as commands/start.py
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
        app_commands.Choice(name="🔙 Full Back (FB)", value="FB"),
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
        view = ClubSelectionView(name, position, interaction.user)
        
        embed = discord.Embed(
            title="🏟️ Choose Your Starting Club",
            description=f"**{name}** ({position})\n\nYou have **3 contract offers** from different leagues:",
            color=discord.Color.blue()
        )
        
        # Show all 3 offers with full details
        for i, club in enumerate(view.clubs, 1):
            if club['league'] == 'Premier League':
                league_emoji = "🔴"
                difficulty = "⭐⭐⭐ Very Hard"
            elif club['league'] == 'Championship':
                league_emoji = "🔵"
                difficulty = "⭐⭐ Medium"
            else:
                league_emoji = "🟢"
                difficulty = "⭐ Easier"
            
            embed.add_field(
                name=f"{league_emoji} Option {i}: {club['team_name']}",
                value=f"**League:** {club['league']}\n"
                      f"**Wage:** £{club['wage']:,}/week (~£{club['wage']*52:,}/year)\n"
                      f"**Contract:** 3 years\n"
                      f"**Difficulty:** {difficulty}",
                inline=False
            )
        
        embed.add_field(
            name="💡 Tips",
            value="🟢 **League One:** Easier competition, faster development\n"
                  "🔵 **Championship:** Balanced challenge\n"
                  "🔴 **Premier League:** Harder games, better wages",
            inline=False
        )
        
        embed.set_footer(text="Click a button below to sign with that club")
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class ClubSelectionView(discord.ui.View):
    def __init__(self, player_name: str, position: str, user: discord.User):
        super().__init__(timeout=180)
        self.player_name = player_name
        self.position = position
        self.user = user
        
        # Generate 3 club options from different leagues
        self.clubs = self.generate_club_options()
        
        # Create buttons for each club
        for i, club in enumerate(self.clubs):
            button = ClubButton(club, i)
            self.add_item(button)
    
    def generate_club_options(self):
        """Generate 3 club offers from different leagues"""
        from data.teams import ALL_TEAMS
        import random
        
        # Get teams from each league
        league_one_teams = [t for t in ALL_TEAMS if t['league'] == 'League One']
        championship_teams = [t for t in ALL_TEAMS if t['league'] == 'Championship']
        premier_league_teams = [t for t in ALL_TEAMS if t['league'] == 'Premier League']
        
        # Select one from each
        clubs = [
            random.choice(league_one_teams).copy(),
            random.choice(championship_teams).copy(),
            random.choice(premier_league_teams).copy()
        ]
        
        # Add wage info
        for club in clubs:
            if club['league'] == 'Premier League':
                club['wage'] = random.randint(15000, 25000)
            elif club['league'] == 'Championship':
                club['wage'] = random.randint(8000, 12000)
            else:  # League One
                club['wage'] = random.randint(3000, 6000)
        
        return clubs


class ClubButton(discord.ui.Button):
    def __init__(self, club: dict, index: int):
        self.club = club
        
        # Color based on league
        if club['league'] == 'Premier League':
            style = discord.ButtonStyle.danger  # Red
            emoji = "🔴"
        elif club['league'] == 'Championship':
            style = discord.ButtonStyle.primary  # Blue
            emoji = "🔵"
        else:
            style = discord.ButtonStyle.success  # Green
            emoji = "🟢"
        
        # Show league and wage in button label
        label = f"{club['team_name']}"
        
        super().__init__(
            label=label,
            style=style,
            emoji=emoji,
            custom_id=f"club_{index}"
        )
    
    async def callback(self, interaction: discord.Interaction):
        # Verify it's the correct user
        if interaction.user.id != self.view.user.id:
            await interaction.response.send_message("❌ This isn't your player creation!", ephemeral=True)
            return
        
        # Create the player
        await self.create_player(interaction)
    
    async def create_player(self, interaction: discord.Interaction):
        """Create the player with selected club"""
        
        # Base stats (adjusted by position)
        base_stats = self.calculate_starting_stats(self.view.position)
        
        # Calculate starting overall
        overall = (base_stats['pace'] + base_stats['shooting'] + base_stats['passing'] + 
                  base_stats['dribbling'] + base_stats['defending'] + base_stats['physical']) // 6
        
        # Potential (60-75 for new players)
        potential = random.randint(65, 78)
        
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
                self.view.player_name,
                self.view.position,
                18,  # Starting age
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
                3,  # 3-year contract
                50,  # Starting form
                75,  # Starting morale
                (await db.get_game_state())['current_week']
            )
        
        # Add news
        await db.add_news(
            f"NEW SIGNING: {self.view.player_name} joins {self.club['team_name']}",
            f"18-year-old {self.view.position} {self.view.player_name} has signed with {self.club['team_name']} "
            f"on a 3-year deal worth £{self.club['wage']:,} per week.",
            "player_news",
            interaction.user.id,
            7
        )
        
        # Success embed
        from utils.football_data_api import get_team_crest_url
        
        embed = discord.Embed(
            title="✅ CAREER STARTED!",
            description=f"## {self.view.player_name}\n**{self.club['team_name']}** • {self.club['league']}",
            color=discord.Color.green()
        )
        
        crest = get_team_crest_url(self.club['team_id'])
        if crest:
            embed.set_thumbnail(url=crest)
        
        embed.add_field(
            name="📊 Starting Stats",
            value=f"**{overall} OVR** • ⭐ {potential} POT\n"
                  f"Age: **18** • Position: **{self.view.position}**",
            inline=False
        )
        
        embed.add_field(
            name="💼 Contract",
            value=f"**£{self.club['wage']:,}/week**\n3 years",
            inline=True
        )
        
        embed.add_field(
            name="📈 Next Steps",
            value="• `/train` - Train daily to improve\n"
                  "• `/season` - Check match schedule\n"
                  "• `/profile` - View your stats",
            inline=True
        )
        
        embed.set_footer(text="Welcome to your football career! 🎉")
        
        # Disable all buttons
        for item in self.view.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self.view)
    
    def calculate_starting_stats(self, position: str):
        """Calculate starting stats based on position"""
        if position == 'GK':
            return {
                'pace': random.randint(45, 55),
                'shooting': random.randint(40, 50),
                'passing': random.randint(50, 60),
                'dribbling': random.randint(45, 55),
                'defending': random.randint(55, 65),
                'physical': random.randint(55, 65)
            }
        elif position in ['ST', 'W']:
            return {
                'pace': random.randint(60, 70),
                'shooting': random.randint(55, 65),
                'passing': random.randint(50, 60),
                'dribbling': random.randint(55, 65),
                'defending': random.randint(35, 45),
                'physical': random.randint(50, 60)
            }
        elif position in ['CAM', 'CM']:
            return {
                'pace': random.randint(55, 65),
                'shooting': random.randint(50, 60),
                'passing': random.randint(60, 70),
                'dribbling': random.randint(55, 65),
                'defending': random.randint(45, 55),
                'physical': random.randint(50, 60)
            }
        elif position == 'CDM':
            return {
                'pace': random.randint(50, 60),
                'shooting': random.randint(45, 55),
                'passing': random.randint(55, 65),
                'dribbling': random.randint(50, 60),
                'defending': random.randint(55, 65),
                'physical': random.randint(60, 70)
            }
        else:  # CB, FB
            return {
                'pace': random.randint(55, 65) if position == 'FB' else random.randint(45, 55),
                'shooting': random.randint(35, 45),
                'passing': random.randint(50, 60),
                'dribbling': random.randint(45, 55),
                'defending': random.randint(60, 70),
                'physical': random.randint(60, 70)
            }


async def setup(bot):
    await bot.add_cog(StartCommands(bot))
