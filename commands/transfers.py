"""
Transfer Commands - ENHANCED VERSION
Critical fix: Line 116 changed from interaction.response.edit_message to interaction.edit_original_response
Enhancement #19: Better Transfer Offer Display with team stats and league info
"""
import discord
from discord import app_commands
from discord.ext import commands
from database import db
from utils.transfer_window_manager import (
    get_pending_offers,
    accept_transfer_offer,
    reject_transfer_offer,
    reject_all_offers,
    is_transfer_window_open
)


class TransferOfferView(discord.ui.View):
    def __init__(self, user_id, offers, bot):
        super().__init__(timeout=300)  # 5 minute timeout
        self.user_id = user_id
        self.offers = offers
        self.bot = bot

        # Create a select menu for choosing which offer to interact with
        options = []
        for i, offer in enumerate(offers[:25], 1):  # Discord limit: 25 options
            wage_emoji = "🔥" if offer['offer_type'] == 'improved' else "🔄" if offer['offer_type'] == 'renewal' else "⚽"
            options.append(
                discord.SelectOption(
                    label=f"{offer['team_name']}",
                    description=f"£{offer['wage_offer']:,}/wk | {offer['contract_length']}yr | ID: {offer['offer_id']}",
                    value=str(offer['offer_id']),
                    emoji=wage_emoji
                )
            )

        self.offer_select = discord.ui.Select(
            placeholder="Select an offer to view details...",
            options=options,
            row=0
        )
        self.offer_select.callback = self.select_callback
        self.add_item(self.offer_select)

        self.selected_offer_id = None

    def get_league_color(self, league):
        """Return appropriate color for league tier"""
        colors = {
            'Premier League': discord.Color.purple(),
            'Championship': discord.Color.blue(),
            'League One': discord.Color.green(),
            'League Two': discord.Color.orange()
        }
        return colors.get(league, discord.Color.gold())

    async def select_callback(self, interaction: discord.Interaction):
        """Handle offer selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ These aren't your offers!", ephemeral=True)
            return

        # CRITICAL FIX: Defer immediately
        await interaction.response.defer()

        self.selected_offer_id = int(self.offer_select.values[0])

        # Find the selected offer
        selected_offer = next((o for o in self.offers if o['offer_id'] == self.selected_offer_id), None)

        if not selected_offer:
            await interaction.followup.send("❌ Offer not found!", ephemeral=True)
            return

        # Get current player info
        player = await db.get_player(self.user_id)

        # ENHANCEMENT #19: Get team stats
        async with db.pool.acquire() as conn:
            team_stats = await conn.fetchrow("""
                SELECT t.position, t.points, t.played,
                       AVG(n.overall_rating) as squad_quality
                FROM teams t
                LEFT JOIN npc_players n ON t.team_id = n.team_id AND n.retired = FALSE
                WHERE t.team_id = $1
                GROUP BY t.team_id, t.position, t.points, t.played
            """, selected_offer['team_id'])

        # Create detailed embed for selected offer with league color
        embed = discord.Embed(
            title=f"📋 Offer from {selected_offer['team_name']}",
            color=self.get_league_color(selected_offer['league'])
        )

        # Offer type indicator
        if selected_offer['offer_type'] == 'improved':
            embed.add_field(
                name="🔥 IMPROVED OFFER",
                value="This club has increased their wage offer!",
                inline=False
            )
        elif selected_offer['offer_type'] == 'renewal':
            embed.add_field(
                name="🔄 CONTRACT RENEWAL",
                value="Your current club wants to extend your contract!",
                inline=False
            )

        # ENHANCEMENT #19: League tier indicator with team position
        tier_emoji = {
            'Premier League': '👑',
            'Championship': '🥈',
            'League One': '🥉',
            'League Two': '🎖️'
        }
        
        if team_stats:
            embed.add_field(
                name=f"{tier_emoji.get(selected_offer['league'], '⚽')} {selected_offer['league']}",
                value=f"Position: **{team_stats['position']}** | Points: **{team_stats['points']}** ({team_stats['played']} played)",
                inline=False
            )

            # ENHANCEMENT #19: Squad quality indicator
            if team_stats['squad_quality']:
                quality = float(team_stats['squad_quality'])
                quality_desc = "Elite" if quality >= 80 else "Strong" if quality >= 75 else "Good" if quality >= 70 else "Average"
                embed.add_field(
                    name="🏆 Squad Quality",
                    value=f"**{quality:.1f}** OVR ({quality_desc})",
                    inline=True
                )
        else:
            embed.add_field(
                name=f"{tier_emoji.get(selected_offer['league'], '⚽')} {selected_offer['league']}",
                value="League information available",
                inline=False
            )

        # Wage comparison
        wage_diff = selected_offer['wage_offer'] - player['contract_wage']
        wage_change = f"+£{wage_diff:,}" if wage_diff > 0 else f"£{wage_diff:,}"
        wage_percent = ((selected_offer['wage_offer'] - player['contract_wage']) / player['contract_wage']) * 100

        embed.add_field(
            name="💰 Wage Offer",
            value=f"**£{selected_offer['wage_offer']:,}/week**\n"
                  f"Current: £{player['contract_wage']:,}/week\n"
                  f"Change: {wage_change} ({wage_percent:+.1f}%)",
            inline=True
        )

        embed.add_field(
            name="📄 Contract Length",
            value=f"**{selected_offer['contract_length']} years**\n"
                  f"Current: {player['contract_years']} years left",
            inline=True
        )

        # Enable accept/reject buttons now that an offer is selected
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = False

        # CRITICAL FIX: Use edit_original_response instead of interaction.response.edit_message
        await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="✅ Accept Offer", style=discord.ButtonStyle.success, disabled=True, row=1)
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Accept the selected offer"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ These aren't your offers!", ephemeral=True)
            return

        if not self.selected_offer_id:
            await interaction.response.send_message("❌ Please select an offer first!", ephemeral=True)
            return

        # CRITICAL: Defer immediately - transfer processing takes time
        await interaction.response.defer()

        result, error = await accept_transfer_offer(self.user_id, self.selected_offer_id, self.bot)

        if error:
            await interaction.followup.send(f"❌ {error}", ephemeral=True)
            return

        # Create success embed
        embed = discord.Embed(
            title="✅ TRANSFER COMPLETE!",
            description=f"**{result['player_name']}** has completed his move!",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Transfer Details",
            value=f"**From:** {result['old_team']}\n"
                  f"**To:** {result['new_team']}\n"
                  f"**Fee:** £{result['fee']:,}" + (" (Free Transfer)" if result['fee'] == 0 else ""),
            inline=False
        )

        embed.add_field(
            name="Your New Contract",
            value=f"💰 **£{result['wage']:,}/week**\n"
                  f"📄 **{result['contract_length']} years**",
            inline=False
        )

        embed.set_footer(text="Good luck at your new club!")

        # Disable all buttons after accepting
        for item in self.children:
            item.disabled = True

        await interaction.edit_original_response(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="❌ Reject Offer", style=discord.ButtonStyle.danger, disabled=True, row=1)
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Reject the selected offer"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ These aren't your offers!", ephemeral=True)
            return

        if not self.selected_offer_id:
            await interaction.response.send_message("❌ Please select an offer first!", ephemeral=True)
            return

        # CRITICAL: Defer immediately
        await interaction.response.defer()

        success = await reject_transfer_offer(self.user_id, self.selected_offer_id)

        if success:
            # Remove rejected offer from list
            self.offers = [o for o in self.offers if o['offer_id'] != self.selected_offer_id]

            if not self.offers:
                await interaction.edit_original_response(
                    content="✅ All offers rejected!",
                    embed=None,
                    view=None
                )
                self.stop()
                return

            # Recreate the view without the rejected offer
            new_view = TransferOfferView(self.user_id, self.offers, self.bot)

            player = await db.get_player(self.user_id)
            embed = discord.Embed(
                title="📬 Your Transfer Offers",
                description=f"**{player['player_name']}** ({player['overall_rating']} OVR)\n"
                            f"Current: {player['team_id']} | £{player['contract_wage']:,}/week\n\n"
                            f"✅ Offer rejected! You have **{len(self.offers)} offers** remaining:",
                color=discord.Color.gold()
            )

            await interaction.edit_original_response(embed=embed, view=new_view)
            self.stop()
        else:
            await interaction.followup.send("❌ Could not reject offer.", ephemeral=True)

    @discord.ui.button(label="🗑️ Reject All", style=discord.ButtonStyle.secondary, row=2)
    async def reject_all_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Reject all offers"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ These aren't your offers!", ephemeral=True)
            return

        # Create confirmation view
        confirm_view = ConfirmRejectView()
        await interaction.response.send_message(
            "⚠️ Are you sure you want to reject **ALL** transfer offers?",
            view=confirm_view,
            ephemeral=True
        )

        await confirm_view.wait()

        if confirm_view.confirmed:
            await reject_all_offers(self.user_id)

            # Update original message
            for item in self.children:
                item.disabled = True

            embed = discord.Embed(
                title="✅ All Offers Rejected",
                description="You've rejected all transfer offers. You'll stay at your current club.",
                color=discord.Color.red()
            )

            # Get the original message from the interaction
            original_response = await interaction.original_response()
            await original_response.edit(embed=embed, view=self)
            self.stop()


class TransferCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="offers", description="View your current transfer offers")
    async def offers(self, interaction: discord.Interaction):
        """View transfer offers with interactive buttons"""

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

        state = await db.get_game_state()
        window_open = await is_transfer_window_open(state['current_week'])

        if not window_open:
            await interaction.response.send_message(
                "❌ Transfer window is currently **CLOSED**!\n\n"
                "Transfer windows open during specific weeks of the season.",
                ephemeral=True
            )
            return

        offers = await get_pending_offers(interaction.user.id)

        if not offers:
            await interaction.response.send_message(
                "📭 You have no transfer offers at the moment.\n\n"
                "Offers are generated each week during transfer windows based on your performance.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="📬 Your Transfer Offers",
            description=f"**{player['player_name']}** ({player['overall_rating']} OVR)\n"
                        f"Current: {player['team_id']} | £{player['contract_wage']:,}/week\n\n"
                        f"You have **{len(offers)} offers** waiting!\n\n"
                        "**Select an offer below to view details and accept/reject.**",
            color=discord.Color.gold()
        )

        state = await db.get_game_state()
        embed.set_footer(text=f"Offers expire at end of Week {state['current_week']}")

        view = TransferOfferView(interaction.user.id, offers, self.bot)
        await interaction.response.send_message(embed=embed, view=view)

    # Keep as method for /player to call
    async def my_contract(self, interaction: discord.Interaction):
        """View contract details (called by /player command)"""

        player = await db.get_player(interaction.user.id)

        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet!",
                ephemeral=True
            )
            return

        if player['team_id'] == 'free_agent':
            embed = discord.Embed(
                title="🆓 Free Agent",
                description=f"**{player['player_name']}** is currently a free agent.\n\n"
                            "Wait for transfer offers during transfer windows!",
                color=discord.Color.orange()
            )
        else:
            team = await db.get_team(player['team_id'])

            embed = discord.Embed(
                title="📄 Contract Details",
                description=f"**{player['player_name']}** at **{team['team_name']}**",
                color=discord.Color.blue()
            )

            embed.add_field(
                name="💰 Wage",
                value=f"**£{player['contract_wage']:,}** per week\n"
                      f"(~£{player['contract_wage'] * 52:,} per year)",
                inline=True
            )

            embed.add_field(
                name="⏳ Contract Length",
                value=f"**{player['contract_years']} years** remaining",
                inline=True
            )

            embed.add_field(
                name="🏟️ Club Info",
                value=f"**Team:** {team['team_name']}\n"
                      f"**League:** {team['league']}",
                inline=False
            )

            if player['contract_years'] <= 1:
                embed.add_field(
                    name="⚠️ Contract Expiring",
                    value="Your contract is expiring soon! You may receive renewal offers during transfer windows.",
                    inline=False
                )

        await interaction.response.send_message(embed=embed)

    # Keep as method for /player to call
    async def transfer_history(self, interaction: discord.Interaction):
        """View transfer history (called by /player command)"""

        player = await db.get_player(interaction.user.id)

        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet!",
                ephemeral=True
            )
            return

        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT t.*, t1.team_name as from_team_name, t2.team_name as to_team_name
                   FROM transfers t
                   LEFT JOIN teams t1 ON t.from_team = t1.team_id
                   LEFT JOIN teams t2 ON t.to_team = t2.team_id
                   WHERE t.user_id = $1
                   ORDER BY t.transfer_date DESC
                   LIMIT 10""",
                interaction.user.id
            )
            transfers = [dict(row) for row in rows]

        if not transfers:
            await interaction.response.send_message(
                "📭 No transfer history yet!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"📜 {player['player_name']}'s Transfer History",
            color=discord.Color.blue()
        )

        for i, transfer in enumerate(transfers, 1):
            from_name = transfer['from_team_name'] if transfer['from_team_name'] else 'Free Agent'
            to_name = transfer['to_team_name'] if transfer['to_team_name'] else 'Unknown'

            date = transfer['transfer_date']
            if isinstance(date, str):
                date_str = date[:10]
            else:
                date_str = date.strftime('%Y-%m-%d')

            transfer_type = "🆓" if transfer['fee'] == 0 else "💼"

            embed.add_field(
                name=f"{transfer_type} Transfer #{i}",
                value=f"**{from_name}** ➡️ **{to_name}**\n"
                      f"Fee: £{transfer['fee']:,}\n"
                      f"Wage: £{transfer['wage']:,}/week\n"
                      f"Date: {date_str}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)


class ConfirmRejectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.confirmed = False

    @discord.ui.button(label="✅ Yes, Reject All", style=discord.ButtonStyle.danger)
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
    await bot.add_cog(TransferCommands(bot))
