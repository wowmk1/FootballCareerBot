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
        # ✅ NEW: EUROPEAN COMPETITION STATS
        # ============================================
        async with db.pool.acquire() as conn:
            euro_stats = await conn.fetchrow("""
                SELECT 
                    SUM(appearances) as euro_apps, 
                    SUM(goals) as euro_goals, 
                    SUM(assists) as euro_assists
                FROM player_european_stats 
                WHERE user_id = $1
            """, target_user.id)
            
            in_competition = await conn.fetchval("""
                SELECT competition 
                FROM european_groups 
                WHERE team_id = $1 
                LIMIT 1
            """, player['team_id'])
        
        # Add European stats to embed if they exist
        if euro_stats and euro_stats['euro_apps'] and euro_stats['euro_apps'] > 0:
            comp_name = "Champions League" if in_competition == 'CL' else "Europa League" if in_competition == 'EL' else "European"
            embed.add_field(
                name=f"🏆 {comp_name} Stats",
                value=f"⚽ Goals: {euro_stats['euro_goals'] or 0}\n"
                      f"🅰️ Assists: {euro_stats['euro_assists'] or 0}\n"
                      f"👕 Apps: {euro_stats['euro_apps'] or 0}",
                inline=True
            )
        # ============================================
        
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
        
        # ============================================
        # ✅ NEW: TRAINING COOLDOWN INFO
        # ============================================
        from datetime import datetime, timedelta
        import config
        
        if player['last_training']:
            last_train = datetime.fromisoformat(player['last_training'])
            time_since = datetime.now() - last_train
            
            if time_since < timedelta(hours=config.TRAINING_COOLDOWN_HOURS):
                # Still on cooldown
                next_train = last_train + timedelta(hours=config.TRAINING_COOLDOWN_HOURS)
                time_until = next_train - datetime.now()
                
                hours_left = int(time_until.total_seconds() // 3600)
                minutes_left = int((time_until.total_seconds() % 3600) // 60)
                
                cooldown_text = f"⏰ Training available in **{hours_left}h {minutes_left}m**"
            else:
                # Ready to train
                cooldown_text = "✅ **TRAINING READY!** Use `/train`"
        else:
            cooldown_text = "✅ **TRAINING READY!** Use `/train`"
        
        embed.add_field(
            name="💪 Training Status",
            value=cooldown_text,
            inline=False
        )
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
        
        # Combine stats into fewer fields to stay under 25 field limit
        p1_stats = ""
        p2_stats = ""
        
        for stat, label in zip(stats, labels):
            p1_val = compare_stat(player1[stat], player2[stat])
            p2_val = compare_stat(player2[stat], player1[stat])
            p1_stats += f"**{label}:** {p1_val}\n"
            p2_stats += f"**{label}:** {p2_val}\n"
        
        embed.add_field(
            name=f"📊 Stats - {player1['player_name']}",
            value=p1_stats,
            inline=True
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)  # Spacer
        embed.add_field(
            name=f"📊 Stats - {player2['player_name']}",
            value=p2_stats,
            inline=True
        )
        
        # Season stats
        embed.add_field(
            name="⚽ Season Stats",
            value=f"**Goals:** {player1['season_goals']}\n"
                  f"**Assists:** {player1['season_assists']}\n"
                  f"**Apps:** {player1['season_apps']}",
            inline=True
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(
            name="⚽ Season Stats",
            value=f"**Goals:** {player2['season_goals']}\n"
                  f"**Assists:** {player2['season_assists']}\n"
                  f"**Apps:** {player2['season_apps']}",
            inline=True
        )
        
        # Add form comparison
        from utils.form_morale_system import get_form_description
        
        form1_desc = get_form_description(player1['form'])
        form2_desc = get_form_description(player2['form'])
        
        embed.add_field(
            name="📈 Current Form",
            value=f"{form1_desc} ({player1['form']})",
            inline=True
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(
            name="📈 Current Form",
            value=f"{form2_desc} ({player2['form']})",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="squad", description="View your team's squad")
    async def squad(self, interaction: discord.Interaction):
        """View your team's full squad"""
        
        await interaction.response.defer()
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.followup.send(
                "You haven't created a player yet! Use `/start` to begin.",
                ephemeral=True
            )
            return
        
        if player['retired']:
            await interaction.followup.send(
                "Your player has retired!",
                ephemeral=True
            )
            return
        
        if player['team_id'] == 'free_agent':
            await interaction.followup.send(
                "You're a free agent! Sign with a team to see their squad.",
                ephemeral=True
            )
            return
        
        # Get team info
        team = await db.get_team(player['team_id'])
        
        if not team:
            await interaction.followup.send(
                "Team not found!",
                ephemeral=True
            )
            return
        
        # Get all user players on this team
        async with db.pool.acquire() as conn:
            user_players = await conn.fetch("""
                SELECT player_name, position, overall_rating, age, user_id
                FROM players
                WHERE team_id = $1 AND retired = FALSE
                ORDER BY overall_rating DESC
            """, player['team_id'])
            
            # Get all NPC players on this team
            npc_players = await conn.fetch("""
                SELECT player_name, position, overall_rating, age
                FROM npc_players
                WHERE team_id = $1 AND retired = FALSE
                ORDER BY overall_rating DESC
            """, player['team_id'])
        
        # Combine all players
        all_players = []
        
        for p in user_players:
            all_players.append({
                'name': p['player_name'],
                'position': p['position'],
                'rating': p['overall_rating'],
                'age': p['age'],
                'is_user': True,
                'is_you': p['user_id'] == interaction.user.id
            })
        
        for p in npc_players:
            all_players.append({
                'name': p['player_name'],
                'position': p['position'],
                'rating': p['overall_rating'],
                'age': p['age'],
                'is_user': False,
                'is_you': False
            })
        
        # Sort by position order
        position_order = ['GK', 'CB', 'FB', 'CDM', 'CM', 'CAM', 'W', 'ST']
        all_players.sort(key=lambda x: (position_order.index(x['position']) if x['position'] in position_order else 99, -x['rating']))
        
        # Build embed
        embed = discord.Embed(
            title=f"{team['team_name']} Squad",
            description=f"**{team['league']}** • {len(all_players)} players",
            color=discord.Color.blue()
        )
        
        crest = get_team_crest_url(team['team_id'])
        if crest:
            embed.set_thumbnail(url=crest)
        
        # Group by position
        positions = {}
        for p in all_players:
            pos = p['position']
            if pos not in positions:
                positions[pos] = []
            positions[pos].append(p)
        
        # Display by position
        for pos in position_order:
            if pos not in positions:
                continue
            
            players_text = ""
            for p in positions[pos]:
                # Highlight user
                if p['is_you']:
                    marker = "👤 **YOU** • "
                elif p['is_user']:
                    marker = "👤 "
                else:
                    marker = ""
                
                players_text += f"{marker}{p['name']} - **{p['rating']}** OVR (Age {p['age']})\n"
            
            if players_text:
                # Position emoji
                pos_emoji = {
                    'GK': '🧤', 'CB': '🧱', 'FB': '🔙',
                    'CDM': '🛡️', 'CM': '⚙️', 'CAM': '🎯',
                    'W': '🏃', 'ST': '⚽'
                }
                
                embed.add_field(
                    name=f"{pos_emoji.get(pos, '⚽')} {pos}",
                    value=players_text,
                    inline=False
                )
        
        # Squad stats
        avg_rating = sum(p['rating'] for p in all_players) / len(all_players)
        avg_age = sum(p['age'] for p in all_players) / len(all_players)
        
        embed.add_field(
            name="📊 Squad Stats",
            value=f"**Avg Rating:** {avg_rating:.1f}\n"
                  f"**Avg Age:** {avg_age:.1f}\n"
                  f"**Total Players:** {len(all_players)}",
            inline=False
        )
        
        embed.set_footer(text="👤 = User-controlled player")
        
        await interaction.followup.send(embed=embed)

    # ============================================
    # ✅ NEW COMMAND: Enhanced Career Statistics Dashboard
    # ============================================
    @app_commands.command(name="career", description="View your complete career progression and statistics")
    async def career(self, interaction: discord.Interaction):
        """Enhanced career dashboard with progression tracking"""
        await interaction.response.defer()
        
        player = await db.get_player(interaction.user.id)
        if not player:
            await interaction.followup.send("❌ No player found!", ephemeral=True)
            return
        
        # Get season-by-season stats
        async with db.pool.acquire() as conn:
            # Career milestones
            milestones = []
            if player['career_goals'] >= 1:
                milestones.append(f"⚽ **{player['career_goals']}** Career Goals")
            if player['career_goals'] >= 50:
                milestones.append("🎯 50 Goal Club")
            if player['career_goals'] >= 100:
                milestones.append("🔥 Century Maker")
            
            if player['career_assists'] >= 30:
                milestones.append(f"🅰️ **{player['career_assists']}** Career Assists")
            
            if player['career_apps'] >= 100:
                milestones.append(f"👕 **{player['career_apps']}** Appearances")
            if player['career_apps'] >= 300:
                milestones.append("🏆 Club Legend Status")
            
            if player.get('career_motm', 0) >= 10:
                milestones.append(f"⭐ **{player['career_motm']}** MOTM Awards")
            
            if player['training_streak'] >= 30:
                milestones.append(f"💪 **{player['training_streak']}** Day Training Streak")
            
            # Transfer history
            transfers = await conn.fetch("""
                SELECT t.*, t1.team_name as from_team, t2.team_name as to_team
                FROM transfers t
                LEFT JOIN teams t1 ON t.from_team = t1.team_id
                LEFT JOIN teams t2 ON t.to_team = t2.team_id
                WHERE t.user_id = $1
                ORDER BY t.transfer_date DESC
                LIMIT 5
            """, player['user_id'])
            
            # ============================================
            # ✅ NEW: European career stats
            # ============================================
            euro_career = await conn.fetchrow("""
                SELECT 
                    SUM(appearances) as total_apps,
                    SUM(goals) as total_goals,
                    SUM(assists) as total_assists
                FROM player_european_stats
                WHERE user_id = $1
            """, player['user_id'])
            # ============================================
            
            # Rating progression (estimate)
            seasons_played = player['career_apps'] // 30
            starting_rating = player['overall_rating'] - (seasons_played * 2)  # Rough estimate
        
        import config
        
        embed = discord.Embed(
            title=f"📈 {player['player_name']} - Career Dashboard",
            description=f"**{player['position']}** • Age {player['age']} • {player['overall_rating']} OVR",
            color=discord.Color.blue()
        )
        
        # Career stats
        goals_per_game = player['career_goals'] / player['career_apps'] if player['career_apps'] > 0 else 0
        assists_per_game = player['career_assists'] / player['career_apps'] if player['career_apps'] > 0 else 0
        
        embed.add_field(
            name="📊 Career Statistics",
            value=f"⚽ **{player['career_goals']}** goals ({goals_per_game:.2f} per game)\n"
                  f"🅰️ **{player['career_assists']}** assists ({assists_per_game:.2f} per game)\n"
                  f"👕 **{player['career_apps']}** appearances\n"
                  f"⭐ **{player.get('career_motm', 0)}** MOTM awards",
            inline=False
        )
        
        # ============================================
        # ✅ NEW: European career statistics
        # ============================================
        if euro_career and euro_career['total_apps'] and euro_career['total_apps'] > 0:
            euro_goals_per_game = euro_career['total_goals'] / euro_career['total_apps'] if euro_career['total_apps'] > 0 else 0
            embed.add_field(
                name="🏆 European Career",
                value=f"⚽ **{euro_career['total_goals'] or 0}** goals ({euro_goals_per_game:.2f} per game)\n"
                      f"🅰️ **{euro_career['total_assists'] or 0}** assists\n"
                      f"👕 **{euro_career['total_apps']}** appearances",
                inline=False
            )
        # ============================================
        
        # Current season
        embed.add_field(
            name="🗓️ This Season",
            value=f"⚽ {player['season_goals']} goals\n"
                  f"🅰️ {player['season_assists']} assists\n"
                  f"👕 {player['season_apps']} apps\n"
                  f"⭐ {player.get('season_motm', 0)} MOTM",
            inline=True
        )
        
        # Peak years remaining
        years_left = config.RETIREMENT_AGE - player['age']
        peak_years = max(0, 30 - player['age'])
        
        embed.add_field(
            name="⏳ Career Timeline",
            value=f"**{years_left}** years until retirement\n"
                  f"**{peak_years}** peak years remaining\n"
                  f"Started: Age {starting_rating}",
            inline=True
        )
        
        # Progression
        improvement = player['overall_rating'] - starting_rating
        embed.add_field(
            name="📈 Development",
            value=f"**+{improvement}** OVR since debut\n"
                  f"Current: **{player['overall_rating']}** OVR\n"
                  f"Potential: ⭐ **{player['potential']}** POT\n"
                  f"**{player['potential'] - player['overall_rating']}** OVR to reach peak",
            inline=False
        )
        
        # Transfer history
        if transfers:
            transfer_text = ""
            for t in transfers:
                from_name = t['from_team'] or 'Free Agent'
                to_name = t['to_team'] or 'Unknown'
                fee_str = f"£{t['fee']:,}" if t['fee'] > 0 else "Free"
                transfer_text += f"• {from_name} → {to_name} ({fee_str})\n"
            
            embed.add_field(
                name="💼 Transfer History",
                value=transfer_text[:1024],  # Discord limit
                inline=False
            )
        
        # Milestones
        if milestones:
            embed.add_field(
                name="🏅 Career Milestones",
                value="\n".join(milestones[:10]),
                inline=False
            )
        
        # Team crest
        from utils.football_data_api import get_team_crest_url
        crest = get_team_crest_url(player['team_id'])
        if crest:
            embed.set_thumbnail(url=crest)
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PlayerCommands(bot))
