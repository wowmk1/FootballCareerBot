import discord
from discord.ext import commands
import asyncio
from database import db
from datetime import datetime
import random
import config
from utils.football_data_api import get_team_crest_url, get_competition_logo


class MatchEngine:
    def __init__(self, bot):
        self.bot = bot
        self.active_matches = {}
        self.pinned_messages = {}

    def get_position_events(self, position):
        """Enhanced position-specific events with defensive actions"""
        position_events = {
            'ST': ['shoot', 'hold_up_play', 'run_in_behind', 'press_defender'],
            'W': ['dribble', 'cross', 'cut_inside', 'track_back', 'shoot'],
            'CAM': ['through_ball', 'shoot', 'key_pass', 'dribble', 'press'],
            'CM': ['pass', 'through_ball', 'long_ball', 'tackle', 'interception'],
            'CDM': ['tackle', 'interception', 'pass', 'block', 'cover'],
            'FB': ['tackle', 'cross', 'overlap', 'clearance', 'track_runner'],
            'CB': ['tackle', 'clearance', 'block', 'pass'],
            'GK': ['save', 'claim_cross', 'distribution', 'sweep']
        }
        return position_events.get(position, ['pass', 'dribble', 'tackle'])

    def get_detailed_scenario(self, position, minute, attacking_team, defending_team, defender):
        """Generate detailed, immersive scenario description"""
        
        defender_name = defender['player_name'] if defender else "a defender"
        def_team = defending_team['team_name']
        att_team = attacking_team['team_name']
        
        scenarios = {
            'ST': [
                f"💨 **{att_team} counter-attack!**\nYou break free from the defensive line. {defender_name} chasing back desperately!",
                f"🎯 Ball played into your feet in the box!\n{def_team}'s defense scrambling. {defender_name} closing you down fast!",
                f"⚡ Through ball splits the defense!\nYou're racing towards goal! Only {defender_name} to beat!",
                f"🎪 Cross coming in from the wing!\nYou position yourself in the box. {defender_name} marking tight!"
            ],
            'W': [
                f"💨 Space opens up on the flank!\nYou receive the ball with room to run. {defender_name} moving to intercept!",
                f"🎯 1v1 situation developing!\n{defender_name} squares up. The crowd roars with anticipation!",
                f"⚡ Ball at your feet on the touchline!\nCut inside or go outside? {defender_name} blocking your path!"
            ],
            'CAM': [
                f"🎯 Pocket of space in the hole!\nYou find yourself unmarked momentarily. {defender_name} rushing to close you down!",
                f"⚡ Ball drops to you 25 yards out!\nStrikers making runs. {def_team}'s midfield scrambling back!",
                f"🎪 Quick one-two with your striker!\nYou're in behind! {defender_name} slides across to block!"
            ],
            'CM': [
                f"💪 Won the ball in midfield!\nTransition opportunity! {def_team}'s defense exposed!",
                f"🎯 Time and space in the center circle!\nForwards making runs. {defender_name} pressing!"
            ],
            'CDM': [
                f"🛡️ DANGER! They're breaking through!\n{defender_name} driving at your defense! You're the last line!",
                f"⚡ Ball breaks loose in midfield!\nWin it back or they counter! {att_team}'s defense needs you!"
            ],
            'FB': [
                f"🏃 Winger running at you with pace!\n{defender_name} in full flight! Stand strong!",
                f"⚡ Overlapping run opportunity!\nYour winger has the ball. {def_team}'s defense tracking back!"
            ],
            'CB': [
                f"🛡️ CRITICAL MOMENT! Striker through on goal!\n{defender_name} bearing down! Last-ditch defending needed!",
                f"💪 Aerial duel incoming!\nCross flying in. {defender_name} challenging! Command the box!"
            ],
            'GK': [
                f"🧤 1v1 WITH THE STRIKER!\n{defender_name} clean through! Make yourself big!",
                f"🎯 Shot from distance!\nPowerful strike heading your way! Quick reactions needed!",
                f"⚡ Cross swinging into your box!\nStrikers lurking. Claim it or punch clear?"
            ]
        }
        
        position_scenarios = scenarios.get(position, scenarios['CM'])
        return random.choice(position_scenarios)

    def get_action_description(self, action):
        descriptions = {
            'shoot': "⚡ **SHOOTS!**", 'pass': "🎯 Looks to pass", 'dribble': "💨 Takes on the defender",
            'tackle': "🛡️ Goes for the tackle", 'cross': "📤 Delivers a cross", 'clearance': "🚀 Clears the danger",
            'save': "🧤 Diving save attempt", 'through_ball': "⚡ Threads through ball",
            'interception': "👀 Reads the play", 'block': "🧱 Throws body on line",
            'cut_inside': "↩️ Cuts inside", 'key_pass': "🔑 Key pass", 'long_ball': "📡 Long ball forward",
            'overlap': "🏃 Overlapping run", 'claim_cross': "✊ Claims the cross",
            'distribution': "🎯 Quick distribution", 'hold_up_play': "💪 Holds up play",
            'run_in_behind': "🏃 Runs in behind", 'press_defender': "⚡ Presses high",
            'track_back': "🔙 Tracks back", 'press': "⚡ Presses", 'cover': "🛡️ Covers space",
            'track_runner': "🏃 Tracks runner", 'sweep': "🧹 Sweeps up"
        }
        return descriptions.get(action, f"Attempts {action}")

    def get_stat_for_action(self, action):
        stat_map = {
            'shoot': 'shooting', 'pass': 'passing', 'dribble': 'dribbling', 'tackle': 'defending',
            'cross': 'passing', 'clearance': 'defending', 'save': 'defending', 'through_ball': 'passing',
            'interception': 'defending', 'block': 'physical', 'cut_inside': 'dribbling',
            'key_pass': 'passing', 'long_ball': 'passing', 'overlap': 'pace',
            'claim_cross': 'physical', 'distribution': 'passing', 'hold_up_play': 'physical',
            'run_in_behind': 'pace', 'press_defender': 'physical', 'track_back': 'pace',
            'press': 'physical', 'cover': 'defending', 'track_runner': 'pace', 'sweep': 'pace'
        }
        return stat_map.get(action, 'pace')

    def get_defender_stat(self, action):
        defender_stat_map = {
            'shoot': 'defending', 'pass': 'pace', 'dribble': 'defending', 'tackle': 'dribbling',
            'cross': 'pace', 'clearance': 'shooting', 'through_ball': 'pace', 'interception': 'passing',
            'block': 'shooting', 'cut_inside': 'defending', 'key_pass': 'pace',
            'long_ball': 'pace', 'overlap': 'pace', 'hold_up_play': 'defending',
            'run_in_behind': 'defending', 'press_defender': 'passing', 'track_back': 'pace',
            'press': 'dribbling', 'cover': 'pace', 'track_runner': 'pace'
        }
        return defender_stat_map.get(action, 'defending')

    def calculate_success_chance(self, player_stat, defender_stat):
        stat_diff = player_stat - defender_stat
        chance = 50 + (stat_diff * 2.5)
        return max(5, min(95, int(chance)))

    def get_recommendation(self, player, adjusted_stats, available_actions):
        """Get best action with rating impact shown"""
        action_scores = {}
        recommendable_actions = [a for a in available_actions if a not in ['sweep']]
        if not recommendable_actions:
            return available_actions[0], 50, 0.0

        for action in recommendable_actions:
            stat = self.get_stat_for_action(action)
            stat_value = adjusted_stats.get(stat, 50)
            rating_impact = self.estimate_rating_impact(action, player['position'])
            action_scores[action] = (stat_value, rating_impact)

        best_action = max(action_scores, key=lambda k: action_scores[k][0])
        best_stat = adjusted_stats.get(self.get_stat_for_action(best_action), 50)
        rating_impact = action_scores[best_action][1]

        return best_action, best_stat, rating_impact

    def estimate_rating_impact(self, action, position):
        """Estimate how much action affects rating if successful"""
        position_weights = {
            'ST': {'shoot': 1.2, 'hold_up_play': 0.4, 'run_in_behind': 0.5, 'press_defender': 0.3},
            'W': {'dribble': 0.8, 'shoot': 0.9, 'cross': 0.6, 'cut_inside': 0.7, 'track_back': 0.4},
            'CAM': {'through_ball': 0.8, 'pass': 0.5, 'shoot': 0.8, 'dribble': 0.6, 'press': 0.3},
            'CM': {'pass': 0.6, 'through_ball': 0.7, 'tackle': 0.5, 'dribble': 0.4, 'interception': 0.5},
            'CDM': {'tackle': 0.8, 'interception': 0.8, 'pass': 0.5, 'block': 0.7, 'cover': 0.6},
            'FB': {'tackle': 0.7, 'cross': 0.6, 'overlap': 0.5, 'track_runner': 0.6, 'clearance': 0.5},
            'CB': {'tackle': 0.8, 'clearance': 0.7, 'block': 0.8, 'pass': 0.4},
            'GK': {'save': 1.5, 'claim_cross': 0.8, 'distribution': 0.4, 'sweep': 0.7}
        }

        weights = position_weights.get(position, {})
        return weights.get(action, 0.3)

    def calculate_rating_change(self, action, success, roll, position):
        """More realistic rating changes"""
        base_impact = self.estimate_rating_impact(action, position)

        if success:
            rating_change = base_impact * 0.15
            if roll == 20:
                rating_change *= 2.0
        else:
            rating_change = -base_impact * 0.1
            if roll == 1:
                rating_change = -0.3

        if action == 'shoot' and success:
            rating_change = 1.2

        return rating_change

    def apply_form_to_stats(self, player):
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

    def get_commentary(self):
        lines = [
            "The tension is palpable!", "The crowd roars!", "What a moment this is!",
            "Can you feel the atmosphere?", "This is what football is all about!",
            "The fans are on the edge of their seats!", "Incredible scenes here!",
            "The pressure is mounting!", "Both teams giving it their all!", "This is end-to-end stuff!"
        ]
        return random.choice(lines)

    async def update_pinned_score(self, channel, match_id, home_team, away_team, home_score, away_score, minute):
        try:
            embed = discord.Embed(
                title="⚽ LIVE MATCH",
                description=f"## {home_team['team_name']} {home_score} - {away_score} {away_team['team_name']}\n\n**{minute}'** - Match in progress",
                color=discord.Color.green()
            )

            home_crest = get_team_crest_url(home_team['team_id'])
            if home_crest:
                embed.set_thumbnail(url=home_crest)
            
            comp_logo = get_competition_logo(home_team.get('league', 'Premier League'))
            if comp_logo:
                embed.set_footer(
                    text=f"{home_team.get('league', 'Premier League')} • Minute {minute}",
                    icon_url=comp_logo
                )

            if match_id in self.pinned_messages:
                msg = self.pinned_messages[match_id]
                try:
                    await msg.edit(embed=embed)
                except:
                    new_msg = await channel.send(embed=embed)
                    try:
                        await new_msg.pin()
                    except:
                        pass
                    self.pinned_messages[match_id] = new_msg
            else:
                msg = await channel.send(embed=embed)
                try:
                    await msg.pin()
                except:
                    pass
                self.pinned_messages[match_id] = msg
        except Exception as e:
            print(f"Error updating pinned score: {e}")

    async def post_goal_celebration(self, channel, scorer_name, team_name, team_id, home_score, away_score):
        celebrations = [
            "🔥🔥🔥 **GOOOOAAAALLL!!!** 🔥🔥🔥", "⚽⚽⚽ **WHAT A GOAL!!!** ⚽⚽⚽",
            "💥💥💥 **SPECTACULAR!!!** 💥💥💥", "🎯🎯🎯 **INCREDIBLE FINISH!!!** 🎯🎯🎯",
            "⭐⭐⭐ **ABSOLUTE SCENES!!!** ⭐⭐⭐"
        ]
        embed = discord.Embed(
            title=random.choice(celebrations),
            description=f"## **{scorer_name}** scores for {team_name}!\n\n**{home_score} - {away_score}**",
            color=discord.Color.gold()
        )
        
        team_crest = get_team_crest_url(team_id)
        if team_crest:
            embed.set_thumbnail(url=team_crest)
        
        await channel.send(embed=embed)

    async def post_halftime_summary(self, channel, home_team, away_team, home_score, away_score, participants,
                                    match_id):
        embed = discord.Embed(
            title="⸻ HALF-TIME",
            description=f"## {home_team['team_name']} {home_score} - {away_score} {away_team['team_name']}",
            color=discord.Color.orange()
        )
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT user_id, match_rating FROM match_participants WHERE match_id = $1 ORDER BY match_rating DESC LIMIT 3",
                match_id
            )
        if rows:
            top_performers = ""
            for row in rows:
                player = await db.get_player(row['user_id'])
                if player:
                    top_performers += f"⭐ {player['player_name']}: {row['match_rating']:.1f}/10\n"
            if top_performers:
                embed.add_field(name="🌟 Top Performers", value=top_performers, inline=False)
        embed.add_field(name="⏱️", value="Second half coming up...", inline=False)
        await channel.send(embed=embed)
        await asyncio.sleep(3)

    def get_follow_up_event(self, action, success, position):
        """Enhanced follow-ups with progression chains"""
        if not success:
            return None

        follow_ups = {
            'dribble': {'ST': 'shoot', 'W': ['shoot', 'cross'], 'CAM': ['shoot', 'through_ball'],
                        'CM': 'pass', 'CDM': 'pass', 'FB': 'cross', 'CB': 'pass'},
            'cut_inside': {'W': 'shoot', 'CAM': 'shoot'},
            'hold_up_play': {'ST': ['pass', 'shoot']},
            'run_in_behind': {'ST': 'shoot', 'W': 'shoot'},
            'tackle': {'CB': 'pass', 'FB': 'pass', 'CDM': 'pass', 'CM': 'through_ball'},
            'interception': {'CDM': 'pass', 'CM': 'pass', 'CB': 'pass'},
        }

        follow_up = follow_ups.get(action, {}).get(position)
        if isinstance(follow_up, list):
            return random.choice(follow_up)
        return follow_up

    async def handle_teammate_followup(self, channel, player, action, minute, match_id, attacking_team):
        """Handle teammate scoring after successful pass/cross - WORKING VERSION"""
        
        if action not in ['pass', 'through_ball', 'cross', 'key_pass']:
            return None
        
        if random.random() > 0.45:
            return None
        
        async with db.pool.acquire() as conn:
            teammate = await conn.fetchrow(
                """SELECT player_name, position, overall_rating, shooting
                   FROM npc_players
                   WHERE team_id = $1
                     AND position IN ('ST', 'W', 'CAM')
                     AND retired = FALSE
                   ORDER BY RANDOM() LIMIT 1""",
                attacking_team['team_id']
            )
        
        if not teammate:
            return None
        
        teammate = dict(teammate)
        
        embed = discord.Embed(
            title="⚡ TEAMMATE OPPORTUNITY!",
            description=f"**{teammate['player_name']}** receives from {player['player_name']}!\n\n"
                        f"🎯 Position: {teammate['position']}\n"
                        f"📊 Shooting: **{teammate['shooting']}**",
            color=discord.Color.orange()
        )
        suspense_msg = await channel.send(embed=embed)
        await asyncio.sleep(2)
        
        teammate_roll = random.randint(1, 20)
        shooting_bonus = teammate['shooting'] // 10
        total = teammate_roll + shooting_bonus
        
        difficulty = {
            'through_ball': 12,
            'cross': 14,
            'pass': 13,
            'key_pass': 11
        }.get(action, 13)
        
        success = total >= difficulty
        
        result_embed = discord.Embed(
            title=f"🎲 {teammate['player_name']}'s FINISH",
            color=discord.Color.green() if success else discord.Color.red()
        )
        
        result_embed.add_field(
            name="📊 The Roll",
            value=f"🎲 Roll: **{teammate_roll}**\n"
                  f"📈 Shooting Bonus: **+{shooting_bonus}**\n"
                  f"💯 Total: **{total}** vs DC {difficulty}",
            inline=False
        )
        
        if success:
            result_embed.add_field(
                name="⚽ GOOOOOAL!",
                value=f"**{teammate['player_name']}** buries it!\n"
                      f"🅰️ **ASSIST: {player['player_name']}**",
                inline=False
            )
            
            async with db.pool.acquire() as conn:
                await conn.execute(
                    """UPDATE players 
                       SET season_assists = season_assists + 1, 
                           career_assists = career_assists + 1 
                       WHERE user_id = $1""",
                    player['user_id']
                )
                
                await conn.execute(
                    """UPDATE match_participants 
                       SET match_rating = LEAST(10.0, match_rating + 0.8) 
                       WHERE match_id = $1 AND user_id = $2""",
                    match_id, player['user_id']
                )
                
                await conn.execute(
                    """UPDATE npc_players 
                       SET season_goals = season_goals + 1 
                       WHERE player_name = $1 AND team_id = $2""",
                    teammate['player_name'], attacking_team['team_id']
                )
            
            from utils.form_morale_system import update_player_morale
            await update_player_morale(player['user_id'], 'assist')
            
            await suspense_msg.delete()
            await channel.send(embed=result_embed)
            
            return 'goal'
        else:
            miss_msgs = [
                "Blazes it over the bar!",
                "Straight at the keeper!",
                "Hits the post!",
                "Slices it wide!",
                "What a miss!"
            ]
            
            result_embed.add_field(
                name="❌ MISS!",
                value=random.choice(miss_msgs),
                inline=False
            )
            
            await suspense_msg.delete()
            await channel.send(embed=result_embed)
            
            return None

    async def start_match(self, fixture: dict, interaction: discord.Interaction):
        home_team = await db.get_team(fixture['home_team_id'])
        away_team = await db.get_team(fixture['away_team_id'])

        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="⚽ ACTIVE MATCHES")
        if not category:
            category = await guild.create_category("⚽ ACTIVE MATCHES")

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

        match_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

        num_events = random.randint(config.MATCH_EVENTS_PER_GAME_MIN, config.MATCH_EVENTS_PER_GAME_MAX)

        embed = discord.Embed(
            title="🟢 MATCH STARTING!",
            description=f"## {home_team['team_name']} 🆚 {away_team['team_name']}\n\n**{fixture['competition']}** • Week {fixture['week_number']}",
            color=discord.Color.green()
        )

        home_crest = get_team_crest_url(fixture['home_team_id'])
        if home_crest:
            embed.set_thumbnail(url=home_crest)

        embed.add_field(name="🏠 Home", value=f"**{home_team['team_name']}**\n{home_team['league']}", inline=True)
        embed.add_field(name="✈️ Away", value=f"**{away_team['team_name']}**\n{away_team['league']}", inline=True)
        
        embed.add_field(
            name="📊 Match Info",
            value=f"🎯 {num_events} key moments\n⏱️ 30s decision time\n🎲 Stat + D20 battle system",
            inline=True
        )

        player_mentions = []
        for user_id in player_users:
            member = guild.get_member(user_id)
            if member:
                player_mentions.append(member.mention)

        if player_mentions:
            embed.add_field(name="👥 Players Involved", value=" ".join(player_mentions), inline=False)

        embed.set_footer(text="⚡ Match begins in 5 seconds...")

        await interaction.followup.send(
            f"✅ Match channel created: {match_channel.mention}\n🎮 {home_team['team_name']} vs {away_team['team_name']}",
            ephemeral=True
        )

        message = await match_channel.send(embed=embed)

        async with db.pool.acquire() as conn:
            result = await conn.fetchrow('''
                                         INSERT INTO active_matches (fixture_id, home_team_id, away_team_id, channel_id,
                                                                     message_id, match_state, current_minute,
                                                                     last_event_time)
                                         VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING match_id
                                         ''', fixture['fixture_id'], fixture['home_team_id'], fixture['away_team_id'],
                                         match_channel.id, message.id, 'in_progress', 0, datetime.now().isoformat())
            match_id = result['match_id']

        for user_id in player_users:
            player = await db.get_player(user_id)
            if player:
                async with db.pool.acquire() as conn:
                    await conn.execute(
                        'INSERT INTO match_participants (match_id, user_id, team_id, match_rating) VALUES ($1, $2, $3, $4)',
                        match_id, user_id, player['team_id'], 5.0)

        await asyncio.sleep(5)
        await self.run_match(match_id, fixture, match_channel, num_events)

    async def run_match(self, match_id: int, fixture: dict, channel: discord.TextChannel, num_events: int):
        home_team = await db.get_team(fixture['home_team_id'])
        away_team = await db.get_team(fixture['away_team_id'])
        home_score = 0
        away_score = 0

        async with db.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM match_participants WHERE match_id = $1", match_id)
            participants = [dict(row) for row in rows]

        home_participants = [p for p in participants if p['team_id'] == fixture['home_team_id']]
        away_participants = [p for p in participants if p['team_id'] == fixture['away_team_id']]

        possible_minutes = list(range(5, 91, 5))
        minutes = sorted(random.sample(possible_minutes, min(num_events, len(possible_minutes))))

        await self.update_pinned_score(channel, match_id, home_team, away_team, home_score, away_score, 0)

        for i, minute in enumerate(minutes):
            event_num = i + 1
            await self.update_pinned_score(channel, match_id, home_team, away_team, home_score, away_score, minute)

            if random.random() < 0.3:
                await channel.send(f"*{self.get_commentary()}*")
                await asyncio.sleep(1)

            embed = discord.Embed(
                title=f"⚡ KEY MOMENT #{event_num}/{num_events} — {minute}'",
                description=f"## {home_team['team_name']} {home_score} - {away_score} {away_team['team_name']}",
                color=discord.Color.blue()
            )
            await channel.send(embed=embed)
            await asyncio.sleep(2)

            if minute == 45:
                await self.post_halftime_summary(channel, home_team, away_team, home_score, away_score, participants,
                                                 match_id)

            attacking_team = random.choice(['home', 'away'])
            if attacking_team == 'home':
                if home_participants:
                    participant = random.choice(home_participants)
                    player = await db.get_player(participant['user_id'])
                    if player:
                        result = await self.handle_player_moment(channel, player, participant, minute, home_team,
                                                                 away_team, True, match_id)
                        if result == 'goal':
                            home_score += 1
                            await self.post_goal_celebration(channel, player['player_name'], home_team['team_name'],
                                                             home_team['team_id'], home_score, away_score)
                            await self.update_pinned_score(channel, match_id, home_team, away_team, home_score,
                                                           away_score, minute)
                else:
                    result = await self.handle_npc_moment(channel, fixture['home_team_id'], minute, home_team,
                                                          away_team, True)
                    if result == 'goal':
                        home_score += 1
                        await self.update_pinned_score(channel, match_id, home_team, away_team, home_score, away_score,
                                                       minute)
            else:
                if away_participants:
                    participant = random.choice(away_participants)
                    player = await db.get_player(participant['user_id'])
                    if player:
                        result = await self.handle_player_moment(channel, player, participant, minute, away_team,
                                                                 home_team, False, match_id)
                        if result == 'goal':
                            away_score += 1
                            await self.post_goal_celebration(channel, player['player_name'], away_team['team_name'],
                                                             away_team['team_id'], home_score, away_score)
                            await self.update_pinned_score(channel, match_id, home_team, away_team, home_score,
                                                           away_score, minute)
                else:
                    result = await self.handle_npc_moment(channel, fixture['away_team_id'], minute, away_team,
                                                          home_team, False)
                    if result == 'goal':
                        away_score += 1
                        await self.update_pinned_score(channel, match_id, home_team, away_team, home_score, away_score,
                                                       minute)

            async with db.pool.acquire() as conn:
                await conn.execute(
                    'UPDATE active_matches SET home_score = $1, away_score = $2, current_minute = $3 WHERE match_id = $4',
                    home_score, away_score, minute, match_id)

            await asyncio.sleep(2)

        await self.end_match(match_id, fixture, channel, home_score, away_score, participants)

    async def handle_player_moment(self, channel, player, participant, minute, attacking_team, defending_team,
                                   is_home, match_id):
        member = channel.guild.get_member(player['user_id'])
        if not member:
            return await self.auto_resolve_moment(player, minute, attacking_team, defending_team)

        adjusted_stats = self.apply_form_to_stats(player)
        available_actions = self.get_position_events(player['position'])

        async with db.pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT * FROM npc_players WHERE team_id = $1 AND position IN ('CB', 'FB', 'CDM', 'GK') ORDER BY RANDOM() LIMIT 1",
                defending_team['team_id']
            )
            defender = dict(result) if result else None

        recommended_action, best_stat, rec_rating_impact = self.get_recommendation(player, adjusted_stats,
                                                                                   available_actions)

        from utils.form_morale_system import get_form_description
        form_desc = get_form_description(player['form'])

        scenario_text = self.get_detailed_scenario(player['position'], minute, attacking_team, defending_team, defender)

        embed = discord.Embed(
            title=f"🎯 {member.display_name}'S BIG MOMENT!",
            description=f"## {player['player_name']} ({player['position']})\n**Minute {minute}'** | Form: {form_desc}\n\n{scenario_text}",
            color=discord.Color.gold()
        )

        team_crest = get_team_crest_url(attacking_team['team_id'])
        if team_crest:
            embed.set_thumbnail(url=team_crest)

        embed.add_field(
            name="📊 Your Stats (Form-Adjusted)",
            value=f"⚡ PAC: **{adjusted_stats['pace']}** | 🎯 SHO: **{adjusted_stats['shooting']}** | 🎪 PAS: **{adjusted_stats['passing']}**\n"
                  f"🪄 DRI: **{adjusted_stats['dribbling']}** | 🛡️ DEF: **{adjusted_stats['defending']}** | 💪 PHY: **{adjusted_stats['physical']}**",
            inline=False
        )

        if defender:
            opp_crest = get_team_crest_url(defending_team['team_id'])
            embed.set_footer(
                text=f"Defending: {defender['player_name']} ({defender['position']}) • {defending_team['team_name']}",
                icon_url=opp_crest if opp_crest else None
            )
            
            embed.add_field(
                name=f"🛡️ Defending: {defender['player_name']} ({defender['position']})",
                value=f"⚡ PAC: **{defender['pace']}** | 🛡️ DEF: **{defender['defending']}** | 💪 PHY: **{defender['physical']}**",
                inline=False
            )

        matchup_text = ""
        for action in available_actions:
            player_stat_name = self.get_stat_for_action(action)
            player_stat_value = adjusted_stats[player_stat_name]
            defender_stat_name = self.get_defender_stat(action)
            defender_stat_value = defender[defender_stat_name] if defender else 70
            chance = self.calculate_success_chance(player_stat_value, defender_stat_value)
            rating_impact = self.estimate_rating_impact(action, player['position'])

            emoji = "🟢" if chance >= 60 else "🟡" if chance >= 45 else "🔴"
            star = "⭐" if action == recommended_action else "  "
            action_display = action.replace('_', ' ').title()

            matchup_text += f"{star}{emoji} **{action_display}**\n"
            matchup_text += f"   You: {player_stat_name.upper()} {player_stat_value} vs Them: {defender_stat_name.upper()} {defender_stat_value}\n"
            matchup_text += f"   Success: ~{chance}% | Rating Impact: **+{rating_impact:.1f}** 📈\n\n"

        embed.add_field(name="📈 ACTION MATCHUPS & RATING IMPACTS", value=matchup_text, inline=False)
        embed.add_field(name="💡 AI RECOMMENDATION",
                        value=f"**{recommended_action.replace('_', ' ').upper()}** ⭐\nBest stat matchup! (+{rec_rating_impact:.1f} rating)",
                        inline=False)
        embed.add_field(name="⏱️ TIME LIMIT", value="**30 SECONDS** to choose!", inline=False)

        view = EnhancedActionView(available_actions, recommended_action, timeout=30)
        message = await channel.send(content=f"📢 {member.mention}", embed=embed, view=view)
        await view.wait()

        action = view.chosen_action if view.chosen_action else recommended_action
        if not view.chosen_action:
            await channel.send(f"⏰ {member.mention} **AUTO-SELECTED**: {action.upper()}")

        result = await self.execute_action_with_duel(channel, player, adjusted_stats, defender, action, minute,
                                                     match_id, member, attacking_team)

        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT match_rating, actions_taken FROM match_participants WHERE match_id = $1 AND user_id = $2",
                match_id, player['user_id'])

        if row:
            mini_embed = discord.Embed(
                description=f"**{player['player_name']}** | Rating: **{row['match_rating']:.1f}/10** | Actions: {row['actions_taken']}",
                color=discord.Color.blue()
            )
            await channel.send(embed=mini_embed)

        if result.get('goal'):
            return 'goal'

        if result['success']:
            follow_up = self.get_follow_up_event(action, True, player['position'])
            if follow_up:
                await asyncio.sleep(2)
                follow_result = await self.execute_follow_up_action(channel, player, adjusted_stats,
                                                                    defender, follow_up, minute, match_id, member, attacking_team)
                if follow_result == 'goal':
                    return 'goal'
        
        return None

    async def execute_action_with_duel(self, channel, player, adjusted_stats, defender, action, minute,
                                       match_id, member=None, attacking_team=None):
        stat_name = self.get_stat_for_action(action)
        player_stat = adjusted_stats[stat_name]
        player_roll = random.randint(1, 20)
        player_total = player_stat + player_roll

        defender_roll = 0
        defender_total = 0
        defender_stat_value = 0

        if defender and action in ['dribble', 'shoot', 'cut_inside', 'pass', 'through_ball', 'cross', 'run_in_behind',
                                   'hold_up_play']:
            defender_stat_name = self.get_defender_stat(action)
            defender_stat_value = defender[defender_stat_name]
            defender_roll = random.randint(1, 20)
            defender_total = defender_stat_value + defender_roll

        success = player_total > defender_total if defender_total > 0 else player_roll >= 10
        action_desc = self.get_action_description(action)

        suspense_embed = discord.Embed(title=f"{action_desc}",
                                       description=f"**{player['player_name']}** {action_desc.lower()}...",
                                       color=discord.Color.orange())
        if member:
            suspense_embed.set_footer(text=f"{member.display_name} is in action!")
        suspense_msg = await channel.send(embed=suspense_embed)
        await asyncio.sleep(1.5)

        result_embed = discord.Embed(
            title=f"🎲 {action.replace('_', ' ').upper()} — THE SHOWDOWN!",
            color=discord.Color.green() if success else discord.Color.red()
        )

        if defender and defender_total > 0:
            result_embed.add_field(
                name="⚔️ Battle of Stats",
                value=f"**YOU ({stat_name.upper()}: {player_stat})**\n🎲 Roll: **{player_roll}**\n💯 Total: **{player_total}**\n\n"
                      f"**{defender['player_name']} ({self.get_defender_stat(action).upper()}: {defender_stat_value})**\n🎲 Roll: **{defender_roll}**\n💯 Total: **{defender_total}**",
                inline=False
            )
        else:
            result_embed.add_field(name="🎲 Your Roll",
                                   value=f"**{stat_name.upper()}: {player_stat}**\n🎲 Roll: **{player_roll}**\n💯 Total: **{player_total}**",
                                   inline=False)

        is_goal = False
        if action == 'shoot' and success:
            if player_roll == 20 or player_total >= defender_total + 10:
                result_embed.add_field(name="⚽ GOOOOAAAL!",
                                       value=f"**{player['player_name']}** SCORES! What a finish!",
                                       inline=False)
                is_goal = True
                async with db.pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE players SET season_goals = season_goals + 1, career_goals = career_goals + 1 WHERE user_id = $1",
                        player['user_id'])
                from utils.form_morale_system import update_player_morale
                await update_player_morale(player['user_id'], 'goal')
            else:
                result_embed.add_field(name="🧤 SAVED!",
                                       value=f"Goalkeeper {random.choice(['palms it away', 'tips over the bar', 'makes a brilliant save'])}!",
                                       inline=False)
        elif success:
            success_msgs = {'pass': "Perfect delivery!", 'dribble': "Beats the defender!",
                            'tackle': "Clean tackle!", 'cross': "Dangerous ball in!",
                            'clearance': "Cleared!", 'through_ball': "Perfect pass!",
                            'interception': "Reads it!", 'cut_inside': "Cuts inside!",
                            'key_pass': "Genius!", 'long_ball': "Pinpoint!",
                            'overlap': "Beats them for pace!", 'block': "Heroic block!",
                            'claim_cross': "Commanding!", 'distribution': "Quick thinking!",
                            'hold_up_play': "Strong hold!", 'run_in_behind': "Perfect timing!",
                            'press_defender': "Forces error!", 'track_back': "Great recovery!",
                            'press': "Wins it back!", 'cover': "Covers perfectly!",
                            'track_runner': "Stays with them!", 'sweep': "Sweeps up danger!"}
            result_embed.add_field(name="✅ SUCCESS!",
                                   value=success_msgs.get(action, f"Great {action.replace('_', ' ')}!"),
                                   inline=False)
        else:
            fail_msgs = {'shoot': "Wide!", 'pass': "Intercepted!", 'dribble': "Defender stands strong!",
                         'tackle': "Missed!", 'cross': "Overhit!", 'clearance': "Poor clearance!",
                         'through_ball': "Too heavy!", 'interception': "Out of reach!",
                         'cut_inside': "Closed down!", 'key_pass': "No one there!",
                         'long_ball': "Out of play!", 'overlap': "Tracked back!",
                         'block': "Gets through!", 'claim_cross': "Spills it!",
                         'distribution': "Poor pass!", 'hold_up_play': "Dispossessed!",
                         'run_in_behind': "Offside!", 'press_defender': "Can't close down!",
                         'track_back': "Too slow!", 'press': "Can't win it!",
                         'cover': "Gap exposed!", 'track_runner': "Lost them!", 'sweep': "Misjudged!"}
            result_embed.add_field(name="❌ FAILED!",
                                   value=fail_msgs.get(action, f"{action.replace('_', ' ')} unsuccessful!"),
                                   inline=False)

        if player_roll == 20:
            result_embed.add_field(name="🌟 CRITICAL SUCCESS!", value="Perfect execution!", inline=False)
        elif player_roll == 1:
            result_embed.add_field(name="💥 CRITICAL FAILURE!", value="Disaster!", inline=False)

        await suspense_msg.delete()
        await channel.send(embed=result_embed)

        rating_change = self.calculate_rating_change(action, success, player_roll, player['position'])
        async with db.pool.acquire() as conn:
            await conn.execute(
                'UPDATE match_participants SET match_rating = GREATEST(0.0, LEAST(10.0, match_rating + $1)), actions_taken = actions_taken + 1 WHERE match_id = $2 AND user_id = $3',
                rating_change, match_id, player['user_id'])

        # CHECK FOR TEAMMATE SCORING
        if success and attacking_team and action in ['pass', 'through_ball', 'cross', 'key_pass']:
            teammate_result = await self.handle_teammate_followup(
                channel, player, action, minute, match_id, attacking_team
            )
            
            if teammate_result == 'goal':
                return {'success': True, 'goal': True, 'assist': True, 'roll': player_roll}

        return {'success': success, 'goal': is_goal, 'roll': player_roll}

    async def execute_follow_up_action(self, channel, player, adjusted_stats, defender, action, minute, match_id,
                                       member, attacking_team):
        embed = discord.Embed(title=f"⚡ FOLLOW-UP: {action.upper()}!",
                              description=f"**{player['player_name']}** continues the attack!",
                              color=discord.Color.orange())
        await channel.send(embed=embed)
        await asyncio.sleep(1)
        result = await self.execute_action_with_duel(channel, player, adjusted_stats, defender, action,
                                                     minute, match_id, member, attacking_team)
        return 'goal' if result.get('goal') else None

    async def handle_npc_moment(self, channel, team_id, minute, attacking_team, defending_team, is_home):
        async with db.pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT * FROM npc_players WHERE team_id = $1 AND retired = FALSE ORDER BY RANDOM() LIMIT 1",
                team_id)
            npc = dict(result) if result else None
        if not npc:
            return None
        action = random.choice(['shoot', 'pass', 'dribble'])
        stat_value = {'shoot': npc['shooting'], 'pass': npc['passing'], 'dribble': npc['dribbling']}[action]
        roll = random.randint(1, 20)
        total = stat_value + roll
        dc = 80 if action == 'shoot' else 75
        success = total >= dc
        outcome = None
        if action == 'shoot' and success and (roll == 20 or roll >= 18):
            embed = discord.Embed(title=f"⚽ NPC GOAL — Minute {minute}'",
                                  description=f"## **{npc['player_name']}** scores for {attacking_team['team_name']}!",
                                  color=discord.Color.blue())
            embed.add_field(name="🎲 The Shot",
                            value=f"Roll: {roll} + {stat_value} = **{total}** (needed {dc})", inline=False)
            outcome = 'goal'
            async with db.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE npc_players SET season_goals = season_goals + 1 WHERE npc_id = $1",
                    npc['npc_id'])
        else:
            embed = discord.Embed(title=f"🤖 NPC Action — Minute {minute}'",
                                  description=f"**{npc['player_name']}** attempts {action}",
                                  color=discord.Color.blue())
            embed.add_field(name="🎲 Roll",
                            value=f"{roll} + {stat_value} = **{total}** vs DC {dc}\n{'✅ Success' if success else '❌ Failed'}",
                            inline=False)
        await channel.send(embed=embed)
        return outcome

    async def end_match(self, match_id, fixture, channel, home_score, away_score, participants):
        home_team = await db.get_team(fixture['home_team_id'])
        away_team = await db.get_team(fixture['away_team_id'])
        async with db.pool.acquire() as conn:
            await conn.execute(
                'UPDATE fixtures SET home_score = $1, away_score = $2, played = TRUE, playable = FALSE WHERE fixture_id = $3',
                home_score, away_score, fixture['fixture_id'])
            await conn.execute(
                'UPDATE active_matches SET match_state = $1, home_score = $2, away_score = $3 WHERE match_id = $4',
                'completed', home_score, away_score, match_id)
        await self.update_team_stats(fixture['home_team_id'], home_score, away_score)
        await self.update_team_stats(fixture['away_team_id'], away_score, home_score)
        embed = discord.Embed(title="🏁 FULL TIME!",
                              description=f"## {home_team['team_name']} {home_score} - {away_score} {away_team['team_name']}",
                              color=discord.Color.gold())

        home_crest = get_team_crest_url(fixture['home_team_id'])
        if home_crest:
            embed.set_thumbnail(url=home_crest)

        from utils.form_morale_system import update_player_form, update_player_morale
        if participants:
            ratings_text = ""
            for p in participants:
                player = await db.get_player(p['user_id'])
                if player:
                    async with db.pool.acquire() as conn:
                        result = await conn.fetchrow(
                            "SELECT match_rating, actions_taken FROM match_participants WHERE match_id = $1 AND user_id = $2",
                            match_id, p['user_id'])
                    if result:
                        raw_rating = result['match_rating']
                        final_rating = max(0.0, min(10.0, raw_rating))
                        new_form = await update_player_form(p['user_id'], final_rating)
                        if player['team_id'] == fixture['home_team_id']:
                            await update_player_morale(p['user_id'],
                                                       'win' if home_score > away_score else 'loss' if home_score < away_score else 'draw')
                        else:
                            await update_player_morale(p['user_id'],
                                                       'win' if away_score > home_score else 'loss' if away_score < home_score else 'draw')
                        async with db.pool.acquire() as conn:
                            if player['season_apps'] > 0:
                                old_total = player['season_rating'] * player['season_apps']
                                new_avg = (old_total + final_rating) / (player['season_apps'] + 1)
                            else:
                                new_avg = final_rating
                            await conn.execute(
                                "UPDATE players SET season_apps = season_apps + 1, career_apps = career_apps + 1, season_rating = $1 WHERE user_id = $2",
                                new_avg, p['user_id'])
                        rating_emoji = "🌟" if final_rating >= 8 else "⭐" if final_rating >= 7 else "✅" if final_rating >= 6 else "📉"
                        ratings_text += f"{rating_emoji} **{player['player_name']}**: {final_rating:.1f}/10 ({result['actions_taken']} actions)\n"
            if ratings_text:
                embed.add_field(name="⭐ Player Ratings", value=ratings_text, inline=False)
        embed.set_footer(text="Channel deletes in 60 seconds")
        await channel.send(embed=embed)
        await db.add_news(f"{home_team['team_name']} {home_score}-{away_score} {away_team['team_name']}",
                          f"FT Week {fixture['week_number']}", "match_news", None, 3,
                          fixture['week_number'])

        await asyncio.sleep(60)
        try:
            await channel.delete()
        except:
            pass

    async def update_team_stats(self, team_id, goals_for, goals_against):
        if goals_for > goals_against:
            won, drawn, lost, points = 1, 0, 0, 3
        elif goals_for == goals_against:
            won, drawn, lost, points = 0, 1, 0, 1
        else:
            won, drawn, lost, points = 0, 0, 1, 0
        async with db.pool.acquire() as conn:
            await conn.execute(
                'UPDATE teams SET played = played + 1, won = won + $1, drawn = drawn + $2, lost = lost + $3, goals_for = goals_for + $4, goals_against = goals_against + $5, points = points + $6 WHERE team_id = $7',
                won, drawn, lost, goals_for, goals_against, points, team_id)

    async def auto_resolve_moment(self, player, minute, attacking_team, defending_team):
        return None


