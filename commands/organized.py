"""
Organized commands - Player and League grouped commands
"""
import discord
from discord import app_commands
from discord.ext import commands
from database import db


class OrganizedCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="player", description="👤 Player information")
    @app_commands.describe(
        action="What to view",
        user="User to compare with or view"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="📊 My Profile", value="profile"),
        app_commands.Choice(name="⚖️ Compare with Another Player", value="compare"),
        app_commands.Choice(name="📄 My Contract", value="contract"),
        app_commands.Choice(name="📜 Transfer History", value="history"),
    ])
    async def player_cmd(
        self, 
        interaction: discord.Interaction, 
        action: str,
        user: discord.User = None
    ):
        """Player information commands"""
        
        if action == "profile":
            await self._show_profile(interaction, user or interaction.user)
        elif action == "compare":
            if not user:
                await interaction.response.send_message("❌ Please specify a user to compare with", ephemeral=True)
                return
            await self._compare_players(interaction, user)
        elif action == "contract":
            await self._show_contract(interaction)
        elif action == "history":
            await self._show_history(interaction)
    
    @app_commands.command(name="league_info", description="🏆 League information")
    @app_commands.describe(
        action="What to view",
        league="Which league"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="📊 League Table", value="table"),
            app_commands.Choice(name="👟 Top Scorers", value="scorers"),
            app_commands.Choice(name="📅 My Fixtures", value="fixtures"),
            app_commands.Choice(name="📋 Recent Results", value="results"),
        ],
        league=[
            app_commands.Choice(name="Premier League", value="Premier League"),
            app_commands.Choice(name="Championship", value="Championship"),
            app_commands.Choice(name="League One", value="League One"),
        ]
    )
    async def league_info_cmd(
        self, 
        interaction: discord.Interaction, 
        action: str,
        league: str = None
    ):
        """League information commands"""
        
        if action == "table":
            await self._show_table(interaction, league or "Premier League")
        elif action == "scorers":
            await self._show_scorers(interaction, league)
        elif action == "fixtures":
            await self._show_fixtures(interaction)
        elif action == "results":
            await self._show_results(interaction)
    
    async def _show_profile(self, interaction: discord.Interaction, user: discord.User):
        """Show player profile"""
        # Import here to avoid circular imports
        from commands.player import PlayerCommands
        player_cog = self.bot.get_cog('PlayerCommands')
        if player_cog:
            await player_cog.profile.callback(player_cog, interaction, user)
        else:
            await interaction.response.send_message("❌ Profile command not available", ephemeral=True)
    
    async def _compare_players(self, interaction: discord.Interaction, user: discord.User):
        """Compare players"""
        from commands.player import PlayerCommands
        player_cog = self.bot.get_cog('PlayerCommands')
        if player_cog:
            await player_cog.compare.callback(player_cog, interaction, user)
        else:
            await interaction.response.send_message("❌ Compare command not available", ephemeral=True)
    
    async def _show_contract(self, interaction: discord.Interaction):
        """Show contract"""
        from commands.transfers import TransferCommands
        transfer_cog = self.bot.get_cog('TransferCommands')
        if transfer_cog:
            await transfer_cog.my_contract.callback(transfer_cog, interaction)
        else:
            await interaction.response.send_message("❌ Contract command not available", ephemeral=True)
    
    async def _show_history(self, interaction: discord.Interaction):
        """Show transfer history"""
        from commands.transfers import TransferCommands
        transfer_cog = self.bot.get_cog('TransferCommands')
        if transfer_cog:
            await transfer_cog.transfer_history.callback(transfer_cog, interaction)
        else:
            await interaction.response.send_message("❌ History command not available", ephemeral=True)
    
    async def _show_table(self, interaction: discord.Interaction, league: str):
        """Show league table"""
        from commands.leagues import LeagueCommands
        league_cog = self.bot.get_cog('LeagueCommands')
        if league_cog:
            await league_cog.league.callback(league_cog, interaction, league)
        else:
            await interaction.response.send_message("❌ League command not available", ephemeral=True)
    
    async def _show_scorers(self, interaction: discord.Interaction, league: str):
        """Show top scorers"""
        from commands.leagues import LeagueCommands
        league_cog = self.bot.get_cog('LeagueCommands')
        if league_cog:
            await league_cog.top_scorers.callback(league_cog, interaction)
        else:
            await interaction.response.send_message("❌ Scorers command not available", ephemeral=True)
    
    async def _show_fixtures(self, interaction: discord.Interaction):
        """Show fixtures"""
        from commands.season import SeasonCommands
        season_cog = self.bot.get_cog('SeasonCommands')
        if season_cog:
            await season_cog.fixtures.callback(season_cog, interaction)
        else:
            await interaction.response.send_message("❌ Fixtures command not available", ephemeral=True)
    
    async def _show_results(self, interaction: discord.Interaction):
        """Show results"""
        from commands.season import SeasonCommands
        season_cog = self.bot.get_cog('SeasonCommands')
        if season_cog:
            await season_cog.results.callback(season_cog, interaction)
        else:
            await interaction.response.send_message("❌ Results command not available", ephemeral=True)


async def setup(bot):
    await bot.add_cog(OrganizedCommands(bot))
