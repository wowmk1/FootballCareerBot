import discord
from discord.ext import commands
import asyncio
from database import db
from datetime import datetime
import random
import config
from utils.dice_roller import roll_d20, calculate_modifier, get_difficulty_class

class MatchEngine:
    def __init__(self, bot):
        self.bot = bot
        self.active_matches = {}
    
    def get_position_events(self, position):
        """Get event types based on player position"""
        position_events = {
            'ST': ['shoot', 'header', 'through_ball_receive', 'penalty_area_dribble'],
            'W': ['dribble', 'cross', 'shoot', 'cut_inside'],
            'CAM': ['through_ball', 'shoot', 'dribble', 'key_pass'],
            'CM': ['pass', 'through_ball', 'long_ball', 'tackle'],
            'CDM': ['tackle', 'interception', 'pass', 'block'],
            'FB': ['tackle', 'cross', 'overlap', 'clearance'],
            'CB': ['tackle', 'header', 'clearance', 'block'],
            'GK': ['save', 'claim_cross', 'distribution']
        }
        return position_events.get(position, ['pass', 'dribble', 'tackle'])
    
    def get_follow_up_event(self, action, success, position):
        """Determine follow-up event after an action"""
        if not success:
            return None
        
        follow_ups = {
            'dribble': {
                'ST': 'shoot',
                'W': ['shoot', 'cross'],
                'CAM': ['shoot', 'through_ball'],
                'CM': 'pass',
                'CDM': 'pass',
                'FB': 'cross',
                'CB': 'pass'
            },
            'tackle': {
                'CB': 'clearance',
                'FB': 'pass',
                'CDM': 'pass',
                'CM': 'through_ball'
            },
            'interception': {
                'CDM': 'pass',
                'CM': 'pass',
                'CB': 'pass'
            },
            'through_ball_receive': {
                'ST': 'shoot',
                'W': 'shoot'
            }
        }
        
        follow_up = follow_ups.get(action, {}).get(position)
        if isinstance(follow_up, list):
            return random.choice(follow_up)
        return follow_up
    
    def calculate_rating_change(self, action, success, roll, position):
        """Calculate rating change based on position-specific weights"""
        
        position_weights = {
            'ST': {'shoot': 2.0, 'header': 2.0, 'dribble': 1.0, 'pass': 0.5},
            'W': {'dribble': 2.0, 'shoot': 1.5, 'cross': 1.5, 'pass': 0.8},
            'CAM': {'through_ball': 2.0, 'pass': 1.5, 'shoot': 1.5, 'dribble': 1.2},
            'CM': {'pass': 2.0, 'through_ball': 1.5, 'tackle': 1.0, 'dribble': 1.0},
            'CDM': {'tackle': 2.0, 'interception': 2.0, 'pass': 1.2, 'block': 1.5},
            'FB': {'tackle': 1.5, 'cross': 1.5, 'pass': 1.2, 'overlap': 1.0},
            'CB': {'tackle': 2.0, 'header': 2.0, 'clearance': 1.8, 'block': 2.0},
            'GK': {'save': 3.0, 'claim_cross': 2.0, 'distribution': 1.0}
        }
        
        base_change = 0.2 if success else -0.1
        weight = position_weights.get(position, {}).get(action, 1.0)
        
        if roll == 20:
            base_change *= 2
        elif roll == 1:
            base_change = -0.4
        
        if action == 'shoot' and success:
            base_change = 1.5 * weight
        
        return base_change * weight
    
    def apply_form_to_stats(self, player):
        """Apply form modifier to player stats"""
        from utils.form_morale_system import get_form_modifier
        
        form_mod = get_form_modifier(player['form'])
        
        return {
            'pace': max(1, min(99, player['pace'] + form_mod)),
            'shooting': max(1, min(99, player['shooting'] + form_mod)),
            'passing': max(1, min(99, player['passing'] + form_mod)),
            'dribbling': max(1, min(99, player['dribbling'] + form_mod)),
            'defending': max(1, min(99, player['defending'] + form_mod)),
            'physical': max(1, min(99, player['physical'] + form_mod))
        }
    
    async def start_match(self, fixture: dict, interaction: discord.Interaction):
        """Start an interactive match"""
        
        home_team = await db.get_team(fixture['home_team_id'])
        away_team = await db.get_team(fixture['away_team_id'])
        
        guild = interaction.guild
        
        category = discord.utils.get(guild.categories, name="ACTIVE MATCHES")
        if not category:
            category = await guild.create_category("ACTIVE MATCHES")
        
        channel_name = f"week{fixture['week_number']}-{fixture['home_team_id']}-{fixture['away_team_id']}"
        channel_name = channel_name[:100].lower().replace(' ', '-')
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT user_id FROM players WHERE (team_id = $1 OR team_id = $2) AND retired = FALSE",
                fixture['home_team_id'], fixture['away_team_id']
            )
            player_users = [row['user_id'] for row in rows]
        
        for user_id in player_users:
            member = guild.get_member(user_id)
            if member:
                overwrites[member] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        match_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )
        
        num_events = random.randint(config.MATCH_EVENTS_PER_GAME_MIN, config.MATCH_EVENTS_PER_GAME_MAX)
        
        embed = discord.Embed(
            title="⚽ MATCH STARTING!",
            description=f"**{home_team['team_name']}** vs **{away_team['team_name']}**\n\n"
                       f"Week {fixture['week_number']} - {fixture['competition']}",
            color=discord.Color.green()
        )
        
        embed.add_field(name="🏠 Home", value=home_team['team_name'], inline=True)
        embed.add_field(name="✈️ Away", value=away_team['team_name'], inline=True)
        embed.add_field(name="📊 Events", value=f"{num_events} key moments", inline=True)
        
        # Show team crests if available
        from utils.football_data_api import get_team_crest_url
        home_crest = get_team_crest_url(fixture['home_team_id'])
        if home_crest:
            embed.set_thumbnail(url=home_crest)
        
        player_mentions = []
        for user_id in player_users:
            member = guild.get_member(user_id)
            if member:
                player_mentions.append(member.mention)
        
        if player_mentions:
            embed.add_field(
                name="👥 Players",
                value=" ".join(player_mentions),
                inline=False
            )
        
        embed.add_field(
            name="🎲 Match System",
            value="• Position-specific events\n• Sequential actions\n• D20 duels vs opponents\n• Form affects performance",
            inline=False
        )
        
        embed.set_footer(text="Match begins in 5 seconds...")
        
        await interaction.followup.send(
            f"✅ Match channel: {match_channel.mention}\n"
            f"🎮 {home_team['team_name']} vs {away_team['team_name']}",
            ephemeral=True
        )
        
        message = await match_channel.send(embed=embed)
        
        async with db.pool.acquire() as conn:
            result = await conn.fetchrow('''
                INSERT INTO active_matches (
                    fixture_id, home_team_id, away_team_id, channel_id, 
                    message_id, match_state, current_minute, last_event_time
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING match_id
            ''',
                fixture['fixture_id'],
                fixture['home_team_id'],
                fixture['away_team_id'],
                match_channel.id,
                message.id,
                'in_progress',
                0,
                datetime.now().isoformat()
            )
            match_id = result['match_id']
        
        for user_id in player_users:
            player = await db.get_player(user_id)
            if player:
                async with db.pool.acquire() as conn:
                    await conn.execute('''
                        INSERT INTO match_participants (match_id, user_id, team_id, match_rating)
                        VALUES ($1, $2, $3, $4)
                    ''', match_id, user_id, player['team_id'], 5.0)
        
        await asyncio.sleep(5)
        
        await self.run_match(match_id, fixture, match_channel, num_events)
    
    async def run_match(self, match_id: int, fixture: dict, channel: discord.TextChannel, num_events: int):
        """Run the full match simulation"""
        
        home_team = await db.get_team(fixture['home_team_id'])
        away_team = await db.get_team(fixture['away_team_id'])
        
        home_score = 0
        away_score = 0
        
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM match_participants WHERE match_id = $1",
                match_id
            )
            participants = [dict(row) for row in rows]
        
        home_participants = [p for p in participants if p['team_id'] == fixture['home_team_id']]
        away_participants = [p for p in participants if p['team_id'] == fixture['away_team_id']]
        
        possible_minutes = list(range(5, 91, 5))
        minutes = sorted(random.sample(possible_minutes, min(num_events, len(possible_minutes))))
        
        for i, minute in enumerate(minutes):
            event_num = i + 1
            
            embed = discord.Embed(
                title=f"⚽ Event {event_num}/{num_events} - Minute {minute}'",
                description=f"**{home_team['team_name']} {home_score} - {away_score} {away_team['team_name']}**",
                color=discord.Color.blue()
            )
            
            await channel.send(embed=embed)
            await asyncio.sleep(2)
            
            attacking_team = random.choice(['home', 'away'])
            
            if attacking_team == 'home':
                if home_participants:
                    participant = random.choice(home_participants)
                    player = await db.get_player(participant['user_id'])
                    
                    if player:
                        result = await self.handle_player_moment(
                            channel, player, participant, minute, 
                            home_team, away_team, True, match_id
                        )
                        
                        if result == 'goal':
                            home_score += 1
                else:
                    result = await self.handle_npc_moment(
                        channel, fixture['home_team_id'], minute, 
                        home_team, away_team, True
                    )
                    if result == 'goal':
                        home_score += 1
            else:
                if away_participants:
                    participant = random.choice(away_participants)
                    player = await db.get_player(participant['user_id'])
                    
                    if player:
                        result = await self.handle_player_moment(
                            channel, player, participant, minute,
                            away_team, home_team, False, match_id
                        )
                        
                        if result == 'goal':
                            away_score += 1
                else:
                    result = await self.handle_npc_moment(
                        channel, fixture['away_team_id'], minute,
                        away_team, home_team, False
                    )
                    if result == 'goal':
                        away_score += 1
            
            async with db.pool.acquire() as conn:
                await conn.execute('''
                    UPDATE active_matches 
                    SET home_score = $1, away_score = $2, current_minute = $3
                    WHERE match_id = $4
                ''', home_score, away_score, minute, match_id)
            
            await asyncio.sleep(3)
        
        await self.end_match(match_id, fixture, channel, home_score, away_score, participants)
    
    async def handle_player_moment(self, channel, player, participant, minute, attacking_team, defending_team, is_home, match_id):
        """Handle player's interactive moment with form-adjusted stats"""
        
        member = channel.guild.get_member(player['user_id'])
        if not member:
            return await self.auto_resolve_moment(player, minute, attacking_team, defending_team)
        
        # Apply form to stats
        adjusted_stats = self.apply_form_to_stats(player)
        
        # Get position-specific events
        available_actions = self.get_position_events(player['position'])
        
        # Get defender
        async with db.pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT * FROM npc_players WHERE team_id = $1 AND position IN ('CB', 'FB', 'CDM', 'GK') ORDER BY RANDOM() LIMIT 1",
                defending_team['team_id']
            )
            defender = dict(result) if result else None
        
        # Build embed
        from utils.form_morale_system import get_form_description
        form_desc = get_form_description(player['form'])
        
        embed = discord.Embed(
            title=f"🎯 {member.display_name}'s Moment!",
            description=f"**Minute {minute}'** | **{player['player_name']}** ({player['position']})\nForm: {form_desc}",
            color=discord.Color.gold()
        )
        
        if defender:
            embed.add_field(
                name="🛡️ Opponent",
                value=f"**{defender['player_name']}** ({defender['position']})\n"
                      f"DEF: {defender['defending']} | PHY: {defender['physical']}",
                inline=True
            )
        
        embed.add_field(
            name="📊 Your Stats (Form-Adjusted)",
            value=f"⚡ Pace: {adjusted_stats['pace']}\n"
                  f"🎯 Shooting: {adjusted_stats['shooting']}\n"
                  f"🎪 Passing: {adjusted_stats['passing']}\n"
                  f"🪄 Dribbling: {adjusted_stats['dribbling']}\n"
                  f"🛡️ Defending: {adjusted_stats['defending']}",
            inline=True
        )
        
        embed.add_field(
            name="⏱️ Time",
            value="**30 seconds** to choose!",
            inline=False
        )
        
        view = EnhancedActionView(available_actions, timeout=30)
        
        message = await channel.send(content=member.mention, embed=embed, view=view)
        
        await view.wait()
        
        action = view.chosen_action if view.chosen_action else random.choice(available_actions)
        
        if not view.chosen_action:
            await channel.send(f"⏰ {member.mention} auto: **{action.upper()}**")
        
        # Execute action with form-adjusted stats
        result = await self.execute_action_with_duel(
            channel, player, adjusted_stats, defender, action, minute, match_id
        )
        
        # Check for follow-up
        if result['success']:
            follow_up = self.get_follow_up_event(action, True, player['position'])
            if follow_up:
                await asyncio.sleep(2)
                follow_result = await self.execute_follow_up_action(
                    channel, player, adjusted_stats, defender, follow_up, minute, match_id, member
                )
                
                if follow_result == 'goal':
                    return 'goal'
        
        return 'goal' if result.get('goal') else None
    
    async def execute_action_with_duel(self, channel, player, adjusted_stats, defender, action, minute, match_id):
        """Execute action with NPC opponent rolling dice"""
        
        stat_map = {
            'shoot': adjusted_stats['shooting'],
            'pass': adjusted_stats['passing'],
            'dribble': adjusted_stats['dribbling'],
            'tackle': adjusted_stats['defending'],
            'header': adjusted_stats['physical'],
            'cross': adjusted_stats['passing'],
            'clearance': adjusted_stats['defending']
        }
        
        player_stat = stat_map.get(action, adjusted_stats['pace'])
        player_mod = calculate_modifier(player_stat)
        player_roll = roll_d20()
        player_total = player_roll + player_mod
        
        # Opponent rolls
        defender_roll = 0
        defender_total = 0
        dc = get_difficulty_class(action)
        
        if defender and action in ['dribble', 'shoot', 'header']:
            defender_roll = roll_d20()
            defender_mod = calculate_modifier(defender['defending'])
            defender_total = defender_roll + defender_mod
            dc = max(10, dc + (defender_mod - 5))
        
        success = player_total >= dc
        
        # Build result embed
        result_embed = discord.Embed(
            title=f"🎲 {action.upper()} - The Duel!",
            color=discord.Color.green() if success else discord.Color.red()
        )
        
        if defender and defender_total > 0:
            result_embed.add_field(
                name="⚔️ Dice Battle",
                value=f"**YOU**: {player_roll} + {player_mod} = **{player_total}**\n"
                      f"**{defender['player_name']}**: {defender_roll} + {calculate_modifier(defender['defending'])} = **{defender_total}**\n"
                      f"DC: {dc}",
                inline=False
            )
        else:
            result_embed.add_field(
                name="🎲 Your Roll",
                value=f"{player_roll} + {player_mod} = **{player_total}** vs DC {dc}",
                inline=False
            )
        
        # Determine outcome
        is_goal = False
        if action == 'shoot' and success:
            if player_roll == 20 or player_total >= dc + 5:
                result_embed.add_field(name="⚽ GOAL!", value=f"**{player['player_name']}** scores!", inline=False)
                is_goal = True
                
                async with db.pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE players SET season_goals = season_goals + 1, career_goals = career_goals + 1 WHERE user_id = $1",
                        player['user_id']
                    )
                
                # Morale boost for goal
                from utils.form_morale_system import update_player_morale
                await update_player_morale(player['user_id'], 'goal')
            else:
                result_embed.add_field(name="🧤 Saved!", value="Keeper denies it!", inline=False)
        elif success:
            result_embed.add_field(name="✅ Success!", value=f"Great {action}!", inline=False)
        else:
            result_embed.add_field(name="❌ Failed!", value=f"{action} unsuccessful", inline=False)
        
        await channel.send(embed=result_embed)
        
        # Update rating
        rating_change = self.calculate_rating_change(action, success, player_roll, player['position'])
        
        async with db.pool.acquire() as conn:
            await conn.execute('''
                UPDATE match_participants 
                SET match_rating = match_rating + $1, actions_taken = actions_taken + 1
                WHERE match_id = $2 AND user_id = $3
            ''', rating_change, match_id, player['user_id'])
        
        return {'success': success, 'goal': is_goal, 'roll': player_roll}
    
    async def execute_follow_up_action(self, channel, player, adjusted_stats, defender, action, minute, match_id, member):
        """Execute automatic follow-up action"""
        
        embed = discord.Embed(
            title=f"⚡ FOLLOW-UP: {action.upper()}!",
            description=f"**{player['player_name']}** continues!",
            color=discord.Color.orange()
        )
        
        await channel.send(embed=embed)
        await asyncio.sleep(1)
        
        result = await self.execute_action_with_duel(
            channel, player, adjusted_stats, defender, action, minute, match_id
        )
        
        return 'goal' if result.get('goal') else None
    
    async def handle_npc_moment(self, channel, team_id, minute, attacking_team, defending_team, is_home):
        """Handle NPC moment"""
        
        async with db.pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT * FROM npc_players WHERE team_id = $1 AND retired = FALSE ORDER BY RANDOM() LIMIT 1",
                team_id
            )
            npc = dict(result) if result else None
        
        if not npc:
            return None
        
        action = random.choice(['shoot', 'pass', 'dribble'])
        
        stat_map = {
            'shoot': npc['shooting'],
            'pass': npc['passing'],
            'dribble': npc['dribbling']
        }
        
        stat_value = stat_map[action]
        modifier = calculate_modifier(stat_value)
        dc = get_difficulty_class(action)
        
        roll = roll_d20()
        total = roll + modifier
        success = total >= dc
        
        outcome = None
        
        if action == 'shoot' and success and (roll == 20 or total >= dc + 5):
            embed = discord.Embed(
                title=f"⚽ NPC GOAL - Minute {minute}'",
                description=f"**{npc['player_name']}** scores for {attacking_team['team_name']}!",
                color=discord.Color.blue()
            )
            outcome = 'goal'
            
            async with db.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE npc_players SET season_goals = season_goals + 1 WHERE npc_id = $1",
                    npc['npc_id']
                )
        else:
            embed = discord.Embed(
                title=f"🤖 NPC Action - Minute {minute}'",
                description=f"**{npc['player_name']}** attempts {action}\nRoll: {roll} + {modifier} = {total}",
                color=discord.Color.blue()
            )
        
        await channel.send(embed=embed)
        return outcome
    
    async def end_match(self, match_id, fixture, channel, home_score, away_score, participants):
        """End match and update stats including form"""
        
        home_team = await db.get_team(fixture['home_team_id'])
        away_team = await db.get_team(fixture['away_team_id'])
        
        async with db.pool.acquire() as conn:
            await conn.execute('''
                UPDATE fixtures 
                SET home_score = $1, away_score = $2, played = TRUE, playable = FALSE
                WHERE fixture_id = $3
            ''', home_score, away_score, fixture['fixture_id'])
            
            await conn.execute('''
                UPDATE active_matches 
                SET match_state = $1, home_score = $2, away_score = $3
                WHERE match_id = $4
            ''', 'completed', home_score, away_score, match_id)
        
        await self.update_team_stats(fixture['home_team_id'], home_score, away_score)
        await self.update_team_stats(fixture['away_team_id'], away_score, home_score)
        
        embed = discord.Embed(
            title="🏁 FULL TIME!",
            description=f"**{home_team['team_name']} {home_score} - {away_score} {away_team['team_name']}**",
            color=discord.Color.gold()
        )
        
        # Update form and morale for participants
        from utils.form_morale_system import update_player_form, update_player_morale
        
        if participants:
            ratings_text = ""
            for p in participants:
                player = await db.get_player(p['user_id'])
                if player:
                    async with db.pool.acquire() as conn:
                        result = await conn.fetchrow(
                            "SELECT match_rating, actions_taken FROM match_participants WHERE match_id = $1 AND user_id = $2",
                            match_id, p['user_id']
                        )
                    
                    if result:
                        raw_rating = result['match_rating']
                        actions = result['actions_taken']
                        final_rating = max(0.0, min(10.0, raw_rating))
                        
                        # Update form
                        new_form = await update_player_form(p['user_id'], final_rating)
                        
                        # Update morale based on result
                        if player['team_id'] == fixture['home_team_id']:
                            if home_score > away_score:
                                await update_player_morale(p['user_id'], 'win')
                            elif home_score < away_score:
                                await update_player_morale(p['user_id'], 'loss')
                            else:
                                await update_player_morale(p['user_id'], 'draw')
                        else:
                            if away_score > home_score:
                                await update_player_morale(p['user_id'], 'win')
                            elif away_score < home_score:
                                await update_player_morale(p['user_id'], 'loss')
                            else:
                                await update_player_morale(p['user_id'], 'draw')
                        
                        # Update season stats
                        async with db.pool.acquire() as conn:
                            if player['season_apps'] > 0:
                                old_total = player['season_rating'] * player['season_apps']
                                new_total = old_total + final_rating
                                new_avg = new_total / (player['season_apps'] + 1)
                            else:
                                new_avg = final_rating
                            
                            await conn.execute("""
                                UPDATE players 
                                SET season_apps = season_apps + 1, 
                                    career_apps = career_apps + 1, 
                                    season_rating = $1 
                                WHERE user_id = $2
                            """, new_avg, p['user_id'])
                        
                        ratings_text += f"**{player['player_name']}**: {final_rating:.1f}/10 ({actions} actions)\n"
            
            if ratings_text:
                embed.add_field(name="⭐ Player Ratings", value=ratings_text, inline=False)
        
        embed.set_footer(text="Channel deletes in 60s")
        
        await channel.send(embed=embed)
        
        await db.add_news(
            f"{home_team['team_name']} {home_score}-{away_score} {away_team['team_name']}",
            f"FT Week {fixture['week_number']}",
            "match_news",
            None,
            3,
            fixture['week_number']
        )
        
        await asyncio.sleep(60)
        
        try:
            await channel.delete()
        except:
            pass
    
    async def update_team_stats(self, team_id, goals_for, goals_against):
        """Update team stats"""
        
        if goals_for > goals_against:
            won, drawn, lost, points = 1, 0, 0, 3
        elif goals_for == goals_against:
            won, drawn, lost, points = 0, 1, 0, 1
        else:
            won, drawn, lost, points = 0, 0, 1, 0
        
        async with db.pool.acquire() as conn:
            await conn.execute('''
                UPDATE teams SET
                played = played + 1,
                won = won + $1,
                drawn = drawn + $2,
                lost = lost + $3,
                goals_for = goals_for + $4,
                goals_against = goals_against + $5,
                points = points + $6
                WHERE team_id = $7
            ''', won, drawn, lost, goals_for, goals_against, points, team_id)
    
    async def auto_resolve_moment(self, player, minute, attacking_team, defending_team):
        """Auto-resolve when player unavailable"""
        return None

class EnhancedActionView(discord.ui.View):
    def __init__(self, available_actions, timeout=30):
        super().__init__(timeout=timeout)
        self.chosen_action = None
        
        emoji_map = {
            'shoot': '🎯',
            'pass': '🎪',
            'dribble': '🪄',
            'tackle': '🛡️',
            'header': '🗣️',
            'cross': '📐',
            'clearance': '🚀',
            'through_ball': '⚡',
            'save': '🧤'
        }
        
        for action in available_actions[:5]:
            button = ActionButton(action, emoji_map.get(action, '⚽'))
            self.add_item(button)
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

class ActionButton(discord.ui.Button):
    def __init__(self, action, emoji):
        super().__init__(
            label=action.replace('_', ' ').title(),
            emoji=emoji,
            style=discord.ButtonStyle.primary
        )
        self.action = action
    
    async def callback(self, interaction: discord.Interaction):
        self.chosen_action = self.action
        
        for item in self.view.children:
            item.disabled = True
        
        await interaction.response.edit_message(view=self.view)
        self.view.stop()

match_engine = None
