import discord
from discord import app_commands
from discord.ext import commands
from database import db

class TransferCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="transfer_market", description="Browse available teams to join")
    async def transfer_market(self, interaction: discord.Interaction):
        """View available teams"""
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet! Use `/start` to begin.",
                ephemeral=True
            )
            return
        
        if player['retired']:
            await interaction.response.send_message(
                "🏆 Your player has retired! Use `/start` to create a new player.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="💼 Transfer Market",
            description="Transfer system coming soon!\n\n"
                       "In future updates, you'll be able to:\n"
                       "• Browse teams looking for players\n"
                       "• Negotiate contracts\n"
                       "• Move between leagues\n"
                       "• Build your career path",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🏠 Your Current Status",
            value=f"Team: **{player['team_id']}**\n"
                  f"League: **{player['league'] or 'Free Agent'}**",
            inline=False
        )
        
        embed.set_footer(text="Stay tuned for transfer system updates!")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(TransferCommands(bot))
