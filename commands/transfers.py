import discord
from discord import app_commands
from discord.ext import commands
from database import db
import random

class TransferCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="transfer_market", description="Browse teams interested in signing you")
    async def transfer_market(self, interaction: discord.Interaction):
        """View available transfer opportunities"""
        
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
        
        # Generate interested clubs based on player rating
        rating = player['overall_rating']
        potential = player['potential']
        
        # Determine which leagues are interested
        interested_teams = []
        
        # Premier League clubs (for top players)
        if rating >= 75 or potential >= 82:
            async with db.pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM teams WHERE league = $1 ORDER BY RANDOM() LIMIT 3",
                    'Premier League'
                )
                interested_teams.extend([dict(row) for row in rows])
        
        # Championship clubs (for mid-tier players)
        if rating >= 65 or potential >= 72:
            async with db.pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM teams WHERE league = $1 ORDER BY RANDOM() LIMIT 3",
                    'Championship'
                )
                interested_teams.extend([dict(row) for row in rows])
        
        # League One clubs (for developing players)
        if rating >= 55:
            async with db.pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM teams WHERE league = $1 ORDER BY RANDOM() LIMIT 3",
                    'League One'
                )
                interested_teams.extend([dict(row) for row in rows])
        
        # Remove current team
        interested_teams = [t for t in interested_teams if t['team_id'] != player['team_id']]
        
        if not interested_teams:
            await interaction.response.send_message(
                "📭 No clubs are currently interested in signing you.\n\n"
                "💡 Improve your stats with `/train` and perform well in matches to attract interest!",
                ephemeral=True
            )
            return
        
        # Limit to 6 teams
        interested_teams = interested_teams[:6]
        
        embed = discord.Embed(
            title="💼 Transfer Market",
            description=f"**{player['player_name']}** - {len(interested_teams)} clubs interested",
            color=discord.Color.blue()
        )
        
        current_team = await db.get_team(player['team_id']) if player['team_id'] != 'free_agent' else None
        
        if current_team:
            embed.add_field(
                name="🏠 Current Club",
                value=f"**{current_team['team_name']}** ({current_team['league']})\n"
                      f"💰 £{player['contract_wage']:,}/week | ⏳ {player['contract_years']} years left",
                inline=False
            )
        else:
            embed.add_field(
                name="🏠 Current Status",
                value="🆓 Free Agent",
                inline=False
            )
        
        embed.add_field(
            name="📊 Your Market Value",
            value=f"⭐ Rating: **{rating}** OVR\n🌟 Potential: **{potential}** OVR",
            inline=False
        )
        
        # Calculate wage offers for each team
        for team in interested_teams:
            base_wage = player['overall_rating'] * 1000
            
            if team['league'] == 'Premier League':
                wage_offer = int(base_wage * random.uniform(1.5, 2.5))
            elif team['league'] == 'Championship':
                wage_offer = int(base_wage * random.uniform(0.8, 1.2))
            else:
                wage_offer = int(base_wage * random.uniform(0.4, 0.7))
            
            contract_length = random.randint(2, 4)
            
            # Store offer temporarily
            team['wage_offer'] = wage_offer
            team['contract_offer'] = contract_length
        
        view = TransferView(interested_teams, player)
        
        await interaction.response.send_message(embed=embed, view=view)
    
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
                "🆓 You're a free agent! Use `/transfer_market` to find a club.",
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
                value="Your contract expires soon. Check `/transfer_market` for new opportunities!",
                inline=False
            )
        
        embed.set_footer(text="Use /transfer_market to explore transfer opportunities")
        
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
                'loan': '📤',
                'free_transfer': '🆓'
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

class TransferView(discord.ui.View):
    def __init__(self, teams, player):
        super().__init__(timeout=180)
        self.teams = teams
        self.player = player
        
        # Add buttons for each team
        for i, team in enumerate(teams[:5]):  # Limit to 5 buttons
            button = TransferButton(team, player, i)
            self.add_item(button)

