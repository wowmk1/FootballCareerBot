import discord
from discord import ui
import random
from datetime import datetime
from database import db
from utils.dice_roller import dice_roller
import config
import asyncio

class MatchActionView(ui.View):
    """Discord UI buttons for match actions"""
    
    def __init__(self, match_engine, event_data, timeout=10):
        super().__init__(timeout=timeout)
        self.match_engine = match_engine
        self.event_data = event_data
        self.responded = False
        self.selected_action = None
    
    @ui.button(label="🥅 Shoot", style=discord.ButtonStyle.danger, custom_id="shoot")
    async def shoot_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_action(interaction, config.ACTION_SHOOT)
    
    @ui.button(label="👟 Pass", style=discord.ButtonStyle.primary, custom_id="pass")
    async def pass_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_action(interaction, config.ACTION_PASS)
    
    @ui.button(label="🏃 Dribble", style=discord.ButtonStyle.success, custom_id="dribble")
    async def dribble_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_action(interaction, config.ACTION_DRIBBLE)
    
    async def handle_action(self, interaction: discord.Interaction, action):
        """Handle player's action selection"""
        if interaction.user.id != self.event_data['user_id']:
            await interaction.response.send_message(
                "❌ This isn't your moment!",
                ephemeral=True
            )
            return
        
        if self.responded:
            await interaction.response.send_message(
                "⚠️ Already responded!",
                ephemeral=True
            )
            return
        
        self.responded = True
        self.selected_action = action
        self.stop()
        
        await interaction.response.defer()
    
    async def on_timeout(self):
        """Auto-roll if player doesn't respond"""
        if not self.responded:
            position = self.event_data.get('position', 'ST')
            if position in ['ST', 'W']:
                self.selected_action = config.ACTION_SHOOT
            elif position in ['CAM', 'CM']:
                self.selected_action = config.ACTION_PASS
            else:
                self.selected_action = random.choice([config.ACTION_SHOOT, config.ACTION_PASS, config.ACTION_DRIBBLE])


