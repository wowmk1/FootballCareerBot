"""
Organized commands - Player and League as TRUE command groups
This creates: /player profile, /player compare, /league table, etc.
"""
import discord
from discord import app_commands
from discord.ext import commands
from database import db


class OrganizedCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # ========== PLAYER COMMAND GROUP ==========
    player_group = app_commands.Group(name="player", description="👤 Player information and stats")
    
    @player_group.command(name="profile", description="📊 View your profile or another player's")
    @app_commands.describe(user="User to view (leave empty for yourself)")
    async def player_profile(self, interaction: discord.Interaction, user: discord.User = None):
        """Show player profile"""
        from commands.player import PlayerCommands
        player_cog = self.bot.get_cog('PlayerCommands')
        if player_cog:
            await player_cog.profile(interaction, user or interaction.user)
        else:
            await interaction.response.send_message("❌ Profile command not available", ephemeral=True)
    
    @player_group.command(name="compare", description="⚖️ Compare your stats with another player")
    @app_commands.describe(user="Player to compare with")
    async def player_compare(self, interaction: discord.Interaction, user: discord.User):
        """Compare players"""
        from commands.player import PlayerCommands
        player_cog = self.bot.get_cog('PlayerCommands')
        if player_cog:
            await player_cog.compare(interaction, user)
        else:
            await interaction.response.send_message("❌ Compare command not available", ephemeral=True)
    
    @player_group.command(name="contract", description="📄 View your current contract")
    async def player_contract(self, interaction: discord.Interaction):
        """Show contract"""
        from commands.transfers import TransferCommands
        transfer_cog = self.bot.get_cog('TransferCommands')
        if transfer_cog:
            await transfer_cog.my_contract(interaction)
        else:
            await interaction.response.send_message("❌ Contract command not available", ephemeral=True)
    
    @player_group.command(name="history", description="📜 View your transfer history")
    async def player_history(self, interaction: discord.Interaction):
        """Show transfer history"""
        from commands.
