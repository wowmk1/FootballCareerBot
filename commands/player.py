import discord
from discord import app_commands
from discord.ext import commands
from database import db
from utils.football_data_api import get_team_crest_url

class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def profile(self, interaction: discord.Interaction, user: discord.User = None):
        """View player profile (called by /player command)"""
        target_user = user or interaction.user
        
        player = await db.get_player(target_user.id)
        
        if not player:
            if target_user == interaction.user:
                await interaction.response.send_message(
                    "❌ You haven't created a player yet! Use `/start` to begin.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"❌ {target_user.mention} hasn't created a player yet!",
                    ephemeral=True
                )
            return
        
        team = await db.get_team(player['team_id']) if player['team_id'] else None
        
        embed = discord.Embed(
            title=f"⚽ {player['player_name']}",
            description=f"{player['position']} • {player['age']} years old",
            color=discord.Color.blue()
        )
        
        if team:
            crest_url = get_team_crest_url(player['team_id'])
            if crest_url:
                embed.set_thumbnail(url=crest_url)
            
            embed.add_field(
                name="🏟️ Club",
                value=f"**{team['team_name']}**\n{player['league']}",
                inline=True
            )
        else:
            embed.add_field(
                name="🏟️ Club",
                value="Free Agent",
                inline=True
            )
        
        embed.add_field(
            name="📊 Overall",
            value=f"**{player['overall_rating']}** OVR\n⭐ {player['potential']} POT",
            inline=True
        )
        
        embed.add_field(
            name="💰 Contract",
            value=f"£{player['contract_wage']:,}/wk\n{player['contract_years']} years left" if player['contract_wage'] else "No contract",
            inline=True
        )
        
        stats_text = (
            f"⚡ Pace: {player['pace']}\n"
            f"🎯 Shooting: {player['shooting']}\n"
            f"🎨 Passing: {player['passing']}\n"
            f"⚽ Dribbling: {player['dribbling']}\n"
            f"🛡️ Defending: {player['defending']}\n"
            f"💪 Physical: {player['physical']}"
        )
        embed.add_field(name="📈 Attributes", value=stats_text, inline=True)
        
        # Season stats (handle missing MOTM column gracefully)
        season_motm = player.get('season_motm', 0)
        season_text = (
            f"⚽ Goals: {player['season_goals']}\n"
            f"🅰️ Assists: {player['season_assists']}\n"
            f"👕 Appearances: {player['season_apps']}\n"
            f"⭐ MOTM: {season_motm}"
        )
        embed.add_field(name="📊 Season Stats", value=season_text, inline=True)
        
        # Career stats (handle missing MOTM column gracefully)
        career_motm = player.get('career_motm', 0)
        career_text = (
            f"⚽ {player['career_goals']} goals\n"
            f"🅰️ {player['career_assists']} assists\n"
            f"👕 {player['career_apps']} appearances\n"
            f"⭐ {career_motm} MOTM"
        )
        embed.add_field(name="🏆 Career Stats", value=career_text, inline=True)
        
        # ============================================
        # FORM & TRAINING STREAK SECTION
        # ============================================
        from utils.form_morale_system import get_form_description, get_morale_description
        
        form_desc = get_form_description(player['form'])
        morale_desc = get_morale_description(player['morale'])
        
        status_text = f"📊 Form: **{form_desc}** ({player['form']}/100)\n"
        status_text += f"😊 Morale: **{morale_desc}** ({player['morale']}/100)"
        
        if player['training_streak'] > 0:
            status_text += f"\n🔥 Training: **{player['training_streak']} day streak**"
        
        embed.add_field(
            name="🎯 Player Status",
            value=status_text,
            inline=False
        )
        # ============================================
        # END OF FORM SECTION
        # ============================================
        
        embed.set_footer(text=f"Player ID: {target_user.id}")
        
        await interaction.response.send_message(embed=embed)
    
    async def compare(self, interaction: discord.Interaction, user: discord.User):
        """Compare stats with another player (called by /player command)"""
        player1 = await db.get_player(interaction.user.id)
        player2 = await db.get_player(user.id)
        
        if not player1:
            await interaction.response.send_message(
                "❌ You haven't created a player yet! Use `/start` to begin.",
                ephemeral=True
            )
            return
        
        if not player2:
            await interaction.response.send_message(
                f"❌ {user.mention} hasn't created a player yet!",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="⚖️ Player Comparison",
            color=discord.Color.gold()
        )
        
        team1 = await db.get_team(player1['team_id']) if player1['team_id'] else None
        team2 = await db.get_team(player2['team_id']) if player2['team_id'] else None
        
        embed.add_field(
            name=f"{player1['player_name']}",
            value=f"{player1['position']} • {player1['age']}y\n{team1['team_name'] if team1 else 'Free Agent'}",
            inline=True
        )
        
        embed.add_field(name="VS", value="⚔️", inline=True)
        
        embed.add_field(
            name=f"{player2['player_name']}",
            value=f"{player2['position']} • {player2['age']}y\n{team2['team_name'] if team2 else 'Free Agent'}",
            inline=True
        )
        
        def compare_stat(val1, val2):
            if val1 > val2:
                return f"**{val1}** 🟢"
            elif val1 < val2:
                return f"{val1} 🔴"
            else:
                return f"{val1} ⚪"
        
        stats = ['overall_rating', 'potential', 'pace', 'shooting', 'passing', 'dribbling', 'defending', 'physical']
        labels = ['Overall', 'Potential', 'Pace', 'Shooting', 'Passing', 'Dribbling', 'Defending', 'Physical']
        
        for stat, label in zip(stats, labels):
            p1_display = compare_stat(player1[stat], player2[stat])
            p2_display = compare_stat(player2[stat], player1[stat])
            
            embed.add_field(name=f"📊 {label}", value=p1_display, inline=True)
            embed.add_field(name="", value="", inline=True)
            embed.add_field(name=f"📊 {label}", value=p2_display, inline=True)
        
        embed.add_field(
            name="Season Stats",
            value=f"⚽ {player1['season_goals']} | 🅰️ {player1['season_assists']} | 👕 {player1['season_apps']}",
            inline=True
        )
        embed.add_field(name="", value="", inline=True)
        embed.add_field(
            name="Season Stats",
            value=f"⚽ {player2['season_goals']} | 🅰️ {player2['season_assists']} | 👕 {player2['season_apps']}",
            inline=True
        )
        
        # Add form comparison
        from utils.form_morale_system import get_form_description
        
        form1_desc = get_form_description(player1['form'])
        form2_desc = get_form_description(player2['form'])
        
        embed.add_field(
            name="Current Form",
            value=f"{form1_desc} ({player1['form']})",
            inline=True
        )
        embed.add_field(name="", value="", inline=True)
        embed.add_field(
            name="Current Form",
            value=f"{form2_desc} ({player2['form']})",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PlayerCommands(bot))
