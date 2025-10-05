"""
Complete Transfer Commands with Transfer Window System
INCLUDES: Market Value, All Transfer Functions, Improved Economics
"""

import discord
from discord import app_commands
from discord.ext import commands
from database import db
import random
from utils.transfer_window_manager import (
    is_transfer_window_open,
    get_pending_offers,
    accept_transfer_offer,
    reject_transfer_offer,
    reject_all_offers,
    get_current_transfer_window
)

class TransferCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="offers", description="View your current transfer offers")
    async def offers(self, interaction: discord.Interaction):
        """View pending transfer offers"""
        
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
        
        state = await db.get_game_state()
        current_week = state['current_week']
        
        # Check if transfer window is open
        if not await is_transfer_window_open(current_week):
            next_window_weeks = [w for w in [4, 5, 6, 20, 21, 22] if w > current_week]
            if next_window_weeks:
                next_window = min(next_window_weeks)
                await interaction.response.send_message(
                    f"🔒 **Transfer Window is CLOSED**\n\n"
                    f"📅 Next window opens: **Week {next_window}**\n"
                    f"⏰ Current week: **Week {current_week}**\n\n"
                    f"💡 Transfer windows: Weeks 4-6 (January) and 20-22 (Summer)",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"🔒 **Transfer Window is CLOSED**\n\n"
                    f"Season is ending soon. Windows were Weeks 4-6 and 20-22.",
                    ephemeral=True
                )
            return
        
        # Check if player already transferred this window
        current_transfer_window = get_current_transfer_window(current_week)
        if player.get('last_transfer_window') == current_transfer_window:
            await interaction.response.send_message(
                "✅ **You've already transferred this window!**\n\n"
                "You can only make one transfer per window.\n"
                "Next window opens in a few weeks.",
                ephemeral=True
            )
            return
        
        # Get pending offers
        offers = await get_pending_offers(interaction.user.id)
        
        if not offers:
            await interaction.response.send_message(
                "🔭 **No offers yet this week!**\n\n"
                "Clubs scout during the week and make offers.\n"
                "Check back later or wait for notifications!",
                ephemeral=True
            )
            return
        
        # Create embed
        embed = discord.Embed(
            title="📬 Your Transfer Offers",
            description=f"**{player['player_name']}** - {len(offers)} clubs interested",
            color=discord.Color.gold()
        )
        
        current_team = await db.get_team(player['team_id']) if player['team_id'] != 'free_agent' else None
        
        if current_team:
            embed.add_field(
                name="🏠 Current Club",
                value=f"**{current_team['team_name']}** ({current_team['league']})\n"
                      f"💰 £{player['contract_wage']:,}/week | ⏳ {player['contract_years']} years left",
                inline=False
            )
        
        embed.add_field(
            name="⏰ Transfer Window Status",
            value=f"🟢 **OPEN** - Week {current_week}\n"
                  f"Offers expire at end of this week",
            inline=False
        )
        
        # Add each offer
        for i, offer in enumerate(offers, 1):
            offer_type_emoji = {
                'standard': '📄',
                'renewal': '🔄',
                'improved': '⬆️'
            }.get(offer['offer_type'], '📄')
            
            offer_type_text = {
                'standard': '',
                'renewal': ' (CONTRACT RENEWAL)',
                'improved': ' (IMPROVED OFFER!)'
            }.get(offer['offer_type'], '')
            
            yearly_wage = offer['wage_offer'] * 52
            total_value = yearly_wage * offer['contract_length']
            
            offer_text = f"{offer_type_emoji} **{offer['team_name']}**{offer_type_text}\n"
            offer_text += f"🏆 {offer['league']}\n"
            offer_text += f"💰 £{offer['wage_offer']:,}/week (£{yearly_wage:,}/year)\n"
            offer_text += f"⏳ {offer['contract_length']} year contract\n"
            offer_text += f"💵 Total: £{total_value:,}\n"
            
            if offer.get('performance_bonus') and offer['performance_bonus'] > 0:
                offer_text += f"✨ Performance bonus included!\n"
            
            offer_text += f"\n**ID: {offer['offer_id']}**"
            
            embed.add_field(
                name=f"Offer #{i}",
                value=offer_text,
                inline=False
            )
        
        embed.add_field(
            name="📋 How to Respond",
            value="• `/accept_offer <offer_id>` - Sign with that club\n"
                  "• `/reject_offer <offer_id>` - Decline specific offer\n"
                  "• `/reject_all` - Reject all offers and stay",
            inline=False
        )
        
        embed.set_footer(text="⚠️ You can only transfer ONCE per window!")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="accept_offer", description="Accept a transfer offer and sign with a new club")
    @app_commands.describe(offer_id="The ID of the offer to accept (from /offers)")
    async def accept_offer(self, interaction: discord.Interaction, offer_id: int):
        """Accept a transfer offer"""
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet!",
                ephemeral=True
            )
            return
        
        state = await db.get_game_state()
        current_week = state['current_week']
        
        if not await is_transfer_window_open(current_week):
            await interaction.response.send_message(
                "🔒 Transfer window is closed!",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        result, error = await accept_transfer_offer(interaction.user.id, offer_id)
        
        if error:
            await interaction.followup.send(
                f"❌ **Transfer Failed**\n\n{error}",
                ephemeral=True
            )
            return
        
        # Success!
        embed = discord.Embed(
            title="✅ TRANSFER COMPLETE!",
            description=f"**{result['player_name']}** has signed for **{result['new_team']}**!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="📊 Transfer Details",
            value=f"**From:** {result['old_team']}\n"
                  f"**To:** {result['new_team']}",
            inline=False
        )
        
        if result['fee'] > 0:
            embed.add_field(name="💰 Transfer Fee", value=f"£{result['fee']:,}", inline=True)
        
        embed.add_field(
            name="💼 Contract",
            value=f"£{result['wage']:,}/week\n{result['contract_length']} years",
            inline=True
        )
        
        embed.add_field(
            name="🔒 Window Status",
            value="You've used your one transfer this window.\nNo more moves until next window!",
            inline=False
        )
        
        embed.set_footer(text="Good luck at your new club! Use /fixtures to see your matches.")
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="reject_offer", description="Reject a specific transfer offer")
    @app_commands.describe(offer_id="The ID of the offer to reject")
    async def reject_offer(self, interaction: discord.Interaction, offer_id: int):
        """Reject a single offer"""
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet!",
                ephemeral=True
            )
            return
        
        await reject_transfer_offer(interaction.user.id, offer_id)
        
        embed = discord.Embed(
            title="❌ Offer Rejected",
            description=f"You've declined offer #{offer_id}.\n\n"
                       "The club may return with an improved offer next week!",
            color=discord.Color.red()
        )
        
        embed.set_footer(text="Use /offers to see remaining offers")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="reject_all", description="Reject all current offers and stay at your club")
    async def reject_all_cmd(self, interaction: discord.Interaction):
        """Reject all pending offers"""
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet!",
                ephemeral=True
            )
            return
        
        offers = await get_pending_offers(interaction.user.id)
        
        if not offers:
            await interaction.response.send_message(
                "🔭 You have no pending offers to reject!",
                ephemeral=True
            )
            return
        
        await reject_all_offers(interaction.user.id)
        
        current_team = await db.get_team(player['team_id']) if player['team_id'] != 'free_agent' else None
        
        embed = discord.Embed(
            title="✅ All Offers Rejected",
            description=f"You've declined all {len(offers)} offers.",
            color=discord.Color.blue()
        )
        
        if current_team:
            embed.add_field(
                name="🏠 Staying At",
                value=f"**{current_team['team_name']}**\n{current_team['league']}",
                inline=False
            )
        
        embed.add_field(
            name="💡 Next Steps",
            value="Clubs may return with improved offers next week!\n"
                  "Check `/offers` regularly during the transfer window.",
            inline=False
        )
        
        embed.set_footer(text="Loyalty to your club noted!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="my_contract", description="View your current contract details")
    async def my_contract(self, interaction: discord.Interaction):
        """View contract info"""
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet! Use `/start` to begin.",
                ephemeral=True
            )
            return
        
        if player['team_id'] == 'free_agent':
            await interaction.response.send_message(
                "🆓 You're a free agent! Use `/offers` during transfer windows to find a club.",
                ephemeral=True
            )
            return
        
        team = await db.get_team(player['team_id'])
        
        embed = discord.Embed(
            title="📄 Contract Details",
            description=f"**{player['player_name']}**",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="🏠 Club", value=f"**{team['team_name']}**", inline=True)
        embed.add_field(name="🏆 League", value=team['league'], inline=True)
        embed.add_field(name="📋 Position", value=player['position'], inline=True)
        
        embed.add_field(
            name="💰 Wages",
            value=f"**£{player['contract_wage']:,}** per week\n"
                  f"**£{player['contract_wage'] * 52:,}** per year",
            inline=True
        )
        
        embed.add_field(
            name="⏳ Contract Length",
            value=f"**{player['contract_years']} years** remaining",
            inline=True
        )
        
        total_value = player['contract_wage'] * 52 * player['contract_years']
        embed.add_field(
            name="💵 Total Contract Value",
            value=f"**£{total_value:,}**",
            inline=True
        )
        
        embed.add_field(
            name="📊 Your Stats",
            value=f"⭐ Overall: **{player['overall_rating']}**\n"
                  f"🌟 Potential: **{player['potential']}**\n"
                  f"🎂 Age: **{player['age']}**",
            inline=False
        )
        
        if player['contract_years'] <= 1:
            embed.add_field(
                name="⚠️ Contract Expiring Soon!",
                value="Your contract expires soon. Check `/offers` during transfer windows for opportunities!",
                inline=False
            )
        
        state = await db.get_game_state()
        current_week = state['current_week']
        
        if await is_transfer_window_open(current_week):
            embed.add_field(
                name="🟢 Transfer Window Open",
                value="Use `/offers` to see clubs interested in you!",
                inline=False
            )
        else:
            next_windows = [w for w in [4, 5, 6, 20, 21, 22] if w > current_week]
            if next_windows:
                embed.set_footer(text=f"Next transfer window: Week {min(next_windows)}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="transfer_history", description="View your transfer history")
    async def transfer_history(self, interaction: discord.Interaction):
        """View past transfers"""
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet! Use `/start` to begin.",
                ephemeral=True
            )
            return
        
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM transfers 
                   WHERE user_id = $1 
                   ORDER BY transfer_date DESC 
                   LIMIT 10""",
                interaction.user.id
            )
            transfers = [dict(row) for row in rows]
        
        if not transfers:
            await interaction.response.send_message(
                "📋 No transfer history yet!",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="📜 Transfer History",
            description=f"**{player['player_name']}** - Career moves",
            color=discord.Color.blue()
        )
        
        for transfer in transfers:
            from_team = await db.get_team(transfer['from_team']) if transfer['from_team'] != 'free_agent' else None
            to_team = await db.get_team(transfer['to_team']) if transfer['to_team'] != 'free_agent' else None
            
            from_name = from_team['team_name'] if from_team else '🆓 Free Agent'
            to_name = to_team['team_name'] if to_team else '🆓 Free Agent'
            
            transfer_type_emoji = {
                'signing': '✍️',
                'transfer': '🔄',
                'loan': '🔀',
                'free_transfer': '🆓',
                'admin_assignment': '⚙️'
            }.get(transfer['transfer_type'], '➡️')
            
            date = transfer['transfer_date']
            if isinstance(date, str):
                date_str = date[:10]
            else:
                date_str = date.strftime('%Y-%m-%d')
            
            if transfer['fee'] > 0:
                fee_text = f"Fee: £{transfer['fee']:,}"
            else:
                fee_text = "Free transfer"
            
            embed.add_field(
                name=f"{transfer_type_emoji} {from_name} → {to_name}",
                value=f"{fee_text}\n"
                      f"💰 £{transfer['wage']:,}/week | ⏳ {transfer['contract_length']}y\n"
                      f"📅 {date_str}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="market_value", description="Check your estimated market value and potential suitors")
    async def market_value(self, interaction: discord.Interaction):
        """Show player's market value and interested clubs"""
        
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
        
        # Calculate market value
        base_value = player['overall_rating'] * 100000
        age_modifier = 1.0
        if player['age'] < 23:
            age_modifier = 1.5
        elif player['age'] > 30:
            age_modifier = 0.6
        
        estimated_value = int(base_value * age_modifier)
        
        # Calculate wage expectation
        base_wage = (player['overall_rating'] ** 2) * 10
        
        embed = discord.Embed(
            title=f"💰 Market Valuation - {player['player_name']}",
            description=f"Your current market standing",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="📊 Player Profile",
            value=f"⭐ Rating: **{player['overall_rating']}** OVR\n"
                  f"🌟 Potential: **{player['potential']}** OVR\n"
                  f"🎂 Age: **{player['age']}** years\n"
                  f"📋 Position: **{player['position']}**",
            inline=True
        )
        
        embed.add_field(
            name="💵 Estimated Transfer Value",
            value=f"**£{estimated_value:,}**\n"
                  f"{'⬆️ Youth premium' if player['age'] < 23 else '⬇️ Age discount' if player['age'] > 30 else '✅ Prime age'}",
            inline=True
        )
        
        # Determine interested leagues
        rating = player['overall_rating']
        potential = player['potential']
        
        interested_leagues = []
        if rating >= 75 or potential >= 82:
            interested_leagues.append("⭐ **Premier League** clubs")
        if rating >= 65 or potential >= 72:
            interested_leagues.append("🥈 **Championship** clubs")
        if rating >= 55:
            interested_leagues.append("🥉 **League One** clubs")
        
        if interested_leagues:
            embed.add_field(
                name="🔍 Clubs Interested In You",
                value="\n".join(interested_leagues),
                inline=False
            )
        else:
            embed.add_field(
                name="🔍 Interest Level",
                value="⚠️ Limited interest - improve your rating!",
                inline=False
            )
        
        # Wage expectations by league
        pl_wage = int(base_wage * 2.0)
        champ_wage = int(base_wage * 1.0)
        l1_wage = int(base_wage * 0.5)
        
        embed.add_field(
            name="💼 Wage Expectations",
            value=f"⭐ Premier League: **£{pl_wage:,}**/week\n"
                  f"🥈 Championship: **£{champ_wage:,}**/week\n"
                  f"🥉 League One: **£{l1_wage:,}**/week",
            inline=True
        )
        
        # Current contract status
        if player['team_id'] != 'free_agent':
            team = await db.get_team(player['team_id'])
            embed.add_field(
                name="📄 Current Contract",
                value=f"🏠 **{team['team_name']}**\n"
                      f"💰 £{player['contract_wage']:,}/week\n"
                      f"⏳ {player['contract_years']} years left",
                inline=True
            )
            
            if player['contract_wage'] < base_wage * 0.7:
                embed.add_field(
                    name="💡 Contract Status",
                    value="⚠️ You're underpaid! Look for offers during transfer windows.",
                    inline=False
                )
        else:
            embed.add_field(
                name="📄 Current Status",
                value="🆓 **Free Agent**\nAvailable for transfer",
                inline=True
            )
        
        state = await db.get_game_state()
        current_week = state['current_week']
        
        if await is_transfer_window_open(current_week):
            embed.add_field(
                name="🟢 Transfer Window Open",
                value="Use `/offers` to see actual offers from clubs!",
                inline=False
            )
        else:
            next_windows = [w for w in [4, 5, 6, 20, 21, 22] if w > current_week]
            if next_windows:
                embed.set_footer(text=f"Next transfer window: Week {min(next_windows)} | Use /offers during windows")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="transfer_market", description="[OLD SYSTEM - Use /offers instead]")
    async def transfer_market(self, interaction: discord.Interaction):
        """Legacy command - redirects to new system"""
        
        state = await db.get_game_state()
        current_week = state['current_week']
        
        if await is_transfer_window_open(current_week):
            await interaction.response.send_message(
                "🔄 **Transfer System Updated!**\n\n"
                "The transfer market now uses a window system.\n\n"
                "✅ Use `/offers` to see clubs interested in you!\n\n"
                "📅 Transfer windows are:\n"
                "• Weeks 4-6 (January)\n"
                "• Weeks 20-22 (Summer)\n\n"
                "You'll receive notifications when new offers arrive!",
                ephemeral=True
            )
        else:
            next_window_weeks = [w for w in [4, 5, 6, 20, 21, 22] if w > current_week]
            if next_window_weeks:
                next_window = min(next_window_weeks)
                await interaction.response.send_message(
                    "🔒 **Transfer Window is CLOSED**\n\n"
                    f"📅 Next window opens: **Week {next_window}**\n\n"
                    "✅ Use `/offers` when the window opens to see clubs interested in you!",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "🔒 **Transfer Window is CLOSED**\n\n"
                    "Season is ending. Windows were Weeks 4-6 and 20-22.",
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(TransferCommands(bot))