class EnhancedActionView(discord.ui.View):
    def __init__(self, available_actions, recommended_action, timeout=30):
        super().__init__(timeout=timeout)
        self.chosen_action = None
        emoji_map = {'shoot': '🎯', 'pass': '🎪', 'dribble': '🪄', 'tackle': '🛡️', 'cross': '📤',
                     'clearance': '🚀', 'through_ball': '⚡', 'save': '🧤', 'interception': '👀', 'block': '🧱',
                     'cut_inside': '↩️', 'key_pass': '🔑', 'long_ball': '📡',
                     'overlap': '🏃', 'claim_cross': '✊', 'distribution': '🎯', 'hold_up_play': '💪',
                     'run_in_behind': '🏃', 'press_defender': '⚡', 'track_back': '🔙',
                     'press': '⚡', 'cover': '🛡️', 'track_runner': '🏃', 'sweep': '🧹'}
        for action in available_actions[:5]:
            button = ActionButton(action, emoji_map.get(action, '⚽'),
                                  highlighted=(action == recommended_action))
            self.add_item(button)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class ActionButton(discord.ui.Button):
    def __init__(self, action, emoji, highlighted=False):
        super().__init__(label=action.replace('_', ' ').title(), emoji=emoji,
                         style=discord.ButtonStyle.success if highlighted else discord.ButtonStyle.primary)
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        self.view.chosen_action = self.action
        for item in self.view.children:
            item.disabled = True
        await interaction.response.edit_message(view=self.view)
        self.view.stop()


match_engine = None