class MatchEngine:
    """Handles interactive DnD-style match gameplay"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_matches = {}
    
    async def start_interactive_match(self, fixture_id, guild, announcement_channel):
        """Start an interactive match in a Discord guild"""
        
        async with db.db.execute(
            "SELECT * FROM fixtures WHERE fixture_id = ?",
            (fixture_id,)
        ) as cursor:
            fixture = dict(await cursor.fetchone())
        
        if not fixture or fixture['played']:
            return None
        
        home_team = await db.get_team(fixture['home_team_id'])
        away_team = await db.get_team(fixture['away_team_id'])
        
        # Get user players in these teams
        async with db.db.execute("""
            SELECT user_id, player_name, position, overall_rating, pace, shooting, passing, dribbling, defending, physical
            FROM players 
            WHERE (team_id = ? OR team_id = ?) AND retired = 0
        """, (fixture['home_team_id'], fixture['away_team_id'])) as cursor:
            rows = await cursor.fetchall()
            participants = [dict(row) for row in rows]
        
        if not participants:
            return None
        
        # Create match channel
        category = discord.utils.get(guild.categories, name="ACTIVE MATCHES")
        if not category:
            category = await guild.create_category("ACTIVE MATCHES")
        
        channel_name = f"week{fixture['week_number']}-{home_team['team_name'][:10].lower().replace(' ', '')}-vs-{away_team['team_name'][:10].lower().replace(' ', '')}"
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False)
        }
        
        for participant in participants:
            member = guild.get_member(participant['user_id'])
            if member:
                overwrites[member] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        match_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )
        
        # Create active match record
        await db.db.execute('''
            INSERT INTO active_matches (
                fixture_id, home_team_id, away_team_id, channel_id, match_state
            ) VALUES (?, ?, ?, ?, 'waiting')
        ''', (fixture_id, fixture['home_team_id'], fixture['away_team_id'], match_channel.id))
        await db.db.commit()
        
        async with db.db.execute(
            "SELECT match_id FROM active_matches WHERE fixture_id = ?",
            (fixture_id,)
        ) as cursor:
            match_id = (await cursor.fetchone())['match_id']
        
        # Add participants
        for participant in participants:
            player = await db.get_player(participant['user_id'])
            await db.db.execute('''
                INSERT INTO match_participants (match_id, user_id, team_id, joined)
                VALUES (?, ?, ?, 1)
            ''', (match_id, participant['user_id'], player['team_id']))
        await db.db.commit()
        
        # Send match start embed in announcement channel
        embed = discord.Embed(
            title="⚽ MATCH STARTING!",
            description=f"**{home_team['team_name']}** vs **{away_team['team_name']}**",
            color=discord.Color.green()
        )
        
        embed.add_field(name="📺 Watch Live", value=f"Match happening in {match_channel.mention}!", inline=False)
        embed.add_field(name="👥 Players", value=", ".join([f"<@{p['user_id']}>" for p in participants]), inline=False)
        
        await announcement_channel.send(embed=embed)
        
        # Send welcome in match channel
        welcome_embed = discord.Embed(
            title="⚽ LIVE MATCH STARTING!",
            description=f"**{home_team['team_name']}** vs **{away_team['team_name']}**",
            color=discord.Color.green()
        )
        
        welcome_embed.add_field(name="🏟️ Competition", value=fixture['competition'], inline=True)
        welcome_embed.add_field(name="📅 Week", value=str(fixture['week_number']), inline=True)
        welcome_embed.add_field(name="👥 Players", value=f"{len(participants)} active", inline=True)
        
        welcome_embed.add_field(
            name="🎮 How It Works",
            value=(
                "• You'll face **key moments** during the match\n"
                "• Choose actions with buttons in **10 seconds**\n"
                "• Roll d20 + your stats vs DC\n"
                "• Affect the score with your decisions!"
            ),
            inline=False
        )
        
        welcome_embed.set_footer(text="Match begins in 10 seconds...")
        
        await match_channel.send(" ".join([f"<@{p['user_id']}>" for p in participants]))
        await match_channel.send(embed=welcome_embed)
        await asyncio.sleep(10)
        
        # Update match state
        await db.db.execute(
            "UPDATE active_matches SET match_state = 'active' WHERE match_id = ?",
            (match_id,)
        )
        await db.db.commit()
        
        # Run the match
        await self.run_match_events(match_id, match_channel, participants, home_team, away_team)
        
        return match_id
    
    async def run_match_events(self, match_id, channel, participants, home_team, away_team):
        """Run through all match events"""
        
        total_events = config.MATCH_EVENTS_PER_GAME
        home_score = 0
        away_score = 0
        
        for event_num in range(1, total_events + 1):
            minute = (event_num * 90) // total_events
            
            participant_data = random.choice(participants)
            player = await db.get_player(participant_data['user_id'])
            player_team = await db.get_team(player['team_id'])
            
            is_home = player['team_id'] == home_team['team_id']
            opponent_team = away_team if is_home else home_team
            
            situation = {
                'in_box': random.random() > 0.5,
                'under_pressure': random.random() > 0.6,
                'crowded': random.random() > 0.7,
                'one_on_one': random.random() > 0.8
            }
            
            event_embed = discord.Embed(
                title=f"⚽ {minute}' - KEY MOMENT!",
                description=f"**{player['player_name']}** ({player_team['team_name']})",
                color=discord.Color.gold()
            )
            
            situation_text = []
            if situation['in_box']:
                situation_text.append("🎯 In the box!")
            if situation['one_on_one']:
                situation_text.append("👤 One-on-one with keeper!")
            if situation['crowded']:
                situation_text.append("🧍🧍🧍 Crowded area")
            if situation['under_pressure']:
                situation_text.append("⚡ Under pressure")
            
            if not situation_text:
                situation_text.append("⚽ Standard situation")
            
            event_embed.add_field(
                name="📊 Situation",
                value="\n".join(situation_text),
                inline=False
            )
            
            event_embed.add_field(
                name="📊 Current Score",
                value=f"**{home_team['team_name']} {home_score} - {away_score} {away_team['team_name']}**",
                inline=False
            )
            
            event_embed.set_footer(text=f"⏱️ {config.AUTO_ROLL_TIMEOUT} seconds to decide...")
            
            view = MatchActionView(
                self, 
                {
                    'user_id': participant_data['user_id'],
                    'position': player['position']
                },
                timeout=config.AUTO_ROLL_TIMEOUT
            )
            
            message = await channel.send(
                content=f"<@{participant_data['user_id']}> Your moment!",
                embed=event_embed,
                view=view
            )
            
            await view.wait()
            
            selected_action = view.selected_action
            
            stat_map = {
                config.ACTION_SHOOT: player['shooting'],
                config.ACTION_PASS: player['passing'],
                config.ACTION_DRIBBLE: player['dribbling']
            }
            
            stat_value = stat_map[selected_action]
            
            dc = dice_roller.determine_difficulty(selected_action, situation)
            
            roll_result = dice_roller.make_check(stat_value, dc)
            
            action_text = {
                config.ACTION_SHOOT: "shoots",
                config.ACTION_PASS: "passes",
                config.ACTION_DRIBBLE: "dribbles"
            }
            
            result_embed = discord.Embed(
                title=f"⚽ {minute}' - {player['player_name']} {action_text[selected_action]}!",
                color=discord.Color.green() if roll_result['success'] else discord.Color.red()
            )
            
            result_text = dice_roller.format_roll_result(roll_result, "")
            result_embed.add_field(name="🎲 Roll Result", value=result_text, inline=False)
            
            if selected_action == config.ACTION_SHOOT and roll_result['success']:
                if is_home:
                    home_score += 1
                else:
                    away_score += 1
                
                if roll_result['critical_success']:
                    result_embed.add_field(
                        name="⚽ GOOOAL!",
                        value=f"🌟 **SPECTACULAR GOAL!** What a finish!\n\n**{home_team['team_name']} {home_score} - {away_score} {away_team['team_name']}**",
                        inline=False
                    )
                else:
                    result_embed.add_field(
                        name="⚽ GOAL!",
                        value=f"**{player['player_name']}** scores!\n\n**{home_team['team_name']} {home_score} - {away_score} {away_team['team_name']}**",
                        inline=False
                    )
                
                await db.db.execute('''
                    UPDATE match_participants 
                    SET goals_scored = goals_scored + 1, match_rating = match_rating + 1.5
                    WHERE match_id = ? AND user_id = ?
                ''', (match_id, participant_data['user_id']))
                
            elif selected_action == config.ACTION_PASS and roll_result['success']:
                result_embed.add_field(
                    name="✅ Great Pass!",
                    value=f"Perfect ball from **{player['player_name']}**!",
                    inline=False
                )
                
                await db.db.execute('''
                    UPDATE match_participants 
                    SET match_rating = match_rating + 0.3
                    WHERE match_id = ? AND user_id = ?
                ''', (match_id, participant_data['user_id']))
                
            elif selected_action == config.ACTION_DRIBBLE and roll_result['success']:
                result_embed.add_field(
                    name="🏃 Brilliant Dribble!",
                    value=f"**{player['player_name']}** beats the defender!",
                    inline=False
                )
                
                await db.db.execute('''
                    UPDATE match_participants 
                    SET match_rating = match_rating + 0.5
                    WHERE match_id = ? AND user_id = ?
                ''', (match_id, participant_data['user_id']))
                
            else:
                if roll_result['critical_failure']:
                    result_embed.add_field(
                        name="💥 Disaster!",
                        value=f"**{player['player_name']}** loses the ball completely!",
                        inline=False
                    )
                    
                    await db.db.execute('''
                        UPDATE match_participants 
                        SET match_rating = match_rating - 0.5
                        WHERE match_id = ? AND user_id = ?
                    ''', (match_id, participant_data['user_id']))
                else:
                    result_embed.add_field(
                        name="❌ Action Failed",
                        value=f"**{opponent_team['team_name']}** defends well.",
                        inline=False
                    )
                    
                    await db.db.execute('''
                        UPDATE match_participants 
                        SET match_rating = match_rating - 0.2
                        WHERE match_id = ? AND user_id = ?
                    ''', (match_id, participant_data['user_id']))
            
            await db.db.execute('''
                UPDATE match_participants 
                SET actions_taken = actions_taken + 1
                WHERE match_id = ? AND user_id = ?
            ''', (match_id, participant_data['user_id']))
            
            await db.db.execute(
                "UPDATE active_matches SET home_score = ?, away_score = ?, current_minute = ?, events_completed = ? WHERE match_id = ?",
                (home_score, away_score, minute, event_num, match_id)
            )
            
            await db.db.commit()
            
            await channel.send(embed=result_embed)
            await asyncio.sleep(3)
        
        await self.finish_match(match_id, channel, home_team, away_team, home_score, away_score)
    
    async def finish_match(self, match_id, channel, home_team, away_team, home_score, away_score):
        """Finish the match and update all stats"""
        
        async with db.db.execute(
            "SELECT fixture_id FROM active_matches WHERE match_id = ?",
            (match_id,)
        ) as cursor:
            fixture_id = (await cursor.fetchone())['fixture_id']
        
        await db.db.execute('''
            UPDATE fixtures 
            SET home_score = ?, away_score = ?, played = 1, playable = 0
            WHERE fixture_id = ?
        ''', (home_score, away_score, fixture_id))
        
        from utils.match_simulator import update_team_stats
        await update_team_stats(home_team['team_id'], home_score, away_score, True)
        await update_team_stats(away_team['team_id'], away_score, home_score, False)
        
        async with db.db.execute("""
            SELECT mp.*, p.player_name, p.user_id
            FROM match_participants mp
            JOIN players p ON mp.user_id = p.user_id
            WHERE mp.match_id = ?
        """, (match_id,)) as cursor:
            rows = await cursor.fetchall()
            participants = [dict(row) for row in rows]
        
        for participant in participants:
            rating = participant['match_rating']
            
            await db.db.execute('''
                UPDATE players SET
                season_goals = season_goals + ?,
                season_assists = season_assists + ?,
                season_apps = season_apps + 1,
                season_rating = CASE 
                    WHEN season_apps = 0 THEN ?
                    ELSE ((season_rating * season_apps) + ?) / (season_apps + 1)
                END,
                career_goals = career_goals + ?,
                career_assists = career_assists + ?,
                career_apps = career_apps + 1
                WHERE user_id = ?
            ''', (
                participant['goals_scored'],
                participant['assists'],
                rating,
                rating,
                participant['goals_scored'],
                participant['assists'],
                participant['user_id']
            ))
        
        await db.db.commit()
        
        final_embed = discord.Embed(
            title="🏁 FULL TIME!",
            description=f"**{home_team['team_name']} {home_score} - {away_score} {away_team['team_name']}**",
            color=discord.Color.blue()
        )
        
        if home_score > away_score:
            result_text = f"🏆 **{home_team['team_name']} WIN!**"
        elif away_score > home_score:
            result_text = f"🏆 **{away_team['team_name']} WIN!**"
        else:
            result_text = "🤝 **DRAW!**"
        
        final_embed.add_field(name="Result", value=result_text, inline=False)
        
        ratings_text = "**Player Ratings:**\n\n"
        for participant in participants:
            rating = min(10.0, max(1.0, participant['match_rating']))
            
            if rating >= 8.5:
                rating_emoji = "🌟"
            elif rating >= 7.5:
                rating_emoji = "⭐"
            elif rating >= 6.5:
                rating_emoji = "✅"
            elif rating >= 5.0:
                rating_emoji = "➖"
            else:
                rating_emoji = "❌"
            
            stats_line = f"{rating_emoji} **{participant['player_name']}**: {rating:.1f}"
            
            if participant['goals_scored'] > 0:
                stats_line += f" ⚽x{participant['goals_scored']}"
            if participant['assists'] > 0:
                stats_line += f" 🅰️x{participant['assists']}"
            
            stats_line += f" ({participant['actions_taken']} actions)\n"
            ratings_text += stats_line
        
        final_embed.add_field(name="📊 Performance", value=ratings_text, inline=False)
        
        best_participant = max(participants, key=lambda p: p['match_rating'])
        final_embed.add_field(
            name="🏅 Man of the Match",
            value=f"**{best_participant['player_name']}** - {best_participant['match_rating']:.1f} rating!",
            inline=False
        )
        
        final_embed.set_footer(text="Match complete! Channel will be deleted in 60 seconds.")
        
        await channel.send(embed=final_embed)
        
        for participant in participants:
            if participant['goals_scored'] > 0:
                await db.add_news(
                    f"{participant['player_name']} Scores!",
                    f"{participant['player_name']} scored {participant['goals_scored']} goal(s) in the {home_score}-{away_score} result.",
                    "match_news",
                    participant['user_id'],
                    8
                )
        
        await db.db.execute("DELETE FROM active_matches WHERE match_id = ?", (match_id,))
        await db.db.execute("DELETE FROM match_participants WHERE match_id = ?", (match_id,))
        await db.db.commit()
        
        await asyncio.sleep(60)
        await channel.delete()

match_engine = None
