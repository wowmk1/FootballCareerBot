import discord
from discord import app_commands
from discord.ext import commands
from database import db

class MatchCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="fixtures", description="View your upcoming matches")
    async def fixtures(self, interaction: discord.Interaction):
        """View upcoming fixtures"""
        
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
        
        if player['team_id'] == 'free_agent':
            await interaction.response.send_message(
                "❌ You're a free agent! Sign for a club to see fixtures.\n\n"
                "💡 Use `/clubs` to see available teams (transfers coming soon)",
                ephemeral=True
            )
            return
        
        fixtures = await db.get_player_team_fixtures(interaction.user.id, limit=10)
        
        if not fixtures:
            await interaction.response.send_message(
                "📅 No upcoming fixtures! The season may have ended or fixtures aren't generated yet.\n\n"
                "💡 Use `/season` to check season status.",
                ephemeral=True
            )
            return
        
        team = await db.get_team(player['team_id'])
        
        embed = discord.Embed(
            title=f"📅 {team['team_name']} - Upcoming Fixtures",
            description=f"**{team['league']}** | Your next matches:",
            color=discord.Color.blue()
        )
        
        for idx, fixture in enumerate(fixtures, 1):
            is_home = fixture['home_team_id'] == player['team_id']
            opponent_id = fixture['away_team_id'] if is_home else fixture['home_team_id']
            
            opponent = await db.get_team(opponent_id)
            
            if is_home:
                match_text = f"🏠 vs **{opponent['team_name']}**"
            else:
                match_text = f"✈️ at **{opponent['team_name']}**"
            
            async with db.db.execute(
                "SELECT player_name FROM players WHERE team_id = ? AND retired = 0 LIMIT 3",
                (opponent_id,)
            ) as cursor:
                opponent_players = await cursor.fetchall()
            
            if opponent_players:
                player_names = ", ".join([p['player_name'] for p in opponent_players])
                match_text += f"\n👥 Face: {player_names}"
            
            playable_status = " 🎮" if fixture['playable'] else ""
            
            embed.add_field(
                name=f"Week {fixture['week_number']} - {fixture['competition']}{playable_status}",
                value=match_text,
                inline=False
            )
        
        embed.set_footer(text="🎮 = Interactive match available | Use /play_match during match windows!")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="results", description="View recent match results")
    async def results(self, interaction: discord.Interaction):
        """View recent results"""
        
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
        
        if player['team_id'] == 'free_agent':
            await interaction.response.send_message(
                "❌ You're a free agent!",
                ephemeral=True
            )
            return
        
        async with db.db.execute(
            """SELECT * FROM fixtures 
               WHERE (home_team_id = ? OR away_team_id = ?) 
               AND played = 1 
               ORDER BY week_number DESC 
               LIMIT 10""",
            (player['team_id'], player['team_id'])
        ) as cursor:
            rows = await cursor.fetchall()
            fixtures = [dict(row) for row in rows]
        
        if not fixtures:
            await interaction.response.send_message(
                "📊 No matches played yet! Wait for the first match day.",
                ephemeral=True
            )
            return
        
        team = await db.get_team(player['team_id'])
        
        embed = discord.Embed(
            title=f"📊 {team['team_name']} - Recent Results",
            description=f"**{team['league']}** | Last 10 matches:",
            color=discord.Color.blue()
        )
        
        for fixture in fixtures:
            home_team = await db.get_team(fixture['home_team_id'])
            away_team = await db.get_team(fixture['away_team_id'])
            
            is_home = fixture['home_team_id'] == player['team_id']
            
            if is_home:
                if fixture['home_score'] > fixture['away_score']:
                    result = "✅ W"
                    color = "🟢"
                elif fixture['home_score'] < fixture['away_score']:
                    result = "❌ L"
                    color = "🔴"
                else:
                    result = "➖ D"
                    color = "🟡"
            else:
                if fixture['away_score'] > fixture['home_score']:
                    result = "✅ W"
                    color = "🟢"
                elif fixture['away_score'] < fixture['home_score']:
                    result = "❌ L"
                    color = "🔴"
                else:
                    result = "➖ D"
                    color = "🟡"
            
            score = f"{fixture['home_score']}-{fixture['away_score']}"
            
            embed.add_field(
                name=f"{result} Week {fixture['week_number']}",
                value=f"{color} **{home_team['team_name']}** {score} **{away_team['team_name']}**",
                inline=False
            )
        
        form_results = []
        for fixture in fixtures[:5]:
            is_home = fixture['home_team_id'] == player['team_id']
            if is_home:
                if fixture['home_score'] > fixture['away_score']:
                    form_results.append("W")
                elif fixture['home_score'] < fixture['away_score']:
                    form_results.append("L")
                else:
                    form_results.append("D")
            else:
                if fixture['away_score'] > fixture['home_score']:
                    form_results.append("W")
                elif fixture['away_score'] < fixture['home_score']:
                    form_results.append("L")
                else:
                    form_results.append("D")
        
        embed.add_field(
            name="📈 Current Form (Last 5)",
            value=" - ".join(form_results),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(MatchCommands(bot))
