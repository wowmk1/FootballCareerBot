import discord
from discord import app_commands
from discord.ext import commands
from database import db
import random

class TransferCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="transfer", description="View transfer offers and sign for clubs")
    async def transfer(self, interaction: discord.Interaction):
        """View transfer offers"""
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet! Use `/start` to begin.",
                ephemeral=True
            )
            return
        
        if player['retired']:
            await interaction.response.send_message(
                "🏆 Your player has retired!",
                ephemeral=True
            )
            return
        
        if player['overall_rating'] < 65:
            target_league = "League One"
        elif player['overall_rating'] < 73:
            target_league = "Championship"
        else:
            target_league = "Premier League"
        
        async with db.db.execute(
            "SELECT * FROM teams WHERE league = ? ORDER BY RANDOM() LIMIT 5",
            (target_league,)
        ) as cursor:
            rows = await cursor.fetchall()
            clubs = [dict(row) for row in rows]
        
        if not clubs:
            await interaction.response.send_message(
                "❌ No clubs available right now!",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="💼 Transfer Market",
            description=f"**{player['player_name']}** ({player['overall_rating']} OVR) - Available Offers:",
            color=discord.Color.green()
        )
        
        if player['team_id'] != 'free_agent':
            current_team = await db.get_team(player['team_id'])
            embed.add_field(
                name="📍 Current Club",
                value=f"**{current_team['team_name']}** ({current_team['league']})\n"
                      f"💰 £{player['contract_wage']:,}/week | ⏳ {player['contract_years']} years left",
                inline=False
            )
        
        for idx, club in enumerate(clubs, 1):
            base_wage = player['overall_rating'] * 500
            wage_offer = random.randint(int(base_wage * 0.8), int(base_wage * 1.2))
            contract_years = random.randint(2, 4)
            
            if player['overall_rating'] >= 75:
                playing_time = "⭐⭐⭐⭐⭐ Guaranteed Starter"
            elif player['overall_rating'] >= 70:
                playing_time = "⭐⭐⭐⭐ Regular Starter"
            elif player['overall_rating'] >= 65:
                playing_time = "⭐⭐⭐ Rotation Player"
            else:
                playing_time = "⭐⭐ Squad Player"
            
            embed.add_field(
                name=f"{idx}. {club['team_name']}",
                value=(
                    f"🏆 **{club['league']}**\n"
                    f"💰 £{wage_offer:,}/week\n"
                    f"📝 {contract_years} year contract\n"
                    f"⏱️ {playing_time}"
                ),
                inline=True
            )
        
        embed.add_field(
            name="📋 How to Sign",
            value="Automatic transfers coming soon!\nFor now, this shows potential offers based on your rating.",
            inline=False
        )
        
        embed.set_footer(text="Transfer system will be fully automated in future updates!")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="clubs", description="View all clubs in each league")
    @app_commands.describe(league="Which league to view")
    @app_commands.choices(league=[
        app_commands.Choice(name="Premier League", value="Premier League"),
        app_commands.Choice(name="Championship", value="Championship"),
        app_commands.Choice(name="League One", value="League One"),
    ])
    async def clubs(self, interaction: discord.Interaction, league: str = "Premier League"):
        """View clubs in a league"""
        
        async with db.db.execute(
            "SELECT * FROM teams WHERE league = ? ORDER BY team_name",
            (league,)
        ) as cursor:
            rows = await cursor.fetchall()
            clubs = [dict(row) for row in rows]
        
        if not clubs:
            await interaction.response.send_message(
                f"❌ No clubs found in {league}!",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"🏢 {league} - All Clubs",
            description=f"**{len(clubs)} teams** in this league:",
            color=discord.Color.blue()
        )
        
        clubs_per_field = 10
        for i in range(0, len(clubs), clubs_per_field):
            club_batch = clubs[i:i+clubs_per_field]
            
            club_list = []
            for club in club_batch:
                async with db.db.execute(
                    "SELECT COUNT(*) as count FROM players WHERE team_id = ? AND retired = 0",
                    (club['team_id'],)
                ) as cursor:
                    result = await cursor.fetchone()
                    player_count = result['count']
                
                marker = f" ({player_count} ⭐)" if player_count > 0 else ""
                club_list.append(f"• {club['team_name']}{marker}")
            
            field_name = f"Teams {i+1}-{min(i+clubs_per_field, len(clubs))}"
            embed.add_field(
                name=field_name,
                value="\n".join(club_list),
                inline=True
            )
        
        embed.set_footer(text="⭐ = Has user-controlled players | Use /transfer to get offers")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(TransferCommands(bot))
