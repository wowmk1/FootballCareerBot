import discord
from discord.ext import commands
import asyncio
from database import db
from datetime import datetime
import random
import config

# Import crest functions at top level
try:
    from utils.football_data_api import get_team_crest_url, get_competition_logo

    print("✅ Loaded crests_database directly")
except ImportError:
    print("⚠️ crests_database not found, using fallback")


    def get_team_crest_url(team_id):
        return ""


    def get_competition_logo(comp):
        return ""


class MatchEngine:
    def __init__(self, bot):
        self.bot = bot
        self.active_matches = {}
        self.pinned_messages = {}

    def get_action_description_detailed(self, action):
        """Get detailed description with follow-up info"""
        descriptions = {
            'shoot': "⚽ **SHOOT**: Take a shot on goal\n→ Success: Possible goal | Fail: Blocked/saved",
            'pass': "🎯 **PASS**: Find a teammate safely\n→ Success: 35% chance teammate scores (assist) | Fail: Intercepted",
            'dribble': "💨 **DRIBBLE**: Take on defender 1v1\n→ Success: Create space, may get shooting chance | Fail: Dispossessed",
            'tackle': "🛡️ **TACKLE**: Win the ball back\n→ Success: Gain possession | Fail: Beaten/foul",
            'cross': "📤 **CROSS**: Deliver ball into box\n→ Success: 40% chance teammate scores (assist) | Fail: Cleared",
            'clearance': "🚀 **CLEAR**: Get ball away from danger\n→ Success: Safety | Fail: Poor clearance",
            'save': "🧤 **SAVE**: Stop the shot\n→ Success: Keep clean sheet | Fail: Goal conceded",
            'through_ball': "⚡ **THROUGH BALL**: Split defense\n→ Success: 40% chance teammate scores (assist) | Fail: Intercepted",
            'interception': "👀 **INTERCEPT**: Read and cut out pass\n→ Success: Win possession | Fail: Miss the ball",
            'block': "🧱 **BLOCK**: Body on the line\n→ Success: Heroic block | Fail: Shot gets through",
            'cut_inside': "↩️ **CUT INSIDE**: Move to center for shot\n→ Success: Shooting opportunity | Fail: Closed down",
            'key_pass': "🔑 **KEY PASS**: Create clear chance\n→ Success: 45% chance teammate scores (assist) | Fail: Defended",
            'long_ball': "📡 **LONG BALL**: Switch play/launch attack\n→ Success: Create opportunity | Fail: Intercepted",
            'overlap': "🏃 **OVERLAP**: Run past teammate\n→ Success: Crossing opportunity | Fail: Tracked back",
            'claim_cross': "✊ **CLAIM CROSS**: Catch/punch away\n→ Success: Command box | Fail: Drop/spill",
            'distribution': "🎯 **DISTRIBUTE**: Start attack from GK\n→ Success: Launch counter | Fail: Poor pass",
            'hold_up_play': "💪 **HOLD UP**: Shield ball for support\n→ Success: Maintain possession, pass option | Fail: Dispossessed",
            'run_in_behind': "🏃 **RUN BEHIND**: Off-ball run\n→ Success: 1v1 with keeper possible | Fail: Offside/caught",
            'press_defender': "⚡ **PRESS HIGH**: Force mistake\n→ Success: Win ball high | Fail: Bypassed",
            'track_back': "🔙 **TRACK BACK**: Help defense\n→ Success: Stop attack | Fail: Too slow",
            'press': "⚡ **PRESS**: Hunt the ball\n→ Success: Win possession | Fail: Bypassed",
            'cover': "🛡️ **COVER**: Fill defensive gap\n→ Success: Stop attack | Fail: Exposed",
            'track_runner': "🏃 **TRACK RUNNER**: Stay with attacker\n→ Success: Deny space | Fail: Lost them",
            'sweep': "🧹 **SWEEP**: Rush out behind defense\n→ Success: Clear danger | Fail: Caught out"
        }
        return descriptions.get(action, f"Attempt {action.replace('_', ' ')}")

    def get_position_events(self, position):
        """Position-specific actions - BUTTONS MUST MATCH DESCRIPTIONS"""
        position_events = {
            'ST': ['shoot', 'pass', 'hold_up_play', 'run_in_behind', 'press_defender'],
            'W': ['shoot', 'dribble', 'cross', 'cut_inside', 'pass'],
            'CAM': ['shoot', 'through_ball', 'key_pass', 'dribble', 'pass'],
            'CM': ['pass', 'through_ball', 'long_ball', 'tackle', 'shoot'],
            'CDM': ['tackle', 'interception', 'pass', 'block', 'cover'],
            'FB': ['tackle', 'cross', 'overlap', 'clearance', 'track_runner'],
            'CB': ['tackle', 'clearance', 'block', 'pass', 'interception'],
            'GK': ['save', 'claim_cross', 'distribution', 'clearance', 'sweep']
        }
        return position_events.get(position, ['pass', 'dribble', 'tackle', 'shoot', 'clearance'])

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
            print(f"❌ Error updating pinned score: {e}")

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
                        if result and result.get('goal'):
                            home_score += 1
                            await self.post_goal_celebration(channel, result['scorer_name'], home_team['team_name'],
                                                             home_team['team_id'], home_score, away_score, result.get('assister_name'))
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
                        if result and result.get('goal'):
                            away_score += 1
                            await self.post_goal_celebration(channel, result['scorer_name'], away_team['team_name'],
                                                             away_team['team_id'], home_score, away_score, result.get('assister_name'))
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
            return None

        adjusted_stats = self.apply_form_to_stats(player)
        available_actions = self.get_position_events(player['position'])

        async with db.pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT * FROM npc_players WHERE team_id = $1 AND position IN ('CB', 'FB', 'CDM', 'GK') ORDER BY RANDOM() LIMIT 1",
                defending_team['team_id']
            )
            defender = dict(result) if result else None

        from utils.form_morale_system import get_form_description
        form_desc = get_form_description(player['form'])

        scenario_text = f"Ball comes to you in a dangerous area!\n{defending_team['team_name']}'s defense scrambling!"

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
            if opp_crest:
                embed.set_footer(
                    text=f"Defending: {defender['player_name']} ({defender['position']}) • {defending_team['team_name']}",
                    icon_url=opp_crest
                )
            else:
                embed.set_footer(
                    text=f"Defending: {defender['player_name']} ({defender['position']}) • {defending_team['team_name']}")

            embed.add_field(
                name=f"🛡️ Defending: {defender['player_name']} ({defender['position']})",
                value=f"⚡ PAC: **{defender['pace']}** | 🛡️ DEF: **{defender['defending']}** | 💪 PHY: **{defender['physical']}**",
                inline=False
            )

        actions_text = ""
        for action in available_actions:
            player_stat_name = self.get_stat_for_action(action)
            player_stat_value = adjusted_stats[player_stat_name]
            defender_stat_name = self.get_defender_stat(action)
            defender_stat_value = defender[defender_stat_name] if defender else 70
            chance = self.calculate_success_chance(player_stat_value, defender_stat_value)

            emoji = "🟢" if chance >= 60 else "🟡" if chance >= 45 else "🔴"

            action_desc = self.get_action_description_detailed(action)
            actions_text += f"{emoji} {action_desc}\n   Success: ~{chance}%\n\n"

        embed.add_field(name="⚡ AVAILABLE ACTIONS", value=actions_text, inline=False)
        embed.add_field(name="⏱️ TIME LIMIT", value="**30 SECONDS** to choose!", inline=False)

        view = EnhancedActionView(available_actions, timeout=30)
        message = await channel.send(content=f"📢 {member.mention}", embed=embed, view=view)
        await view.wait()

        action = view.chosen_action if view.chosen_action else random.choice(available_actions)
        if not view.chosen_action:
            await channel.send(f"⏰ {member.mention} **AUTO-SELECTED**: {action.upper()}")

        result = await self.execute_action_with_duel(channel, player, adjusted_stats, defender, action, minute,
                                                     match_id, member, attacking_team)

        return result

    async def execute_action_with_duel(self, channel, player, adjusted_stats, defender, action, minute,
                                       match_id, member, attacking_team):
        stat_name = self.get_stat_for_action(action)
        player_stat = adjusted_stats[stat_name]
        player_roll = random.randint(1, 20)
        player_total = player_stat + player_roll

        defender_roll = 0
        defender_total = 0
        defender_stat_value = 0

        if defender:
            defender_stat_name = self.get_defender_stat(action)
            defender_stat_value = defender[defender_stat_name]
            defender_roll = random.randint(1, 20)
            defender_total = defender_stat_value + defender_roll

        success = player_total > defender_total if defender_total > 0 else player_roll >= 10

        suspense_embed = discord.Embed(
            title=f"⚡ {action.replace('_', ' ').upper()}!",
            description=f"**{player['player_name']}** attempts the action...",
            color=discord.Color.orange()
        )
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
            result_embed.add_field(
                name="🎲 Your Roll",
                value=f"**{stat_name.upper()}: {player_stat}**\n🎲 Roll: **{player_roll}**\n💯 Total: **{player_total}**",
                inline=False
            )

        is_goal = False
        scorer_name = None
        assister_name = None
        rating_change = 0

        if action == 'shoot' and success:
            if player_roll == 20 or player_total >= defender_total + 10:
                result_embed.add_field(
                    name="⚽ GOOOOAAAL!",
                    value=f"**{player['player_name']}** SCORES! What a finish!",
                    inline=False
                )
                is_goal = True
                scorer_name = player['player_name']
                rating_change = 1.2
                
                async with db.pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE players SET season_goals = season_goals + 1, career_goals = career_goals + 1 WHERE user_id = $1",
                        player['user_id']
                    )
                from utils.form_morale_system import update_player_morale
                await update_player_morale(player['user_id'], 'goal')
            else:
                result_embed.add_field(
                    name="🧤 SAVED!",
                    value=f"Goalkeeper makes a brilliant save!",
                    inline=False
                )
                rating_change = -0.1

        elif action in ['pass', 'through_ball', 'key_pass', 'cross'] and success:
            assist_chance = {'pass': 0.35, 'through_ball': 0.40, 'key_pass': 0.45, 'cross': 0.40}
            if random.random() < assist_chance.get(action, 0.35):
                teammate_result = await self.handle_teammate_goal(channel, player, attacking_team, match_id)
                if teammate_result:
                    is_goal = True
                    scorer_name = teammate_result['scorer_name']
                    assister_name = player['player_name']
                    rating_change = 0.8
                    
                    result_embed.add_field(
                        name="⚽ TEAMMATE SCORES FROM YOUR PASS!",
                        value=f"**{scorer_name}** finishes it!\n🅰️ **ASSIST: {player['player_name']}**\nGreat {action.replace('_', ' ')}!",
                        inline=False
                    )
                else:
                    result_embed.add_field(name="✅ SUCCESS!",
                                           value=f"Great {action.replace('_', ' ')}! Chance created.", inline=False)
                    rating_change = 0.3
            else:
                result_embed.add_field(name="✅ SUCCESS!", value=f"Perfect {action.replace('_', ' ')}!", inline=False)
                rating_change = 0.3

        elif action == 'dribble' and success:
            result_embed.add_field(name="✅ BEATEN THE DEFENDER!", value=f"You've created space!", inline=False)
            rating_change = 0.3

        elif success:
            result_embed.add_field(name="✅ SUCCESS!", value=f"Great {action.replace('_', ' ')}!", inline=False)
            rating_change = 0.3

        else:
            result_embed.add_field(name="❌ FAILED!", value=f"{action.replace('_', ' ')} unsuccessful!", inline=False)
            rating_change = -0.1

        await suspense_msg.delete()
        await channel.send(embed=result_embed)

        # Update match rating
        async with db.pool.acquire() as conn:
            await conn.execute(
                'UPDATE match_participants SET match_rating = GREATEST(0.0, LEAST(10.0, match_rating + $1)), actions_taken = actions_taken + 1 WHERE match_id = $2 AND user_id = $3',
                rating_change, match_id, player['user_id']
            )

        return {
            'success': success, 
            'goal': is_goal, 
            'roll': player_roll,
            'scorer_name': scorer_name,
            'assister_name': assister_name
        }

    async def handle_teammate_goal(self, channel, player, attacking_team, match_id):
        """Handle teammate scoring after assist - returns dict with scorer info"""
        async with db.pool.acquire() as conn:
            teammate = await conn.fetchrow(
                """SELECT player_name FROM npc_players
                   WHERE team_id = $1 AND position IN ('ST', 'W', 'CAM') AND retired = FALSE
                   ORDER BY RANDOM() LIMIT 1""",
                attacking_team['team_id']
            )
            if teammate:
                await conn.execute(
                    """UPDATE players SET season_assists = season_assists + 1, career_assists = career_assists + 1 
                       WHERE user_id = $1""",
                    player['user_id']
                )
                return {'scorer_name': teammate['player_name']}
        return None

    async def handle_npc_moment(self, channel, team_id, minute, attacking_team, defending_team, is_home):
        async with db.pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT * FROM npc_players WHERE team_id = $1 AND retired = FALSE ORDER BY RANDOM() LIMIT 1",
                team_id
            )
            npc = dict(result) if result else None

        if not npc:
            return None

        action = random.choice(['shoot', 'pass'])
        stat_value = npc['shooting'] if action == 'shoot' else npc['passing']
        roll = random.randint(1, 20)
        total = stat_value + roll

        success = total >= 75

        if action == 'shoot' and success and roll >= 18:
            embed = discord.Embed(
                title=f"⚽ NPC GOAL — Minute {minute}'",
                description=f"## **{npc['player_name']}** scores for {attacking_team['team_name']}!",
                color=discord.Color.blue()
            )
            await channel.send(embed=embed)
            async with db.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE npc_players SET season_goals = season_goals + 1 WHERE npc_id = $1",
                    npc['npc_id']
                )
            return 'goal'

        return None

    async def post_goal_celebration(self, channel, scorer_name, team_name, team_id, home_score, away_score, assister_name=None):
        celebrations = ["🔥🔥🔥 **GOOOOAAAALLL!!!** 🔥🔥🔥", "⚽⚽⚽ **WHAT A GOAL!!!** ⚽⚽⚽"]
        
        description = f"## **{scorer_name}** scores for {team_name}!\n\n"
        if assister_name:
            description += f"🅰️ **ASSIST:** {assister_name}\n\n"
        description += f"**{home_score} - {away_score}**"
        
        embed = discord.Embed(
            title=random.choice(celebrations),
            description=description,
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
        await channel.send(embed=embed)
        await asyncio.sleep(3)

    async def end_match(self, match_id, fixture, channel, home_score, away_score, participants):
        home_team = await db.get_team(fixture['home_team_id'])
        away_team = await db.get_team(fixture['away_team_id'])

        async with db.pool.acquire() as conn:
            await conn.execute(
                'UPDATE fixtures SET home_score = $1, away_score = $2, played = TRUE, playable = FALSE WHERE fixture_id = $3',
                home_score, away_score, fixture['fixture_id']
            )

        await self.update_team_stats(fixture['home_team_id'], home_score, away_score)
        await self.update_team_stats(fixture['away_team_id'], away_score, home_score)

        # ============================================
        # UPDATE FORM BASED ON MATCH RATINGS
        # ============================================
        from utils.form_morale_system import update_player_form

        for participant in participants:
            if participant['user_id']:
                new_form = await update_player_form(
                    participant['user_id'],
                    participant['match_rating']
                )
                print(
                    f"  📊 Form updated for user {participant['user_id']}: Rating {participant['match_rating']:.1f} → Form {new_form}")

        # ============================================
        # UPDATE MORALE BASED ON MATCH RESULT
        # ============================================
        from utils.form_morale_system import update_player_morale

        for participant in participants:
            if participant['user_id']:
                player_team = participant['team_id']

                # Determine if player won, lost, or drew
                if player_team == fixture['home_team_id']:
                    if home_score > away_score:
                        await update_player_morale(participant['user_id'], 'win')
                        print(f"  😊 Morale boost for user {participant['user_id']} (WIN)")
                    elif home_score < away_score:
                        await update_player_morale(participant['user_id'], 'loss')
                        print(f"  😕 Morale drop for user {participant['user_id']} (LOSS)")
                    else:
                        await update_player_morale(participant['user_id'], 'draw')
                        print(f"  😐 Morale unchanged for user {participant['user_id']} (DRAW)")
                else:  # Away team
                    if away_score > home_score:
                        await update_player_morale(participant['user_id'], 'win')
                        print(f"  😊 Morale boost for user {participant['user_id']} (WIN)")
                    elif away_score < home_score:
                        await update_player_morale(participant['user_id'], 'loss')
                        print(f"  😕 Morale drop for user {participant['user_id']} (LOSS)")
                    else:
                        await update_player_morale(participant['user_id'], 'draw')
                        print(f"  😐 Morale unchanged for user {participant['user_id']} (DRAW)")

        # ============================================
        # END OF MORALE UPDATE
        # ============================================

        # ============================================
        # END OF FORM UPDATE
        # ============================================

        embed = discord.Embed(
            title="🏁 FULL TIME!",
            description=f"## {home_team['team_name']} {home_score} - {away_score} {away_team['team_name']}",
            color=discord.Color.gold()
        )

        home_crest = get_team_crest_url(fixture['home_team_id'])
        if home_crest:
            embed.set_thumbnail(url=home_crest)

        # POST RESULT TO match-results CHANNEL
        try:
            from utils.event_poster import post_match_result_to_channel
            await post_match_result_to_channel(self.bot, channel.guild, fixture, home_score, away_score)
        except Exception as e:
            print(f"❌ Could not post match result: {e}")

        embed.set_footer(text="Channel deletes in 60 seconds")
        await channel.send(embed=embed)

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
                won, drawn, lost, goals_for, goals_against, points, team_id
            )


