import discord
from discord import app_commands
from discord.ext import commands
from database import db
from utils.football_data_api import get_team_crest_url

class TransferCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="offers", description="View your current transfer offers")
    async def offers(self, interaction: discord.Interaction):
        """View pending transfer offers with interactive buttons"""
        
        from utils.transfer_window_manager import (
            is_transfer_window_open,
            get_pending_offers,
            get_current_transfer_window
        )
        
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
        
        if not await is_transfer_window_open(current_week):
            next_window_weeks = [w for w in [4, 5, 6, 20, 21, 22] if w > current_week]
            if next_window_weeks:
                next_window = min(next_window_weeks)
                await interaction.response.send_message(
                    f"🔒 **Transfer Window CLOSED**\n\n"
                    f"📅 Opens: **Week {next_window}**\n"
                    f"⏰ Current: **Week {current_week}**",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"🔒 **Transfer Window CLOSED**\nSeason ending soon.",
                    ephemeral=True
                )
            return
        
        current_transfer_window = get_current_transfer_window(current_week)
        if player.get('last_transfer_window') == current_transfer_window:
            await interaction.response.send_message(
                "✅ **Already transferred this window!**\n"
                "One transfer per window maximum.",
                ephemeral=True
            )
            return
        
        offers = await get_pending_offers(interaction.user.id)
        
        if not offers:
            await interaction.response.send_message(
                "🔭 **No offers yet!**\nCheck back later or wait for notifications!",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="📬 Your Transfer Offers",
            description=f"**{player['player_name']}** - {len(offers)} clubs interested",
            color=discord.Color.gold()
        )
        
        current_team = await db.get_team(player['team_id']) if player['team_id'] != 'free_agent' else None
        
        if current_team:
            # ADD CURRENT TEAM CREST
            current_crest = get_team_crest_url(player['team_id'])
            if current_crest:
                embed.set_thumbnail(url=current_crest)
            
            embed.add_field(
                name="🏠 Current Club",
                value=f"**{current_team['team_name']}**\n"
                      f"💰 £{player['contract_wage']:,}/wk | ⏳ {player['contract_years']}y",
                inline=False
            )
        
        for i, offer in enumerate(offers[:3], 1):
            offer_type_emoji = {
                'standard': '📄',
                'renewal': '🔄',
                'improved': '⬆️'
            }.get(offer['offer_type'], '📄')
            
            yearly_wage = offer['wage_offer'] * 52
            
            offer_text = f"{offer_type_emoji} **{offer['team_name']}**\n"
            offer_text += f"🏆 {offer['league']}\n"
            offer_text += f"💰 £{offer['wage_offer']:,}/week\n"
            offer_text += f"⏳ {offer['contract_length']} years\n"
            offer_text += f"💵 Total: £{yearly_wage * offer['contract_length']:,}"
            
            embed.add_field(
                name=f"Offer #{i}",
                value=offer_text,
                inline=True
            )
        
        # ADD BEST OFFER TEAM'S CREST AS IMAGE
        if offers:
            best_offer = max(offers[:3], key=lambda x: x['wage_offer'])
            best_crest = get_team_crest_url(best_offer['team_id'])
            if best_crest:
                embed.set_image(url=best_crest)
                embed.set_footer(text=f"Highest offer: {best_offer['team_name']} • £{best_offer['wage_offer']:,}/wk")
        
        if len(offers) > 3:
            embed.set_footer(text=f"Showing 3 of {len(offers)} offers • Use buttons to accept/reject")
        
        view = TransferOfferView(offers[:3], interaction.user.id)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command(name="my_contract", description="View your current contract details")
    async def my_contract(self, interaction: discord.Interaction):
        """View contract info"""
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet!",
                ephemeral=True
            )
            return
        
        if player['team_id'] == 'free_agent':
            await interaction.response.send_message(
                "🆓 You're a free agent! Use `/offers` during transfer windows.",
                ephemeral=True
            )
            return
        
        team = await db.get_team(player['team_id'])
        
        embed = discord.Embed(
            title="📄 Contract Details",
            description=f"**{player['player_name']}**",
            color=discord.Color.gold()
        )
        
        # ADD TEAM CREST
        crest_url = get_team_crest_url(player['team_id'])
        if crest_url:
            embed.set_thumbnail(url=crest_url)
        
        embed.add_field(name="🏠 Club", value=f"**{team['team_name']}**", inline=True)
        embed.add_field(name="🏆 League", value=team['league'], inline=True)
        embed.add_field(name="📋 Position", value=player['position'], inline=True)
        
        embed.add_field(
            name="💰 Wages",
            value=f"**£{player['contract_wage']:,}**/week\n"
                  f"**£{player['contract_wage'] * 52:,}**/year",
            inline=True
        )
        
        embed.add_field(
            name="⏳ Length",
            value=f"**{player['contract_years']}** years left",
            inline=True
        )
        
        total_value = player['contract_wage'] * 52 * player['contract_years']
        embed.add_field(
            name="💵 Total Value",
            value=f"**£{total_value:,}**",
            inline=True
        )
        
        if player['contract_years'] <= 1:
            embed.add_field(
                name="⚠️ Contract Expiring!",
                value="Check `/offers` for opportunities!",
                inline=False
            )
        
        # ADD LEAGUE LOGO AS FOOTER
        from utils.football_data_api import get_competition_logo
        league_logo = get_competition_logo(team['league'])
        if league_logo:
            embed.set_footer(
                text=f"{team['league']} • Contract Details",
                icon_url=league_logo
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="transfer_history", description="View your transfer history")
    async def transfer_history(self, interaction: discord.Interaction):
        """View past transfers"""
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet!",
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
        
        # ADD CURRENT TEAM CREST
        if player['team_id'] != 'free_agent':
            current_crest = get_team_crest_url(player['team_id'])
            if current_crest:
                embed.set_thumbnail(url=current_crest)
        
        for transfer in transfers[:8]:
            from_team = await db.get_team(transfer['from_team']) if transfer['from_team'] != 'free_agent' else None
            to_team = await db.get_team(transfer['to_team']) if transfer['to_team'] != 'free_agent' else None
            
            from_name = from_team['team_name'] if from_team else '🆓 Free Agent'
            to_name = to_team['team_name'] if to_team else '🆓 Free Agent'
            
            transfer_type_emoji = {
                'signing': '✍️',
                'transfer': '🔄',
                'free_transfer': '🆓',
                'admin_assignment': '⚙️'
            }.get(transfer['transfer_type'], '➡️')
            
            date = transfer['transfer_date']
            date_str = date[:10] if isinstance(date, str) else date.strftime('%Y-%m-%d')
            
            fee_text = f"£{transfer['fee']:,}" if transfer['fee'] > 0 else "Free"
            
            embed.add_field(
                name=f"{transfer_type_emoji} {from_name} → {to_name}",
                value=f"{fee_text} | £{transfer['wage']:,}/wk | {transfer['contract_length']}y\n{date_str}",
                inline=False
            )
        
        # ADD MOST RECENT TEAM'S CREST AS IMAGE
        if transfers:
            latest_transfer = transfers[0]
            if latest_transfer['to_team'] != 'free_agent':
                latest_crest = get_team_crest_url(latest_transfer['to_team'])
                if latest_crest:
                    embed.set_image(url=latest_crest)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class TransferOfferView(discord.ui.View):
    def __init__(self, offers, user_id):
        super().__init__(timeout=300)
        self.offers = offers
        self.user_id = user_id
        
        for i, offer in enumerate(offers):
            button = AcceptOfferButton(offer, i+1)
            self.add_item(button)
        
        reject_button = discord.ui.Button(
            label="❌ Reject All",
            style=discord.ButtonStyle.danger,
            custom_id="reject_all"
        )
        reject_button.callback = self.reject_all_callback
        self.add_item(reject_button)
    
    async def reject_all_callback(self, interaction: discord.Interaction):
        """Reject all offers"""
        from utils.transfer_window_manager import reject_all_offers
        
        await reject_all_offers(self.user_id)
        
        embed = discord.Embed(
            title="✅ All Offers Rejected",
            description="You've stayed at your current club.",
            color=discord.Color.blue()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

class AcceptOfferButton(discord.ui.Button):
    def __init__(self, offer, number):
        super().__init__(
            label=f"✅ Accept #{number}",
            style=discord.ButtonStyle.success,
            custom_id=f"accept_{offer['offer_id']}"
        )
        self.offer = offer
    
    async def callback(self, interaction: discord.Interaction):
        """Accept this offer"""
        from utils.transfer_window_manager import accept_transfer_offer
        
        await interaction.response.defer()
        
        result, error = await accept_transfer_offer(interaction.user.id, self.offer['offer_id'], self.view.bot if hasattr(self.view, 'bot') else None)
        
        if error:
            await interaction.followup.send(
                f"❌ **Transfer Failed**\n{error}",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="✅ TRANSFER COMPLETE!",
            description=f"**{result['player_name']}** → **{result['new_team']}**!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="📊 Details",
            value=f"From: {result['old_team']}\nTo: {result['new_team']}",
            inline=False
        )
        
        if result['fee'] > 0:
            embed.add_field(name="💰 Fee", value=f"£{result['fee']:,}", inline=True)
        
        embed.add_field(
            name="💼 Contract",
            value=f"£{result['wage']:,}/week\n{result['contract_length']} years",
            inline=True
        )
        
        # ADD NEW TEAM CREST
        new_crest = get_team_crest_url(self.offer['team_id'])
        if new_crest:
            embed.set_thumbnail(url=new_crest)
        
        await interaction.edit_original_response(embed=embed, view=None)
        self.view.stop()

async def setup(bot):
    await bot.add_cog(TransferCommands(bot))        
    offers = await get_pending_offers(interaction.user.id)
        
        if not offers:
            await interaction.response.send_message(
                "🔭 **No offers yet!**\nCheck back later or wait for notifications!",
                ephemeral=True
            )
            return
        
        # Create interactive embed with buttons
        embed = discord.Embed(
            title="📬 Your Transfer Offers",
            description=f"**{player['player_name']}** - {len(offers)} clubs interested",
            color=discord.Color.gold()
        )
        
        current_team = await db.get_team(player['team_id']) if player['team_id'] != 'free_agent' else None
        
        if current_team:
            embed.add_field(
                name="🏠 Current Club",
                value=f"**{current_team['team_name']}**\n"
                      f"💰 £{player['contract_wage']:,}/wk | ⏳ {player['contract_years']}y",
                inline=False
            )
        
        # Show first 3 offers
        for i, offer in enumerate(offers[:3], 1):
            offer_type_emoji = {
                'standard': '📄',
                'renewal': '🔄',
                'improved': '⬆️'
            }.get(offer['offer_type'], '📄')
            
            yearly_wage = offer['wage_offer'] * 52
            
            offer_text = f"{offer_type_emoji} **{offer['team_name']}**\n"
            offer_text += f"🏆 {offer['league']}\n"
            offer_text += f"💰 £{offer['wage_offer']:,}/week\n"
            offer_text += f"⏳ {offer['contract_length']} years\n"
            offer_text += f"💵 Total: £{yearly_wage * offer['contract_length']:,}"
            
            embed.add_field(
                name=f"Offer #{i}",
                value=offer_text,
                inline=True
            )
        
        if len(offers) > 3:
            embed.set_footer(text=f"Showing 3 of {len(offers)} offers • Use buttons to accept/reject")
        
        # Create button view
        view = TransferOfferView(offers[:3], interaction.user.id)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command(name="my_contract", description="View your current contract details")
    async def my_contract(self, interaction: discord.Interaction):
        """View contract info"""
        
        from utils.transfer_window_manager import is_transfer_window_open
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet!",
                ephemeral=True
            )
            return
        
        if player['team_id'] == 'free_agent':
            await interaction.response.send_message(
                "🆓 You're a free agent! Use `/offers` during transfer windows.",
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
            value=f"**£{player['contract_wage']:,}**/week\n"
                  f"**£{player['contract_wage'] * 52:,}**/year",
            inline=True
        )
        
        embed.add_field(
            name="⏳ Length",
            value=f"**{player['contract_years']}** years left",
            inline=True
        )
        
        total_value = player['contract_wage'] * 52 * player['contract_years']
        embed.add_field(
            name="💵 Total Value",
            value=f"**£{total_value:,}**",
            inline=True
        )
        
        if player['contract_years'] <= 1:
            embed.add_field(
                name="⚠️ Contract Expiring!",
                value="Check `/offers` for opportunities!",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="transfer_history", description="View your transfer history")
    async def transfer_history(self, interaction: discord.Interaction):
        """View past transfers"""
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet!",
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
        
        for transfer in transfers[:8]:
            from_team = await db.get_team(transfer['from_team']) if transfer['from_team'] != 'free_agent' else None
            to_team = await db.get_team(transfer['to_team']) if transfer['to_team'] != 'free_agent' else None
            
            from_name = from_team['team_name'] if from_team else '🆓 Free Agent'
            to_name = to_team['team_name'] if to_team else '🆓 Free Agent'
            
            transfer_type_emoji = {
                'signing': '✍️',
                'transfer': '🔄',
                'free_transfer': '🆓',
                'admin_assignment': '⚙️'
            }.get(transfer['transfer_type'], '➡️')
            
            date = transfer['transfer_date']
            date_str = date[:10] if isinstance(date, str) else date.strftime('%Y-%m-%d')
            
            fee_text = f"£{transfer['fee']:,}" if transfer['fee'] > 0 else "Free"
            
            embed.add_field(
                name=f"{transfer_type_emoji} {from_name} → {to_name}",
                value=f"{fee_text} | £{transfer['wage']:,}/wk | {transfer['contract_length']}y\n{date_str}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class TransferOfferView(discord.ui.View):
    def __init__(self, offers, user_id):
        super().__init__(timeout=300)  # 5 minute timeout
        self.offers = offers
        self.user_id = user_id
        
        # Add button for each offer
        for i, offer in enumerate(offers):
            button = AcceptOfferButton(offer, i+1)
            self.add_item(button)
        
        # Add reject all button
        reject_button = discord.ui.Button(
            label="❌ Reject All",
            style=discord.ButtonStyle.danger,
            custom_id="reject_all"
        )
        reject_button.callback = self.reject_all_callback
        self.add_item(reject_button)
    
    async def reject_all_callback(self, interaction: discord.Interaction):
        """Reject all offers"""
        from utils.transfer_window_manager import reject_all_offers
        
        await reject_all_offers(self.user_id)
        
        embed = discord.Embed(
            title="✅ All Offers Rejected",
            description="You've stayed at your current club.",
            color=discord.Color.blue()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

class AcceptOfferButton(discord.ui.Button):
    def __init__(self, offer, number):
        super().__init__(
            label=f"✅ Accept #{number}",
            style=discord.ButtonStyle.success,
            custom_id=f"accept_{offer['offer_id']}"
        )
        self.offer = offer
    
    async def callback(self, interaction: discord.Interaction):
        """Accept this offer"""
        from utils.transfer_window_manager import accept_transfer_offer
        
        await interaction.response.defer()
        
        result, error = await accept_transfer_offer(interaction.user.id, self.offer['offer_id'])
        
        if error:
            await interaction.followup.send(
                f"❌ **Transfer Failed**\n{error}",
                ephemeral=True
            )
            return
        
        # Success!
        embed = discord.Embed(
            title="✅ TRANSFER COMPLETE!",
            description=f"**{result['player_name']}** → **{result['new_team']}**!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="📊 Details",
            value=f"From: {result['old_team']}\nTo: {result['new_team']}",
            inline=False
        )
        
        if result['fee'] > 0:
            embed.add_field(name="💰 Fee", value=f"£{result['fee']:,}", inline=True)
        
        embed.add_field(
            name="💼 Contract",
            value=f"£{result['wage']:,}/week\n{result['contract_length']} years",
            inline=True
        )
        
        await interaction.edit_original_response(embed=embed, view=None)
        self.view.stop()

async def setup(bot):
    await bot.add_cog(TransferCommands(bot))
