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

class TransferCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="offers", description="View your current transfer offers")
    async def offers(self, interaction: discord.Interaction):
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
                       f"You have **{len(offers)} offers** waiting:",
            color=discord.Color.gold()
        )
        
        for i, offer in enumerate(offers, 1):
            offer_type_text = ""
            if offer['offer_type'] == 'improved':
                offer_type_text = " 🔥 **IMPROVED OFFER**"
            elif offer['offer_type'] == 'renewal':
                offer_type_text = " 🔄 **CONTRACT RENEWAL**"
            
            wage_comparison = ""
            if offer['wage_offer'] > player['contract_wage']:
                increase = ((offer['wage_offer'] - player['contract_wage']) / player['contract_wage']) * 100
                wage_comparison = f" (+{increase:.0f}%)"
            
            embed.add_field(
                name=f"#{i} - {offer['team_name']}{offer_type_text}",
                value=f"💰 **£{offer['wage_offer']:,}/week**{wage_comparison}\n"
                     f"📄 {offer['contract_length']} year contract\n"
                     f"🏟️ League: {offer['league']}\n"
                     f"🆔 Offer ID: `{offer['offer_id']}`",
                inline=False
            )
        
        embed.add_field(
            name="⚡ How to Respond",
            value="Use `/accept_offer <offer_id>` to accept an offer\n"
                 "Use `/reject_offer <offer_id>` to reject a specific offer\n"
                 "Use `/reject_all_offers` to reject all offers",
            inline=False
        )
        
        embed.set_footer(text=f"Offers expire at end of Week {state['current_week']}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="accept_offer", description="Accept a transfer offer")
    @app_commands.describe(offer_id="The ID of the offer to accept")
    async def accept_offer(self, interaction: discord.Interaction, offer_id: int):
        """Accept a transfer offer"""
        
        await interaction.response.defer()
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.followup.send(
                "❌ You haven't created a player yet!",
                ephemeral=True
            )
            return
        
        result, error = await accept_transfer_offer(interaction.user.id, offer_id, self.bot)
        
        if error:
            await interaction.followup.send(f"❌ {error}", ephemeral=True)
            return
        
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
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="reject_offer", description="Reject a specific transfer offer")
    @app_commands.describe(offer_id="The ID of the offer to reject")
    async def reject_offer(self, interaction: discord.Interaction, offer_id: int):
        """Reject a specific offer"""
        
        success = await reject_transfer_offer(interaction.user.id, offer_id)
        
        if success:
            await interaction.response.send_message(
                f"✅ Offer #{offer_id} rejected.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Could not reject offer. Check the offer ID.",
                ephemeral=True
            )
    
    @app_commands.command(name="reject_all_offers", description="Reject all pending transfer offers")
    async def reject_all_offers_cmd(self, interaction: discord.Interaction):
        """Reject all offers"""
        
        view = ConfirmRejectView()
        await interaction.response.send_message(
            "⚠️ Are you sure you want to reject **ALL** transfer offers?",
            view=view,
            ephemeral=True
        )
        
        await view.wait()
        
        if view.confirmed:
            await reject_all_offers(interaction.user.id)
            await interaction.followup.send(
                "✅ All transfer offers rejected.",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "Cancelled.",
                ephemeral=True
            )
    
    @app_commands.command(name="my_contract", description="View your current contract details")
    async def my_contract(self, interaction: discord.Interaction):
        """View contract details"""
        
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
    
    @app_commands.command(name="transfer_history", description="View your transfer history")
    async def transfer_history(self, interaction: discord.Interaction):
        """View transfer history"""
        
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
