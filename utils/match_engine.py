"""
CRITICAL FIXES:
1. ✅ Match stats now properly increment (goals, assists, actions)
2. ✅ Match rating properly retrieved for MOTM display
3. ✅ All counters working correctly
4. ✅ MOTM DM notification added
5. ✅ Hat-trick notification added
6. ✅ Red card suspension notification added
7. ✅ Form update now uses CORRECT match ratings from database
8. ✅ Action buttons now verify user identity - prevents cross-player interference
9. ✅ MEMORY LEAK FIXED - Auto-cleanup of old matches every hour
10. ✅ European competition support added
11. ✅ ENHANCED D20 SYSTEM - Weighted stats (70/30), position bonuses, accurate probabilities
12. ✅ FOLLOW-UP ACTIONS - Dynamic gameplay with realistic chains (all positions)
"""
import discord
from discord.ext import commands
import asyncio
from database import db
from datetime import datetime, timedelta
import random
import config
import logging
from typing import Dict

logger = logging.getLogger(__name__)

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
        self.active_matches: Dict[int, dict] = {}
        self.pinned_messages: Dict[int, discord.Message] = {}
        self._last_cleanup = datetime.now()
        self._match_timestamps: Dict[int, datetime] = {}

    async def cleanup_old_matches(self):
        """Remove matches older than 6 hours from memory"""
        cutoff = datetime.now() - timedelta(hours=6)
        removed_matches = 0
        removed_messages = 0

        for match_id in list(self.active_matches.keys()):
            match_time = self._match_timestamps.get(match_id, datetime.now())
            if match_time < cutoff:
                del self.active_matches[match_id]
                removed_matches += 1
                if match_id in self._match_timestamps:
                    del self._match_timestamps[match_id]

        for match_id in list(self.pinned_messages.keys()):
            if match_id not in self.active_matches:
                try:
                    msg = self.pinned_messages[match_id]
                    await msg.unpin()
                except:
                    pass
                del self.pinned_messages[match_id]
                removed_messages += 1

        if removed_matches > 0 or removed_messages > 0:
            logger.info(f"🧹 Cleaned up {removed_matches} old matches and {removed_messages} pinned messages")

        self._last_cleanup = datetime.now()

    async def maybe_cleanup(self):
        """Cleanup every hour"""
        if datetime.now() - self._last_cleanup > timedelta(hours=1):
            await self.cleanup_old_matches()

    # ═══════════════════════════════════════════════════════════════
    # ENHANCED D20 SYSTEM - NEW FUNCTIONS
    # ═══════════════════════════════════════════════════════════════

    def get_action_stats(self, action):
        """
        Returns weighted stat configuration for each action
        Format: (attacker_primary, attacker_secondary, defender_primary, defender_secondary)
        Primary = 70% weight, Secondary = 30% weight
        """
        stat_configs = {
            # SHOOTING
            'shoot': ('shooting', 'physical', 'defending', 'physical'),
            'header': ('physical', 'shooting', 'physical', 'defending'),
            
            # PASSING
            'pass': ('passing', 'dribbling', 'pace', 'defending'),
            'through_ball': ('passing', 'dribbling', 'pace', 'defending'),
            'key_pass': ('passing', 'dribbling', 'defending', 'pace'),
            'cross': ('passing', 'physical', 'physical', 'defending'),
            'long_ball': ('passing', 'physical', 'pace', 'defending'),
            
            # DRIBBLING
            'dribble': ('dribbling', 'pace', 'defending', 'pace'),
            'cut_inside': ('dribbling', 'pace', 'defending', 'pace'),
            'overlap': ('pace', 'physical', 'pace', 'defending'),
            'run_in_behind': ('pace', 'dribbling', 'pace', 'defending'),
            
            # PHYSICAL
            'hold_up_play': ('physical', 'dribbling', 'physical', 'defending'),
            
            # DEFENSIVE
            'tackle': ('defending', 'physical', 'dribbling', 'physical'),
            'clearance': ('defending', 'physical', 'shooting', 'pace'),
            'interception': ('defending', 'pace', 'passing', 'pace'),
            'block': ('defending', 'physical', 'shooting', 'physical'),
            'press': ('pace', 'physical', 'passing', 'dribbling'),
            'track_back': ('pace', 'physical', 'pace', 'dribbling'),
            'cover': ('defending', 'pace', 'passing', 'pace'),
            'track_runner': ('pace', 'defending', 'pace', 'dribbling'),
            'press_defender': ('pace', 'physical', 'passing', 'dribbling'),
            
            # GOALKEEPER
            'save': ('defending', 'physical', 'shooting', 'physical'),
            'claim_cross': ('physical', 'defending', 'passing', 'physical'),
            'distribution': ('passing', 'physical', 'pace', 'defending'),
            'sweep': ('pace', 'defending', 'pace', 'passing'),
        }
        return stat_configs.get(action, ('dribbling', 'pace', 'defending', 'pace'))

    def calculate_weighted_stat(self, player_stats, primary_stat, secondary_stat):
        """Calculate weighted stat: 70% primary + 30% secondary"""
        primary_value = player_stats.get(primary_stat, 60)
        secondary_value = player_stats.get(secondary_stat, 60)
        weighted = int((primary_value * 0.7) + (secondary_value * 0.3))
        return max(40, min(99, weighted))

    def get_position_bonus(self, position, action):
        """Position-specific bonuses to d20 rolls"""
        bonuses = {
            'ST': {
                'shoot': 3, 'header': 2, 'hold_up_play': 2, 'run_in_behind': 2
            },
            'W': {
                'dribble': 3, 'cross': 2, 'cut_inside': 2, 'overlap': 2
            },
            'CAM': {
                'pass': 2, 'through_ball': 3, 'key_pass': 3, 'shoot': 1
            },
            'CM': {
                'pass': 2, 'tackle': 2, 'interception': 2, 'long_ball': 2
            },
            'CDM': {
                'tackle': 3, 'interception': 3, 'block': 2, 'cover': 2
            },
            'FB': {
                'tackle': 2, 'cross': 2, 'overlap': 2, 'clearance': 2, 'track_runner': 2
            },
            'CB': {
                'tackle': 3, 'clearance': 3, 'block': 3, 'header': 2, 'interception': 2
            },
            'GK': {
                'save': 5, 'claim_cross': 3, 'distribution': 1, 'sweep': 2
            }
        }
        return bonuses.get(position, {}).get(action, 0)

    def calculate_d20_success_probability(self, player_stat, defender_stat):
        """Calculate exact probability that (player_stat + d20) > (defender_stat + d20)"""
        if defender_stat == 0:
            return 55  # No defender = need 10+ on d20
        
        stat_diff = defender_stat - player_stat
        wins = 0
        
        for p_roll in range(1, 21):
            max_losing_roll = p_roll - stat_diff - 1
            losing_rolls = max(0, min(20, max_losing_roll))
            wins += losing_rolls
        
        probability = (wins / 400) * 100
        return int(probability)

    # ═══════════════════════════════════════════════════════════════
    # FOLLOW-UP ACTIONS SYSTEM
    # ═══════════════════════════════════════════════════════════════

    def get_followup_config(self, action, success):
        """
        Defines realistic follow-up chances after actions
        NOW WORKS FOR ALL POSITION MATCHUPS (midfield vs midfield, etc.)
        """
        followups = {
            # SUCCESSFUL ACTIONS
            'dribble_success': {
                'chance': 0.30,  # 30% - beating defender doesn't always = shot
                'type': 'shooting_chance',
                'desc': "Space created! Shooting opportunity..."
            },
            'cut_inside_success': {
                'chance': 0.40,  # 40% - wingers cutting in often shoot
                'type': 'shooting_chance',
                'desc': "Cut onto strong foot! Shot incoming..."
            },
            'tackle_success': {
                'chance': 0.40,  # 40% - winning ball often leads to break
                'type': 'counter_attack',
                'desc': "Ball won! Counter-attack developing..."
            },
            'interception_success': {
                'chance': 0.40,  # 40% - reading play leads to breaks
                'type': 'counter_attack',
                'desc': "Intercepted! Quick break on..."
            },
            'hold_up_play_success': {
                'chance': 0.25,  # 25% - not every hold-up creates chance
                'type': 'layoff_pass',
                'desc': "Held up! Teammate making run..."
            },
            'run_in_behind_success': {
                'chance': 0.60,  # 60% - beating trap = usually through
                'type': '1v1_keeper',
                'desc': "Through on goal! One-on-one!"
            },
            'block_success': {
                'chance': 0.20,  # 20% - most blocks go away
                'type': 'loose_ball',
                'desc': "Blocked! Ball ricochets loose..."
            },
            'save_success': {
                'chance': 0.25,  # 25% - GK can start counter
                'type': 'distribution_counter',
                'desc': "Great save! Launch counter?"
            },
            'header_success': {
                'chance': 0.15,  # 15% - headers can lead to scrambles
                'type': 'loose_ball',
                'desc': "Header! Ball drops loose..."
            },
            
            # FAILED ACTIONS
            'shoot_fail': {
                'chance': 0.15,  # 15% - most shots go away
                'type': 'rebound',
                'desc': "Shot blocked! Rebound..."
            },
            'header_fail': {
                'chance': 0.20,  # 20% - missed headers often fall to someone
                'type': 'loose_ball',
                'desc': "Missed header! Loose ball..."
            },
            'clearance_fail': {
                'chance': 0.35,  # 35% - poor clearances dangerous
                'type': 'falls_to_attacker',
                'desc': "Poor clearance! Falls to attacker..."
            },
            'pass_fail': {
                'chance': 0.25,  # 25% - interceptions can lead to counters
                'type': 'interception_counter',
                'desc': "Intercepted! They break..."
            },
            'dribble_fail': {
                'chance': 0.20,  # 20% - losing ball can be dangerous
                'type': 'dispossessed_counter',
                'desc': "Dispossessed! Counter on..."
            },
        }
        
        key = f"{action}_{'success' if success else 'fail'}"
        return followups.get(key, None)

    async def handle_followup_action(self, channel, action, success, player, attacking_team,
                                     defending_team, match_id, is_european=False):
        """Execute follow-up action after primary action"""
        config = self.get_followup_config(action, success)
        
        if not config or random.random() > config['chance']:
            return None
        
        # Show follow-up developing
        followup_embed = discord.Embed(
            title="⚡ FOLLOW-UP!",
            description=config['desc'],
            color=discord.Color.orange()
        )
        await channel.send(embed=followup_embed)
        await asyncio.sleep(1.5)
        
        # Execute based on type - PASS PLAYER INFO FOR RATING UPDATES
        if config['type'] == 'shooting_chance':
            return await self.followup_shooting_chance(channel, player, attacking_team, 
                                                      defending_team, match_id, is_european)
        elif config['type'] == 'counter_attack' or config['type'] == 'distribution_counter':
            return await self.followup_counter_attack(channel, player, attacking_team, defending_team, 
                                                     match_id, is_european)
        elif config['type'] == '1v1_keeper':
            return await self.followup_1v1_keeper(channel, player, attacking_team, 
                                                 defending_team, match_id, is_european)
        elif config['type'] == 'rebound':
            return await self.followup_rebound(channel, player, attacking_team, defending_team, 
                                              match_id, is_european)
        elif config['type'] == 'layoff_pass':
            return await self.followup_layoff_pass(channel, player, attacking_team, 
                                                  match_id, is_european)
        elif config['type'] == 'loose_ball':
            return await self.followup_loose_ball(channel, player, attacking_team, defending_team, 
                                                 match_id, is_european)
        elif config['type'] == 'falls_to_attacker':
            return await self.followup_long_shot(channel, player, attacking_team, match_id, is_european)
        elif config['type'] == 'interception_counter' or config['type'] == 'dispossessed_counter':
            return await self.followup_interception_counter(channel, player, defending_team, attacking_team, 
                                                           match_id, is_european)
        
        return None

    async def followup_shooting_chance(self, channel, player, attacking_team, defending_team, 
                                       match_id, is_european=False):
        """After successful dribble - you get a shot!"""
        adjusted_stats = self.apply_form_to_stats(player)
        
        # Get keeper
        async with db.pool.acquire() as conn:
            if is_european:
                keeper = await conn.fetchrow("""
                    SELECT * FROM npc_players WHERE team_id = $1 AND position = 'GK' AND retired = FALSE
                    UNION ALL
                    SELECT * FROM european_npc_players WHERE team_id = $1 AND position = 'GK' AND retired = FALSE
                    LIMIT 1
                """, defending_team['team_id'])
            else:
                keeper = await conn.fetchrow("""
                    SELECT * FROM npc_players WHERE team_id = $1 AND position = 'GK' AND retired = FALSE
                    LIMIT 1
                """, defending_team['team_id'])
            keeper = dict(keeper) if keeper else None
        
        # Shot calculation
        att_p, att_s, def_p, def_s = self.get_action_stats('shoot')
        player_stat = self.calculate_weighted_stat(adjusted_stats, att_p, att_s)
        position_bonus = self.get_position_bonus(player['position'], 'shoot')
        
        player_roll = random.randint(1, 20)
        player_total = player_stat + player_roll + position_bonus
        
        if keeper:
            keeper_stat = self.calculate_weighted_stat(keeper, def_p, def_s)
            keeper_roll = random.randint(1, 20)
            keeper_total = keeper_stat + keeper_roll + 5  # GK bonus
        else:
            keeper_total = 0
        
        success = player_total > keeper_total
        is_goal = success and (player_roll >= 15 or player_total >= keeper_total + 8)
        
        result_embed = discord.Embed(
            title="💥 FOLLOW-UP SHOT!",
            description=f"**{player['player_name']}** unleashes it!\n\nYou: {player_total} vs Keeper: {keeper_total}",
            color=discord.Color.green() if is_goal else discord.Color.red()
        )
        
        if is_goal:
            result_embed.add_field(name="⚽ GOAL!", value=f"**{player['player_name']}** scores!", inline=False)
            async with db.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE match_participants SET goals_scored = goals_scored + 1,
                    match_rating = GREATEST(0.0, LEAST(10.0, match_rating + 1.0))
                    WHERE match_id = $1 AND user_id = $2
                """, match_id, player['user_id'])
                await conn.execute("""
                    UPDATE players SET season_goals = season_goals + 1, career_goals = career_goals + 1
                    WHERE user_id = $1
                """, player['user_id'])
        elif success:
            result_embed.add_field(name="🧤 SAVED!", value="Keeper denies you!", inline=False)
        else:
            result_embed.add_field(name="❌ WIDE!", value="Shot off target!", inline=False)
        
        await channel.send(embed=result_embed)
        return {'goal': is_goal, 'scorer_name': player['player_name'] if is_goal else None}

    async def followup_1v1_keeper(self, channel, player, attacking_team, defending_team, 
                                  match_id, is_european=False):
        """1v1 with keeper - high pressure moment"""
        adjusted_stats = self.apply_form_to_stats(player)
        
        embed = discord.Embed(
            title="🏃💨 ONE-ON-ONE!",
            description=f"**{player['player_name']}** through on goal!",
            color=discord.Color.gold()
        )
        await channel.send(embed=embed)
        await asyncio.sleep(1)
        
        # Get keeper
        async with db.pool.acquire() as conn:
            if is_european:
                keeper = await conn.fetchrow("""
                    SELECT * FROM npc_players WHERE team_id = $1 AND position = 'GK' AND retired = FALSE
                    UNION ALL
                    SELECT * FROM european_npc_players WHERE team_id = $1 AND position = 'GK' AND retired = FALSE
                    LIMIT 1
                """, defending_team['team_id'])
            else:
                keeper = await conn.fetchrow("""
                    SELECT * FROM npc_players WHERE team_id = $1 AND position = 'GK' AND retired = FALSE
                    LIMIT 1
                """, defending_team['team_id'])
        
        player_stat = adjusted_stats['shooting']
        keeper_stat = keeper['defending'] if keeper else 70
        
        player_roll = random.randint(1, 20)
        keeper_roll = random.randint(1, 20)
        
        player_total = player_stat + player_roll + 3
        keeper_total = keeper_stat + keeper_roll
        
        # 65% chance to score in 1v1 (realistic)
        is_goal = player_total > keeper_total
        
        result_embed = discord.Embed(
            title="⚔️ 1v1 SHOWDOWN!",
            color=discord.Color.green() if is_goal else discord.Color.red()
        )
        
        if is_goal:
            result_embed.add_field(
                name="⚽ CLINICAL!",
                value=f"**{player['player_name']}** stays cool!\n\nYou: {player_total} vs Keeper: {keeper_total}",
                inline=False
            )
            async with db.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE match_participants SET goals_scored = goals_scored + 1,
                    match_rating = GREATEST(0.0, LEAST(10.0, match_rating + 1.5))
                    WHERE match_id = $1 AND user_id = $2
                """, match_id, player['user_id'])
                await conn.execute("""
                    UPDATE players SET season_goals = season_goals + 1, career_goals = career_goals + 1
                    WHERE user_id = $1
                """, player['user_id'])
        else:
            result_embed.add_field(
                name="🧤 KEEPER SAVES!",
                value=f"Brilliant save!\n\nKeeper: {keeper_total} vs You: {player_total}",
                inline=False
            )
        
        await channel.send(embed=result_embed)
        return {'goal': is_goal, 'scorer_name': player['player_name'] if is_goal else None}

    async def followup_counter_attack(self, channel, player, attacking_team, defending_team, 
                                     match_id, is_european=False):
        """Quick counter-attack - NOW CREDITS THE PLAYER WHO WON THE BALL"""
        embed = discord.Embed(
            title="⚡💨 COUNTER-ATTACK!",
            description=f"**{attacking_team['team_name']}** breaks forward!",
            color=discord.Color.orange()
        )
        await channel.send(embed=embed)
        await asyncio.sleep(1)
        
        # Get fast attacker
        async with db.pool.acquire() as conn:
            if is_european:
                attacker = await conn.fetchrow("""
                    SELECT * FROM npc_players WHERE team_id = $1 AND position IN ('ST', 'W') AND retired = FALSE
                    ORDER BY pace DESC LIMIT 1
                    UNION ALL
                    SELECT * FROM european_npc_players WHERE team_id = $1 AND position IN ('ST', 'W') AND retired = FALSE
                    ORDER BY pace DESC LIMIT 1
                """, attacking_team['team_id'])
            else:
                attacker = await conn.fetchrow("""
                    SELECT * FROM npc_players WHERE team_id = $1 AND position IN ('ST', 'W') AND retired = FALSE
                    ORDER BY pace DESC LIMIT 1
                """, attacking_team['team_id'])
        
        if not attacker:
            return None
        
        counter_stat = (attacker['pace'] + attacker['dribbling']) // 2
        roll = random.randint(1, 20)
        total = counter_stat + roll + 5
        
        # 25% realistic counter goal rate
        is_goal = total >= 95
        
        result_embed = discord.Embed(
            title="💥 COUNTER RESULT",
            color=discord.Color.green() if is_goal else discord.Color.blue()
        )
        
        if is_goal:
            result_embed.add_field(
                name="⚽ COUNTER GOAL!",
                value=f"**{attacker['player_name']}** finishes the break!",
                inline=False
            )
            
            # ═══ CREDIT THE PLAYER WHO WON THE BALL! ═══
            if player:
                result_embed.add_field(
                    name="🎯 Key Contribution",
                    value=f"**{player['player_name']}** won the ball!",
                    inline=False
                )
                
                async with db.pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE match_participants
                        SET match_rating = GREATEST(0.0, LEAST(10.0, match_rating + 0.6))
                        WHERE match_id = $1 AND user_id = $2
                    """, match_id, player['user_id'])
                print(f"  ⚡ Counter goal credit: +0.6 rating to {player['player_name']}")
            
            # Update NPC stats
            async with db.pool.acquire() as conn:
                if is_european and 'european_npc_id' in attacker:
                    await conn.execute("""
                        UPDATE european_npc_players SET season_goals = season_goals + 1
                        WHERE european_npc_id = $1
                    """, attacker['european_npc_id'])
                else:
                    await conn.execute("""
                        UPDATE npc_players SET season_goals = season_goals + 1 WHERE npc_id = $1
                    """, attacker['npc_id'])
        else:
            result_embed.add_field(
                name="🛡️ DEFENDED!",
                value=f"Counter stopped by {defending_team['team_name']}!",
                inline=False
            )
            
            # Small credit for winning ball even if counter failed
            if player:
                async with db.pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE match_participants
                        SET match_rating = GREATEST(0.0, LEAST(10.0, match_rating + 0.2))
                        WHERE match_id = $1 AND user_id = $2
                    """, match_id, player['user_id'])
        
        await channel.send(embed=result_embed)
        return {'goal': is_goal, 'scorer_name': attacker['player_name'] if is_goal else None}

    async def followup_rebound(self, channel, player, attacking_team, defending_team, match_id, is_european=False):
        """Rebound falls to teammate - NOW CREDITS THE ORIGINAL SHOOTER"""
        async with db.pool.acquire() as conn:
            if is_european:
                attacker = await conn.fetchrow("""
                    SELECT * FROM npc_players WHERE team_id = $1 AND position IN ('ST', 'W', 'CAM') AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
                    UNION ALL
                    SELECT * FROM european_npc_players WHERE team_id = $1 AND position IN ('ST', 'W', 'CAM') AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
                """, attacking_team['team_id'])
            else:
                attacker = await conn.fetchrow("""
                    SELECT * FROM npc_players WHERE team_id = $1 AND position IN ('ST', 'W', 'CAM') AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
                """, attacking_team['team_id'])
        
        if not attacker:
            return None
        
        rebound_stat = (attacker['pace'] + attacker['shooting']) // 2
        roll = random.randint(1, 20)
        total = rebound_stat + roll
        
        is_goal = total >= 85
        
        result_embed = discord.Embed(
            title="🔄 REBOUND!",
            color=discord.Color.gold() if is_goal else discord.Color.blue()
        )
        
        if is_goal:
            result_embed.add_field(
                name="⚽ REBOUND GOAL!",
                value=f"**{attacker['player_name']}** pounces on it!",
                inline=False
            )
            
            # ═══ CREDIT THE ORIGINAL SHOOTER! ═══
            if player:
                result_embed.add_field(
                    name="🎯 Created Chance",
                    value=f"**{player['player_name']}'s** shot led to the goal!",
                    inline=False
                )
                
                async with db.pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE match_participants
                        SET match_rating = GREATEST(0.0, LEAST(10.0, match_rating + 0.4))
                        WHERE match_id = $1 AND user_id = $2
                    """, match_id, player['user_id'])
                print(f"  🔄 Rebound goal credit: +0.4 rating to {player['player_name']}")
            
            # Update NPC stats
            async with db.pool.acquire() as conn:
                if is_european and 'european_npc_id' in attacker:
                    await conn.execute("""
                        UPDATE european_npc_players SET season_goals = season_goals + 1
                        WHERE european_npc_id = $1
                    """, attacker['european_npc_id'])
                else:
                    await conn.execute("""
                        UPDATE npc_players SET season_goals = season_goals + 1 WHERE npc_id = $1
                    """, attacker['npc_id'])
        else:
            result_embed.add_field(name="❌ CLEARED!", value="Defender gets there first!", inline=False)
        
        await channel.send(embed=result_embed)
        return {'goal': is_goal, 'scorer_name': attacker['player_name'] if is_goal else None}

    async def followup_layoff_pass(self, channel, player, attacking_team, match_id, is_european=False):
        """Hold-up play leads to layoff"""
        async with db.pool.acquire() as conn:
            if is_european:
                midfielder = await conn.fetchrow("""
                    SELECT * FROM npc_players WHERE team_id = $1 AND position IN ('CAM', 'CM') AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
                    UNION ALL
                    SELECT * FROM european_npc_players WHERE team_id = $1 AND position IN ('CAM', 'CM') AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
                """, attacking_team['team_id'])
            else:
                midfielder = await conn.fetchrow("""
                    SELECT * FROM npc_players WHERE team_id = $1 AND position IN ('CAM', 'CM') AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
                """, attacking_team['team_id'])
        
        if not midfielder:
            return None
        
        embed = discord.Embed(
            title="🔄 LAYOFF!",
            description=f"**{midfielder['player_name']}** arrives late!",
            color=discord.Color.blue()
        )
        await channel.send(embed=embed)
        await asyncio.sleep(1)
        
        shot_roll = random.randint(1, 20)
        shot_total = midfielder['shooting'] + shot_roll
        is_goal = shot_total >= 85
        
        result_embed = discord.Embed(
            title="💥 LATE RUN!",
            color=discord.Color.gold() if is_goal else discord.Color.blue()
        )
        
        if is_goal:
            result_embed.add_field(
                name="⚽ LAYOFF GOAL!",
                value=f"**{midfielder['player_name']}** finishes!\n🅰️ **ASSIST: {player['player_name']}**",
                inline=False
            )
            async with db.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE match_participants SET assists = assists + 1,
                    match_rating = GREATEST(0.0, LEAST(10.0, match_rating + 0.8))
                    WHERE match_id = $1 AND user_id = $2
                """, match_id, player['user_id'])
                await conn.execute("""
                    UPDATE players SET season_assists = season_assists + 1, career_assists = career_assists + 1
                    WHERE user_id = $1
                """, player['user_id'])
            return {
                'goal': True,
                'scorer_name': midfielder['player_name'],
                'assister_name': player['player_name']
            }
        else:
            result_embed.add_field(name="❌ SAVED!", value="Keeper makes the save!", inline=False)
        
        await channel.send(embed=result_embed)
        return None

    async def followup_loose_ball(self, channel, attacking_team, defending_team, is_european=False):
        """50-50 ball"""
        async with db.pool.acquire() as conn:
            if is_european:
                attacker = await conn.fetchrow("""
                    SELECT * FROM npc_players WHERE team_id = $1 AND retired = FALSE ORDER BY RANDOM() LIMIT 1
                    UNION ALL
                    SELECT * FROM european_npc_players WHERE team_id = $1 AND retired = FALSE ORDER BY RANDOM() LIMIT 1
                """, attacking_team['team_id'])
                defender = await conn.fetchrow("""
                    SELECT * FROM npc_players WHERE team_id = $1 AND retired = FALSE ORDER BY RANDOM() LIMIT 1
                    UNION ALL
                    SELECT * FROM european_npc_players WHERE team_id = $1 AND retired = FALSE ORDER BY RANDOM() LIMIT 1
                """, defending_team['team_id'])
            else:
                attacker = await conn.fetchrow("""
                    SELECT * FROM npc_players WHERE team_id = $1 AND retired = FALSE ORDER BY RANDOM() LIMIT 1
                """, attacking_team['team_id'])
                defender = await conn.fetchrow("""
                    SELECT * FROM npc_players WHERE team_id = $1 AND retired = FALSE ORDER BY RANDOM() LIMIT 1
                """, defending_team['team_id'])
        
        if not attacker or not defender:
            return None
        
        attacker_total = attacker['pace'] + random.randint(1, 20)
        defender_total = defender['pace'] + random.randint(1, 20)
        
        result_embed = discord.Embed(
            title="⚡ 50-50!",
            description=f"**{attacker['player_name']}** vs **{defender['player_name']}**\n\n"
                       f"Attacker: {attacker_total} | Defender: {defender_total}",
            color=discord.Color.green() if attacker_total > defender_total else discord.Color.red()
        )
        
        if attacker_total > defender_total:
            result_embed.add_field(name="✅ ATTACKER WINS!", value=f"{attacking_team['team_name']} keeps it!", inline=False)
        else:
            result_embed.add_field(name="🛡️ DEFENDER CLEARS!", value=f"{defending_team['team_name']} wins it!", inline=False)
        
        await channel.send(embed=result_embed)
        return None

    async def followup_long_shot(self, channel, player, attacking_team, match_id, is_european=False):
        """Long shot from edge of box - NOW PENALIZES POOR CLEARANCES"""
        async with db.pool.acquire() as conn:
            if is_european:
                attacker = await conn.fetchrow("""
                    SELECT * FROM npc_players WHERE team_id = $1 AND position IN ('CAM', 'CM') AND retired = FALSE
                    ORDER BY shooting DESC LIMIT 1
                    UNION ALL
                    SELECT * FROM european_npc_players WHERE team_id = $1 AND position IN ('CAM', 'CM') AND retired = FALSE
                    ORDER BY shooting DESC LIMIT 1
                """, attacking_team['team_id'])
            else:
                attacker = await conn.fetchrow("""
                    SELECT * FROM npc_players WHERE team_id = $1 AND position IN ('CAM', 'CM') AND retired = FALSE
                    ORDER BY shooting DESC LIMIT 1
                """, attacking_team['team_id'])
        
        if not attacker:
            return None
        
        embed = discord.Embed(
            title="💥 LONG SHOT!",
            description=f"**{attacker['player_name']}** from distance!",
            color=discord.Color.orange()
        )
        await channel.send(embed=embed)
        await asyncio.sleep(1)
        
        shot_total = attacker['shooting'] + random.randint(1, 20)
        is_goal = shot_total >= 98  # Long shots very difficult
        
        result_embed = discord.Embed(
            title="🚀 LONG RANGE!",
            color=discord.Color.gold() if is_goal else discord.Color.blue()
        )
        
        if is_goal:
            result_embed.add_field(
                name="⚽ SCREAMER!",
                value=f"**{attacker['player_name']}** into the top corner!",
                inline=False
            )
            
            # ═══ PENALIZE PLAYER FOR POOR CLEARANCE LEADING TO GOAL ═══
            if player:
                result_embed.add_field(
                    name="⚠️ Poor Clearance",
                    value=f"**{player['player_name']}'s** clearance fell straight to them!",
                    inline=False
                )
                
                async with db.pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE match_participants
                        SET match_rating = GREATEST(0.0, LEAST(10.0, match_rating - 0.3))
                        WHERE match_id = $1 AND user_id = $2
                    """, match_id, player['user_id'])
                print(f"  ❌ Poor clearance led to goal: -0.3 rating to {player['player_name']}")
            
            # Update NPC stats
            async with db.pool.acquire() as conn:
                if is_european and 'european_npc_id' in attacker:
                    await conn.execute("""
                        UPDATE european_npc_players SET season_goals = season_goals + 1
                        WHERE european_npc_id = $1
                    """, attacker['european_npc_id'])
                else:
                    await conn.execute("""
                        UPDATE npc_players SET season_goals = season_goals + 1 WHERE npc_id = $1
                    """, attacker['npc_id'])
            
            return {'goal': True, 'scorer_name': attacker['player_name']}
        else:
            result_embed.add_field(name="❌ WIDE!", value="Long-range effort off target!", inline=False)
        
        await channel.send(embed=result_embed)
        return None

    # ═══════════════════════════════════════════════════════════════
    # ORIGINAL FUNCTIONS (keeping everything else the same)
    # ═══════════════════════════════════════════════════════════════

    def get_contextual_defender_positions(self, player_position, action):
        """
        Get realistic defender positions based on player position and action
        Returns list of positions that would realistically oppose this action
        """
        
        # Position-based matchups
        matchups = {
            # STRIKERS face CBs primarily, occasionally CDMs
            'ST': {
                'shoot': ['CB', 'GK'],
                'header': ['CB', 'FB'],
                'hold_up_play': ['CB', 'CDM'],
                'run_in_behind': ['CB', 'FB'],
                'pass': ['CB', 'CDM']
            },
            
            # WINGERS face FBs primarily, occasionally CBs or wingers tracking back
            'W': {
                'dribble': ['FB', 'W', 'CB'],
                'cross': ['FB', 'CB'],
                'cut_inside': ['FB', 'CDM', 'CB'],
                'shoot': ['CB', 'CDM', 'GK'],
                'track_back': ['W', 'FB']  # Defensive action
            },
            
            # ATTACKING MIDS face CDMs/CMs primarily
            'CAM': {
                'shoot': ['CDM', 'CB', 'GK'],
                'through_ball': ['CDM', 'CM', 'CB'],
                'key_pass': ['CDM', 'CM'],
                'dribble': ['CDM', 'CM', 'CB'],
                'long_ball': ['CDM', 'CM']
            },
            
            # CENTRAL MIDS face other CMs/CDMs
            'CM': {
                'pass': ['CM', 'CDM'],
                'through_ball': ['CM', 'CDM', 'CB'],
                'long_ball': ['CM', 'CDM'],
                'tackle': ['CM', 'CAM', 'W'],  # Winning ball from attacking players
                'shoot': ['CDM', 'CB', 'GK']
            },
            
            # DEFENSIVE MIDS face CAMs/CMs/STs
            'CDM': {
                'tackle': ['CAM', 'CM', 'ST'],
                'interception': ['CAM', 'CM', 'ST'],
                'pass': ['CAM', 'CM'],
                'block': ['CAM', 'CM', 'ST'],
                'cover': ['CAM', 'ST']
            },
            
            # FULLBACKS face wingers primarily, occasionally strikers
            'FB': {
                'tackle': ['W', 'ST', 'CAM'],
                'cross': ['FB', 'CB'],  # Overlapping, opposed by defenders
                'overlap': ['FB', 'W'],
                'clearance': ['W', 'ST'],
                'track_runner': ['W', 'ST']
            },
            
            # CENTER BACKS face strikers primarily
            'CB': {
                'tackle': ['ST', 'W', 'CAM'],
                'clearance': ['ST', 'W'],
                'block': ['ST', 'CAM', 'CM'],
                'header': ['ST', 'W'],
                'pass': ['ST', 'CAM']  # When building from back
            },
            
            # GOALKEEPERS face strikers
            'GK': {
                'save': ['ST', 'W', 'CAM', 'CM'],
                'claim_cross': ['ST', 'W'],
                'distribution': ['ST', 'CAM'],
                'sweep': ['ST', 'W'],
                'clearance': ['ST']
            }
        }
        
        # Get appropriate positions for this matchup
        if player_position in matchups and action in matchups[player_position]:
            return matchups[player_position][action]
        
        # Default fallback based on player position
        default_matchups = {
            'ST': ['CB', 'CDM'],
            'W': ['FB', 'CB'],
            'CAM': ['CDM', 'CM'],
            'CM': ['CM', 'CDM'],
            'CDM': ['CAM', 'CM'],
            'FB': ['W', 'ST'],
            'CB': ['ST', 'W'],
            'GK': ['ST', 'W', 'CAM']
        }
        
        return default_matchups.get(player_position, ['CB', 'CDM', 'FB', 'GK'])
        """Get detailed description with follow-up info"""
        descriptions = {
            'shoot': "⚽ **SHOOT**: Take a shot on goal\n→ Success: Possible goal | Fail: Blocked/saved",
            'header': "🎯 **HEADER**: Aerial challenge\n→ Success: Possible goal/clear | Fail: Defender wins",
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
        """Position-specific actions - BALANCED & REALISTIC"""
        position_events = {
            'ST': ['shoot', 'header', 'hold_up_play', 'run_in_behind', 'pass'],
            'W': ['dribble', 'cross', 'cut_inside', 'shoot', 'track_back'],
            'CAM': ['shoot', 'through_ball', 'key_pass', 'dribble', 'long_ball'],
            'CM': ['pass', 'through_ball', 'long_ball', 'tackle', 'shoot'],
            'CDM': ['tackle', 'interception', 'pass', 'block', 'cover'],
            'FB': ['tackle', 'cross', 'overlap', 'clearance', 'track_runner'],
            'CB': ['tackle', 'clearance', 'block', 'header', 'pass'],
            'GK': ['save', 'claim_cross', 'distribution', 'sweep', 'clearance']
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

    async def start_match(self, fixture: dict, interaction: discord.Interaction, is_european: bool = False):
        """Start a match - supports both domestic and European competitions"""

        # Get teams from appropriate tables
        if is_european:
            home_team = await self.get_team_info(fixture['home_team_id'], is_european=True)
            away_team = await self.get_team_info(fixture['away_team_id'], is_european=True)
        else:
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

        # Competition display
        comp_display = fixture.get('competition', 'League')
        if is_european:
            comp_display = "🏆 Champions League" if fixture.get('competition') == 'CL' else "🏆 Europa League"
            if fixture.get('leg', 1) > 1:
                comp_display += f" (Leg {fixture['leg']})"

        embed = discord.Embed(
            title="🟢 MATCH STARTING!",
            description=f"## {home_team['team_name']} 🆚 {away_team['team_name']}\n\n**{comp_display}** • Week {fixture['week_number']}",
            color=discord.Color.green()
        )

        home_crest = get_team_crest_url(fixture['home_team_id'])
        if home_crest:
            embed.set_thumbnail(url=home_crest)

        rivalry = None
        try:
            from data.rivalries import get_rivalry
            rivalry = get_rivalry(fixture['home_team_id'], fixture['away_team_id'])
            if rivalry:
                embed.add_field(
                    name="🔥 RIVALRY MATCH!",
                    value=f"**{rivalry['name']}**\nExpect fireworks in this heated derby!",
                    inline=False
                )
                embed.color = discord.Color.red()
        except ImportError:
            pass

        embed.add_field(name="🏠 Home", value=f"**{home_team['team_name']}**\n{home_team.get('league', 'N/A')}",
                        inline=True)
        embed.add_field(name="✈️ Away", value=f"**{away_team['team_name']}**\n{away_team.get('league', 'N/A')}",
                        inline=True)

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

        # Track when this match started for cleanup
        self._match_timestamps[match_id] = datetime.now()

        self.active_matches[match_id] = {'rivalry': rivalry, 'is_european': is_european}

        for user_id in player_users:
            player = await db.get_player(user_id)
            if player:
                async with db.pool.acquire() as conn:
                    await conn.execute(
                        'INSERT INTO match_participants (match_id, user_id, team_id, match_rating) VALUES ($1, $2, $3, $4)',
                        match_id, user_id, player['team_id'], 5.0)

        await asyncio.sleep(5)
        await self.run_match(match_id, fixture, match_channel, num_events, is_european)

    async def get_team_info(self, team_id, is_european=False):
        """Get team info from appropriate table"""
        async with db.pool.acquire() as conn:
            if is_european:
                # Try european_teams first
                team = await conn.fetchrow("""
                                           SELECT team_id, team_name, 'European' as league
                                           FROM european_teams
                                           WHERE team_id = $1
                                           """, team_id)

                # Fallback to regular teams
                if not team:
                    team = await conn.fetchrow("""
                                               SELECT team_id, team_name, league
                                               FROM teams
                                               WHERE team_id = $1
                                               """, team_id)
            else:
                team = await conn.fetchrow("""
                                           SELECT team_id, team_name, league
                                           FROM teams
                                           WHERE team_id = $1
                                           """, team_id)

            return dict(team) if team else None

    async def run_match(self, match_id: int, fixture: dict, channel: discord.TextChannel, num_events: int,
                        is_european: bool = False):
        # Check if cleanup needed (runs every hour)
        await self.maybe_cleanup()

        home_team = await self.get_team_info(fixture['home_team_id'], is_european)
        away_team = await self.get_team_info(fixture['away_team_id'], is_european)
        home_score = 0
        away_score = 0

        async with db.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM match_participants WHERE match_id = $1", match_id)
            participants = [dict(row) for row in rows]

        home_participants = [p for p in participants if p['team_id'] == fixture['home_team_id']]
        away_participants = [p for p in participants if p['team_id'] == fixture['away_team_id']]

        possible_minutes = list(range(3, 91, 3))
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
                                                                 away_team, True, match_id, is_european)
                        if result and result.get('goal'):
                            home_score += 1
                            await self.post_goal_celebration(channel, result['scorer_name'], home_team['team_name'],
                                                             home_team['team_id'], home_score, away_score,
                                                             result.get('assister_name'))
                            await self.update_pinned_score(channel, match_id, home_team, away_team, home_score,
                                                           away_score, minute)
                else:
                    result = await self.handle_npc_moment(channel, fixture['home_team_id'], minute, home_team,
                                                          away_team, True, is_european)
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
                                                                 home_team, False, match_id, is_european)
                        if result and result.get('goal'):
                            away_score += 1
                            await self.post_goal_celebration(channel, result['scorer_name'], away_team['team_name'],
                                                             away_team['team_id'], home_score, away_score,
                                                             result.get('assister_name'))
                            await self.update_pinned_score(channel, match_id, home_team, away_team, home_score,
                                                           away_score, minute)
                else:
                    result = await self.handle_npc_moment(channel, fixture['away_team_id'], minute, away_team,
                                                          home_team, False, is_european)
                    if result == 'goal':
                        away_score += 1
                        await self.update_pinned_score(channel, match_id, home_team, away_team, home_score, away_score,
                                                       minute)

            async with db.pool.acquire() as conn:
                await conn.execute(
                    'UPDATE active_matches SET home_score = $1, away_score = $2, current_minute = $3 WHERE match_id = $4',
                    home_score, away_score, minute, match_id)

            await asyncio.sleep(2)

        await self.end_match(match_id, fixture, channel, home_score, away_score, participants, is_european)

    async def handle_player_moment(self, channel, player, participant, minute, attacking_team, defending_team,
                                   is_home, match_id, is_european=False):
        member = channel.guild.get_member(player['user_id'])
        if not member:
            return None

        adjusted_stats = self.apply_form_to_stats(player)
        available_actions = self.get_position_events(player['position'])

        # ═══ GET CONTEXTUAL DEFENDER BASED ON PLAYER POSITION ═══
        # Pick a random action to determine defender type (more realistic)
        sample_action = random.choice(available_actions)
        defender_positions = self.get_contextual_defender_positions(player['position'], sample_action)
        
        # Build position filter for SQL
        position_filter = ', '.join([f"'{pos}'" for pos in defender_positions])

        async with db.pool.acquire() as conn:
            if is_european:
                result = await conn.fetchrow(f"""
                    SELECT * FROM npc_players
                    WHERE team_id = $1 AND position IN ({position_filter}) AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
                    UNION ALL
                    SELECT * FROM european_npc_players
                    WHERE team_id = $1 AND position IN ({position_filter}) AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
                """, defending_team['team_id'])
            else:
                result = await conn.fetchrow(f"""
                    SELECT * FROM npc_players 
                    WHERE team_id = $1 AND position IN ({position_filter}) AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
                """, defending_team['team_id'])
            defender = dict(result) if result else None
        
        # Fallback: if no appropriate defender found, get any defender
        if not defender:
            async with db.pool.acquire() as conn:
                if is_european:
                    result = await conn.fetchrow("""
                        SELECT * FROM npc_players
                        WHERE team_id = $1 AND position IN ('CB', 'FB', 'CDM', 'GK') AND retired = FALSE
                        ORDER BY RANDOM() LIMIT 1
                        UNION ALL
                        SELECT * FROM european_npc_players
                        WHERE team_id = $1 AND position IN ('CB', 'FB', 'CDM', 'GK') AND retired = FALSE
                        ORDER BY RANDOM() LIMIT 1
                    """, defending_team['team_id'])
                else:
                    result = await conn.fetchrow("""
                        SELECT * FROM npc_players 
                        WHERE team_id = $1 AND position IN ('CB', 'FB', 'CDM', 'GK') AND retired = FALSE
                        ORDER BY RANDOM() LIMIT 1
                    """, defending_team['team_id'])
                defender = dict(result) if result else None

        from utils.form_morale_system import get_form_description
        form_desc = get_form_description(player['form'])

        # ═══ CONTEXTUAL SCENARIO TEXT ═══
        if defender:
            defender_pos = defender.get('position', 'DEF')
            
            # Create realistic scenario based on matchup
            scenarios = {
                ('ST', 'CB'): f"You receive the ball with {defender['player_name']} marking you tight!",
                ('ST', 'GK'): f"Through ball! Just you and keeper {defender['player_name']}!",
                ('W', 'FB'): f"Ball at your feet, {defender['player_name']} closing you down!",
                ('W', 'CB'): f"You cut inside, {defender['player_name']} shifts across to cover!",
                ('CAM', 'CDM'): f"Space in the hole! {defender['player_name']} steps up to close you!",
                ('CAM', 'CM'): f"Midfield battle! {defender['player_name']} pressing hard!",
                ('CM', 'CM'): f"50-50 challenge with {defender['player_name']} in midfield!",
                ('CM', 'CDM'): f"You look to break the lines, {defender['player_name']} reads it!",
                ('CDM', 'CAM'): f"Opposition playmaker incoming! {defender['player_name']} on the ball!",
                ('CDM', 'ST'): f"Striker dropping deep! {defender['player_name']} trying to turn you!",
                ('FB', 'W'): f"Winger {defender['player_name']} running at you with pace!",
                ('CB', 'ST'): f"Striker {defender['player_name']} making a run! Can you stop them?",
                ('GK', 'ST'): f"Shot incoming from {defender['player_name']}! React fast!"
            }
            
            matchup_key = (player['position'], defender_pos)
            scenario_text = scenarios.get(matchup_key, 
                f"Ball comes to you! {defender['player_name']} ({defender_pos}) closing in!")
        else:
            scenario_text = f"Ball comes to you in a dangerous area!\n{defending_team['team_name']}'s defense scrambling!"

        embed = discord.Embed(
            title=f"🎯 {member.display_name}'S MOMENT!",
            description=f"## {player['player_name']} ({player['position']})\n**{minute}'** | Form: {form_desc}\n\n{scenario_text}",
            color=discord.Color.gold()
        )

        team_crest = get_team_crest_url(attacking_team['team_id'])
        if team_crest:
            embed.set_thumbnail(url=team_crest)

        # ═══ CLEAN ACTION DISPLAY ═══
        actions_text = ""
        for action in available_actions[:5]:
            # Get stat configuration
            att_p, att_s, def_p, def_s = self.get_action_stats(action)
            
            # Calculate weighted stats
            player_weighted = self.calculate_weighted_stat(adjusted_stats, att_p, att_s)
            player_pos_bonus = self.get_position_bonus(player['position'], action)
            
            if defender:
                defender_weighted = self.calculate_weighted_stat(defender, def_p, def_s)
                defender_pos_bonus = self.get_position_bonus(defender.get('position', 'CB'), action)
                
                # Calculate probability WITH position bonuses factored in
                # Average effect of position bonuses on probability (~10% per +2 bonus)
                bonus_diff = player_pos_bonus - defender_pos_bonus
                chance = self.calculate_d20_success_probability(player_weighted, defender_weighted)
                # Adjust for position bonus difference (each +1 bonus ≈ 2.5% chance)
                chance = max(5, min(95, chance + (bonus_diff * 2)))
            else:
                defender_weighted = 0
                chance = 55 + (player_pos_bonus * 2)  # Unopposed, just position bonus helps
            
            # Color coding
            if chance >= 65:
                emoji = "🟢"
            elif chance >= 50:
                emoji = "🟡"
            else:
                emoji = "🔴"
            
            # CLEAN, SCANNABLE FORMAT
            action_name = action.replace('_', ' ').title()
            actions_text += f"{emoji} **{action_name}** — {chance}%\n"
            
            # Show key stats compactly
            actions_text += f"   {att_p[:3].upper()}/{att_s[:3].upper()}: {player_weighted}"
            if player_pos_bonus > 0:
                actions_text += f" (+{player_pos_bonus})"
            
            if defender:
                actions_text += f" vs {defender_weighted}"
                if defender_pos_bonus > 0:
                    actions_text += f" (+{defender_pos_bonus})"
                actions_text += "\n"
            else:
                actions_text += "\n"
            
            actions_text += "\n"

        embed.add_field(name="⚡ CHOOSE ACTION", value=actions_text, inline=False)
        
        if defender:
            embed.set_footer(text=f"⚔️ vs {defender['player_name']} ({defender['position']}) • 30 sec!")
        else:
            embed.set_footer(text="⏱️ 30 seconds!")

        view = EnhancedActionView(available_actions, player['user_id'], timeout=30)
        message = await channel.send(content=f"📢 {member.mention}", embed=embed, view=view)
        await view.wait()

        action = view.chosen_action if view.chosen_action else random.choice(available_actions)
        if not view.chosen_action:
            await channel.send(f"⏰ {member.mention} **AUTO-SELECTED**: {action.upper()}")

        result = await self.execute_action_with_duel(channel, player, adjusted_stats, defender, action, minute,
                                                     match_id, member, attacking_team, is_european)

        return result

    async def execute_action_with_duel(self, channel, player, adjusted_stats, defender, action, minute,
                                       match_id, member, attacking_team, is_european=False):
        
        # Get stat configuration
        att_p, att_s, def_p, def_s = self.get_action_stats(action)
        
        # Calculate weighted stats
        player_stat = self.calculate_weighted_stat(adjusted_stats, att_p, att_s)
        
        # Get position bonus
        position_bonus = self.get_position_bonus(player['position'], action)
        
        # D20 ROLL
        player_roll = random.randint(1, 20)
        player_roll_with_bonus = player_roll + position_bonus
        player_total = player_stat + player_roll_with_bonus
        
        # Defender rolls
        defender_roll = 0
        defender_total = 0
        defender_stat_value = 0
        defender_position_bonus = 0
        
        if defender:
            defender_stat_value = self.calculate_weighted_stat(defender, def_p, def_s)
            defender_roll = random.randint(1, 20)
            
            # ═══ CRITICAL: NPCs GET POSITION BONUSES TOO! ═══
            defender_position_bonus = self.get_position_bonus(defender.get('position', 'CB'), action)
            defender_total = defender_stat_value + defender_roll + defender_position_bonus
        
        # SUCCESS CHECK
        success = player_total > defender_total if defender_total > 0 else player_roll_with_bonus >= 10
        
        # CRITICAL SUCCESS/FAILURE
        critical_success = player_roll == 20
        critical_failure = player_roll == 1
        
        # Suspense
        suspense_embed = discord.Embed(
            title=f"⚡ {action.replace('_', ' ').upper()}!",
            description=f"**{player['player_name']}** attempts the action...",
            color=discord.Color.orange()
        )
        suspense_msg = await channel.send(embed=suspense_embed)
        await asyncio.sleep(1.5)
        
        # ═══ CLEAN RESULT DISPLAY ═══
        result_embed = discord.Embed(
            title=f"🎲 {action.replace('_', ' ').upper()}",
            color=discord.Color.green() if success else discord.Color.red()
        )
        
        # Show the duel
        if defender and defender_total > 0:
            duel_text = f"**YOU**\n"
            duel_text += f"{att_p.upper()}/{att_s.upper()}: **{player_stat}**\n"
            duel_text += f"🎲 **{player_roll}**"
            if position_bonus > 0:
                duel_text += f" +{position_bonus} ({player['position']})"
            duel_text += f" = **{player_roll_with_bonus}**\n"
            duel_text += f"Total: **{player_total}**\n\n"
            
            duel_text += f"**{defender['player_name']}**\n"
            duel_text += f"{def_p.upper()}/{def_s.upper()}: **{defender_stat_value}**\n"
            duel_text += f"🎲 **{defender_roll}**"
            if defender_position_bonus > 0:
                duel_text += f" +{defender_position_bonus} ({defender.get('position', 'DEF')})"
            duel_text += f"\n"
            duel_text += f"Total: **{defender_total}**\n\n"
            
            if success:
                duel_text += f"✅ **YOU WIN**"
            else:
                duel_text += f"❌ **DEFENDER WINS**"
            
            result_embed.add_field(name="⚔️ Duel", value=duel_text, inline=False)
        else:
            result_embed.add_field(
                name="🎲 Roll",
                value=f"Stat: **{player_stat}** | Roll: **{player_roll_with_bonus}** | Total: **{player_total}**\n\n"
                      f"{'✅ Success!' if success else '❌ Failed!'}",
                inline=False
            )
        
        is_goal = False
        scorer_name = None
        assister_name = None
        rating_change = 0
        
        # ═══ CRITICAL HIT ═══
        if critical_success:
            result_embed.add_field(
                name="🌟 NAT 20!",
                value="Perfect execution!",
                inline=False
            )
            rating_change = 0.5
            
            # Shooting/heading actions = guaranteed goal on nat 20
            if action in ['shoot', 'header']:
                is_goal = True
                scorer_name = player['player_name']
                rating_change = 1.8
                
                # Update stats for critical goal
                async with db.pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE match_participants SET goals_scored = goals_scored + 1
                        WHERE match_id = $1 AND user_id = $2
                    """, match_id, player['user_id'])
                    
                    await conn.execute(
                        "UPDATE players SET season_goals = season_goals + 1, career_goals = career_goals + 1 WHERE user_id = $1",
                        player['user_id']
                    )
                    
                    goals_row = await conn.fetchrow(
                        "SELECT goals_scored FROM match_participants WHERE match_id = $1 AND user_id = $2",
                        match_id, player['user_id']
                    )
                    if goals_row and goals_row['goals_scored'] == 3:
                        await self.send_hattrick_notification(player, attacking_team)
                
                from utils.form_morale_system import update_player_morale
                await update_player_morale(player['user_id'], 'goal')
        
        # ═══ CRITICAL FAILURE ═══
        elif critical_failure:
            result_embed.add_field(
                name="💥 NAT 1!",
                value="Disaster!",
                inline=False
            )
            rating_change = -0.5
            success = False
        
        # ═══ NORMAL OUTCOMES ═══
        if not is_goal and not critical_failure:
            if action in ['shoot', 'header'] and success:
                if player_roll_with_bonus >= 18 or player_total >= defender_total + 10:
                    goal_type = "header" if action == 'header' else "shot"
                    result_embed.add_field(name="⚽ GOAL!", value=f"**{player['player_name']}** scores from the {goal_type}!", inline=False)
                    is_goal = True
                    scorer_name = player['player_name']
                    rating_change = 1.2
                    
                    async with db.pool.acquire() as conn:
                        await conn.execute("""
                            UPDATE match_participants SET goals_scored = goals_scored + 1
                            WHERE match_id = $1 AND user_id = $2
                        """, match_id, player['user_id'])
                        
                        await conn.execute(
                            "UPDATE players SET season_goals = season_goals + 1, career_goals = career_goals + 1 WHERE user_id = $1",
                            player['user_id']
                        )
                        
                        goals_row = await conn.fetchrow(
                            "SELECT goals_scored FROM match_participants WHERE match_id = $1 AND user_id = $2",
                            match_id, player['user_id']
                        )
                        if goals_row and goals_row['goals_scored'] == 3:
                            await self.send_hattrick_notification(player, attacking_team)
                    
                    from utils.form_morale_system import update_player_morale
                    await update_player_morale(player['user_id'], 'goal')
                else:
                    result_embed.add_field(name="🧤 SAVED!", value="Keeper saves it!", inline=False)
                    rating_change = -0.1
            
            elif action in ['pass', 'through_ball', 'key_pass', 'cross'] and success:
                assist_chance = {'pass': 0.35, 'through_ball': 0.40, 'key_pass': 0.45, 'cross': 0.40}
                if random.random() < assist_chance.get(action, 0.35):
                    teammate_result = await self.handle_teammate_goal(channel, player, attacking_team, match_id, is_european)
                    if teammate_result:
                        is_goal = True
                        scorer_name = teammate_result['scorer_name']
                        assister_name = player['player_name']
                        rating_change = 0.8
                        
                        async with db.pool.acquire() as conn:
                            await conn.execute("""
                                UPDATE match_participants SET assists = assists + 1
                                WHERE match_id = $1 AND user_id = $2
                            """, match_id, player['user_id'])
                        
                        result_embed.add_field(
                            name="⚽ TEAMMATE SCORES!",
                            value=f"**{scorer_name}** finishes!\n🅰️ **{player['player_name']}**",
                            inline=False
                        )
                    else:
                        result_embed.add_field(name="✅ GREAT PASS!", value="Chance created!", inline=False)
                        rating_change = 0.3
                else:
                    result_embed.add_field(name="✅ SUCCESS!", value=f"Good {action.replace('_', ' ')}!", inline=False)
                    rating_change = 0.3
            
            elif success:
                result_embed.add_field(name="✅ SUCCESS!", value=f"Great {action.replace('_', ' ')}!", inline=False)
                rating_change = 0.3
            
            else:
                result_embed.add_field(name="❌ FAILED!", value="Unsuccessful!", inline=False)
                rating_change = -0.1
        
        await suspense_msg.delete()
        await channel.send(embed=result_embed)
        
        # Update rating
        async with db.pool.acquire() as conn:
            await conn.execute("""
                UPDATE match_participants
                SET match_rating = GREATEST(0.0, LEAST(10.0, match_rating + $1)),
                    actions_taken = actions_taken + 1
                WHERE match_id = $2 AND user_id = $3
            """, rating_change, match_id, player['user_id'])
        
        # ═══════════════════════════════════════════════════════════════
        # CHECK FOR FOLLOW-UP ACTIONS
        # ═══════════════════════════════════════════════════════════════
        
        followup_result = await self.handle_followup_action(
            channel, action, success, player, attacking_team, defending_team, match_id, is_european
        )
        
        # If follow-up resulted in goal, override
        if followup_result and followup_result.get('goal'):
            is_goal = True
            scorer_name = followup_result.get('scorer_name')
            assister_name = followup_result.get('assister_name')
        
        return {
            'success': success,
            'goal': is_goal,
            'roll': player_roll,
            'scorer_name': scorer_name,
            'assister_name': assister_name
        }

    async def send_hattrick_notification(self, player, team):
        """Send DM when player scores hat-trick"""
        try:
            user = await self.bot.fetch_user(player['user_id'])
            embed = discord.Embed(
                title="🎩⚽⚽⚽ HAT-TRICK!",
                description=f"**{player['player_name']}**, you scored 3 goals in one match!\n\n**{team['team_name']}** will remember this legendary performance!",
                color=discord.Color.purple()
            )
            team_crest = get_team_crest_url(team['team_id'])
            if team_crest:
                embed.set_thumbnail(url=team_crest)
            embed.set_footer(text="⭐ A historic achievement!")
            await user.send(embed=embed)
            print(f"🎩 Hat-trick notification sent to {player['player_name']}")
        except Exception as e:
            print(f"❌ Could not send hat-trick DM to {player['user_id']}: {e}")

    async def send_red_card_notification(self, player, attacking_team, defending_team):
        """Send DM when player receives red card"""
        try:
            user = await self.bot.fetch_user(player['user_id'])
            embed = discord.Embed(
                title="🟥 RED CARD - SUSPENSION!",
                description=f"**{player['player_name']}**, you've been sent off!\n\n**YOU WILL MISS THE NEXT MATCH** due to suspension.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="⚠️ What This Means",
                value="• Cannot participate in next fixture\n• Team plays without you\n• Impacts your form rating",
                inline=False
            )
            team_crest = get_team_crest_url(attacking_team['team_id'])
            if team_crest:
                embed.set_thumbnail(url=team_crest)
            embed.set_footer(text=f"Match: {attacking_team['team_name']} vs {defending_team['team_name']}")
            await user.send(embed=embed)
            print(f"🟥 Red card notification sent to {player['player_name']}")
        except Exception as e:
            print(f"❌ Could not send red card DM to {player['user_id']}: {e}")

    async def handle_teammate_goal(self, channel, player, attacking_team, match_id, is_european=False):
        """Handle teammate scoring after assist"""
        async with db.pool.acquire() as conn:
            if is_european:
                teammate = await conn.fetchrow(
                    """SELECT player_name FROM npc_players
                       WHERE team_id = $1 AND position IN ('ST', 'W', 'CAM') AND retired = FALSE
                       ORDER BY RANDOM() LIMIT 1
                       UNION ALL
                    SELECT player_name FROM european_npc_players
                    WHERE team_id = $1 AND position IN ('ST', 'W', 'CAM') AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1""",
                    attacking_team['team_id']
                )
            else:
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

    async def handle_npc_moment(self, channel, team_id, minute, attacking_team, defending_team, is_home,
                                is_european=False):
        async with db.pool.acquire() as conn:
            if is_european:
                result = await conn.fetchrow("""
                    SELECT * FROM npc_players WHERE team_id = $1 AND retired = FALSE ORDER BY RANDOM() LIMIT 1
                    UNION ALL
                    SELECT * FROM european_npc_players WHERE team_id = $1 AND retired = FALSE ORDER BY RANDOM() LIMIT 1
                """, team_id)
            else:
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
                title=f"⚽ NPC GOAL — {minute}'",
                description=f"## **{npc['player_name']}** scores for {attacking_team['team_name']}!",
                color=discord.Color.blue()
            )
            await channel.send(embed=embed)
            async with db.pool.acquire() as conn:
                if is_european and 'european_npc_id' in npc:
                    await conn.execute(
                        "UPDATE european_npc_players SET season_goals = season_goals + 1 WHERE european_npc_id = $1",
                        npc['european_npc_id']
                    )
                else:
                    await conn.execute(
                        "UPDATE npc_players SET season_goals = season_goals + 1 WHERE npc_id = $1",
                        npc['npc_id']
                    )
            return 'goal'

        return None

    async def post_goal_celebration(self, channel, scorer_name, team_name, team_id, home_score, away_score,
                                    assister_name=None):
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

    async def end_match(self, match_id, fixture, channel, home_score, away_score, participants, is_european=False):
        home_team = await self.get_team_info(fixture['home_team_id'], is_european)
        away_team = await self.get_team_info(fixture['away_team_id'], is_european)

        async with db.pool.acquire() as conn:
            if is_european:
                await conn.execute(
                    'UPDATE european_fixtures SET home_score = $1, away_score = $2, played = TRUE, playable = FALSE WHERE fixture_id = $3',
                    home_score, away_score, fixture['fixture_id']
                )
            else:
                await conn.execute(
                    'UPDATE fixtures SET home_score = $1, away_score = $2, played = TRUE, playable = FALSE WHERE fixture_id = $3',
                    home_score, away_score, fixture['fixture_id']
                )

        if not is_european:
            await self.update_team_stats(fixture['home_team_id'], home_score, away_score)
            await self.update_team_stats(fixture['away_team_id'], away_score, home_score)

        from utils.form_morale_system import update_player_form, update_player_morale

        async with db.pool.acquire() as conn:
            updated_ratings = await conn.fetch("""
                SELECT user_id, match_rating FROM match_participants
                WHERE match_id = $1 AND user_id IS NOT NULL
            """, match_id)

        rating_lookup = {row['user_id']: row['match_rating'] for row in updated_ratings}

        for participant in participants:
            if participant['user_id']:
                actual_rating = rating_lookup.get(participant['user_id'], participant['match_rating'])
                new_form = await update_player_form(participant['user_id'], actual_rating)
                print(f"  📊 Form updated for user {participant['user_id']}: Rating {actual_rating:.1f} → Form {new_form}")

        for participant in participants:
            if participant['user_id']:
                async with db.pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE players SET season_apps = season_apps + 1, career_apps = career_apps + 1
                        WHERE user_id = $1
                    """, participant['user_id'])
                print(f"  👕 Appearance recorded for user {participant['user_id']}")

        for participant in participants:
            if participant['user_id']:
                player_team = participant['team_id']
                if player_team == fixture['home_team_id']:
                    if home_score > away_score:
                        await update_player_morale(participant['user_id'], 'win')
                    elif home_score < away_score:
                        await update_player_morale(participant['user_id'], 'loss')
                    else:
                        await update_player_morale(participant['user_id'], 'draw')
                else:
                    if away_score > home_score:
                        await update_player_morale(participant['user_id'], 'win')
                    elif away_score < home_score:
                        await update_player_morale(participant['user_id'], 'loss')
                    else:
                        await update_player_morale(participant['user_id'], 'draw')

        try:
            from utils.traits_system import check_trait_unlocks
            for participant in participants:
                if participant['user_id']:
                    await check_trait_unlocks(participant['user_id'], bot=self.bot)
        except ImportError:
            pass

        rivalry_info = self.active_matches.get(match_id, {}).get('rivalry')
        if rivalry_info:
            try:
                from data.rivalries import get_rivalry_bonuses
                winning_team_id = fixture['home_team_id'] if home_score > away_score else \
                    fixture['away_team_id'] if away_score > home_score else None

                if winning_team_id:
                    bonuses = get_rivalry_bonuses(rivalry_info['intensity'])
                    for participant in participants:
                        if participant['user_id'] and participant['team_id'] == winning_team_id:
                            await update_player_morale(participant['user_id'], 'win')
                            async with db.pool.acquire() as conn:
                                await conn.execute(
                                    "UPDATE players SET form = LEAST(100, form + $1) WHERE user_id = $2",
                                    bonuses['form_boost'], participant['user_id']
                                )
                    rivalry_embed = discord.Embed(
                        title=f"🔥 {rivalry_info['name']} VICTORY!",
                        description=f"Derby win! Extra bonuses!",
                        color=discord.Color.gold()
                    )
                    await channel.send(embed=rivalry_embed)
            except ImportError:
                pass

        if participants:
            user_participants = [p for p in participants if p['user_id']]

            if user_participants:
                async with db.pool.acquire() as conn:
                    updated_participants = await conn.fetch("""
                        SELECT user_id, match_rating, goals_scored, assists, actions_taken
                        FROM match_participants WHERE match_id = $1 AND user_id IS NOT NULL
                    """, match_id)

                if updated_participants:
                    motm = max(updated_participants, key=lambda p: p['match_rating'])

                    async with db.pool.acquire() as conn:
                        await conn.execute("""
                            UPDATE players SET season_motm = season_motm + 1, career_motm = career_motm + 1
                            WHERE user_id = $1
                        """, motm['user_id'])

                    motm_player = await db.get_player(motm['user_id'])

                    motm_embed = discord.Embed(
                        title="⭐ MAN OF THE MATCH",
                        description=f"**{motm_player['player_name']}**\nRating: **{motm['match_rating']:.1f}/10**",
                        color=discord.Color.gold()
                    )

                    motm_embed.add_field(
                        name="📊 Stats",
                        value=f"Goals: {motm['goals_scored']} | Assists: {motm['assists']} | Actions: {motm['actions_taken']}",
                        inline=False
                    )

                    team_crest = get_team_crest_url(motm_player['team_id'])
                    if team_crest:
                        motm_embed.set_thumbnail(url=team_crest)

                    await channel.send(embed=motm_embed)
                    print(f"⭐ MOTM: {motm_player['player_name']} ({motm['match_rating']:.1f}/10)")

                    try:
                        user = await self.bot.fetch_user(motm['user_id'])
                        dm_embed = discord.Embed(
                            title="⭐ MAN OF THE MATCH!",
                            description=f"**{motm['match_rating']:.1f}/10** in {home_team['team_name']} vs {away_team['team_name']}",
                            color=discord.Color.gold()
                        )
                        dm_embed.add_field(
                            name="📊 Performance",
                            value=f"⚽ Goals: **{motm['goals_scored']}**\n🅰️ Assists: **{motm['assists']}**\n⚡ Actions: **{motm['actions_taken']}**",
                            inline=False
                        )
                        if team_crest:
                            dm_embed.set_thumbnail(url=team_crest)
                        dm_embed.set_footer(text="🏆 Career MOTM increased!")
                        await user.send(embed=dm_embed)
                        print(f"✅ MOTM DM sent to {motm_player['player_name']}")
                    except Exception as e:
                        print(f"❌ Could not DM MOTM to {motm['user_id']}: {e}")

        embed = discord.Embed(
            title="🏁 FULL TIME!",
            description=f"## {home_team['team_name']} {home_score} - {away_score} {away_team['team_name']}",
            color=discord.Color.gold()
        )

        home_crest = get_team_crest_url(fixture['home_team_id'])
        if home_crest:
            embed.set_thumbnail(url=home_crest)

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

    async def simulate_npc_match(self, home_team_id, away_team_id, week=None, is_european=False):
        """Simulate NPC match"""
        async with db.pool.acquire() as conn:
            if is_european:
                home_team = await conn.fetchrow("""
                    SELECT team_id, team_name FROM european_teams WHERE team_id = $1
                """, home_team_id)
                away_team = await conn.fetchrow("""
                    SELECT team_id, team_name FROM european_teams WHERE team_id = $1
                """, away_team_id)

                if not home_team:
                    home_team = await conn.fetchrow("""
                        SELECT team_id, team_name FROM teams WHERE team_id = $1
                    """, home_team_id)
                if not away_team:
                    away_team = await conn.fetchrow("""
                        SELECT team_id, team_name FROM teams WHERE team_id = $1
                    """, away_team_id)
            else:
                home_team = await conn.fetchrow("""
                    SELECT team_id, team_name FROM teams WHERE team_id = $1
                """, home_team_id)
                away_team = await conn.fetchrow("""
                    SELECT team_id, team_name FROM teams WHERE team_id = $1
                """, away_team_id)

            if not home_team or not away_team:
                raise ValueError(f"Could not find teams: {home_team_id}, {away_team_id}")

            if is_european:
                home_npcs = await conn.fetch("""
                    SELECT overall_rating FROM npc_players WHERE team_id = $1 AND retired = FALSE
                    UNION ALL
                    SELECT overall_rating FROM european_npc_players WHERE team_id = $1 AND retired = FALSE
                """, home_team_id)

                away_npcs = await conn.fetch("""
                    SELECT overall_rating FROM npc_players WHERE team_id = $1 AND retired = FALSE
                    UNION ALL
                    SELECT overall_rating FROM european_npc_players WHERE team_id = $1 AND retired = FALSE
                """, away_team_id)
            else:
                home_npcs = await conn.fetch("""
                    SELECT overall_rating FROM npc_players WHERE team_id = $1 AND retired = FALSE
                """, home_team_id)

                away_npcs = await conn.fetch("""
                    SELECT overall_rating FROM npc_players WHERE team_id = $1 AND retired = FALSE
                """, away_team_id)

            home_rating = sum(p['overall_rating'] for p in home_npcs) / len(home_npcs) if home_npcs else 75
            away_rating = sum(p['overall_rating'] for p in away_npcs) / len(away_npcs) if away_npcs else 75

            home_advantage = 5
            home_attack = (home_rating + home_advantage) / 100
            away_attack = away_rating / 100

            home_goals = 0
            away_goals = 0

            num_chances = random.randint(8, 12)

            for _ in range(num_chances):
                if random.random() < (home_attack * 0.25):
                    home_goals += 1

                if random.random() < (away_attack * 0.22):
                    away_goals += 1

            home_goals = min(home_goals, 5)
            away_goals = min(away_goals, 5)

            if random.random() < 0.05:
                home_goals = min(home_goals + random.randint(0, 2), 7)
                away_goals = min(away_goals + random.randint(0, 2), 7)

            return {
                'home_score': home_goals,
                'away_score': away_goals,
                'home_team': home_team['team_name'],
                'away_team': away_team['team_name']
            }


class EnhancedActionView(discord.ui.View):
    def __init__(self, available_actions, user_id, timeout=30):
        super().__init__(timeout=timeout)
        self.chosen_action = None
        self.owner_user_id = user_id

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
        if interaction.user.id != self.view.owner_user_id:
            await interaction.response.send_message(
                "❌ These aren't your action buttons! Wait for your own moment.",
                ephemeral=True
            )
            return

        await interaction.response.defer()
        self.view.chosen_action = self.action
        for item in self.view.children:
            item.disabled = True
        await interaction.edit_original_response(view=self.view)
        self.view.stop()


match_engine = None
