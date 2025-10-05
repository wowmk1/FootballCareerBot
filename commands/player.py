import discord
from discord import app_commands
from discord.ext import commands
from database import db
import random
from datetime import datetime
import config

class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="start", description="Create your football player and start your career!")
    @app_commands.describe(
        player_name="Your player's name (e.g., John Smith)",
        position="Your preferred position"
    )
    @app_commands.choices(position=[
        app_commands.Choice(name="⚽ Striker (ST)", value="ST"),
        app_commands.Choice(name="✨ Winger (W)", value="W"),
        app_commands.Choice(name="🎯 Attacking Midfielder (CAM)", value="CAM"),
        app_commands.Choice(name="⚙️ Central Midfielder (CM)", value="CM"),
        app_commands.Choice(name="🛡️ Defensive Midfielder (CDM)", value="CDM"),
        app_commands.Choice(name="🏃 Full Back (FB)", value="FB"),
        app_commands.Choice(name="💪 Center Back (CB)", value="CB"),
        app_commands.Choice(name="🧤 Goalkeeper (GK)", value="GK"),
    ])
    async def start(self, interaction: discord.Interaction, player_name: str, position: str):
        """Create a new player"""
        
        existing = await db.get_player(interaction.user.id)
        
        if existing:
            if existing['retired']:
                async with db.pool.acquire() as conn:
                    await conn.execute(
                        "DELETE FROM players WHERE user_id = $1",
                        interaction.user.id
                    )
            else:
                await interaction.response.send_message(
                    f"❌ You already have an active player: **{existing['player_name']}** ({existing['age']} years old)!\n\n"
                    f"💡 Players retire at age {config.RETIREMENT_AGE}. You can create a new player after retirement.",
                    ephemeral=True
                )
                return
        
        state = await db.get_game_state()
        current_week = state['current_week'] if state['season_started'] else 0
        
        if not state['season_started']:
            from utils.season_manager import start_season
            await start_season()
            current_week = 1
            
            await db.add_news(
                "⚽ Season 2027/28 Begins!",
                "The football season has officially started! 38 weeks of intense competition await.",
                "league_news",
                None,
                10,
                1
            )
        
        base_stats = {
            'pace': random.randint(55, 68),
            'shooting': random.randint(55, 68),
            'passing': random.randint(55, 68),
            'dribbling': random.randint(55, 68),
            'defending': random.randint(35, 50),
            'physical': random.randint(55, 68)
        }
        
        position_bonuses = {
            'ST': {'shooting': 8, 'physical': 5, 'pace': 3},
            'W': {'pace': 8, 'dribbling': 8, 'shooting': 3},
            'CAM': {'passing': 7, 'dribbling': 6, 'shooting': 4},
            'CM': {'passing': 8, 'physical': 5, 'defending': 3},
            'CDM': {'defending': 10, 'physical': 7, 'passing': 3},
            'FB': {'pace': 6, 'defending': 8, 'physical': 4},
            'CB': {'defending': 12, 'physical': 8, 'pace': -5},
            'GK': {'defending': 15, 'physical': 5, 'pace': -10}
        }
        
        if position in position_bonuses:
            for stat, bonus in position_bonuses[position].items():
                base_stats[stat] = max(35, min(99, base_stats[stat] + bonus))
        
        overall = sum(base_stats.values()) // 6
        potential = random.randint(overall + 12, overall + 28)
        
        async with db.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO players (
                    user_id, discord_username, player_name, position,
                    age, overall_rating, pace, shooting, passing, dribbling, defending, physical,
                    potential, team_id, league, joined_week
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            ''',
                interaction.user.id,
                str(interaction.user),
                player_name,
                position,
                config.STARTING_AGE,
                overall,
                base_stats['pace'],
                base_stats['shooting'],
                base_stats['passing'],
                base_stats['dribbling'],
                base_stats['defending'],
                base_stats['physical'],
                potential,
                'free_agent',
                None,
                current_week
            )
            
            await conn.execute('''
                INSERT INTO user_settings (user_id) 
                VALUES ($1) 
                ON CONFLICT (user_id) DO NOTHING
            ''', interaction.user.id)
        
        await db.add_news(
            f"New Talent: {player_name}",
            f"{player_name} ({position}) enters professional football at age {config.STARTING_AGE}. "
            f"Scouts rate potential at {potential} OVR.",
            "player_news",
            interaction.user.id,
            5,
            current_week
        )
        
        embed = discord.Embed(
            title="⚽ Welcome to Your Football Career!",
            description=f"**{player_name}** has been created!\n\n*\"Every legend starts somewhere...\"*",
            color=discord.Color.green()
        )
        
        embed.add_field(name="📋 Position", value=position, inline=True)
        embed.add_field(name="🎂 Age", value=f"{config.STARTING_AGE} years old", inline=True)
        embed.add_field(name="⭐ Overall", value=f"**{overall}** OVR", inline=True)
        
        embed.add_field(name="📊 Attributes", value=(
            f"⚡ Pace: **{base_stats['pace']}**\n"
            f"🎯 Shooting: **{base_stats['shooting']}**\n"
            f"🎪 Passing: **{base_stats['passing']}**\n"
            f"🪄 Dribbling: **{base_stats['dribbling']}**\n"
            f"🛡️ Defending: **{base_stats['defending']}**\n"
            f"💪 Physical: **{base_stats['physical']}**"
        ), inline=True)
        
        embed.add_field(name="🌟 Potential", value=f"**{potential}** OVR", inline=True)
        embed.add_field(name="🏠 Status", value="🆓 Free Agent", inline=True)
        
        if current_week == 1:
            season_info = f"🎉 **You started the season!**\nWeek 1/{config.SEASON_TOTAL_WEEKS}"
        else:
            season_info = f"📅 **Joined mid-season**\nCurrent: Week {current_week}/{config.SEASON_TOTAL_WEEKS}"
        
        embed.add_field(name="📅 Season Status", value=season_info, inline=False)
        
        embed.add_field(name="⏳ Career Length", value=(
            f"You'll play until age **{config.RETIREMENT_AGE}**\n"
            f"That's **{config.RETIREMENT_AGE - config.STARTING_AGE} years** to build your legacy!"
        ), inline=False)
        
        embed.add_field(name="💡 Next Steps", value=(
            "• `/train` - Train daily to improve\n"
            "• `/season` - Check current week & schedule\n"
            "• `/league` - View league tables\n"
            "• `/help` - See all commands"
        ), inline=False)
        
        embed.set_footer(text="Your journey begins now. Make it legendary! 🏆")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="profile", description="View your player stats and career info")
    @app_commands.describe(user="View another player's profile (optional)")
    async def profile(self, interaction: discord.Interaction, user: discord.User = None):
        """View player profile"""
        
        target_user = user or interaction.user
        player = await db.get_player(target_user.id)
        
        if not player:
            if user:
                await interaction.response.send_message(
                    f"❌ {user.mention} hasn't created a player yet!",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ You haven't created a player yet! Use `/start` to begin your career.",
                    ephemeral=True
                )
            return
        
        if player['retired']:
            embed = discord.Embed(
                title=f"🏆 {player['player_name']} (Retired Legend)",
                description=f"*Retired at age {player['age']} on {player['retirement_date'][:10]}*",
                color=discord.Color.gold()
            )
            
            embed.add_field(name="📋 Position", value=player['position'], inline=True)
            embed.add_field(name="🎂 Retirement Age", value=str(player['age']), inline=True)
            embed.add_field(name="⭐ Peak Rating", value=f"**{player['overall_rating']}** OVR", inline=True)
            
            embed.add_field(name="🏆 Career Legacy", value=(
                f"⚽ Goals: **{player['career_goals']}**\n"
                f"🅰️ Assists: **{player['career_assists']}**\n"
                f"👕 Appearances: **{player['career_apps']}**\n"
                f"⏳ Career span: **{player['age'] - config.STARTING_AGE} years**"
            ), inline=False)
            
            embed.set_footer(text="Use /start to create a new player!")
            
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"{'⭐ ' if user == interaction.user else ''}{player['player_name']}",
            color=discord.Color.blue() if user == interaction.user else discord.Color.greyple()
        )
        
        if player['team_id'] != 'free_agent':
            team = await db.get_team(player['team_id'])
            team_display = f"{team['team_name']} ({team['league']})" if team else player['team_id']
        else:
            team_display = '🆓 Free Agent'
        
        form_icons = min(5, player['form'] // 20)
        form_display = "🔥" * form_icons if form_icons > 0 else "❄️"
        
        years_left = config.RETIREMENT_AGE - player['age']
        
        embed.add_field(name="📋 Position", value=player['position'], inline=True)
        embed.add_field(name="🎂 Age", value=f"{player['age']} ({years_left}y left)", inline=True)
        embed.add_field(name="⭐ Overall", value=f"**{player['overall_rating']}** OVR", inline=True)
        
        embed.add_field(name="🏢 Club", value=team_display, inline=True)
        embed.add_field(name="🔥 Form", value=form_display, inline=True)
        embed.add_field(name="📅 Streak", value=f"{player['training_streak']} days", inline=True)
        
        embed.add_field(name="📊 Attributes", value=(
            f"⚡ Pace: **{player['pace']}**\n"
            f"🎯 Shooting: **{player['shooting']}**\n"
            f"🎪 Passing: **{player['passing']}**\n"
            f"🪄 Dribbling: **{player['dribbling']}**\n"
            f"🛡️ Defending: **{player['defending']}**\n"
            f"💪 Physical: **{player['physical']}**"
        ), inline=True)
        
        avg_rating = f"{player['season_rating']:.1f}" if player['season_apps'] > 0 else "N/A"
        embed.add_field(name="📈 This Season", value=(
            f"⚽ Goals: **{player['season_goals']}**\n"
            f"🅰️ Assists: **{player['season_assists']}**\n"
            f"👕 Apps: **{player['season_apps']}**\n"
            f"⭐ Avg: **{avg_rating}**"
        ), inline=True)
        
        embed.add_field(name="🏆 Career", value=(
            f"⚽ Goals: **{player['career_goals']}**\n"
            f"🅰️ Assists: **{player['career_assists']}**\n"
            f"👕 Apps: **{player['career_apps']}**"
        ), inline=True)
        
        if player['team_id'] != 'free_agent':
            embed.add_field(
                name="💼 Contract",
                value=f"💰 **£{player['contract_wage']:,}**/week\n⏳ **{player['contract_years']}** years left",
                inline=False
            )
        
        if player['injury_weeks'] and player['injury_weeks'] > 0:
            embed.add_field(
                name="🤕 Injury",
                value=f"**{player['injury_type']}** - Out for **{player['injury_weeks']} weeks**",
                inline=False
            )
        
        career_progress = ((player['age'] - config.STARTING_AGE) / (config.RETIREMENT_AGE - config.STARTING_AGE)) * 100
        progress_bar = self._create_progress_bar(career_progress)
        
        embed.add_field(
            name="⏳ Career Timeline",
            value=f"{progress_bar}\n{player['age']}/{config.RETIREMENT_AGE} years old ({int(career_progress)}% complete)",
            inline=False
        )
        
        state = await db.get_game_state()
        embed.add_field(
            name="📅 Season Info",
            value=f"Joined: Week {player['joined_week']}\nCurrent: Week {state['current_week']}/{config.SEASON_TOTAL_WEEKS}",
            inline=False
        )
        
        embed.set_footer(text=f"Potential: {player['potential']} OVR | Retires at {config.RETIREMENT_AGE}")
        
        await interaction.response.send_message(embed=embed)
    
    def _create_progress_bar(self, percentage: float, length: int = 20) -> str:
        """Create a visual progress bar"""
        filled = int((percentage / 100) * length)
        empty = length - filled
        return f"[{'█' * filled}{'░' * empty}]"
    
    @app_commands.command(name="compare", description="Compare your stats with another player")
    @app_commands.describe(user="Player to compare with")
    async def compare(self, interaction: discord.Interaction, user: discord.User):
        """Compare two players"""
        
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
        
        if player1['retired']:
            await interaction.response.send_message(
                "❌ Your player is retired! Use `/start` to create a new player.",
                ephemeral=True
            )
            return
        
        if player2['retired']:
            await interaction.response.send_message(
                f"❌ {user.mention}'s player is retired!",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="⚔️ Player Comparison",
            description=f"**{player1['player_name']}** vs **{player2['player_name']}**",
            color=discord.Color.orange()
        )
        
        def compare_stat(stat1, stat2):
            if stat1 > stat2:
                return f"**{stat1}** ✅", f"{stat2}"
            elif stat2 > stat1:
                return f"{stat1}", f"**{stat2}** ✅"
            else:
                return f"{stat1}", f"{stat2}"
        
        ovr1, ovr2 = compare_stat(player1['overall_rating'], player2['overall_rating'])
        embed.add_field(name="⭐ Overall", value=f"{ovr1} | {ovr2}", inline=False)
        
        embed.add_field(name="📋 Position", value=f"{player1['position']} | {player2['position']}", inline=True)
        age1, age2 = compare_stat(player2['age'], player1['age'])
        embed.add_field(name="🎂 Age", value=f"{age2} | {age1}", inline=True)
        
        pace1, pace2 = compare_stat(player1['pace'], player2['pace'])
        shoot1, shoot2 = compare_stat(player1['shooting'], player2['shooting'])
        pass1, pass2 = compare_stat(player1['passing'], player2['passing'])
        drib1, drib2 = compare_stat(player1['dribbling'], player2['dribbling'])
        def1, def2 = compare_stat(player1['defending'], player2['defending'])
        phys1, phys2 = compare_stat(player1['physical'], player2['physical'])
        
        embed.add_field(name="📊 Stats Comparison", value=(
            f"⚡ Pace: {pace1} | {pace2}\n"
            f"🎯 Shooting: {shoot1} | {shoot2}\n"
            f"🎪 Passing: {pass1} | {pass2}\n"
            f"🪄 Dribbling: {drib1} | {drib2}\n"
            f"🛡️ Defending: {def1} | {def2}\n"
            f"💪 Physical: {phys1} | {phys2}"
        ), inline=False)
        
        goals1, goals2 = compare_stat(player1['season_goals'], player2['season_goals'])
        assists1, assists2 = compare_stat(player1['season_assists'], player2['season_assists'])
        apps1, apps2 = compare_stat(player1['season_apps'], player2['season_apps'])
        
        embed.add_field(name="📈 This Season", value=(
            f"⚽ Goals: {goals1} | {goals2}\n"
            f"🅰️ Assists: {assists1} | {assists2}\n"
            f"👕 Apps: {apps1} | {apps2}"
        ), inline=True)
        
        cgoals1, cgoals2 = compare_stat(player1['career_goals'], player2['career_goals'])
        cassists1, cassists2 = compare_stat(player1['career_assists'], player2['career_assists'])
        capps1, capps2 = compare_stat(player1['career_apps'], player2['career_apps'])
        
        embed.add_field(name="🏆 Career", value=(
            f"⚽ Goals: {cgoals1} | {cgoals2}\n"
            f"🅰️ Assists: {cassists1} | {cassists2}\n"
            f"👕 Apps: {capps1} | {capps2}"
        ), inline=True)
        
        team1 = await db.get_team(player1['team_id']) if player1['team_id'] != 'free_agent' else None
        team2 = await db.get_team(player2['team_id']) if player2['team_id'] != 'free_agent' else None
        
        team1_name = team1['team_name'] if team1 else 'Free Agent'
        team2_name = team2['team_name'] if team2 else 'Free Agent'
        
        embed.add_field(name="🏢 Clubs", value=f"{team1_name} | {team2_name}", inline=False)
        
        embed.set_footer(text="✅ = Higher/Better stat")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PlayerCommands(bot))
