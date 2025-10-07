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
        
        # Get team crest
        from utils.football_data_api import get_team_crest_url
        team_crest = get_team_crest_url(team_id)
        
        if action == 'shoot' and success and (roll == 20 or total >= dc + 5):
            embed = discord.Embed(
                title=f"⚽ NPC GOAL - Minute {minute}'",
                description=f"**{npc['player_name']}** SCORES for {attacking_team['team_name']}!\n\n"
                           f"*The stadium erupts!*",
                color=discord.Color.blue()
            )
            
            if team_crest:
                embed.set_thumbnail(url=team_crest)
            
            embed.add_field(
                name="🎲 The Strike",
                value=f"Roll: {roll} + {modifier} = **{total}** (DC {dc})\n"
                      f"**{npc['player_name']}** ({npc['overall_rating']} OVR) finds the net!",
                inline=False
            )
            
            outcome = 'goal'
            
            async with db.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE npc_players SET season_goals = season_goals + 1 WHERE npc_id = $1",
                    npc['npc_id']
                )
        else:
            narrative = self.get_action_narrative(action, npc['player_name'])
            
            embed = discord.Embed(
                title=f"🤖 NPC Action - Minute {minute}'",
                description=narrative,
                color=discord.Color.blue()
            )
            
            if team_crest:
                embed.set_thumbnail(url=team_crest)
            
            result_text = "✅ Successful!" if success else "❌ Failed!"
            
            embed.add_field(
                name="🎲 Roll Result",
                value=f"{result_text}\n"
                      f"**{npc['player_name']}** ({npc['overall_rating']} OVR)\n"
                      f"Roll: {roll} + {modifier} = **{total}** (DC {dc})",
                inline=False
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
        
        # Get team crests
        from utils.football_data_api import get_team_crest_url
        home_crest = get_team_crest_url(fixture['home_team_id'])
        
        embed = discord.Embed(
            title="🏁 FULL TIME!",
            description=f"**{home_team['team_name']} {home_score} - {away_score} {away_team['team_name']}**\n\n"
                       f"*The final whistle blows! What a match!*",
            color=discord.Color.gold()
        )
        
        if home_crest:
            embed.set_thumbnail(url=home_crest)
        
        # Update form and morale for participants
        from utils.form_morale_system import update_player_form, update_player_morale
        
        if participants:
            ratings_text = ""
            for p in participants:
                player = await db.get_player(p['user_id'])
                if player:
                    async with db.pool.acquire() as conn:
                        result = await conn.fetchrow(
                            "SELECT match_rating, actions_taken, goals_scored FROM match_participants WHERE match_id = $1 AND user_id = $2",
                            match_id, p['user_id']
                        )
                    
                    if result:
                        raw_rating = result['match_rating']
                        actions = result['actions_taken']
                        goals = result['goals_scored']
                        final_rating = max(0.0, min(10.0, raw_rating))
                        
                        # Rating emoji
                        if final_rating >= 8.0:
                            rating_emoji = "⭐⭐⭐"
                        elif final_rating >= 7.0:
                            rating_emoji = "⭐⭐"
                        elif final_rating >= 6.0:
                            rating_emoji = "⭐"
                        else:
                            rating_emoji = "📊"
                        
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
                        
                        goal_text = f" ⚽×{goals}" if goals > 0 else ""
                        ratings_text += f"{rating_emoji} **{player['player_name']}**: {final_rating:.1f}/10{goal_text} ({actions} actions)\n"
            
            if ratings_text:
                embed.add_field(name="⭐ Player Ratings", value=ratings_text, inline=False)
        
        # Match stats
        embed.add_field(
            name="📊 Match Stats",
            value=f"**{home_team['team_name']}**: {home_score} goals\n"
                  f"**{away_team['team_name']}**: {away_score} goals",
            inline=False
        )
        
        embed.set_footer(text="Channel deletes in 60 seconds • GG!")
        
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
            'cross': '📦',
            'clearance': '🚀',
            'through_ball': '⚡',
            'save': '🧤',
            'through_ball_receive': '💨',
            'penalty_area_dribble': '🔥',
            'cut_inside': '↪️',
            'key_pass': '🔑',
            'long_ball': '🌙',
            'interception': '✋',
            'block': '🧱',
            'overlap': '🏃',
            'claim_cross': '✊',
            'distribution': '🎯'
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
        self.view.chosen_action = self.action
        
        for item in self.view.children:
            item.disabled = True
        
        await interaction.response.edit_message(view=self.view)
        self.view.stop()

match_engine = None
