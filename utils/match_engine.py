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
        
        embed = discord.Embed(
            title="⚽ MATCH STARTING!",
            description=f"**{home_team['team_name']}** vs **{away_team['team_name']}**\n\n"
                       f"Week {fixture['week_number']} - {fixture['competition']}",
            color=discord.Color.green()
        )
        
        embed.add_field(name="🏠 Home", value=home_team['team_name'], inline=True)
        embed.add_field(name="✈️ Away", value=away_team['team_name'], inline=True)
        embed.add_field(name="📊 Format", value=f"{config.MATCH_EVENTS_PER_GAME} key moments", inline=True)
        
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
            name="🎲 How to Play",
            value="• Wait for your key moments\n"
                  "• Choose: Shoot, Pass, or Dribble\n"
                  "• Roll d20 + your stats vs DC\n"
                  "• **10 second timer** - auto-rolls if you don't choose!",
            inline=False
        )
        
        embed.set_footer(text="Match begins in 5 seconds...")
        
        await interaction.followup.send(
            f"✅ Match channel created: {match_channel.mention}\n"
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
        
        await self.run_match(match_id, fixture, match_channel)
    
    async def run_match(self, match_id: int, fixture: dict, channel: discord.TextChannel):
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
        
        minutes = [10, 20, 30, 40, 55, 65, 75, 85][:config.MATCH_EVENTS_PER_GAME]
        
        for i, minute in enumerate(minutes):
            event_num = i + 1
            
            embed = discord.Embed(
                title=f"⚽ Match Event {event_num}/{config.MATCH_EVENTS_PER_GAME}",
                description=f"**Minute {minute}'**\n\n"
                           f"**{home_team['team_name']} {home_score} - {away_score} {away_team['team_name']}**",
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
                            home_team, away_team, True
                        )
                        
                        if result == 'goal':
                            home_score += 1
                        elif result == 'assist':
                            pass
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
                            away_team, home_team, False
                        )
                        
                        if result == 'goal':
                            away_score += 1
                        elif result == 'assist':
                            pass
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
    
    async def handle_player_moment(self, channel, player, participant, minute, attacking_team, defending_team, is_home):
    """Handle a player's interactive moment"""
    
    member = channel.guild.get_member(player['user_id'])
    if not member:
        return await self.auto_resolve_moment(player, minute, attacking_team, defending_team)
    
    # Get a random defender
    async with db.pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT * FROM npc_players WHERE team_id = $1 AND position IN ('CB', 'FB', 'CDM', 'GK') ORDER BY RANDOM() LIMIT 1",
            defending_team['team_id']
        )
        defender = dict(result) if result else None
    
    position_actions = {
        'ST': ['shoot', 'pass', 'dribble'],
        'W': ['shoot', 'pass', 'dribble'],
        'CAM': ['pass', 'shoot', 'dribble'],
        'CM': ['pass', 'dribble', 'shoot'],
        'CDM': ['pass', 'dribble'],
        'FB': ['pass', 'dribble'],
        'CB': ['pass'],
        'GK': ['pass']
    }
    
    available_actions = position_actions.get(player['position'], ['shoot', 'pass', 'dribble'])
    
    # Create situation description
    situations = [
        f"⚔️ 1v1 against the defender!",
        f"🎯 Clear shot on goal!",
        f"🏃 Breaking through on the counter!",
        f"📦 In the box with space!",
        f"🎪 Edge of the box opportunity!"
    ]
    
    situation = random.choice(situations)
    
    embed = discord.Embed(
        title=f"🎯 {member.display_name}'s Key Moment!",
        description=f"**Minute {minute}'** - {situation}\n\n"
                    f"**{player['player_name']}** has the ball!\n"
                    f"**You have 10 seconds to decide!**",
        color=discord.Color.gold()
    )
    
    embed.add_field(
        name="📊 Your Stats",
        value=f"⚡ Pace: {player['pace']}\n"
              f"🎯 Shooting: {player['shooting']}\n"
              f"🎪 Passing: {player['passing']}\n"
              f"🪄 Dribbling: {player['dribbling']}",
        inline=True
    )
    
    if defender:
        embed.add_field(
            name="🛡️ Nearest Defender",
            value=f"**{defender['player_name']}**\n"
                  f"DEF: {defender['defending']}\n"
                  f"PHY: {defender['physical']}\n"
                  f"Pos: {defender['position']}",
            inline=True
        )
    
    embed.add_field(
        name="⚽ Match Situation",
        value=f"**{attacking_team['team_name']}** attacking\n"
              f"vs **{defending_team['team_name']}**",
        inline=False
    )
    
    embed.add_field(
        name="💡 Tips",
        value="• **Shoot** if you have clear sight of goal (vs GK)\n"
              "• **Pass** to keep possession (vs interception)\n"
              "• **Dribble** to beat the defender (vs tackle)",
        inline=False
    )
    
    view = ActionView(available_actions, timeout=10)
    
    message = await channel.send(content=member.mention, embed=embed, view=view)
    
    await view.wait()
    
    if view.chosen_action:
        action = view.chosen_action
    else:
        action = random.choice(available_actions)
        await channel.send(f"⏰ {member.mention} didn't choose in time! Auto-selected: **{action.upper()}**")
    
    # Rest of the function stays the same...
    stat_map = {
        'shoot': player['shooting'],
        'pass': player['passing'],
        'dribble': player['dribbling']
    }
    
    stat_value = stat_map.get(action, player['pace'])
    modifier = calculate_modifier(stat_value)
    
    dc = get_difficulty_class(action)
    
    # Adjust DC based on defender
    if defender and action == 'dribble':
        defender_modifier = calculate_modifier(defender['defending'])
        dc = max(10, dc + (defender_modifier - 5))  # Adjust based on defender skill
    
    roll = roll_d20()
    total = roll + modifier
    success = total >= dc
    
    result_embed = discord.Embed(
        title=f"🎲 {action.upper()} Attempt!",
        description=f"**{player['player_name']}** attempts to {action}...",
        color=discord.Color.green() if success else discord.Color.red()
    )
    
    if defender and action == 'dribble':
        result_embed.add_field(
            name="🛡️ Defender Challenge",
            value=f"vs **{defender['player_name']}** (DEF {defender['defending']})",
            inline=False
        )
    
    if roll == 20:
        result_embed.add_field(
            name="🌟 NATURAL 20! CRITICAL SUCCESS!",
            value=f"Roll: **20** + {modifier} = **{total}** vs DC {dc}",
            inline=False
        )
    elif roll == 1:
        result_embed.add_field(
            name="💥 NATURAL 1! CRITICAL FAILURE!",
            value=f"Roll: **1** + {modifier} = **{total}** vs DC {dc}",
            inline=False
        )
    else:
        result_embed.add_field(
            name=f"{'✅ SUCCESS!' if success else '❌ FAILED!'}",
            value=f"Roll: **{roll}** + {modifier} (stat) = **{total}** vs DC {dc}",
            inline=False
        )
    
    # Rest of outcome logic stays the same...
    rating_change = 0
    outcome = None
    
    if action == 'shoot':
        if success:
            if roll == 20 or total >= dc + 5:
                result_embed.add_field(
                    name="⚽ GOOOAL!",
                    value=f"**{player['player_name']}** scores for {attacking_team['team_name']}!",
                    inline=False
                )
                outcome = 'goal'
                rating_change = 1.0
                
                async with db.pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE players SET season_goals = season_goals + 1, career_goals = career_goals + 1 WHERE user_id = $1",
                        player['user_id']
                    )
            else:
                result_embed.add_field(
                    name="🧤 Saved!",
                    value=f"The goalkeeper denies {player['player_name']}!",
                    inline=False
                )
                rating_change = 0.2
        else:
            if roll == 1:
                result_embed.add_field(
                    name="🤦 Miss!",
                    value=f"{player['player_name']} completely misses the target!",
                    inline=False
                )
                rating_change = -0.3
            else:
                result_embed.add_field(
                    name="📍 Off Target",
                    value=f"The shot goes wide!",
                    inline=False
                )
                rating_change = -0.1
    
    elif action == 'pass':
        if success:
            if roll == 20:
                result_embed.add_field(
                    name="✨ Perfect Pass!",
                    value=f"Brilliant vision from {player['player_name']}!",
                    inline=False
                )
                rating_change = 0.3
            else:
                result_embed.add_field(
                    name="✅ Good Pass",
                    value=f"{player['player_name']} finds a teammate!",
                    inline=False
                )
                rating_change = 0.1
        else:
            result_embed.add_field(
                name="❌ Intercepted!",
                value=f"The pass is cut out by {defending_team['team_name']}!",
                inline=False
            )
            rating_change = -0.2
    
    elif action == 'dribble':
        if success:
            if roll == 20:
                result_embed.add_field(
                    name="🌟 Amazing Skill!",
                    value=f"{player['player_name']} beats {defender['player_name'] if defender else 'the defender'}!",
                    inline=False
                )
                rating_change = 0.4
            else:
                result_embed.add_field(
                    name="✅ Gets Past!",
                    value=f"{player['player_name']} dribbles past {defender['player_name'] if defender else 'the defender'}!",
                    inline=False
                )
                rating_change = 0.2
        else:
            result_embed.add_field(
                name="🛑 Tackled!",
                value=f"{defender['player_name'] if defender else 'The defender'} stops {player['player_name']}!",
                inline=False
            )
            rating_change = -0.1
    
    async with db.pool.acquire() as conn:
        await conn.execute('''
            UPDATE match_participants 
            SET match_rating = match_rating + $1, actions_taken = actions_taken + 1
            WHERE participant_id = $2
        ''', rating_change, participant['participant_id'])
        
        await conn.execute('''
            INSERT INTO match_events (
                fixture_id, user_id, event_type, minute, description,
                dice_roll, stat_modifier, total_roll, difficulty_class,
                success, rating_impact
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        ''',
            participant['match_id'],
            player['user_id'],
            action,
            minute,
            result_embed.fields[0].value if result_embed.fields else "",
            roll,
            modifier,
            total,
            dc,
            success,
            rating_change
        )
    
    await channel.send(embed=result_embed)
    
    return outcome
    
    async def handle_npc_moment(self, channel, team_id, minute, attacking_team, defending_team, is_home):
        """Handle an NPC moment"""
        
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
        
        embed = discord.Embed(
            title=f"🤖 NPC Action - Minute {minute}'",
            description=f"**{npc['player_name']}** ({attacking_team['team_name']})",
            color=discord.Color.blue()
        )
        
        outcome = None
        
        if action == 'shoot' and success and (roll == 20 or total >= dc + 5):
            embed.add_field(
                name="⚽ GOAL!",
                value=f"**{npc['player_name']}** scores!\n"
                      f"Roll: {roll} + {modifier} = {total} vs DC {dc}",
                inline=False
            )
            outcome = 'goal'
            
            async with db.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE npc_players SET season_goals = season_goals + 1 WHERE npc_id = $1",
                    npc['npc_id']
                )
        else:
            result_text = "successful" if success else "unsuccessful"
            embed.add_field(
                name=f"Action: {action.upper()}",
                value=f"{result_text.capitalize()} attempt\n"
                      f"Roll: {roll} + {modifier} = {total} vs DC {dc}",
                inline=False
            )
        
        await channel.send(embed=embed)
        
        return outcome
    
    async def auto_resolve_moment(self, player, minute, attacking_team, defending_team):
        """Auto-resolve when player isn't available"""
        
        action = random.choice(['shoot', 'pass', 'dribble'])
        stat_map = {
            'shoot': player['shooting'],
            'pass': player['passing'],
            'dribble': player['dribbling']
        }
        
        stat_value = stat_map[action]
        modifier = calculate_modifier(stat_value)
        dc = get_difficulty_class(action)
        
        roll = roll_d20()
        total = roll + modifier
        success = total >= dc
        
        if action == 'shoot' and success and (roll == 20 or total >= dc + 5):
            async with db.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE players SET season_goals = season_goals + 1, career_goals = career_goals + 1 WHERE user_id = $1",
                    player['user_id']
                )
            return 'goal'
        
        return None
    
    async def end_match(self, match_id, fixture, channel, home_score, away_score, participants):
        """End the match and update all stats"""
        
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
        
        if home_score > away_score:
            embed.add_field(name="🏆 Winner", value=home_team['team_name'], inline=False)
        elif away_score > home_score:
            embed.add_field(name="🏆 Winner", value=away_team['team_name'], inline=False)
        else:
            embed.add_field(name="🤝 Result", value="Draw!", inline=False)
        
        if participants:
            ratings_text = ""
            for p in participants:
                player = await db.get_player(p['user_id'])
                if player:
                    final_rating = max(0, min(10, p['match_rating']))
                    
                    async with db.pool.acquire() as conn:
                        await conn.execute(
                            "UPDATE players SET season_apps = season_apps + 1, career_apps = career_apps + 1, season_rating = ((season_rating * season_apps) + $1) / (season_apps + 1) WHERE user_id = $2",
                            final_rating, p['user_id']
                        )
                    
                    ratings_text += f"**{player['player_name']}**: {final_rating:.1f}/10\n"
            
            if ratings_text:
                embed.add_field(name="⭐ Player Ratings", value=ratings_text, inline=False)
        
        embed.add_field(
            name="📊 Match Stats",
            value=f"Key Moments: {config.MATCH_EVENTS_PER_GAME}\n"
                  f"Goals: {home_score + away_score}",
            inline=False
        )
        
        embed.set_footer(text="This channel will be deleted in 60 seconds...")
        
        await channel.send(embed=embed)
        
        await db.add_news(
            f"{home_team['team_name']} {home_score}-{away_score} {away_team['team_name']}",
            f"Full time in Week {fixture['week_number']}. "
            f"{'Home win' if home_score > away_score else 'Away win' if away_score > home_score else 'Teams share the points'} "
            f"at {home_team['team_name']}.",
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
        """Update team statistics"""
        
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

class ActionView(discord.ui.View):
    def __init__(self, available_actions, timeout=10):
        super().__init__(timeout=timeout)
        self.chosen_action = None
        
        for action in available_actions:
            button = ActionButton(action)
            self.add_item(button)
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

class ActionButton(discord.ui.Button):
    def __init__(self, action):
        emoji_map = {
            'shoot': '🎯',
            'pass': '🎪',
            'dribble': '🪄'
        }
        
        super().__init__(
            label=action.upper(),
            emoji=emoji_map.get(action, '⚽'),
            style=discord.ButtonStyle.primary
        )
        self.action = action
    
    async def callback(self, interaction: discord.Interaction):
        self.view.chosen_action = self.action
        
        for item in self.view.children:
            item.disabled = True
        
        await interaction.response.edit_message(view=self.view)
        self.view.stop()

match_engine = None
