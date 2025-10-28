# commands/adm_sandbox.py
import discord
from discord.ext import commands
from discord import app_commands
import logging

# Import your project's EnhancedActionView. Adjust path if needed.
# If your project uses a different import path, change this line accordingly.
from utils.match_engine import EnhancedActionView

logger = logging.getLogger(__name__)


class SandboxEnhancedActionView(EnhancedActionView):
    """
    EnhancedActionView with two extra testing buttons: Skip and AFK.
    Pressing Skip/AFK will set chosen_action and stop() the view.
    This subclass is built to be compatible with most EnhancedActionView
    variants used in your project.
    """
    def __init__(self, available_actions, owner_user_id, timeout=20):
        # Call parent constructor (signature must match your EnhancedActionView)
        super().__init__(available_actions, owner_user_id, timeout=timeout)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary, row=2)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Resolve owner id from common possible attributes
        owner_id = getattr(self, "owner_user_id", None)
        if owner_id is None:
            owner_id = getattr(getattr(self, "view", None), "owner_user_id", None)

        if interaction.user.id != owner_id:
            return await interaction.response.send_message("You cannot control this turn", ephemeral=True)

        # Defer immediately so Discord knows we handled the click
        await interaction.response.defer(ephemeral=True)
        self.chosen_action = "skip"
        self.stop()

    @discord.ui.button(label="AFK", style=discord.ButtonStyle.danger, row=2)
    async def afk_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        owner_id = getattr(self, "owner_user_id", None)
        if owner_id is None:
            owner_id = getattr(getattr(self, "view", None), "owner_user_id", None)

        if interaction.user.id != owner_id:
            return await interaction.response.send_message("You cannot control this turn", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        self.chosen_action = "afk"
        self.stop()


class SandboxAdmin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="test_match_engine_sandbox", description="Run a sandbox match UI with Skip/AFK buttons")
    @app_commands.guilds()  # optional: limit to certain guilds; remove to enable globally
    async def test_match_engine_sandbox(self, interaction: discord.Interaction):
        """
        Send a sandbox moment message using EnhancedActionView + Skip/AFK buttons.
        This does not run your full match logic — it only demonstrates the UI
        interactions and returns view.chosen_action for testing.
        """

        # Minimal set of sample actions
        available_actions = [
            {"label": "Shoot", "value": "shoot"},
            {"label": "Pass", "value": "pass"},
            {"label": "Dribble", "value": "dribble"},
            {"label": "Cross", "value": "cross"},
        ]

        owner_user = interaction.user

        embed = discord.Embed(
            title="Sandbox: Choose an action",
            description="This is a single test moment. Use the buttons to choose or test Skip/AFK.",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Player", value=f"{owner_user.display_name}", inline=False)
        embed.add_field(name="Available actions", value=", ".join(a["label"] for a in available_actions), inline=False)
        embed.set_footer(text="Skip sets chosen_action == 'skip'. AFK sets chosen_action == 'afk'.")

        # Create view from sandbox subclass
        view = SandboxEnhancedActionView(available_actions, owner_user.id, timeout=30)

        # Try to send using interaction.response first, fallback to followup
        try:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
        except Exception:
            try:
                await interaction.followup.send(embed=embed, view=view, ephemeral=False)
            except Exception as e:
                logger.exception("Failed to send sandbox moment: %s", e)
                return

        # Wait for the view to stop (button press or timeout)
        await view.wait()

        chosen = getattr(view, "chosen_action", None)
        if chosen is None:
            text = "No action chosen. The view timed out (auto-skip path would be used)."
        else:
            text = f"Chosen action: {chosen!r}"

        # Report result back to the user (ephemeral)
        try:
            await interaction.followup.send(content=text, ephemeral=True)
        except Exception:
            try:
                await interaction.channel.send(content=f"{owner_user.mention}: {text}")
            except Exception:
                logger.exception("Failed to report sandbox result")


async def setup(bot: commands.Bot):
    await bot.add_cog(SandboxAdmin(bot))