class EnhancedActionView(discord.ui.View):
    def __init__(self, available_actions, timeout=30):
        super().__init__(timeout=timeout)
        self.chosen_action = None

        emoji_map = {
            'shoot': '🎯', 'pass': '🎪', 'dribble': '🪄', 'tackle': '🛡️', 'cross': '📤',
            'clearance': '🚀', 'through_ball': '⚡', 'save': '🧤', 'interception': '👀',
            'block': '🧱', 'cut_inside': '↩️', 'key_pass': '🔑', 'long_ball': '📡',
            'overlap': '🏃', 'claim_cross': '✊', 'distribution': '🎯', 'hold_up_play': '💪',
            'run_in_behind': '🏃', 'press_defender': '⚡', 'track_back': '🔙',
            'press': '⚡', 'cover': '🛡️', 'track_runner': '🏃', 'sweep': '🧹'
        }

        for action in available_actions[:5]:
            button = ActionButton(action, emoji_map.get(action, '⚽'))
            self.add_item(button)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class ActionButton(discord.ui.Button):
    def __init__(self, action, emoji):
        label = action.replace('_', ' ').title()
        super().__init__(
            label=label,
            emoji=emoji,
            style=discord.ButtonStyle.primary
        )
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        # CRITICAL: Defer immediately to prevent timeout during match actions
        await interaction.response.defer()

        self.view.chosen_action = self.action
        for item in self.view.children:
            item.disabled = True

        # Use edit_original_response after defer
        await interaction.edit_original_response(view=self.view)
        self.view.stop()


match_engine = None
