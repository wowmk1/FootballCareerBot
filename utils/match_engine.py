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