class TransferButton(discord.ui.Button):
    def __init__(self, team, player, index):
        wage_offer = team.get('wage_offer', player['contract_wage'])
        
        super().__init__(
            label=team['team_name'][:25],
            style=discord.ButtonStyle.primary,
            custom_id=f"transfer_{team['team_id']}_{index}"
        )
        self.team = team
        self.player = player
        self.wage_offer = wage_offer
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.player['user_id']:
            await interaction.response.send_message(
                "❌ This is not your transfer menu!",
                ephemeral=True
            )
            return
        
        # Show confirmation
        embed = discord.Embed(
            title="💼 Transfer Offer",
            description=f"**{self.team['team_name']}** wants to sign you!",
            color=discord.Color.green()
        )
        
        embed.add_field(name="🏆 League", value=self.team['league'], inline=True)
        embed.add_field(name="💰 Weekly Wage", value=f"£{self.wage_offer:,}", inline=True)
        embed.add_field(name="⏳ Contract", value=f"{self.team['contract_offer']} years", inline=True)
        
        yearly_wage = self.wage_offer * 52
        total_value = yearly_wage * self.team['contract_offer']
        
        embed.add_field(name="💵 Total Value", value=f"£{total_value:,}", inline=False)
        
        current_team = await db.get_team(self.player['team_id']) if self.player['team_id'] != 'free_agent' else None
        
        if current_team:
            embed.add_field(
                name="📊 Comparison",
                value=f"**Current:** £{self.player['contract_wage']:,}/week at {current_team['team_name']}\n"
                      f"**New Offer:** £{self.wage_offer:,}/week at {self.team['team_name']}",
                inline=False
            )
        
        view = ConfirmTransferView(self.team, self.player, self.wage_offer)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ConfirmTransferView(discord.ui.View):
    def __init__(self, team, player, wage_offer):
        super().__init__(timeout=60)
        self.team = team
        self.player = player
        self.wage_offer = wage_offer
    
    @discord.ui.button(label="✅ Accept Offer", style=discord.ButtonStyle.success)
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player['user_id']:
            await interaction.response.send_message("❌ Not your decision!", ephemeral=True)
            return
        
        old_team_id = self.player['team_id']
        old_team = await db.get_team(old_team_id) if old_team_id != 'free_agent' else None
        
        # Calculate transfer fee
        if old_team and old_team_id != 'free_agent':
            base_fee = self.player['overall_rating'] * 1000000
            transfer_fee = int(base_fee * random.uniform(0.5, 1.5))
        else:
            transfer_fee = 0
        
        # Update player
        async with db.pool.acquire() as conn:
            await conn.execute('''
                UPDATE players 
                SET team_id = $1, league = $2, contract_wage = $3, contract_years = $4
                WHERE user_id = $5
            ''',
                self.team['team_id'],
                self.team['league'],
                self.wage_offer,
                self.team['contract_offer'],
                self.player['user_id']
            )
            
            # Record transfer
            await conn.execute('''
                INSERT INTO transfers (user_id, from_team, to_team, fee, wage, contract_length, transfer_type)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''',
                self.player['user_id'],
                old_team_id,
                self.team['team_id'],
                transfer_fee,
                self.wage_offer,
                self.team['contract_offer'],
                'free_transfer' if transfer_fee == 0 else 'transfer'
            )
        
        # Add news
        old_team_name = old_team['team_name'] if old_team else 'free agency'
        
        await db.add_news(
            f"TRANSFER: {self.player['player_name']} joins {self.team['team_name']}!",
            f"{self.player['player_name']} completes move from {old_team_name} to {self.team['team_name']} "
            f"{'for £' + str(transfer_fee) + ' ' if transfer_fee > 0 else ''}on a {self.team['contract_offer']}-year deal.",
            "transfer_news",
            self.player['user_id'],
            8
        )
        
        embed = discord.Embed(
            title="✅ TRANSFER COMPLETE!",
            description=f"**{self.player['player_name']}** has signed for **{self.team['team_name']}**!",
            color=discord.Color.green()
        )
        
        if transfer_fee > 0:
            embed.add_field(name="💰 Transfer Fee", value=f"£{transfer_fee:,}", inline=True)
        
        embed.add_field(name="💼 Contract", value=f"£{self.wage_offer:,}/week\n{self.team['contract_offer']} years", inline=True)
        embed.add_field(name="🏆 League", value=self.team['league'], inline=True)
        
        embed.set_footer(text="Good luck at your new club! Use /fixtures to see your matches.")
        
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="❌ Reject Offer", style=discord.ButtonStyle.danger)
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player['user_id']:
            await interaction.response.send_message("❌ Not your decision!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="❌ Offer Rejected",
            description=f"You've declined {self.team['team_name']}'s offer.\n\n"
                       "Use `/transfer_market` to see other opportunities.",
            color=discord.Color.red()
        )
        
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

async def setup(bot):
    await bot.add_cog(TransferCommands(bot))
