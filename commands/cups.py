"""
Cup Competition Commands
Handles FA Cup, League Cup, and European competitions
"""
import discord
from discord import app_commands
from discord.ext import commands
from database import db
from utils.football_data_api import get_team_crest_url, get_competition_logo


class CupCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="cups", description="View all cup competitions and your team's status")
    async def cups(self, interaction: discord.Interaction):
        """Display all cup competitions and player's team status"""
        
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
        
        embed = discord.Embed(
            title="🏆 Cup Competitions",
            description=f"**Season {state['current_season']}** • Week {state['current_week']}",
            color=discord.Color.gold()
        )
        
        # Get all cup competitions
        async with db.pool.acquire() as conn:
            competitions = await conn.fetch("""
                SELECT * FROM cup_competitions 
                WHERE season = $1
                ORDER BY competition_type
            """, state['current_season'])
        
        if not competitions:
            embed.add_field(
                name="⚠️ No Competitions",
                value="Cup competitions will be initialized at the start of the season.",
                inline=False
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Check if player's team is in any cups
        if player['team_id'] != 'free_agent':
            team = await db.get_team(player['team_id'])
            
            for comp in competitions:
                comp_dict = dict(comp)
                
                # Check if team has fixtures in this competition
                async with db.pool.acquire() as conn:
                    team_fixtures = await conn.fetch("""
                        SELECT * FROM cup_fixtures
                        WHERE competition_id = $1
                        AND (home_team_id = $2 OR away_team_id = $2)
                        ORDER BY played DESC, fixture_id ASC
                    """, comp_dict['competition_id'], player['team_id'])
                
                cup_emoji = {
                    'fa_cup': '🏆',
                    'league_cup': '🥇',
                    'europa': '🌍',
                    'champions': '⭐'
                }.get(comp_dict['competition_type'], '🏆')
                
                if team_fixtures:
                    # Team is in this competition
                    fixtures_list = [dict(f) for f in team_fixtures]
                    
                    # Get last result
                    played_fixtures = [f for f in fixtures_list if f['played']]
                    unplayed_fixtures = [f for f in fixtures_list if not f['played']]
                    
                    status_text = f"**Current Round:** {comp_dict['current_round']}\n"
                    
                    if played_fixtures:
                        last_match = played_fixtures[0]
                        is_home = last_match['home_team_id'] == player['team_id']
                        
                        if is_home:
                            score_text = f"{last_match['home_score']} - {last_match['away_score']}"
                            opponent = await db.get_team(last_match['away_team_id'])
                        else:
                            score_text = f"{last_match['away_score']} - {last_match['home_score']}"
                            opponent = await db.get_team(last_match['home_team_id'])
                        
                        opponent_name = opponent['team_name'] if opponent else "Unknown"
                        
                        if last_match['winner_team_id'] == player['team_id']:
                            result_emoji = "✅"
                        elif last_match['winner_team_id']:
                            result_emoji = "❌"
                        else:
                            result_emoji = "🟰"
                        
                        status_text += f"**Last Result:** {result_emoji} {score_text} vs {opponent_name}\n"
                    
                    if unplayed_fixtures:
                        next_match = unplayed_fixtures[0]
                        is_home = next_match['home_team_id'] == player['team_id']
                        opponent = await db.get_team(
                            next_match['away_team_id'] if is_home else next_match['home_team_id']
                        )
                        opponent_name = opponent['team_name'] if opponent else "Unknown"
                        venue = "🏠 Home" if is_home else "✈️ Away"
                        
                        if next_match['playable']:
                            status_text += f"**Next Match:** {venue} vs {opponent_name} 🟢 **PLAYABLE NOW**"
                        else:
                            status_text += f"**Next Match:** {venue} vs {opponent_name}"
                    else:
                        if comp_dict['is_active']:
                            status_text += "*Waiting for next round...*"
                        else:
                            status_text += "*✅ Competition Complete*"
                    
                    embed.add_field(
                        name=f"{cup_emoji} {comp_dict['competition_name']}",
                        value=status_text,
                        inline=False
                    )
                else:
                    # Team not in this competition
                    if comp_dict['competition_type'] in ['europa', 'champions']:
                        embed.add_field(
                            name=f"{cup_emoji} {comp_dict['competition_name']}",
                            value="*Team did not qualify*",
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name=f"{cup_emoji} {comp_dict['competition_name']}",
                            value=f"**Round:** {comp_dict['current_round']}\n*Team eliminated or not entered*",
                            inline=False
                        )
        
        embed.add_field(
            name="📋 Commands",
            value="`/cup_fixtures` - View your cup matches\n`/play_match` - Play cup matches when available",
            inline=False
        )
        
        embed.set_footer(text="Cup matches alternate with league matches")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="cup_fixtures", description="View your team's upcoming cup fixtures")
    async def cup_fixtures(self, interaction: discord.Interaction):
        """Display player's team cup fixtures"""
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet!",
                ephemeral=True
            )
            return
        
        if player['team_id'] == 'free_agent':
            await interaction.response.send_message(
                "❌ You're a free agent! Sign with a team to see cup fixtures.",
                ephemeral=True
            )
            return
        
        team = await db.get_team(player['team_id'])
        
        # Get all cup fixtures for this team
        async with db.pool.acquire() as conn:
            fixtures = await conn.fetch("""
                SELECT cf.*, cc.competition_name, cc.competition_type
                FROM cup_fixtures cf
                JOIN cup_competitions cc ON cf.competition_id = cc.competition_id
                WHERE (cf.home_team_id = $1 OR cf.away_team_id = $1)
                ORDER BY cf.played ASC, cf.fixture_id ASC
                LIMIT 10
            """, player['team_id'])
        
        if not fixtures:
            await interaction.response.send_message(
                "📭 Your team has no cup fixtures scheduled yet.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"🏆 {team['team_name']} - Cup Fixtures",
            description=f"Upcoming cup matches for {player['player_name']}",
            color=discord.Color.gold()
        )
        
        team_crest = get_team_crest_url(player['team_id'])
        if team_crest:
            embed.set_thumbnail(url=team_crest)
        
        for fixture in fixtures[:8]:
            fixture = dict(fixture)
            
            is_home = fixture['home_team_id'] == player['team_id']
            opponent_id = fixture['away_team_id'] if is_home else fixture['home_team_id']
            opponent = await db.get_team(opponent_id)
            opponent_name = opponent['team_name'] if opponent else opponent_id
            
            venue = "🏠 Home" if is_home else "✈️ Away"
            
            cup_emoji = {
                'fa_cup': '🏆',
                'league_cup': '🥇',
                'europa': '🌍',
                'champions': '⭐'
            }.get(fixture['competition_type'], '🏆')
            
            if fixture['played']:
                if is_home:
                    score = f"{fixture['home_score']} - {fixture['away_score']}"
                else:
                    score = f"{fixture['away_score']} - {fixture['home_score']}"
                
                if fixture['winner_team_id'] == player['team_id']:
                    result = "✅ Won"
                elif fixture['winner_team_id']:
                    result = "❌ Lost"
                else:
                    result = "🟰 Draw"
                
                if fixture['is_two_legged']:
                    leg_text = f"Leg {fixture['leg_number']}/2"
                    if fixture['leg_number'] == 2:
                        agg_text = f"\nAggregate: {fixture['aggregate_home']} - {fixture['aggregate_away']}"
                    else:
                        agg_text = ""
                else:
                    leg_text = ""
                    agg_text = ""
                
                embed.add_field(
                    name=f"{cup_emoji} {fixture['competition_name']} - {fixture['round']} {leg_text}",
                    value=f"{venue} vs **{opponent_name}**\n{result}: {score}{agg_text}",
                    inline=False
                )
            else:
                status = "🟢 **PLAYABLE NOW**" if fixture['playable'] else "⏰ Upcoming"
                
                if fixture['is_two_legged']:
                    leg_text = f" (Leg {fixture['leg_number']}/2)"
                else:
                    leg_text = ""
                
                embed.add_field(
                    name=f"{cup_emoji} {fixture['competition_name']} - {fixture['round']}{leg_text}",
                    value=f"{venue} vs **{opponent_name}**\n{status}",
                    inline=False
                )
        
        embed.set_footer(text="Use /play_match to play when matches are available")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="cup_standings", description="View cup group standings (if applicable)")
    async def cup_standings(self, interaction: discord.Interaction):
        """Display cup group standings (for group stage competitions)"""
        
        # For now, this is a placeholder since we don't have group stages implemented
        # This would be used for Champions League/Europa League group stages
        
        embed = discord.Embed(
            title="🏆 Cup Standings",
            description="Group stages not yet implemented.\n\nCurrently only knockout competitions are available:\n"
                       "• FA Cup (knockout)\n• League Cup (knockout)",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="📋 Available Commands",
            value="`/cups` - View all competitions\n`/cup_fixtures` - View your fixtures",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(CupCommands(bot))
