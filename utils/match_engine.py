"""
ENHANCED MATCH ENGINE - COMPLETE VERSION WITH ALL FIXES + SKIP/AFK BUTTONS + SHOT PLACEMENT
✅ Fix #1: Fair player distribution (13 moments each)
✅ Fix #2: Teammate scoring priority (75% user, position-weighted)
✅ Fix #3: High engagement (40-50 events, decision every 60-90s)
✅ Fix #4: Exciting NPC moments (saves, near misses, counters)
✅ Fix #5: Enhanced follow-up system (already existed)
✅ Fix #6: Better action descriptions with follow-up info
✅ Fix #7: Recommended action highlighting (⭐)
✅ Fix #8: Tutorial for first-time players
✅ Fix #9: Defending team parameter fix (no more freezing)
✅ Fix #10: Minute generation fix (handles 45+ events)
✅ NEW: Skip Turn button (no tracking)
✅ NEW: Mark AFK button (appears after timeout)
✅ NEW: Auto-play for AFK players
✅ FIXED: Skip vs Timeout distinction (no false AFK marking)
✅ NEW: Interactive Shot Placement System with 5 options
✅ NEW: Beautiful goal visualization graphics
✅ NEW: Risk/reward shooting mechanics
✅ FIXED: european_npc_id column error
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
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

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
        self.match_yellow_cards: Dict[int, Dict[int, int]] = {}
        self.match_stats: Dict[int, dict] = {}

        # ✅ NEW: Timeout and AFK tracking
        self.player_timeouts: Dict[int, set] = {}  # match_id -> {user_ids who timed out}
        self.afk_players: Dict[int, set] = {}  # match_id -> {user_ids marked AFK}

    # ═══════════════════════════════════════════════════════════════
    # EVENT DISTRIBUTION SYSTEM (NEW)
    # ═══════════════════════════════════════════════════════════════

    def calculate_event_distribution(self, home_participants, away_participants):
        """
        ✅ FIX #1: Fair distribution based on player count
        High-engagement system with lots of action
        """
        total_players = len(home_participants) + len(away_participants)

        if total_players == 0:
            return {
                'player_moments': 0,
                'npc_moments': 30,
                'set_pieces': 10,
                'total': 40
            }

        # ✅ Each player gets 13 moments (sweet spot for engagement)
        moments_per_player = 13
        player_moments = total_players * moments_per_player

        # ✅ Solo players get slightly more NPC opposition
        if total_players == 1:
            npc_moments = 20
            set_pieces = 10
        else:
            npc_moments = 15
            set_pieces = 8

        total_events = player_moments + npc_moments + set_pieces

        # ✅ Cap at 55 events to keep matches reasonable (~45 min)
        if total_events > 55:
            excess = total_events - 55
            player_moments = max(total_players * 10, player_moments - excess)
            total_events = player_moments + npc_moments + set_pieces

        return {
            'player_moments': player_moments,
            'npc_moments': npc_moments,
            'set_pieces': set_pieces,
            'total': total_events
        }

    async def create_fair_player_schedule(self, home_participants, away_participants, player_moments):
        """
        ✅ FIX #1: Fair schedule where each player gets equal moments ±1
        Better players get +1 extra moment
        """
        all_participants = home_participants + away_participants

        if not all_participants or player_moments == 0:
            return []

        # Base moments per player
        base_moments = player_moments // len(all_participants)
        extra_moments = player_moments % len(all_participants)

        moments_distribution = {}

        # Everyone gets base amount
        for participant in all_participants:
            moments_distribution[participant['user_id']] = base_moments

        # Distribute extras weighted by rating
        if extra_moments > 0:
            player_ratings = []
            for p in all_participants:
                player = await db.get_player(p['user_id'])
                player_ratings.append((p, player['overall_rating'] if player else 70))

            # Give extras to top-rated players
            player_ratings.sort(key=lambda x: x[1], reverse=True)
            for i in range(extra_moments):
                participant = player_ratings[i][0]
                moments_distribution[participant['user_id']] += 1

        # Create schedule
        schedule = []
        for participant in all_participants:
            player = await db.get_player(participant['user_id'])
            count = moments_distribution[participant['user_id']]
            team_side = 'home' if participant in home_participants else 'away'

            for _ in range(count):
                schedule.append({
                    'type': 'player',
                    'participant': participant,
                    'player': player,
                    'team_side': team_side
                })

            print(f"   {player['player_name']}: {count} moments")

        random.shuffle(schedule)
        return schedule

    async def show_tutorial_if_needed(self, channel, user_id):
        """
        ✅ FIX #8: Tutorial for first-time players
        Shows on first match only
        """
        async with db.pool.acquire() as conn:
            played_before = await conn.fetchval("""
                SELECT COUNT(*) FROM match_participants WHERE user_id = $1
            """, user_id)

            if played_before == 0:
                embed = discord.Embed(
                    title="📚 First Match? Here's How It Works!",
                    description="Welcome to your first interactive match! Here's a quick guide:",
                    color=discord.Color.blue()
                )

                embed.add_field(
                    name="🎯 Reading Your Options",
                    value="⭐ = **Recommended** (best chance of success)\n"
                          "🟢 = Good chance (65%+)\n"
                          "🟡 = Fair chance (50-64%)\n"
                          "🔴 = Risky (below 50%)",
                    inline=False
                )

                embed.add_field(
                    name="📊 Understanding Stats",
                    value="**Example:** `DRI/PAC: 81+3=84 vs 68+2=70`\n"
                          "• `DRI/PAC` = Stats used (Dribbling + Pace)\n"
                          "• `81` = Your base stat\n"
                          "• `+3` = Your position bonus\n"
                          "• `=84` = Your total\n"
                          "• `vs 68+2=70` = Defender's total",
                    inline=False
                )

                embed.add_field(
                    name="🎲 How Success Works",
                    value="After you choose, both you and the defender roll a 20-sided die!\n"
                          "**Your Total + Your Roll vs Their Total + Their Roll**\n\n"
                          "Higher total wins! Even with 60% chance, you can lose on a bad roll.",
                    inline=False
                )

                embed.add_field(
                    name="⚡ Follow-Up Actions",
                    value="Some actions trigger **bonus events**:\n"
                          "• Successful dribble → 30% chance for a shot!\n"
                          "• Good tackle → 40% chance for counter-attack!\n"
                          "Check the `↪` line under each action to see what might happen next.",
                    inline=False
                )

                embed.set_footer(text="⏱️ You have 30 seconds to choose • Pick the ⭐ star if unsure!")

                await channel.send(embed=embed)
                await asyncio.sleep(3)

    def get_followup_description(self, action):
        """✅ FIX #6: Get follow-up action description for display"""
        followup_info = {
            'shoot': "Success: May create rebound (15%) | Fail: Possible rebound (15%)",
            'header': "Success: Ball may drop loose (15%) | Fail: Loose ball (20%)",
            'pass': "Success: 20% teammate scores (assist) | Fail: Counter risk (25%)",
            'through_ball': "Success: 30% teammate scores (assist) | Fail: Intercepted",
            'key_pass': "Success: 40% teammate scores (assist) | Fail: Defended",
            'cross': "Success: 25% teammate scores (assist) | Fail: Cleared",
            'dribble': "Success: 25% shooting chance | Fail: Counter risk (20%)",
            'cut_inside': "Success: 30% shooting chance | Fail: Closed down",
            'tackle': "Success: 30% launch counter | Fail: Beaten/foul risk",
            'interception': "Success: 35% counter-attack | Fail: Miss the ball",
            'hold_up_play': "Success: 25% layoff to teammate | Fail: Dispossessed",
            'run_in_behind': "Success: 55% 1v1 with keeper! | Fail: Offside/caught",
            'block': "Success: 20% loose ball | Fail: Shot through",
            'clearance': "Success: Safety | Fail: 35% falls to attacker",
            'save': "Success: 25% start counter | Fail: Goal",
            'press': "Success: Win ball | Fail: Bypassed",
            'track_back': "Success: Stop attack | Fail: Too slow",
            'cover': "Success: Stop attack | Fail: Exposed",
            'long_ball': "Success: Switch play/create chance | Fail: Intercepted",
            'overlap': "Success: Crossing opportunity | Fail: Tracked back",
            'track_runner': "Success: Deny space | Fail: Lost them",
            'claim_cross': "Success: Command box | Fail: Drop/spill danger",
            'sweep': "Success: Clear danger | Fail: Caught out",
            'distribution': "Success: Launch counter | Fail: Poor pass",
            'press_defender': "Success: Win ball high | Fail: Bypassed"
        }
        return followup_info.get(action, "No follow-up")

    # ═══════════════════════════════════════════════════════════════
    # ✅ NEW: SHOT PLACEMENT SYSTEM
    # ═══════════════════════════════════════════════════════════════

    def get_shot_placement_config(self):
        """
        Shot placement system - players choose where to aim
        Risk/reward mechanics for exciting shooting moments
        """
        return {
            'left_corner': {
                'name': 'Left Corner',
                'emoji': '⬅️',
                'player_bonus': 5,
                'keeper_penalty': -8,
                'miss_chance': 25,
                'stat_used': 'shooting',
                'description': 'High risk, high reward - keeper has to dive far',
                'success_text': 'Shot placed perfectly into the left corner!',
                'fail_text': 'Keeper dives and saves! / Shot goes wide left!',
                'style': discord.ButtonStyle.primary
            },
            'right_corner': {
                'name': 'Right Corner',
                'emoji': '➡️',
                'player_bonus': 5,
                'keeper_penalty': -8,
                'miss_chance': 25,
                'stat_used': 'shooting',
                'description': 'High risk, high reward - keeper has to dive far',
                'success_text': 'Shot placed perfectly into the right corner!',
                'fail_text': 'Keeper dives and saves! / Shot goes wide right!',
                'style': discord.ButtonStyle.primary
            },
            'top_center': {
                'name': 'Top Center',
                'emoji': '⬆️',
                'player_bonus': 2,
                'keeper_penalty': -3,
                'miss_chance': 15,
                'stat_used': 'shooting',
                'description': 'Powerful shot high - can go over the bar',
                'success_text': 'Powerful shot into the top of the net!',
                'fail_text': 'Keeper tips it over! / Shot sails over the bar!',
                'style': discord.ButtonStyle.primary
            },
            'low_center': {
                'name': 'Low Center',
                'emoji': '⬇️',
                'player_bonus': -3,
                'keeper_penalty': 5,
                'miss_chance': 5,
                'stat_used': 'shooting',
                'description': 'Safe option - hard to miss but keeper positioned',
                'success_text': 'Placed shot finds the net!',
                'fail_text': 'Keeper saves comfortably!',
                'style': discord.ButtonStyle.success
            },
            'power_shot': {
                'name': 'Power Shot',
                'emoji': '💥',
                'player_bonus': 8,
                'keeper_penalty': -5,
                'miss_chance': 35,
                'stat_used': 'physical',
                'description': 'Pure power - uses Physical stat, very risky!',
                'success_text': 'SCREAMER! Unstoppable power shot!',
                'fail_text': 'Blasted into Row Z! / Keeper somehow stops the rocket!',
                'style': discord.ButtonStyle.danger
            }
        }

    async def create_goal_visualization(self, placement, keeper_dove, is_goal, player_name, keeper_name):
        """
        Create beautiful goal visualization showing shot trajectory and keeper position
        """
        try:
            # Create canvas
            width, height = 800, 500
            img = Image.new('RGB', (width, height), color='#2b5329')  # Football pitch green
            draw = ImageDraw.Draw(img)

            # Try to load a font, fallback to default
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
                text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            except:
                title_font = ImageFont.load_default()
                text_font = ImageFont.load_default()

            # Draw goal frame (white posts)
            goal_left = 200
            goal_right = 600
            goal_top = 100
            goal_bottom = 350

            # Goal posts
            draw.rectangle([goal_left - 10, goal_top - 10, goal_left, goal_bottom], fill='white')
            draw.rectangle([goal_right, goal_top - 10, goal_right + 10, goal_bottom], fill='white')
            draw.rectangle([goal_left, goal_top - 10, goal_right, goal_top], fill='white')

            # Net pattern
            for i in range(goal_left, goal_right, 30):
                draw.line([(i, goal_top), (i, goal_bottom)], fill='#cccccc', width=1)
            for i in range(goal_top, goal_bottom, 30):
                draw.line([(goal_left, i), (goal_right, i)], fill='#cccccc', width=1)

            # Divide goal into sections (visualize the zones)
            mid_x = (goal_left + goal_right) // 2
            mid_y = (goal_top + goal_bottom) // 2

            # Draw section lines (light)
            draw.line([(mid_x, goal_top), (mid_x, goal_bottom)], fill='#888888', width=2)
            draw.line([(goal_left, mid_y), (goal_right, mid_y)], fill='#888888', width=2)

            # Determine shot position
            shot_positions = {
                'left_corner': (goal_left + 60, goal_top + 60),
                'right_corner': (goal_right - 60, goal_top + 60),
                'top_center': (mid_x, goal_top + 60),
                'low_center': (mid_x, goal_bottom - 60),
                'power_shot': (mid_x, mid_y)
            }

            shot_x, shot_y = shot_positions.get(placement, (mid_x, mid_y))

            # Determine keeper position
            keeper_positions = {
                'left': (goal_left + 80, mid_y),
                'right': (goal_right - 80, mid_y),
                'center': (mid_x, mid_y)
            }

            keeper_x, keeper_y = keeper_positions.get(keeper_dove, (mid_x, mid_y))

            # Draw ball trajectory (from penalty spot to shot position)
            ball_start_x = width // 2
            ball_start_y = height - 50

            # Curved line for ball path
            points = []
            for i in range(20):
                t = i / 19
                # Bezier curve for nice arc
                x = ball_start_x + (shot_x - ball_start_x) * t
                y = ball_start_y - (ball_start_y - shot_y) * t - (50 * (1 - (t * 2 - 1) ** 2))
                points.append((x, y))

            # Draw trajectory line
            for i in range(len(points) - 1):
                draw.line([points[i], points[i + 1]], fill='white', width=4)

            # Draw keeper (emoji-like circle with gloves)
            keeper_radius = 30
            draw.ellipse([keeper_x - keeper_radius, keeper_y - keeper_radius,
                          keeper_x + keeper_radius, keeper_y + keeper_radius],
                         fill='#FFD700', outline='black', width=3)

            # Keeper arms (stretched toward ball)
            if keeper_dove == 'left':
                draw.line([(keeper_x, keeper_y), (keeper_x - 40, keeper_y - 20)], fill='#FFD700', width=8)
            elif keeper_dove == 'right':
                draw.line([(keeper_x, keeper_y), (keeper_x + 40, keeper_y - 20)], fill='#FFD700', width=8)
            else:
                draw.line([(keeper_x - 30, keeper_y), (keeper_x + 30, keeper_y)], fill='#FFD700', width=8)

            # Draw ball at final position
            ball_radius = 15
            ball_color = '#00FF00' if is_goal else '#FF0000'
            draw.ellipse([shot_x - ball_radius, shot_y - ball_radius,
                          shot_x + ball_radius, shot_y + ball_radius],
                         fill=ball_color, outline='black', width=3)

            # Draw result text at top
            result_text = "⚽ GOAL!" if is_goal else "🧤 SAVED / MISSED!"
            result_color = '#00FF00' if is_goal else '#FF4444'

            # Background for text
            draw.rectangle([50, 10, 750, 60], fill='black')
            draw.text((400, 30), result_text, fill=result_color, font=title_font, anchor="mm")

            # Bottom info
            info_text = f"{player_name} → {placement.replace('_', ' ').title()}"
            draw.rectangle([50, height - 50, 750, height - 10], fill='black')
            draw.text((400, height - 30), info_text, fill='white', font=text_font, anchor="mm")

            # Add keeper name
            keeper_text = f"🧤 {keeper_name} (Dove {keeper_dove})"
            draw.text((400, height - 70), keeper_text, fill='#FFD700', font=text_font, anchor="mm")

            # Save to buffer
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            return buffer

        except Exception as e:
            print(f"❌ Error creating goal visualization: {e}")
            return None

    async def handle_exciting_npc_moment(self, channel, moment_type, minute, home_team, away_team, team_side):
        """
        ✅ FIX #4: Exciting NPC moments (not boring build-up)
        Creates tension and drama
        """
        attacking_team = home_team if team_side == 'home' else away_team
        defending_team = away_team if team_side == 'home' else home_team

        if moment_type == 'dramatic_save':
            embed = discord.Embed(
                title=f"🧤 DRAMATIC SAVE! — {minute}'",
                description=f"**{defending_team['team_name']}'s goalkeeper** denies {attacking_team['team_name']}!\nBrilliant reflexes to tip it over the bar!",
                color=discord.Color.blue()
            )
            await channel.send(embed=embed)
            await asyncio.sleep(1)

        elif moment_type == 'near_miss':
            embed = discord.Embed(
                title=f"😱 SO CLOSE! — {minute}'",
                description=f"**{attacking_team['team_name']} almost scores!**\nThe shot grazes the post and goes wide!",
                color=discord.Color.gold()
            )
            await channel.send(embed=embed)
            await asyncio.sleep(1)

        elif moment_type == 'counter_attack':
            # Roll to see if it results in goal
            if random.random() < 0.10:  # 10% chance
                embed = discord.Embed(
                    title=f"⚡💥 COUNTER GOAL! — {minute}'",
                    description=f"**Lightning break from {attacking_team['team_name']}!**\nThey catch the defense sleeping and score!",
                    color=discord.Color.red() if team_side == 'away' else discord.Color.green()
                )
                await channel.send(embed=embed)
                return 'goal'
            else:
                embed = discord.Embed(
                    title=f"⚡ COUNTER ATTACK! — {minute}'",
                    description=f"**{attacking_team['team_name']} breaks forward!**\nThe shot is saved by the keeper!",
                    color=discord.Color.orange()
                )
                await channel.send(embed=embed)
                await asyncio.sleep(1)

        elif moment_type == 'defensive_block':
            embed = discord.Embed(
                title=f"🛡️ HEROIC BLOCK! — {minute}'",
                description=f"**Defender throws body on the line!**\n{defending_team['team_name']} blocks the shot!",
                color=discord.Color.blue()
            )
            await channel.send(embed=embed)
            await asyncio.sleep(1)

        elif moment_type == 'midfield_battle':
            embed = discord.Embed(
                title=f"⚔️ MIDFIELD BATTLE! — {minute}'",
                description=f"**Physical 50-50 challenge!**\nBoth teams fighting for control in the middle of the park!",
                color=discord.Color.purple()
            )
            await channel.send(embed=embed)
            await asyncio.sleep(1)

        return None

    async def handle_teammate_goal(self, channel, assisting_player, attacking_team, match_id, is_european=False):
        """
        ✅ FIX #2: Teammate scoring with priority for user players
        75% chance user teammates score, position-weighted
        ✅ FIXED: Corrected SQL query to not select european_npc_id from npc_players
        """
        async with db.pool.acquire() as conn:
            # ✅ FIRST: Check for user teammates in attacking positions
            user_teammates = await conn.fetch("""
                SELECT p.user_id, p.player_name, p.position, p.overall_rating
                FROM players p
                JOIN match_participants mp ON p.user_id = mp.user_id
                WHERE mp.match_id = $1
                  AND p.team_id = $2
                  AND p.user_id != $3
                  AND p.retired = FALSE
                  AND p.position IN ('ST', 'W', 'CAM')
                ORDER BY p.overall_rating DESC
            """, match_id, attacking_team['team_id'], assisting_player['user_id'])

            if user_teammates:
                # ✅ 75% chance to pass to user teammate
                if random.random() < 0.75:
                    # ✅ FIX #2: Position-weighted (strikers 3x more likely)
                    weights = []
                    teammates_list = [dict(t) for t in user_teammates]
                    for t in teammates_list:
                        if t['position'] == 'ST':
                            weights.append(3)  # Strikers 3x more likely
                        elif t['position'] == 'W':
                            weights.append(2)  # Wingers 2x
                        else:
                            weights.append(1)  # CAMs base chance

                    teammate = random.choices(teammates_list, weights=weights, k=1)[0]

                    # Update assister
                    await conn.execute("""
                        UPDATE players
                        SET season_assists = season_assists + 1,
                            career_assists = career_assists + 1
                        WHERE user_id = $1
                    """, assisting_player['user_id'])

                    # Update scorer
                    await conn.execute("""
                        UPDATE match_participants
                        SET goals_scored = goals_scored + 1,
                            match_rating = GREATEST(0.0, LEAST(10.0, match_rating + 1.2))
                        WHERE match_id = $1 AND user_id = $2
                    """, match_id, teammate['user_id'])

                    await conn.execute("""
                        UPDATE players
                        SET season_goals = season_goals + 1,
                            career_goals = career_goals + 1
                        WHERE user_id = $1
                    """, teammate['user_id'])

                    # ✅ FIX #2: Send DM notification to scorer
                    try:
                        scorer_user = await self.bot.fetch_user(teammate['user_id'])
                        embed = discord.Embed(
                            title="⚽ GOAL - TEAMMATE ASSIST!",
                            description=f"**{teammate['player_name']}**, you finished beautifully!\n\n🅰️ **{assisting_player['player_name']}** with the assist!",
                            color=discord.Color.green()
                        )
                        embed.add_field(
                            name="📊 Impact",
                            value=f"⚽ Goals: +1\n⭐ Rating: +1.2",
                            inline=False
                        )
                        team_crest = get_team_crest_url(attacking_team['team_id'])
                        if team_crest:
                            embed.set_thumbnail(url=team_crest)
                        await scorer_user.send(embed=embed)
                    except Exception as e:
                        print(f"⚠️ Could not send goal DM to {teammate['user_id']}: {e}")

                    # Update morale
                    from utils.form_morale_system import update_player_morale
                    await update_player_morale(teammate['user_id'], 'goal')

                    return {
                        'scorer_name': teammate['player_name'],
                        'scorer_user_id': teammate['user_id'],
                        'is_user_player': True
                    }

            # Fallback to NPC if no user teammates or 25% random chance
            # ✅ FIXED: Separated queries for npc_players and european_npc_players
            if is_european:
                # Try regular NPCs first
                npc_teammate = await conn.fetchrow("""
                    SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                            dribbling, defending, physical, overall_rating
                    FROM npc_players
                    WHERE team_id = $1 AND position IN ('ST', 'W', 'CAM') AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
                """, attacking_team['team_id'])
                
                # If no regular NPC found, try European NPCs
                if not npc_teammate:
                    npc_teammate = await conn.fetchrow("""
                        SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                                dribbling, defending, physical, overall_rating
                        FROM european_npc_players
                        WHERE team_id = $1 AND position IN ('ST', 'W', 'CAM') AND retired = FALSE
                        ORDER BY RANDOM() LIMIT 1
                    """, attacking_team['team_id'])
            else:
                npc_teammate = await conn.fetchrow("""
                    SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                            dribbling, defending, physical, overall_rating
                    FROM npc_players
                    WHERE team_id = $1 AND position IN ('ST', 'W', 'CAM') AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
                """, attacking_team['team_id'])

            if npc_teammate:
                await conn.execute("""
                    UPDATE players
                    SET season_assists = season_assists + 1,
                        career_assists = career_assists + 1
                    WHERE user_id = $1
                """, assisting_player['user_id'])

                return {
                    'scorer_name': npc_teammate['player_name'],
                    'is_user_player': False
                }

        return None

    # ═══════════════════════════════════════════════════════════════
    # HELPER: Generate combined crests image
    # ═══════════════════════════════════════════════════════════════

    async def generate_crests_image(self, home_url, away_url):
        """Generate combined image with both crests side by side"""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                home_img_bytes = None
                away_img_bytes = None

                if home_url:
                    try:
                        async with session.get(home_url, timeout=aiohttp.ClientTimeout(total=5)) as r:
                            if r.status == 200:
                                home_img_bytes = await r.read()
                    except:
                        pass

                if away_url:
                    try:
                        async with session.get(away_url, timeout=aiohttp.ClientTimeout(total=5)) as r:
                            if r.status == 200:
                                away_img_bytes = await r.read()
                    except:
                        pass

            size = (100, 100)
            padding = 40
            width = size[0] * 2 + padding
            height = size[1]
            img = Image.new("RGBA", (width, height), (255, 255, 255, 0))

            if home_img_bytes:
                try:
                    home = Image.open(BytesIO(home_img_bytes)).convert("RGBA").resize(size)
                    img.paste(home, (0, 0), home)
                except:
                    pass

            if away_img_bytes:
                try:
                    away = Image.open(BytesIO(away_img_bytes)).convert("RGBA").resize(size)
                    img.paste(away, (size[0] + padding, 0), away)
                except:
                    pass

            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer
        except Exception as e:
            print(f"Error generating crests image: {e}")
            return None

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
                if match_id in self.match_yellow_cards:
                    del self.match_yellow_cards[match_id]
                if match_id in self.match_stats:
                    del self.match_stats[match_id]
                # ✅ NEW: Cleanup timeout and AFK tracking
                if match_id in self.player_timeouts:
                    del self.player_timeouts[match_id]
                if match_id in self.afk_players:
                    del self.afk_players[match_id]

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

    def initialize_match_stats(self, match_id, home_participants, away_participants):
        """Initialize match statistics tracking"""
        self.match_stats[match_id] = {
            'home': {
                'shots': 0, 'shots_on_target': 0, 'possession': 50,
                'passes_completed': 0, 'passes_attempted': 0,
                'tackles_won': 0, 'tackles_attempted': 0,
                'actions': 0
            },
            'away': {
                'shots': 0, 'shots_on_target': 0, 'possession': 50,
                'passes_completed': 0, 'passes_attempted': 0,
                'tackles_won': 0, 'tackles_attempted': 0,
                'actions': 0
            }
        }
        self.match_yellow_cards[match_id] = {}

    def update_match_stats(self, match_id, team_side, action, success):
        """Update match statistics based on action"""
        if match_id not in self.match_stats:
            return

        if team_side not in self.match_stats[match_id]:  # ⚡ ADD THIS CHECK
            return

        stats = self.match_stats[match_id][team_side]
        stats['actions'] += 1

        if action in ['shoot', 'header']:
            stats['shots'] += 1
            if success:
                stats['shots_on_target'] += 1

        elif action in ['pass', 'through_ball', 'key_pass', 'cross', 'long_ball']:
            stats['passes_attempted'] += 1
            if success:
                stats['passes_completed'] += 1

        elif action == 'tackle':
            stats['tackles_attempted'] += 1
            if success:
                stats['tackles_won'] += 1

        if success:
            stats['possession'] = min(70, stats['possession'] + 1)
            opponent = 'away' if team_side == 'home' else 'home'
            self.match_stats[match_id][opponent]['possession'] = max(30, self.match_stats[match_id][opponent][
                'possession'] - 1)

    def get_home_advantage_bonus(self, is_home, player_position):
        """Calculate home advantage bonus"""
        if not is_home:
            return 0

        attacking_positions = ['ST', 'W', 'CAM']
        if player_position in attacking_positions:
            return 2
        return 1

    async def give_yellow_card(self, player, match_id, channel, reason="dangerous play"):
        """Give yellow card to player"""
        if match_id not in self.match_yellow_cards:
            self.match_yellow_cards[match_id] = {}

        user_id = player['user_id']
        current_yellows = self.match_yellow_cards[match_id].get(user_id, 0)

        embed = discord.Embed(
            title="🟨 YELLOW CARD!",
            description=f"**{player['player_name']}** booked for {reason}!",
            color=discord.Color.gold()
        )

        if current_yellows >= 1:
            embed.title = "🟥 SECOND YELLOW = RED CARD!"
            embed.description = f"**{player['player_name']}** sent off!\n\n⚠️ **SUSPENDED FOR NEXT MATCH**"
            embed.color = discord.Color.red()

            async with db.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE match_participants
                    SET match_rating = GREATEST(0.0, LEAST(10.0, match_rating - 1.0))
                    WHERE match_id = $1 AND user_id = $2
                """, match_id, user_id)

            await self.send_red_card_notification(player, {'team_name': 'Team'}, {'team_name': 'Opposition'})
        else:
            self.match_yellow_cards[match_id][user_id] = current_yellows + 1

            async with db.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE match_participants
                    SET match_rating = GREATEST(0.0, LEAST(10.0, match_rating - 0.3))
                    WHERE match_id = $1 AND user_id = $2
                """, match_id, user_id)

        await channel.send(embed=embed)

    async def handle_set_piece(self, channel, attacking_team, defending_team, minute, match_id, is_european=False):
        """Handle corner kick or free kick"""
        set_piece_type = random.choice(['corner', 'free_kick'])

        async with db.pool.acquire() as conn:
            if is_european:
                if set_piece_type == 'corner':
                    taker = await conn.fetchrow("""
                        SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                               dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                        FROM npc_players
                        WHERE team_id = $1 AND retired = FALSE
                        ORDER BY passing DESC LIMIT 1
                    """, attacking_team['team_id'])
                    
                    if not taker:
                        taker = await conn.fetchrow("""
                            SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                                   dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                            FROM european_npc_players
                            WHERE team_id = $1 AND retired = FALSE
                            ORDER BY passing DESC LIMIT 1
                        """, attacking_team['team_id'])
                else:
                    taker = await conn.fetchrow("""
                        SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                               dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                        FROM npc_players
                        WHERE team_id = $1 AND retired = FALSE
                        ORDER BY shooting DESC LIMIT 1
                    """, attacking_team['team_id'])
                    
                    if not taker:
                        taker = await conn.fetchrow("""
                            SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                                   dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                            FROM european_npc_players
                            WHERE team_id = $1 AND retired = FALSE
                            ORDER BY shooting DESC LIMIT 1
                        """, attacking_team['team_id'])
            else:
                if set_piece_type == 'corner':
                    taker = await conn.fetchrow("""
                        SELECT * FROM npc_players
                        WHERE team_id = $1 AND retired = FALSE
                        ORDER BY passing DESC LIMIT 1
                    """, attacking_team['team_id'])
                else:
                    taker = await conn.fetchrow("""
                        SELECT * FROM npc_players
                        WHERE team_id = $1 AND retired = FALSE
                        ORDER BY shooting DESC LIMIT 1
                    """, attacking_team['team_id'])

        if not taker:
            return None

        embed = discord.Embed(
            title=f"{'⚽ CORNER KICK' if set_piece_type == 'corner' else '🎯 FREE KICK'} — {minute}'",
            description=f"**{taker['player_name']}** steps up for {attacking_team['team_name']}...",
            color=discord.Color.gold()
        )
        await channel.send(embed=embed)
        await asyncio.sleep(2)

        if set_piece_type == 'free_kick':
            roll = random.randint(1, 100)
            # ✅ REBALANCED: Free kicks harder
            success_threshold = min(90, 8 + (taker['shooting'] - 70) // 3)

            if roll <= success_threshold:
                result_embed = discord.Embed(
                    title="⚽ FREE KICK GOAL!",
                    description=f"**{taker['player_name']}** bends it into the top corner!",
                    color=discord.Color.green()
                )
                await channel.send(embed=result_embed)

                async with db.pool.acquire() as conn:
                    if is_european and 'european_npc_id' in taker:
                        await conn.execute("""
                            UPDATE european_npc_players
                            SET season_goals = season_goals + 1
                            WHERE european_npc_id = $1
                        """, taker['european_npc_id'])
                    else:
                        await conn.execute("""
                            UPDATE npc_players
                            SET season_goals = season_goals + 1
                            WHERE npc_id = $1
                        """, taker['npc_id'])

                return {'goal': True, 'scorer_name': taker['player_name'], 'set_piece': True}
            else:
                result_embed = discord.Embed(
                    title="❌ FREE KICK SAVED!",
                    description="Goalkeeper makes a brilliant save!",
                    color=discord.Color.blue()
                )
                await channel.send(embed=result_embed)

        else:
            roll = random.randint(1, 100)
            # ✅ REBALANCED: Corners harder
            success_threshold = min(90, 15 + (taker['passing'] - 70) // 3)

            if roll <= success_threshold:
                async with db.pool.acquire() as conn:
                    if is_european:
                        header_player = await conn.fetchrow("""
                            SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                                   dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                            FROM npc_players
                            WHERE team_id = $1 AND position IN ('ST', 'CB') AND retired = FALSE
                            ORDER BY physical DESC LIMIT 1
                        """, attacking_team['team_id'])
                        
                        if not header_player:
                            header_player = await conn.fetchrow("""
                                SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                                       dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                                FROM european_npc_players
                                WHERE team_id = $1 AND position IN ('ST', 'CB') AND retired = FALSE
                                ORDER BY physical DESC LIMIT 1
                            """, attacking_team['team_id'])
                    else:
                        header_player = await conn.fetchrow("""
                            SELECT * FROM npc_players
                            WHERE team_id = $1 AND position IN ('ST', 'CB') AND retired = FALSE
                            ORDER BY physical DESC LIMIT 1
                        """, attacking_team['team_id'])

                if header_player:
                    result_embed = discord.Embed(
                        title="⚽ CORNER GOAL!",
                        description=f"**{header_player['player_name']}** powers the header home!\n🅰️ Assist: {taker['player_name']}",
                        color=discord.Color.green()
                    )
                    await channel.send(embed=result_embed)

                    async with db.pool.acquire() as conn:
                        if is_european and 'european_npc_id' in header_player:
                            await conn.execute("""
                                UPDATE european_npc_players
                                SET season_goals = season_goals + 1
                                WHERE european_npc_id = $1
                            """, header_player['european_npc_id'])
                        else:
                            await conn.execute("""
                                UPDATE npc_players
                                SET season_goals = season_goals + 1
                                WHERE npc_id = $1
                            """, header_player['npc_id'])

                    return {'goal': True, 'scorer_name': header_player['player_name'], 'set_piece': True}
            else:
                result_embed = discord.Embed(
                    title="❌ CORNER CLEARED!",
                    description="Defending team clears the danger!",
                    color=discord.Color.blue()
                )
                await channel.send(embed=result_embed)

        return None

    async def display_match_stats(self, channel, match_id, home_team, away_team):
        """Display match statistics"""
        if match_id not in self.match_stats:
            return

        home_stats = self.match_stats[match_id]['home']
        away_stats = self.match_stats[match_id]['away']

        home_pass_pct = int((home_stats['passes_completed'] / max(1, home_stats['passes_attempted'])) * 100)
        away_pass_pct = int((away_stats['passes_completed'] / max(1, away_stats['passes_attempted'])) * 100)

        home_tackle_pct = int((home_stats['tackles_won'] / max(1, home_stats['tackles_attempted'])) * 100)
        away_tackle_pct = int((away_stats['tackles_won'] / max(1, away_stats['tackles_attempted'])) * 100)

        embed = discord.Embed(
            title="📊 MATCH STATISTICS",
            description=f"**{home_team['team_name']}** vs **{away_team['team_name']}**",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="⚽ Shots",
            value=f"{home_stats['shots']} — {away_stats['shots']}",
            inline=True
        )

        embed.add_field(
            name="🎯 On Target",
            value=f"{home_stats['shots_on_target']} — {away_stats['shots_on_target']}",
            inline=True
        )

        embed.add_field(
            name="📊 Possession",
            value=f"{home_stats['possession']}% — {away_stats['possession']}%",
            inline=True
        )

        embed.add_field(
            name="🎪 Pass Accuracy",
            value=f"{home_pass_pct}% — {away_pass_pct}%",
            inline=True
        )

        embed.add_field(
            name="🛡️ Tackles Won",
            value=f"{home_tackle_pct}% — {away_tackle_pct}%",
            inline=True
        )

        embed.add_field(
            name="⚡ Total Actions",
            value=f"{home_stats['actions']} — {away_stats['actions']}",
            inline=True
        )

        await channel.send(embed=embed)

    # ═══════════════════════════════════════════════════════════════
    # ENHANCED D20 SYSTEM
    # ═══════════════════════════════════════════════════════════════

    def get_action_stats(self, action):
        """Returns weighted stat configuration for each action"""
        stat_configs = {
            'shoot': ('shooting', 'physical', 'defending', 'physical'),
            'header': ('physical', 'shooting', 'physical', 'defending'),
            'pass': ('passing', 'dribbling', 'pace', 'defending'),
            'through_ball': ('passing', 'dribbling', 'pace', 'defending'),
            'key_pass': ('passing', 'dribbling', 'defending', 'pace'),
            'cross': ('passing', 'physical', 'physical', 'defending'),
            'long_ball': ('passing', 'physical', 'pace', 'defending'),
            'dribble': ('dribbling', 'pace', 'defending', 'pace'),
            'cut_inside': ('dribbling', 'pace', 'defending', 'pace'),
            'overlap': ('pace', 'physical', 'pace', 'defending'),
            'run_in_behind': ('pace', 'dribbling', 'pace', 'defending'),
            'hold_up_play': ('physical', 'dribbling', 'physical', 'defending'),
            'tackle': ('defending', 'physical', 'dribbling', 'physical'),
            'clearance': ('defending', 'physical', 'shooting', 'pace'),
            'interception': ('defending', 'pace', 'passing', 'pace'),
            'block': ('defending', 'physical', 'shooting', 'physical'),
            'press': ('pace', 'physical', 'passing', 'dribbling'),
            'track_back': ('pace', 'physical', 'pace', 'dribbling'),
            'cover': ('defending', 'pace', 'passing', 'pace'),
            'track_runner': ('pace', 'defending', 'pace', 'dribbling'),
            'press_defender': ('pace', 'physical', 'passing', 'dribbling'),
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
            'ST': {'shoot': 3, 'header': 2, 'hold_up_play': 2, 'run_in_behind': 2},
            'W': {'dribble': 3, 'cross': 2, 'cut_inside': 2, 'overlap': 2},
            'CAM': {'pass': 2, 'through_ball': 3, 'key_pass': 3, 'shoot': 1},
            'CM': {'pass': 2, 'tackle': 2, 'interception': 2, 'long_ball': 2},
            'CDM': {'tackle': 3, 'interception': 3, 'block': 2, 'cover': 2},
            'FB': {'tackle': 2, 'cross': 2, 'overlap': 2, 'clearance': 2, 'track_runner': 2},
            'CB': {'tackle': 3, 'clearance': 3, 'block': 3, 'header': 2, 'interception': 2},
            'GK': {'save': 5, 'claim_cross': 3, 'distribution': 1, 'sweep': 2}
        }
        return bonuses.get(position, {}).get(action, 0)

    def calculate_d20_success_probability(self, player_stat, defender_stat):
        """✅ REBALANCED: Diminishing returns on stat advantage"""
        if defender_stat == 0:
            return 55

        stat_diff = player_stat - defender_stat

        # Diminishing returns curve
        if stat_diff >= 20:
            probability = 50 + (20 * 0.75) + ((stat_diff - 20) * 0.25)
        elif stat_diff >= 10:
            probability = 50 + (stat_diff * 0.75)
        elif stat_diff >= 0:
            probability = 50 + (stat_diff * 1.0)
        else:
            probability = 50 + (stat_diff * 1.5)

        return int(max(25, min(75, probability)))

    # ═══════════════════════════════════════════════════════════════
    # FOLLOW-UP ACTIONS SYSTEM
    # ═══════════════════════════════════════════════════════════════

    def get_followup_config(self, action, success):
        """✅ REBALANCED: Reduced follow-up chances for realistic matches"""
        followups = {
            'dribble_success': {'chance': 0.12, 'type': 'shooting_chance',
                                'desc': "Space created! Shooting opportunity..."},
            'cut_inside_success': {'chance': 0.15, 'type': 'shooting_chance',
                                   'desc': "Cut onto strong foot! Shot incoming..."},
            'tackle_success': {'chance': 0.30, 'type': 'counter_attack',
                               'desc': "Ball won! Counter-attack developing..."},
            'interception_success': {'chance': 0.35, 'type': 'counter_attack',
                                     'desc': "Intercepted! Quick break on..."},
            'hold_up_play_success': {'chance': 0.15, 'type': 'layoff_pass', 'desc': "Held up! Teammate making run..."},
            'run_in_behind_success': {'chance': 0.35, 'type': '1v1_keeper', 'desc': "Through on goal! One-on-one!"},
            'block_success': {'chance': 0.20, 'type': 'loose_ball', 'desc': "Blocked! Ball ricochets loose..."},
            'save_success': {'chance': 0.15, 'type': 'distribution_counter', 'desc': "Great save! Launch counter?"},
            'header_success': {'chance': 0.08, 'type': 'loose_ball', 'desc': "Header! Ball drops loose..."},
            'shoot_fail': {'chance': 0.08, 'type': 'rebound', 'desc': "Shot blocked! Rebound..."},
            'header_fail': {'chance': 0.10, 'type': 'loose_ball', 'desc': "Missed header! Loose ball..."},
            'clearance_fail': {'chance': 0.35, 'type': 'falls_to_attacker',
                               'desc': "Poor clearance! Falls to attacker..."},
            'pass_fail': {'chance': 0.25, 'type': 'interception_counter', 'desc': "Intercepted! They break..."},
            'dribble_fail': {'chance': 0.20, 'type': 'dispossessed_counter', 'desc': "Dispossessed! Counter on..."},
        }

        key = f"{action}_{'success' if success else 'fail'}"
        return followups.get(key, None)

    async def handle_followup_action(self, channel, action, success, player, attacking_team,
                                     defending_team, match_id, is_european=False):
        """Execute follow-up action after primary action"""
        config = self.get_followup_config(action, success)

        if not config or random.random() > config['chance']:
            return None

        followup_embed = discord.Embed(
            title="⚡ FOLLOW-UP!",
            description=config['desc'],
            color=discord.Color.orange()
        )
        await channel.send(embed=followup_embed)
        await asyncio.sleep(1.5)

        if config['type'] == 'shooting_chance':
            return await self.followup_shooting_chance(channel, player, attacking_team,
                                                       defending_team, match_id, is_european)
        elif config['type'] in ['counter_attack', 'distribution_counter']:
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
            return await self.followup_loose_ball(channel, attacking_team, defending_team,
                                                  match_id, is_european)
        elif config['type'] == 'falls_to_attacker':
            return await self.followup_long_shot(channel, player, attacking_team, match_id, is_european)
        elif config['type'] in ['interception_counter', 'dispossessed_counter']:
            return await self.followup_interception_counter(channel, player, defending_team, attacking_team,
                                                            match_id, is_european)

        return None

    async def followup_shooting_chance(self, channel, player, attacking_team, defending_team,
                                       match_id, is_european=False):
        """After successful dribble - you get a shot!"""
        adjusted_stats = self.apply_form_to_stats(player)

        async with db.pool.acquire() as conn:
            if is_european:
                keeper = await conn.fetchrow("""
                    SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                           dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                    FROM npc_players
                    WHERE team_id = $1 AND position = 'GK' AND retired = FALSE
                    LIMIT 1
                """, defending_team['team_id'])
                
                if not keeper:
                    keeper = await conn.fetchrow("""
                        SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                               dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                        FROM european_npc_players
                        WHERE team_id = $1 AND position = 'GK' AND retired = FALSE
                        LIMIT 1
                    """, defending_team['team_id'])
            else:
                keeper = await conn.fetchrow("""
                    SELECT * FROM npc_players
                    WHERE team_id = $1 AND position = 'GK' AND retired = FALSE LIMIT 1
                """, defending_team['team_id'])
            keeper = dict(keeper) if keeper else None

        att_p, att_s, def_p, def_s = self.get_action_stats('shoot')
        player_stat = self.calculate_weighted_stat(adjusted_stats, att_p, att_s)
        position_bonus = self.get_position_bonus(player['position'], 'shoot')

        player_roll = random.randint(1, 20)
        player_total = player_stat + player_roll + position_bonus

        if keeper:
            keeper_stat = self.calculate_weighted_stat(keeper, def_p, def_s)
            keeper_roll = random.randint(1, 20)
            keeper_total = keeper_stat + keeper_roll + 5
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
                    UPDATE match_participants
                    SET goals_scored = goals_scored + 1,
                        match_rating = GREATEST(0.0, LEAST(10.0, match_rating + 1.0))
                    WHERE match_id = $1 AND user_id = $2
                """, match_id, player['user_id'])
                await conn.execute("""
                    UPDATE players
                    SET season_goals = season_goals + 1,
                        career_goals = career_goals + 1
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

        async with db.pool.acquire() as conn:
            if is_european:
                keeper = await conn.fetchrow("""
                    SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                           dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                    FROM npc_players
                    WHERE team_id = $1 AND position = 'GK' AND retired = FALSE
                    LIMIT 1
                """, defending_team['team_id'])
                
                if not keeper:
                    keeper = await conn.fetchrow("""
                        SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                               dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                        FROM european_npc_players
                        WHERE team_id = $1 AND position = 'GK' AND retired = FALSE
                        LIMIT 1
                    """, defending_team['team_id'])
            else:
                keeper = await conn.fetchrow("""
                    SELECT * FROM npc_players
                    WHERE team_id = $1 AND position = 'GK' AND retired = FALSE LIMIT 1
                """, defending_team['team_id'])

        player_stat = adjusted_stats['shooting']
        keeper_stat = keeper['defending'] if keeper else 70

        player_roll = random.randint(1, 20)
        keeper_roll = random.randint(1, 20)

        # ✅ REBALANCED: Keeper gets major advantage in 1v1
        player_total = player_stat + player_roll
        keeper_total = keeper_stat + keeper_roll + 11  # Was 0, now +11

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
                    UPDATE match_participants
                    SET goals_scored = goals_scored + 1,
                        match_rating = GREATEST(0.0, LEAST(10.0, match_rating + 1.5))
                    WHERE match_id = $1 AND user_id = $2
                """, match_id, player['user_id'])
                await conn.execute("""
                    UPDATE players
                    SET season_goals = season_goals + 1,
                        career_goals = career_goals + 1
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
        """Quick counter-attack"""
        embed = discord.Embed(
            title="⚡💨 COUNTER-ATTACK!",
            description=f"**{attacking_team['team_name']}** breaks forward!",
            color=discord.Color.orange()
        )
        await channel.send(embed=embed)
        await asyncio.sleep(1)

        async with db.pool.acquire() as conn:
            if is_european:
                attacker = await conn.fetchrow("""
                    SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                           dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                    FROM npc_players
                    WHERE team_id = $1 AND position IN ('ST', 'W') AND retired = FALSE
                    ORDER BY pace DESC LIMIT 1
                """, attacking_team['team_id'])
                
                if not attacker:
                    attacker = await conn.fetchrow("""
                        SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                               dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                        FROM european_npc_players
                        WHERE team_id = $1 AND position IN ('ST', 'W') AND retired = FALSE
                        ORDER BY pace DESC LIMIT 1
                    """, attacking_team['team_id'])
            else:
                attacker = await conn.fetchrow("""
                    SELECT * FROM npc_players
                    WHERE team_id = $1 AND position IN ('ST', 'W') AND retired = FALSE
                    ORDER BY pace DESC LIMIT 1
                """, attacking_team['team_id'])

        if not attacker:
            return None

        counter_stat = (attacker['pace'] + attacker['dribbling']) // 2
        roll = random.randint(1, 20)
        total = counter_stat + roll

        # ✅ REBALANCED: Much harder to score from counters
        is_goal = total >= 105

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

            async with db.pool.acquire() as conn:
                if is_european and 'european_npc_id' in attacker:
                    await conn.execute("""
                        UPDATE european_npc_players
                        SET season_goals = season_goals + 1
                        WHERE european_npc_id = $1
                    """, attacker['european_npc_id'])
                else:
                    await conn.execute("""
                        UPDATE npc_players
                        SET season_goals = season_goals + 1
                        WHERE npc_id = $1
                    """, attacker['npc_id'])
        else:
            result_embed.add_field(
                name="🛡️ DEFENDED!",
                value=f"Counter stopped by {defending_team['team_name']}!",
                inline=False
            )

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
        """Rebound falls to teammate"""
        async with db.pool.acquire() as conn:
            if is_european:
                attacker = await conn.fetchrow("""
                    SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                           dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                    FROM npc_players
                    WHERE team_id = $1 AND position IN ('ST', 'W', 'CAM') AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
                """, attacking_team['team_id'])
                
                if not attacker:
                    attacker = await conn.fetchrow("""
                        SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                               dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                        FROM european_npc_players
                        WHERE team_id = $1 AND position IN ('ST', 'W', 'CAM') AND retired = FALSE
                        ORDER BY RANDOM() LIMIT 1
                    """, attacking_team['team_id'])
            else:
                attacker = await conn.fetchrow("""
                    SELECT * FROM npc_players
                    WHERE team_id = $1 AND position IN ('ST', 'W', 'CAM') AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
                """, attacking_team['team_id'])

        if not attacker:
            return None

        rebound_stat = (attacker['pace'] + attacker['shooting']) // 2
        roll = random.randint(1, 20)
        total = rebound_stat + roll

        # ✅ REBALANCED: Harder to score from rebounds
        is_goal = total >= 95

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

            async with db.pool.acquire() as conn:
                if is_european and 'european_npc_id' in attacker:
                    await conn.execute("""
                        UPDATE european_npc_players
                        SET season_goals = season_goals + 1
                        WHERE european_npc_id = $1
                    """, attacker['european_npc_id'])
                else:
                    await conn.execute("""
                        UPDATE npc_players
                        SET season_goals = season_goals + 1
                        WHERE npc_id = $1
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
                    SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                           dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                    FROM npc_players
                    WHERE team_id = $1 AND position IN ('CAM', 'CM') AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
                """, attacking_team['team_id'])
                
                if not midfielder:
                    midfielder = await conn.fetchrow("""
                        SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                               dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                        FROM european_npc_players
                        WHERE team_id = $1 AND position IN ('CAM', 'CM') AND retired = FALSE
                        ORDER BY RANDOM() LIMIT 1
                    """, attacking_team['team_id'])
            else:
                midfielder = await conn.fetchrow("""
                    SELECT * FROM npc_players
                    WHERE team_id = $1 AND position IN ('CAM', 'CM') AND retired = FALSE
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
        # ✅ REBALANCED: Harder to score from layoffs
        is_goal = shot_total >= 95

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
                    UPDATE match_participants
                    SET assists = assists + 1,
                        match_rating = GREATEST(0.0, LEAST(10.0, match_rating + 0.8))
                    WHERE match_id = $1 AND user_id = $2
                """, match_id, player['user_id'])
                await conn.execute("""
                    UPDATE players
                    SET season_assists = season_assists + 1,
                        career_assists = career_assists + 1
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

    async def followup_loose_ball(self, channel, attacking_team, defending_team, match_id, is_european=False):
        """50-50 ball"""
        async with db.pool.acquire() as conn:
            if is_european:
                attacker = await conn.fetchrow("""
                    SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                           dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                    FROM npc_players
                    WHERE team_id = $1 AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
                """, attacking_team['team_id'])
                
                if not attacker:
                    attacker = await conn.fetchrow("""
                        SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                               dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                        FROM european_npc_players
                        WHERE team_id = $1 AND retired = FALSE
                        ORDER BY RANDOM() LIMIT 1
                    """, attacking_team['team_id'])
                
                defender = await conn.fetchrow("""
                    SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                           dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                    FROM npc_players
                    WHERE team_id = $1 AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
                """, defending_team['team_id'])
                
                if not defender:
                    defender = await conn.fetchrow("""
                        SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                               dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                        FROM european_npc_players
                        WHERE team_id = $1 AND retired = FALSE
                        ORDER BY RANDOM() LIMIT 1
                    """, defending_team['team_id'])
            else:
                attacker = await conn.fetchrow("""
                    SELECT * FROM npc_players
                    WHERE team_id = $1 AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
                """, attacking_team['team_id'])
                defender = await conn.fetchrow("""
                    SELECT * FROM npc_players
                    WHERE team_id = $1 AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
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
            result_embed.add_field(name="✅ ATTACKER WINS!", value=f"{attacking_team['team_name']} keeps it!",
                                   inline=False)
        else:
            result_embed.add_field(name="🛡️ DEFENDER CLEARS!", value=f"{defending_team['team_name']} wins it!",
                                   inline=False)

        await channel.send(embed=result_embed)
        return None

    async def followup_long_shot(self, channel, player, attacking_team, match_id, is_european=False):
        """Long shot from edge of box"""
        async with db.pool.acquire() as conn:
            if is_european:
                attacker = await conn.fetchrow("""
                    SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                           dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                    FROM npc_players
                    WHERE team_id = $1 AND position IN ('CAM', 'CM') AND retired = FALSE
                    ORDER BY shooting DESC LIMIT 1
                """, attacking_team['team_id'])
                
                if not attacker:
                    attacker = await conn.fetchrow("""
                        SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                               dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                        FROM european_npc_players
                        WHERE team_id = $1 AND position IN ('CAM', 'CM') AND retired = FALSE
                        ORDER BY shooting DESC LIMIT 1
                    """, attacking_team['team_id'])
            else:
                attacker = await conn.fetchrow("""
                    SELECT * FROM npc_players
                    WHERE team_id = $1 AND position IN ('CAM', 'CM') AND retired = FALSE
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
        # ✅ REBALANCED: Long shots extremely difficult
        is_goal = shot_total >= 110

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

            async with db.pool.acquire() as conn:
                if is_european and 'european_npc_id' in attacker:
                    await conn.execute("""
                        UPDATE european_npc_players
                        SET season_goals = season_goals + 1
                        WHERE european_npc_id = $1
                    """, attacker['european_npc_id'])
                else:
                    await conn.execute("""
                        UPDATE npc_players
                        SET season_goals = season_goals + 1
                        WHERE npc_id = $1
                    """, attacker['npc_id'])

            return {'goal': True, 'scorer_name': attacker['player_name']}
        else:
            result_embed.add_field(name="❌ WIDE!", value="Long-range effort off target!", inline=False)

        await channel.send(embed=result_embed)
        return None

    async def followup_interception_counter(self, channel, player, defending_team, attacking_team, match_id,
                                            is_european=False):
        """When your pass is intercepted - they counter"""
        return await self.followup_counter_attack(channel, None, defending_team, attacking_team, match_id, is_european)

    def get_contextual_defender_positions(self, player_position, action):
        """Get realistic defender positions based on player position and action"""
        matchups = {
            'ST': {'shoot': ['CB', 'GK'], 'header': ['CB', 'FB'], 'hold_up_play': ['CB', 'CDM'],
                   'run_in_behind': ['CB', 'FB'], 'pass': ['CB', 'CDM']},
            'W': {'dribble': ['FB', 'W', 'CB'], 'cross': ['FB', 'CB'], 'cut_inside': ['FB', 'CDM', 'CB'],
                  'shoot': ['CB', 'CDM', 'GK'], 'track_back': ['W', 'FB']},
            'CAM': {'shoot': ['CDM', 'CB', 'GK'], 'through_ball': ['CDM', 'CM', 'CB'], 'key_pass': ['CDM', 'CM'],
                    'dribble': ['CDM', 'CM', 'CB'], 'long_ball': ['CDM', 'CM']},
            'CM': {'pass': ['CM', 'CDM'], 'through_ball': ['CM', 'CDM', 'CB'], 'long_ball': ['CM', 'CDM'],
                   'tackle': ['CM', 'CAM', 'W'], 'shoot': ['CDM', 'CB', 'GK']},
            'CDM': {'tackle': ['CAM', 'CM', 'ST'], 'interception': ['CAM', 'CM', 'ST'], 'pass': ['CAM', 'CM'],
                    'block': ['CAM', 'CM', 'ST'], 'cover': ['CAM', 'ST']},
            'FB': {'tackle': ['W', 'ST', 'CAM'], 'cross': ['FB', 'CB'], 'overlap': ['FB', 'W'],
                   'clearance': ['W', 'ST'], 'track_runner': ['W', 'ST']},
            'CB': {'tackle': ['ST', 'W', 'CAM'], 'clearance': ['ST', 'W'], 'block': ['ST', 'CAM', 'CM'],
                   'header': ['ST', 'W'], 'pass': ['ST', 'CAM']},
            'GK': {'save': ['ST', 'W', 'CAM', 'CM'], 'claim_cross': ['ST', 'W'], 'distribution': ['ST', 'CAM'],
                   'sweep': ['ST', 'W'], 'clearance': ['ST']}
        }

        if player_position in matchups and action in matchups[player_position]:
            return matchups[player_position][action]

        default_matchups = {
            'ST': ['CB', 'CDM'], 'W': ['FB', 'CB'], 'CAM': ['CDM', 'CM'], 'CM': ['CM', 'CDM'],
            'CDM': ['CAM', 'CM'], 'FB': ['W', 'ST'], 'CB': ['ST', 'W'], 'GK': ['ST', 'W', 'CAM']
        }

        return default_matchups.get(player_position, ['CB', 'CDM', 'FB', 'GK'])

    def get_position_events(self, position):
        """Position-specific actions"""
        position_events = {
            'ST': ['shoot', 'header', 'hold_up_play', 'run_in_behind', 'pass'],
            'W': ['dribble', 'cross', 'cut_inside', 'shoot', 'pass'],
            'CAM': ['shoot', 'through_ball', 'key_pass', 'dribble', 'long_ball'],
            'CM': ['pass', 'through_ball', 'long_ball', 'tackle', 'shoot'],
            'CDM': ['tackle', 'interception', 'pass', 'block', 'cover'],
            'FB': ['tackle', 'cross', 'overlap', 'clearance', 'track_runner'],
            'CB': ['tackle', 'clearance', 'block', 'header', 'pass'],
            'GK': ['save', 'claim_cross', 'distribution', 'sweep', 'clearance']
        }
        return position_events.get(position, ['pass', 'dribble', 'tackle', 'shoot', 'clearance'])

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

    def get_position_scenario(self, position):
        """
        Get weighted scenario type based on position
        Returns: (scenario_type, defender_positions, scenario_description_template)
        """
        scenarios = {
            'ST': [
                (40, 'clear_chance', ['GK'], "Through ball! You're clean through on goal vs {defender}!"),
                (25, 'marked_tight', ['CB'], "You receive the ball with {defender} marking you tight!"),
                (20, 'box_battle', ['CB', 'FB'], "Cross comes in! {defender} challenging you for the header!"),
                (15, 'drop_deep', ['CDM', 'CM'], "You drop deep, {defender} following you out!")
            ],
            'W': [
                (50, '1v1_wing', ['FB'], "Ball at your feet! {defender} closing you down on the wing!"),
                (25, 'space_wing', ['FB', 'W'], "Space opens up! {defender} tracking back!"),
                (15, 'cut_inside', ['CB', 'CDM'], "You cut inside, {defender} shifts across to cover!"),
                (10, 'counter', ['FB', 'CB'], "Counter attack! {defender} scrambling back!")
            ],
            'CAM': [
                (40, 'pocket_space', ['CDM', 'CM'], "Space in the hole! {defender} steps up to close you!"),
                (30, 'creative_moment', ['CDM', 'CB'], "You find space between the lines, {defender} pressing!"),
                (20, 'edge_box', ['CB', 'CDM'], "Edge of the box! {defender} closing you down!"),
                (10, 'transition', ['CM', 'CDM'], "Transition moment! {defender} in your way!")
            ],
            'CM': [
                (50, 'midfield_duel', ['CM', 'CDM'], "50-50 challenge with {defender} in midfield!"),
                (25, 'progressive', ['CM', 'CDM'], "You look to break the lines, {defender} reading it!"),
                (15, 'switch_play', ['CM'], "Space to switch play, {defender} closing!"),
                (10, 'late_run', ['CB', 'CDM'], "Late run into the box! {defender} tracking you!")
            ],
            'CDM': [
                (50, 'defensive_duel', ['CAM', 'CM', 'ST'], "Opposition attack! {defender} trying to turn you!"),
                (25, 'screen_defense', ['CAM', 'ST'], "{defender} dropping deep! You need to cut them off!"),
                (15, 'intercept', ['CM', 'CAM'], "{defender} on the ball! Intercept opportunity!"),
                (10, 'recycle', ['CM'], "Recycle possession, {defender} pressing high!")
            ],
            'FB': [
                (45, 'defensive_1v1', ['W', 'ST'], "Winger {defender} running at you with pace!"),
                (30, 'cover_wide', ['W', 'CAM'], "{defender} attacks the flank! Track them!"),
                (15, 'overlap', ['FB', 'W'], "You push forward! {defender} tracking your run!"),
                (10, 'back_post', ['ST', 'W'], "Cross coming in! {defender} at the back post!")
            ],
            'CB': [
                (50, 'defend_striker', ['ST'], "Striker {defender} making a run! Can you stop them?"),
                (25, 'aerial_duel', ['ST', 'W'], "Ball in the air! {defender} challenging you!"),
                (15, 'cover_space', ['CAM', 'ST'], "{defender} found space! Close them down!"),
                (10, 'build_up', ['ST', 'CAM'], "Building from the back, {defender} pressing high!")
            ],
            'GK': [
                (60, 'shot_save', ['ST', 'W', 'CAM'], "Shot incoming from {defender}! React fast!"),
                (20, 'claim_aerial', ['ST', 'W'], "Cross into your box! {defender} attacking it!"),
                (15, 'sweep', ['ST', 'W'], "{defender} through on goal! Rush out!"),
                (5, 'distribution', ['ST'], "Time to distribute, {defender} pressing!")
            ]
        }

        position_scenarios = scenarios.get(position, scenarios['CM'])

        total_weight = sum(s[0] for s in position_scenarios)
        roll = random.randint(1, total_weight)

        cumulative = 0
        for weight, scenario_type, defender_pos, description in position_scenarios:
            cumulative += weight
            if roll <= cumulative:
                return scenario_type, defender_pos, description

        return position_scenarios[0][1], position_scenarios[0][2], position_scenarios[0][3]

    def get_actions_for_scenario(self, position, scenario_type):
        """
        Get relevant actions for this specific scenario
        Always returns 5 actions: priority actions first, then position defaults to fill
        """
        scenario_priority = {
            'clear_chance': ['shoot', 'pass', 'dribble'],
            'marked_tight': ['hold_up_play', 'pass', 'shoot', 'dribble'],
            'box_battle': ['header', 'shoot', 'hold_up_play'],
            'drop_deep': ['pass', 'through_ball', 'dribble'],
            '1v1_wing': ['dribble', 'cut_inside', 'cross', 'shoot'],
            'space_wing': ['cross', 'dribble', 'cut_inside'],
            'cut_inside': ['shoot', 'cut_inside', 'dribble'],
            'counter': ['dribble', 'pass', 'shoot'],
            'pocket_space': ['through_ball', 'key_pass', 'shoot', 'dribble'],
            'creative_moment': ['key_pass', 'through_ball', 'pass'],
            'edge_box': ['shoot', 'dribble', 'pass'],
            'transition': ['pass', 'through_ball', 'dribble'],
            'midfield_duel': ['tackle', 'pass', 'dribble'],
            'progressive': ['through_ball', 'pass', 'dribble'],
            'switch_play': ['long_ball', 'pass', 'cross'],
            'late_run': ['shoot', 'pass', 'tackle'],
            'defensive_duel': ['tackle', 'interception', 'block'],
            'screen_defense': ['tackle', 'block', 'cover'],
            'intercept': ['interception', 'tackle', 'press'],
            'recycle': ['pass', 'long_ball', 'tackle'],
            'defensive_1v1': ['tackle', 'clearance', 'track_runner'],
            'cover_wide': ['tackle', 'track_runner', 'clearance'],
            'overlap': ['cross', 'overlap', 'pass'],
            'back_post': ['clearance', 'header', 'tackle'],
            'defend_striker': ['tackle', 'block', 'clearance'],
            'aerial_duel': ['header', 'clearance', 'tackle'],
            'cover_space': ['tackle', 'interception', 'block'],
            'build_up': ['pass', 'long_ball', 'clearance'],
            'shot_save': ['save', 'sweep', 'clearance'],
            'claim_aerial': ['claim_cross', 'save', 'sweep'],
            'sweep': ['sweep', 'save', 'clearance'],
            'distribution': ['distribution', 'long_ball', 'pass']
        }

        priority_actions = scenario_priority.get(scenario_type, [])
        all_position_actions = self.get_position_events(position)

        final_actions = []
        for action in priority_actions:
            if action not in final_actions and action in all_position_actions:
                final_actions.append(action)

        for action in all_position_actions:
            if action not in final_actions:
                final_actions.append(action)
            if len(final_actions) >= 5:
                break

        while len(final_actions) < 5 and len(all_position_actions) > len(final_actions):
            for action in all_position_actions:
                if action not in final_actions:
                    final_actions.append(action)
                    break

        return final_actions[:5]

    async def handle_player_moment(self, channel, player, participant, minute, attacking_team, defending_team,
                                   is_home, match_id, is_european=False):
        """
        ✅ UPDATED WITH SKIP & AFK SYSTEM + FIXED SKIP VS TIMEOUT TRACKING
        ✅ UPDATED: Shows 2-stage chances for shoot/header actions
        """
        member = channel.guild.get_member(player['user_id'])
        if not member:
            return None

        # ✅ NEW: Check if player is marked AFK - auto-play immediately
        if match_id in self.afk_players and player['user_id'] in self.afk_players[match_id]:
            scenario_type, defender_positions, scenario_description = self.get_position_scenario(player['position'])
            available_actions = self.get_actions_for_scenario(player['position'], scenario_type)
            action = available_actions[0]  # Use best action

            await channel.send(
                f"💤 **{player['player_name']}** (AFK) - Auto-playing: **{action.upper()}**"
            )

            # Execute action immediately
            adjusted_stats = self.apply_form_to_stats(player)

            async with db.pool.acquire() as conn:
                position_filter = ', '.join([f"'{pos}'" for pos in defender_positions])
                if is_european:
                    result = await conn.fetchrow(f"""
                        SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                               dribbling, defending, physical, overall_rating
                        FROM npc_players
                        WHERE team_id = $1 AND position IN ({position_filter}) AND retired = FALSE
                        ORDER BY RANDOM() LIMIT 1
                    """, defending_team['team_id'])
                    
                    if not result:
                        result = await conn.fetchrow(f"""
                            SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                                   dribbling, defending, physical, overall_rating
                            FROM european_npc_players
                            WHERE team_id = $1 AND position IN ({position_filter}) AND retired = FALSE
                            ORDER BY RANDOM() LIMIT 1
                        """, defending_team['team_id'])
                else:
                    result = await conn.fetchrow(f"""
                        SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                               dribbling, defending, physical, overall_rating
                        FROM npc_players 
                        WHERE team_id = $1 AND position IN ({position_filter}) AND retired = FALSE
                        ORDER BY RANDOM() LIMIT 1
                    """, defending_team['team_id'])
                defender = dict(result) if result else None

            result = await self.execute_action_with_duel(
                channel, player, adjusted_stats, defender, action, minute,
                match_id, member, attacking_team, defending_team, is_european, is_home
            )
            return result

        # ✅ Show tutorial if first match
        await self.show_tutorial_if_needed(channel, player['user_id'])

        # ✅ NEW: Check if this player has timed out before
        if match_id not in self.player_timeouts:
            self.player_timeouts[match_id] = set()

        has_timed_out = player['user_id'] in self.player_timeouts[match_id]

        adjusted_stats = self.apply_form_to_stats(player)
        scenario_type, defender_positions, scenario_description = self.get_position_scenario(player['position'])
        available_actions = self.get_actions_for_scenario(player['position'], scenario_type)

        from utils.form_morale_system import get_form_description
        form_desc = get_form_description(player['form'])

        position_filter = ', '.join([f"'{pos}'" for pos in defender_positions])

        async with db.pool.acquire() as conn:
            if is_european:
                result = await conn.fetchrow(f"""
                        SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                               dribbling, defending, physical, overall_rating
                        FROM npc_players
                        WHERE team_id = $1 AND position IN ({position_filter}) AND retired = FALSE
                        ORDER BY RANDOM() LIMIT 1
                    """, defending_team['team_id'])
                if not result:
                    result = await conn.fetchrow(f"""
                            SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                                   dribbling, defending, physical, overall_rating
                            FROM european_npc_players
                            WHERE team_id = $1 AND position IN ({position_filter}) AND retired = FALSE
                            ORDER BY RANDOM() LIMIT 1
                        """, defending_team['team_id'])
            else:
                result = await conn.fetchrow(f"""
                        SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                               dribbling, defending, physical, overall_rating
                        FROM npc_players 
                        WHERE team_id = $1 AND position IN ({position_filter}) AND retired = FALSE
                        ORDER BY RANDOM() LIMIT 1
                    """, defending_team['team_id'])
            defender = dict(result) if result else None

        if not defender:
            async with db.pool.acquire() as conn:
                if is_european:
                    result = await conn.fetchrow("""
                            SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                                   dribbling, defending, physical, overall_rating
                            FROM npc_players
                            WHERE team_id = $1 AND retired = FALSE
                            ORDER BY RANDOM() LIMIT 1
                        """, defending_team['team_id'])
                    if not result:
                        result = await conn.fetchrow("""
                                SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                                       dribbling, defending, physical, overall_rating
                                FROM european_npc_players
                                WHERE team_id = $1 AND retired = FALSE
                                ORDER BY RANDOM() LIMIT 1
                            """, defending_team['team_id'])
                else:
                    result = await conn.fetchrow("""
                            SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                                   dribbling, defending, physical, overall_rating
                            FROM npc_players
                            WHERE team_id = $1 AND retired = FALSE
                            ORDER BY RANDOM() LIMIT 1
                        """, defending_team['team_id'])
                defender = dict(result) if result else None

        if defender:
            scenario_text = scenario_description.format(
                defender=f"**{defender['player_name']}** ({defender['position']})")
        else:
            scenario_text = f"Key moment in the match! {defending_team['team_name']}'s defense reacting..."

        embed = discord.Embed(
            title=f"🎯 {member.display_name}'S MOMENT!",
            description=f"## {player['player_name']} ({player['position']})\n**{minute}'** | Form: {form_desc}\n\n{scenario_text}",
            color=discord.Color.gold()
        )

        # ✅ NEW: Add timeout warning if they've been AFK before
        if has_timed_out:
            embed.description += "\n\n⚠️ _This player timed out last turn_"

        home_crest = get_team_crest_url(attacking_team['team_id'])
        away_crest = get_team_crest_url(defending_team['team_id'])

        crests_file = None
        if home_crest or away_crest:
            crests_buffer = await self.generate_crests_image(home_crest, away_crest)
            if crests_buffer:
                crests_file = discord.File(fp=crests_buffer, filename=f"crests_{minute}.png")
                embed.set_image(url=f"attachment://crests_{minute}.png")

        embed.add_field(
            name="📖 Quick Guide",
            value="⭐🟢 = **Recommended/Good** (65%+) | 🟡 = **Fair** (50-64%) | 🔴 = **Risky** (<50%)\n"
                  "📊 = Your stats vs opponent | ↪️ = What might happen next",
            inline=False
        )

        # ✅ NEW: Get goalkeeper for 2-stage calculations
        async with db.pool.acquire() as conn:
            if is_european:
                keeper = await conn.fetchrow("""
                    SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                           dribbling, defending, physical, overall_rating
                    FROM npc_players
                    WHERE team_id = $1 AND position = 'GK' AND retired = FALSE
                    LIMIT 1
                """, defending_team['team_id'])
                if not keeper:
                    keeper = await conn.fetchrow("""
                        SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                               dribbling, defending, physical, overall_rating
                        FROM european_npc_players
                        WHERE team_id = $1 AND position = 'GK' AND retired = FALSE
                        LIMIT 1
                    """, defending_team['team_id'])
            else:
                keeper = await conn.fetchrow("""
                    SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                           dribbling, defending, physical, overall_rating
                    FROM npc_players
                    WHERE team_id = $1 AND position = 'GK' AND retired = FALSE LIMIT 1
                """, defending_team['team_id'])
            keeper = dict(keeper) if keeper else None

        actions_data = []
        for action in available_actions:
            att_p, att_s, def_p, def_s = self.get_action_stats(action)
            player_weighted = self.calculate_weighted_stat(adjusted_stats, att_p, att_s)
            player_pos_bonus = self.get_position_bonus(player['position'], action)
            player_effective = player_weighted + player_pos_bonus

            if defender:
                defender_weighted = self.calculate_weighted_stat(defender, def_p, def_s)
                defender_pos_bonus = self.get_position_bonus(defender.get('position', 'CB'), action)
                defender_effective = defender_weighted + defender_pos_bonus
                chance = self.calculate_d20_success_probability(player_effective, defender_effective)
            else:
                defender_weighted = 0
                defender_pos_bonus = 0
                defender_effective = 0
                chance = 60

            if is_home:
                home_bonus = self.get_home_advantage_bonus(is_home, player['position'])
                chance = min(90, chance + home_bonus)

            # ✅ NEW: Calculate 2-stage chances for shoot/header
            keeper_chance = None
            combined_chance = None
            keeper_stat_val = None
            keeper_effective = None
            player_shoot_stat = None

            if action in ['shoot', 'header'] and defender and defender.get('position') != 'GK' and keeper:
                # Stage 1: vs defender chance (already calculated above)
                stage1_chance = chance

                # Stage 2: vs keeper chance
                keeper_att_p, keeper_att_s, keeper_def_p, keeper_def_s = self.get_action_stats('save')
                player_shoot_stat = self.calculate_weighted_stat(adjusted_stats, keeper_att_p, keeper_att_s)
                keeper_stat_val = self.calculate_weighted_stat(keeper, keeper_def_p, keeper_def_s)
                keeper_bonus_val = self.get_position_bonus('GK', 'save')
                keeper_effective = keeper_stat_val + keeper_bonus_val + 5  # GK gets +5 bonus

                stage2_chance = self.calculate_d20_success_probability(player_shoot_stat, keeper_effective)

                # Combined probability (both must succeed)
                combined_chance = int((stage1_chance / 100) * (stage2_chance / 100) * 100)
                keeper_chance = int(stage2_chance)

            actions_data.append({
                'action': action,
                'chance': int(chance),
                'keeper_chance': keeper_chance,
                'combined_chance': combined_chance,
                'player_stat': player_weighted,
                'player_bonus': player_pos_bonus,
                'player_effective': player_effective,
                'defender_stat': defender_weighted if defender else 0,
                'defender_bonus': defender_pos_bonus if defender else 0,
                'defender_effective': defender_effective if defender else 0,
                'primary': att_p[:3].upper(),
                'secondary': att_s[:3].upper(),
                'keeper_stat_val': keeper_stat_val,
                'keeper_effective': keeper_effective,
                'player_shoot_stat': player_shoot_stat
            })

        # ✅ FIXED: Safe sorting that handles None values
        actions_data.sort(
            key=lambda x: x.get('combined_chance') or x.get('chance') or 0,
            reverse=True
        )
        recommended_action = actions_data[0]['action']

        actions_text = ""
        for data in actions_data:
            action = data['action']
            chance = data['chance']
            keeper_chance = data['keeper_chance']
            combined_chance = data['combined_chance']

            # ✅ Use combined chance for difficulty rating if it's a 2-stage action
            display_chance = combined_chance if combined_chance is not None else chance

            if display_chance >= 65:
                emoji, difficulty = "🟢", "GOOD"
            elif display_chance >= 50:
                emoji, difficulty = "🟡", "FAIR"
            else:
                emoji, difficulty = "🔴", "RISKY"

            if action == recommended_action:
                emoji = "⭐" + emoji
                difficulty = "★ BEST"

            action_name = action.replace('_', ' ').title()

            # ✅ NEW: Show 2-stage breakdown for shoot/header with full stats
            if combined_chance is not None:
                actions_text += f"{emoji} **{action_name}** — {chance}% vs {defender.get('position', 'DEF')} → {keeper_chance}% vs GK = **{combined_chance}% total** `[{difficulty}]`\n"

                # Stage 1: vs Defender
                actions_text += f"   📊 Stage 1: {data['primary']}/{data['secondary']} "
                if data['player_bonus'] > 0:
                    actions_text += f"{data['player_stat']}+{data['player_bonus']}=**{data['player_effective']}**"
                else:
                    actions_text += f"**{data['player_effective']}**"
                actions_text += f" vs {defender.get('position', 'DEF')} "
                if data['defender_bonus'] > 0:
                    actions_text += f"{data['defender_stat']}+{data['defender_bonus']}=**{data['defender_effective']}**"
                else:
                    actions_text += f"**{data['defender_effective']}**"
                actions_text += "\n"

                # Stage 2: vs Goalkeeper
                keeper_att_p, keeper_att_s = self.get_action_stats('save')[:2]
                actions_text += f"   📊 Stage 2: {keeper_att_p[:3].upper()}/{keeper_att_s[:3].upper()} **{data['player_shoot_stat']}** vs GK **{data['keeper_effective']}** (+5 save bonus)\n"
                actions_text += f"   ↪️ Two-stage: Beat defender, then beat keeper\n\n"
            else:
                # Single-stage action (normal display)
                actions_text += f"{emoji} **{action_name}** — **{chance}%** `[{difficulty}]`\n"
                actions_text += f"   📊 "

                if data['player_bonus'] > 0:
                    actions_text += f"{data['primary']}/{data['secondary']}: {data['player_stat']}+{data['player_bonus']}=**{data['player_effective']}**"
                else:
                    actions_text += f"{data['primary']}/{data['secondary']}: **{data['player_effective']}**"

                if defender and data['defender_effective'] > 0:
                    actions_text += f" vs "
                    if data['defender_bonus'] > 0:
                        actions_text += f"{data['defender_stat']}+{data['defender_bonus']}=**{data['defender_effective']}**"
                    else:
                        actions_text += f"**{data['defender_effective']}**"

                actions_text += f"\n   ↪️ {self.get_followup_description(action)}\n\n"

        embed.add_field(name="⚡ CHOOSE YOUR ACTION", value=actions_text, inline=False)

        if defender:
            embed.set_footer(
                text=f"⚔️ vs {defender['player_name']} ({defender['position']}) | ⭐ = Best Choice | 🎲 = Die Roll After | ⏱️ 30s")
        else:
            embed.set_footer(text="⭐ = Best Choice | 🎲 = Die Roll After Choice | ⏱️ 30 seconds")

        # ✅ NEW: Create view with AFK button if needed, pass match_engine
        view = EnhancedActionView(available_actions, player['user_id'], timeout=30,
                                  show_afk_button=has_timed_out, match_engine=self)
        view.match_id = match_id  # Pass match context

        if crests_file:
            message = await channel.send(content=f"📢 {member.mention}", embed=embed, file=crests_file, view=view)
        else:
            message = await channel.send(content=f"📢 {member.mention}", embed=embed, view=view)

        await view.wait()

        action = view.chosen_action if view.chosen_action else random.choice(available_actions)

        # ✅ FIXED: Distinguish between skip and timeout
        if not view.chosen_action:
            if view.skipped:
                # Player clicked skip button - don't penalize them
                await channel.send(f"⏭️ {member.mention} **SKIPPED** - Selected: {action.upper()}")
            else:
                # Natural timeout - mark for AFK button next time
                self.player_timeouts[match_id].add(player['user_id'])
                await channel.send(f"⏰ {member.mention} **TIMED OUT** - Auto-selected: {action.upper()}")

        result = await self.execute_action_with_duel(channel, player, adjusted_stats, defender, action, minute,
                                                     match_id, member, attacking_team, defending_team, is_european,
                                                     is_home)
        return result

    async def execute_action_with_duel(self, channel, player, adjusted_stats, defender, action, minute,
                                       match_id, member, attacking_team, defending_team, is_european=False,
                                       is_home=False):

        att_p, att_s, def_p, def_s = self.get_action_stats(action)

        player_stat = self.calculate_weighted_stat(adjusted_stats, att_p, att_s)
        position_bonus = self.get_position_bonus(player['position'], action)
        home_bonus = self.get_home_advantage_bonus(is_home, player['position'])

        player_roll = random.randint(1, 20)
        player_roll_with_bonus = player_roll + position_bonus + home_bonus
        player_total = player_stat + player_roll_with_bonus

        defender_roll = 0
        defender_total = 0
        defender_stat_value = 0
        defender_position_bonus = 0

        if defender:
            defender_stat_value = self.calculate_weighted_stat(defender, def_p, def_s)
            defender_roll = random.randint(1, 20)
            defender_position_bonus = self.get_position_bonus(defender.get('position', 'CB'), action) if defender else 0
            defender_total = defender_stat_value + defender_roll + defender_position_bonus

        success = player_total > defender_total if defender_total > 0 else player_roll_with_bonus >= 10

        # ✅ NEW: Check if this is a shoot/header vs non-GK (needs 2-stage system)
        is_two_stage_shot = (action in ['shoot', 'header'] and
                             success and  # Only if we beat the defender
                             defender and
                             defender.get('position') != 'GK')

        team_side = 'home' if is_home else 'away'
        self.update_match_stats(match_id, team_side, action, success)

        critical_success = player_roll == 20
        critical_failure = player_roll == 1

        suspense_embed = discord.Embed(
            title=f"⚡ {action.replace('_', ' ').upper()}!",
            description=f"**{player['player_name']}** attempts the action...",
            color=discord.Color.orange()
        )
        suspense_msg = await channel.send(embed=suspense_embed)
        await asyncio.sleep(1.5)

        result_embed = discord.Embed(
            title=f"🎲 {action.replace('_', ' ').upper()}",
            color=discord.Color.green() if success else discord.Color.red()
        )

        # ✅ Show stage 1 results (vs defender)
        if defender and defender_total > 0:
            duel_text = f"**YOU**\n"
            duel_text += f"{att_p.upper()}/{att_s.upper()}: **{player_stat}**\n"
            duel_text += f"🎲 **{player_roll}**"
            if position_bonus > 0:
                duel_text += f" +{position_bonus} ({player['position']})"
            if home_bonus > 0:
                duel_text += f" +{home_bonus} (🏠)"
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
                if is_two_stage_shot:
                    duel_text += f"\n⚽ Now facing the goalkeeper..."
            else:
                duel_text += f"❌ **DEFENDER WINS**"

            result_embed.add_field(name="⚔️ Stage 1: vs Defender", value=duel_text, inline=False)
        else:
            result_embed.add_field(
                name="🎲 Roll",
                value=f"Stat: **{player_stat}** | Roll: **{player_roll_with_bonus}** | Total: **{player_total}**\n\n"
                      f"{'✅ Success!' if success else '❌ Failed!'}",
                inline=False
            )

        # ✅ NEW: STAGE 2 - Shot Placement System (if applicable)
        keeper_save = False
        keeper_result_embed = result_embed

        if is_two_stage_shot:
            await channel.send(embed=result_embed)
            await asyncio.sleep(1)

            # Get the goalkeeper
            async with db.pool.acquire() as conn:
                if is_european:
                    keeper = await conn.fetchrow("""
                        SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                               dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                        FROM npc_players
                        WHERE team_id = $1 AND position = 'GK' AND retired = FALSE
                        LIMIT 1
                    """, defending_team['team_id'])
                    
                    if not keeper:
                        keeper = await conn.fetchrow("""
                            SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                                   dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                            FROM european_npc_players
                            WHERE team_id = $1 AND position = 'GK' AND retired = FALSE
                            LIMIT 1
                        """, defending_team['team_id'])
                else:
                    keeper = await conn.fetchrow("""
                        SELECT * FROM npc_players
                        WHERE team_id = $1 AND position = 'GK' AND retired = FALSE LIMIT 1
                    """, defending_team['team_id'])
                keeper = dict(keeper) if keeper else None

            if keeper:
                # 🎯 SHOT PLACEMENT SYSTEM
                shot_placement_config = self.get_shot_placement_config()

                # Create placement choice embed
                placement_embed = discord.Embed(
                    title="🎯 SHOT PLACEMENT - Choose Where to Aim!",
                    description=f"**{player['player_name']}** - You've beaten the defender!\n\n"
                                f"Now choose where to place your shot:",
                    color=discord.Color.gold()
                )

                # Calculate stats for each placement option
                options_text = ""
                for key in ['left_corner', 'right_corner', 'top_center', 'low_center', 'power_shot']:
                    config = shot_placement_config[key]

                    # Get player stat
                    if config['stat_used'] == 'physical':
                        player_placement_stat = adjusted_stats['physical']
                    else:
                        player_placement_stat = adjusted_stats['shooting']

                    player_total_with_bonus = player_placement_stat + config['player_bonus']

                    # Get keeper stat
                    keeper_stat = self.calculate_weighted_stat(keeper, 'defending', 'physical')
                    keeper_bonus_val = self.get_position_bonus('GK', 'save')
                    keeper_total_adjusted = keeper_stat + keeper_bonus_val + 5 + config['keeper_penalty']

                    # Calculate success probability
                    goal_chance = self.calculate_d20_success_probability(
                        player_total_with_bonus,
                        keeper_total_adjusted
                    )

                    # Account for miss chance
                    actual_chance = int(goal_chance * (1 - config['miss_chance'] / 100))

                    # Determine color indicator
                    if actual_chance >= 55:
                        indicator = "🟢"
                    elif actual_chance >= 40:
                        indicator = "🟡"
                    else:
                        indicator = "🔴"

                    options_text += f"{config['emoji']} **{config['name']}** {indicator} — {actual_chance}% chance\n"
                    options_text += f"   Your: {player_total_with_bonus} vs GK: {keeper_total_adjusted} | Miss risk: {config['miss_chance']}%\n"
                    options_text += f"   _{config['description']}_\n\n"

                placement_embed.add_field(
                    name="⚽ Placement Options",
                    value=options_text,
                    inline=False
                )

                placement_embed.set_footer(text="⏱️ 15 seconds to choose | 🟢 = Good | 🟡 = Fair | 🔴 = Risky")

                # Create button view
                placement_view = ShotPlacementView(
                    player, keeper, adjusted_stats, shot_placement_config, timeout=15
                )

                placement_msg = await channel.send(
                    content=f"📢 {member.mention}",
                    embed=placement_embed,
                    view=placement_view
                )

                await placement_view.wait()

                chosen_placement = placement_view.chosen_placement or 'low_center'
                config = shot_placement_config[chosen_placement]

                # Show choice
                choice_embed = discord.Embed(
                    title=f"{config['emoji']} {config['name']} Chosen!",
                    description=f"**{player['player_name']}** aims for the {config['name'].lower()}...",
                    color=discord.Color.orange()
                )
                await channel.send(embed=choice_embed)
                await asyncio.sleep(1.5)

                # STEP 1: Check if shot is on target (miss check)
                miss_roll = random.randint(1, 100)
                shot_missed_target = miss_roll <= config['miss_chance']

                if shot_missed_target:
                    miss_embed = discord.Embed(
                        title="😱 SHOT MISSED!",
                        description=f"**{player['player_name']}'s** shot goes wide!\n\n"
                                    f"Miss roll: {miss_roll} (needed >{config['miss_chance']})",
                        color=discord.Color.red()
                    )

                    # Visual showing ball going wide
                    keeper_dove = random.choice(['left', 'right', 'center'])
                    visual_buffer = await self.create_goal_visualization(
                        chosen_placement, keeper_dove, False,
                        player['player_name'], keeper['player_name']
                    )

                    if visual_buffer:
                        miss_embed.set_image(url="attachment://shot_result.png")
                        shot_file = discord.File(fp=visual_buffer, filename="shot_result.png")
                        await channel.send(embed=miss_embed, file=shot_file)
                    else:
                        await channel.send(embed=miss_embed)

                    # ✅ CORRECT: Mark as failed attempt, not keeper save
                    keeper_save = True  # Keeps the flow the same (no goal)
                    # But you should track this separately if you want accurate keeper stats

                else:
                    # Shot is on target - now keeper duel!
                    if config['stat_used'] == 'physical':
                        player_shoot_stat = adjusted_stats['physical']
                    else:
                        player_shoot_stat = adjusted_stats['shooting']

                    player_shoot_stat_with_bonus = player_shoot_stat + config['player_bonus']
                    player_shoot_roll = random.randint(1, 20)
                    player_shoot_total = player_shoot_stat_with_bonus + player_shoot_roll

                    keeper_stat = self.calculate_weighted_stat(keeper, 'defending', 'physical')
                    keeper_bonus_val = self.get_position_bonus('GK', 'save')
                    keeper_stat_with_penalty = keeper_stat + keeper_bonus_val + 13 + config['keeper_penalty']
                    keeper_roll = random.randint(1, 20)
                    keeper_total = keeper_stat_with_penalty + keeper_roll

                    keeper_save = keeper_total >= player_shoot_total

                    # Determine where keeper dove
                    if chosen_placement in ['left_corner', 'top_center']:
                        keeper_dove = 'left'
                    elif chosen_placement in ['right_corner']:
                        keeper_dove = 'right'
                    else:
                        keeper_dove = 'center'

                    # Show stage 2 results
                    keeper_result_embed = discord.Embed(
                        title="🥅 SHOT vs GOALKEEPER",
                        color=discord.Color.red() if keeper_save else discord.Color.green()
                    )

                    keeper_duel_text = f"**YOU ({config['name'].upper()})**\n"
                    keeper_duel_text += f"{config['stat_used'].upper()[:3]}: **{player_shoot_stat}** +{config['player_bonus']} (placement)\n"
                    keeper_duel_text += f"🎲 **{player_shoot_roll}**\n"
                    keeper_duel_text += f"Total: **{player_shoot_total}**\n\n"

                    keeper_duel_text += f"**{keeper['player_name']} (GK)**\n"
                    keeper_duel_text += f"DEF/PHY: **{keeper_stat}**\n"
                    keeper_duel_text += f"🎲 **{keeper_roll}** +{keeper_bonus_val} (GK) +5 (save) {config['keeper_penalty']:+d} (placement)\n"
                    keeper_duel_text += f"Total: **{keeper_total}**\n\n"

                    if keeper_save:
                        keeper_duel_text += f"🧤 **KEEPER SAVES!**\n_{config['fail_text']}_"
                    else:
                        keeper_duel_text += f"⚽ **GOAL!!!**\n_{config['success_text']}_"

                    keeper_result_embed.add_field(name="⚔️ Duel", value=keeper_duel_text, inline=False)

                    # Add visual
                    visual_buffer = await self.create_goal_visualization(
                        chosen_placement, keeper_dove, not keeper_save,
                        player['player_name'], keeper['player_name']
                    )

                    if visual_buffer:
                        keeper_result_embed.set_image(url="attachment://shot_result.png")
                        shot_file = discord.File(fp=visual_buffer, filename="shot_result.png")
                        await channel.send(embed=keeper_result_embed, file=shot_file)
                    else:
                        await channel.send(embed=keeper_result_embed)

                result_embed = keeper_result_embed

        is_goal = False
        scorer_name = None
        assister_name = None
        rating_change = 0

        if action in ['tackle', 'block'] and not success:
            if defender and player_total < defender_total - 12:
                if random.random() < 0.20:
                    await self.give_yellow_card(player, match_id, channel, "dangerous tackle")

        if critical_success:
            result_embed.add_field(
                name="🌟 NAT 20!",
                value="Perfect execution! Major advantage, but not guaranteed...",
                inline=False
            )
            rating_change = 0.5

            if action in ['shoot', 'header']:
                if not is_two_stage_shot:
                    # Get keeper
                    async with db.pool.acquire() as conn:
                        if is_european:
                            keeper = await conn.fetchrow("""
                                SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                                       dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                                FROM npc_players
                                WHERE team_id = $1 AND position = 'GK' AND retired = FALSE
                                LIMIT 1
                            """, defending_team['team_id'])
                            
                            if not keeper:
                                keeper = await conn.fetchrow("""
                                    SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                                           dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                                    FROM european_npc_players
                                    WHERE team_id = $1 AND position = 'GK' AND retired = FALSE
                                    LIMIT 1
                                """, defending_team['team_id'])
                        else:
                            keeper = await conn.fetchrow("""
                                SELECT * FROM npc_players
                                WHERE team_id = $1 AND position = 'GK' AND retired = FALSE LIMIT 1
                            """, defending_team['team_id'])

                    if keeper:
                        keeper_stat = self.calculate_weighted_stat(keeper, 'defending', 'physical')
                        keeper_roll = random.randint(1, 20)
                        # ✅ REBALANCED: Keeper gets +13 bonus
                        keeper_total = keeper_stat + keeper_roll + 13

                        # Nat 20 gives +15 bonus, keeper has 40% resistance
                        player_vs_keeper = player_stat + 20 + 15

                        if random.random() < 0.40 and keeper_roll >= 15:
                            # Keeper saves Nat 20!
                            result_embed.add_field(
                                name="🧤 MIRACLE SAVE!",
                                value=f"Keeper denies the Nat 20!\nYour {player_vs_keeper} vs GK {keeper_total}",
                                inline=False
                            )
                            rating_change = 0.3
                        elif player_vs_keeper > keeper_total:
                            is_goal = True
                            scorer_name = player['player_name']
                            rating_change = 1.8
                        else:
                            result_embed.add_field(
                                name="🧤 SAVED!",
                                value=f"Keeper positioned perfectly!\nYour {player_vs_keeper} vs GK {keeper_total}",
                                inline=False
                            )
                            rating_change = 0.3
                    else:
                        is_goal = True
                        scorer_name = player['player_name']
                        rating_change = 1.8
                else:
                    # Two-stage shot - nat 20 skips stage 2
                    is_goal = True
                    scorer_name = player['player_name']
                    rating_change = 1.8

                if is_goal:
                    async with db.pool.acquire() as conn:
                        await conn.execute("""
                            UPDATE match_participants
                            SET goals_scored = goals_scored + 1
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

        elif critical_failure:
            result_embed.add_field(
                name="💥 NAT 1!",
                value="Disaster!",
                inline=False
            )
            rating_change = -0.5
            success = False

            if action in ['tackle', 'block']:
                await self.give_yellow_card(player, match_id, channel, "reckless challenge")

        # ✅ UPDATED: Goal logic now accounts for two-stage system
        if not is_goal and not critical_failure:
            if action in ['shoot', 'header'] and success:
                # For two-stage shots, check if keeper saved it
                if is_two_stage_shot:
                    if not keeper_save:
                        # Beat defender AND beat keeper = GOAL
                        is_goal = True
                        scorer_name = player['player_name']
                        rating_change = 1.2

                        async with db.pool.acquire() as conn:
                            await conn.execute("""
                                UPDATE match_participants
                                SET goals_scored = goals_scored + 1
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
                        # Beat defender but keeper saved
                        rating_change = 0.1  # Small bonus for getting shot on target
                else:
                    # Single-stage shot (already vs GK) - use original logic
                    # ✅ REBALANCED: Much harder to score directly
                    if player_roll_with_bonus >= 19 and player_total >= defender_total + 20:
                        is_goal = True
                        scorer_name = player['player_name']
                        rating_change = 1.2

                        async with db.pool.acquire() as conn:
                            await conn.execute("""
                                UPDATE match_participants
                                SET goals_scored = goals_scored + 1
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
                        rating_change = -0.1

            elif action in ['pass', 'through_ball', 'key_pass', 'cross'] and success:
                assist_chance = {'pass': 0.12, 'through_ball': 0.18, 'key_pass': 0.25, 'cross': 0.15}
                if random.random() < assist_chance.get(action, 0.20):
                    teammate_result = await self.handle_teammate_goal(channel, player, attacking_team, match_id,
                                                                      is_european)
                    if teammate_result:
                        is_goal = True
                        scorer_name = teammate_result['scorer_name']
                        assister_name = player['player_name']
                        rating_change = 0.8

                        async with db.pool.acquire() as conn:
                            await conn.execute("""
                                UPDATE match_participants
                                SET assists = assists + 1
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
        # Only send result embed if we didn't already send it for shot placement
        if not is_two_stage_shot or keeper_save:
            await channel.send(embed=result_embed)

        async with db.pool.acquire() as conn:
            await conn.execute("""
                UPDATE match_participants
                SET match_rating = GREATEST(0.0, LEAST(10.0, match_rating + $1)),
                    actions_taken = actions_taken + 1
                WHERE match_id = $2 AND user_id = $3
            """, rating_change, match_id, player['user_id'])

        try:
            from match_visualizer import generate_action_visualization

            viz = await generate_action_visualization(
                action=action,
                player=player,
                defender=defender,
                is_home=is_home,
                success=success,
                is_goal=is_goal,
                animated=False
            )

            await channel.send(file=discord.File(fp=viz, filename="action.png"))
        except Exception as e:
            print(f"⚠️ Visualization error: {e}")

        followup_result = await self.handle_followup_action(
            channel, action, success, player, attacking_team, defending_team, match_id, is_european
        )

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

    async def handle_npc_moment(self, channel, team_id, minute, attacking_team, defending_team, is_home,
                                is_european=False):
        async with db.pool.acquire() as conn:
            if is_european:
                result = await conn.fetchrow("""
                    SELECT player_name, npc_id, team_id, position, pace, shooting, passing, 
                           dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                    FROM npc_players
                    WHERE team_id = $1 AND retired = FALSE
                    ORDER BY RANDOM() LIMIT 1
                """, team_id)
                
                if not result:
                    result = await conn.fetchrow("""
                        SELECT player_name, european_npc_id as npc_id, team_id, position, pace, shooting, passing, 
                               dribbling, defending, physical, overall_rating, season_goals, season_assists, retired
                        FROM european_npc_players
                        WHERE team_id = $1 AND retired = FALSE
                        ORDER BY RANDOM() LIMIT 1
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

        # ✅ REBALANCED: NPC goals much harder
        if action == 'shoot' and success and roll >= 19 and total >= 100:
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

    async def start_match(self, fixture: dict, interaction: discord.Interaction, is_european: bool = False):
        """Start a match - supports both domestic and European competitions"""

        async with db.pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT match_id FROM active_matches WHERE fixture_id = $1",
                fixture['fixture_id']
            )
            if existing:
                print(
                    f"⚠️ Cleaning up existing active match {existing['match_id']} for fixture {fixture['fixture_id']}")
                await conn.execute(
                    "DELETE FROM active_matches WHERE fixture_id = $1",
                    fixture['fixture_id']
                )
                match_id = existing['match_id']
                if match_id in self.active_matches:
                    del self.active_matches[match_id]
                if match_id in self.pinned_messages:
                    try:
                        msg = self.pinned_messages[match_id]
                        await msg.unpin()
                    except:
                        pass
                    del self.pinned_messages[match_id]
                if match_id in self.match_yellow_cards:
                    del self.match_yellow_cards[match_id]
                if match_id in self.match_stats:
                    del self.match_stats[match_id]

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

        for member in guild.members:
            if member.guild_permissions.administrator and member.id not in player_users:
                overwrites[member] = discord.PermissionOverwrite(read_messages=True, send_messages=False)

        spectator_role = discord.utils.get(guild.roles, name="Spectator")
        if spectator_role:
            overwrites[spectator_role] = discord.PermissionOverwrite(read_messages=True, send_messages=False)

        match_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

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
            value=f"⏱️ 30s decision time\n🎲 Stat + D20 battle system",
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
        await self.run_match(match_id, fixture, match_channel, is_european)

    async def get_team_info(self, team_id, is_european=False):
        """Get team info from appropriate table"""
        async with db.pool.acquire() as conn:
            if is_european:
                team = await conn.fetchrow("""
                    SELECT team_id, team_name, 'European' as league
                    FROM european_teams
                    WHERE team_id = $1
                """, team_id)

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

    async def run_match(self, match_id: int, fixture: dict, channel: discord.TextChannel,
                        is_european: bool = False):
        """Complete match engine with all fixes"""
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

        self.initialize_match_stats(match_id, home_participants, away_participants)

        distribution = self.calculate_event_distribution(home_participants, away_participants)

        print(f"📊 Match Setup:")
        print(f"   Total Events: {distribution['total']}")
        print(f"   Player Moments: {distribution['player_moments']}")
        print(f"   NPC Moments: {distribution['npc_moments']}")
        print(f"   Set Pieces: {distribution['set_pieces']}")

        player_schedule = await self.create_fair_player_schedule(
            home_participants,
            away_participants,
            distribution['player_moments']
        )

        complete_schedule = []
        complete_schedule.extend(player_schedule)

        npc_moment_types = [
            'npc_attack', 'npc_attack', 'npc_attack',
            'dramatic_save', 'dramatic_save',
            'near_miss', 'near_miss', 'near_miss',
            'counter_attack', 'counter_attack',
            'defensive_block',
            'midfield_battle',
        ]

        for moment_type in npc_moment_types[:distribution['npc_moments']]:
            complete_schedule.append({
                'type': moment_type,
                'team_side': random.choice(['home', 'away'])
            })

        for _ in range(distribution['set_pieces']):
            complete_schedule.append({
                'type': 'set_piece',
                'team_side': random.choice(['home', 'away'])
            })

        random.shuffle(complete_schedule)

        possible_minutes = list(range(3, 91, 3))

        # ✅ FIX: Ensure we never try to sample more minutes than available
        if len(complete_schedule) > len(possible_minutes):
            # Add more minute slots if needed
            additional_minutes = list(range(4, 91, 2))
            all_minutes = sorted(list(set(possible_minutes + additional_minutes)))

            # If STILL not enough, add every minute as last resort
            if len(complete_schedule) > len(all_minutes):
                all_minutes = list(range(1, 91))

            # Always use min() to prevent sampling more than available
            minutes = sorted(random.sample(all_minutes, min(len(complete_schedule), len(all_minutes))))
        else:
            minutes = sorted(random.sample(possible_minutes, len(complete_schedule)))

        await self.update_pinned_score(channel, match_id, home_team, away_team, home_score, away_score, 0)

        for i, minute in enumerate(minutes):
            if i >= len(complete_schedule):
                break

            event = complete_schedule[i]

            await self.update_pinned_score(channel, match_id, home_team, away_team, home_score, away_score, minute)

            if minute >= 45 and minute < 48 and not hasattr(self, f'_halftime_shown_{match_id}'):
                setattr(self, f'_halftime_shown_{match_id}', True)
                await self.post_halftime_summary(channel, home_team, away_team, home_score, away_score, participants,
                                                 match_id)
                await self.display_match_stats(channel, match_id, home_team, away_team)

            result = None

            if event['type'] == 'player':
                participant = event['participant']
                player = event['player']
                is_home = (event['team_side'] == 'home')
                attacking_team_obj = home_team if is_home else away_team
                defending_team_obj = away_team if is_home else home_team

                result = await self.handle_player_moment(
                    channel, player, participant, minute,
                    attacking_team_obj, defending_team_obj,
                    is_home, match_id, is_european
                )

                if result and result.get('goal'):
                    if is_home:
                        home_score += 1
                    else:
                        away_score += 1
                    await self.post_goal_celebration(
                        channel, result['scorer_name'],
                        attacking_team_obj['team_name'],
                        attacking_team_obj['team_id'],
                        home_score, away_score,
                        result.get('assister_name')
                    )

            elif event['type'] == 'set_piece':
                attacking_team_obj = home_team if event['team_side'] == 'home' else away_team
                defending_team_obj = away_team if event['team_side'] == 'home' else home_team

                set_result = await self.handle_set_piece(
                    channel, attacking_team_obj, defending_team_obj, minute, match_id, is_european
                )

                if set_result and set_result.get('goal'):
                    if event['team_side'] == 'home':
                        home_score += 1
                    else:
                        away_score += 1
                    await self.post_goal_celebration(
                        channel, set_result['scorer_name'],
                        attacking_team_obj['team_name'],
                        attacking_team_obj['team_id'],
                        home_score, away_score,
                        set_result.get('assister_name')
                    )

            elif event['type'] == 'npc_attack':
                attacking_team_obj = home_team if event['team_side'] == 'home' else away_team
                defending_team_obj = away_team if event['team_side'] == 'home' else home_team
                is_home = (event['team_side'] == 'home')

                npc_result = await self.handle_npc_moment(
                    channel, attacking_team_obj['team_id'], minute,
                    attacking_team_obj, defending_team_obj, is_home, is_european
                )

                if npc_result == 'goal':
                    if event['team_side'] == 'home':
                        home_score += 1
                    else:
                        away_score += 1
                    await self.update_pinned_score(channel, match_id, home_team, away_team, home_score, away_score,
                                                   minute)

            else:
                exciting_result = await self.handle_exciting_npc_moment(
                    channel, event['type'], minute, home_team, away_team, event['team_side']
                )

                if exciting_result == 'goal':
                    if event['team_side'] == 'home':
                        home_score += 1
                    else:
                        away_score += 1
                    await self.update_pinned_score(channel, match_id, home_team, away_team, home_score, away_score,
                                                   minute)

            async with db.pool.acquire() as conn:
                await conn.execute(
                    'UPDATE active_matches SET home_score = $1, away_score = $2, current_minute = $3 WHERE match_id = $4',
                    home_score, away_score, minute, match_id
                )

            await asyncio.sleep(1.5)

        await self.end_match(match_id, fixture, channel, home_score, away_score, participants, is_european)

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
                SELECT user_id, match_rating
                FROM match_participants
                WHERE match_id = $1 AND user_id IS NOT NULL
            """, match_id)

        rating_lookup = {row['user_id']: row['match_rating'] for row in updated_ratings}

        for participant in participants:
            if participant['user_id']:
                actual_rating = rating_lookup.get(participant['user_id'], participant['match_rating'])
                new_form = await update_player_form(participant['user_id'], actual_rating)
                print(
                    f"  📊 Form updated for user {participant['user_id']}: Rating {actual_rating:.1f} → Form {new_form}")

        for participant in participants:
            if participant['user_id']:
                async with db.pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE players
                        SET season_apps = season_apps + 1,
                            career_apps = career_apps + 1
                        WHERE user_id = $1
                    """, participant['user_id'])

        # ✅ NEW: Update NPC ratings after match
        try:
            from utils.npc_rating_manager import update_npcs_after_match
            await update_npcs_after_match(match_id, home_score, away_score)
            logger.info(f"✅ Updated NPC ratings for match {match_id}")
        except Exception as e:
            logger.error(f"❌ Error updating NPC ratings after match: {e}")

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
                        FROM match_participants
                        WHERE match_id = $1 AND user_id IS NOT NULL
                    """, match_id)

                if updated_participants:
                    motm = max(updated_participants, key=lambda p: p['match_rating'])

                    async with db.pool.acquire() as conn:
                        await conn.execute("""
                            UPDATE match_participants
                            SET motm = TRUE
                            WHERE match_id = $1 AND user_id = $2
                        """, match_id, motm['user_id'])

                        await conn.execute("""
                            UPDATE players
                            SET season_motm = season_motm + 1,
                                career_motm = career_motm + 1
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
            from match_highlights import MatchHighlightsGenerator

            try:
                highlights_buffer = await MatchHighlightsGenerator.generate_match_highlights(
                    match_id=match_id,
                    max_highlights=5
                )
            except Exception as e:
                print(f"⚠️ Could not generate highlights: {e}")
                highlights_buffer = None

            await post_match_result_to_channel(self.bot, channel.guild, fixture, home_score, away_score,
                                               highlights_buffer)
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
        """Simulate NPC match using actual team strength"""
        async with db.pool.acquire() as conn:
            if is_european:
                home_team = await conn.fetchrow("""
                    SELECT team_id, team_name FROM european_teams WHERE team_id = $1
                """, home_team_id)
                away_team = await conn.fetchrow("""
                    SELECT team_id, team_name FROM teams WHERE team_id = $1
                """, away_team_id)

            if not home_team or not away_team:
                raise ValueError(f"Could not find teams: {home_team_id}, {away_team_id}")

            if is_european:
                home_npcs = await conn.fetch("""
                    SELECT overall_rating FROM npc_players
                    WHERE team_id = $1 AND retired = FALSE
                """, home_team_id)
                
                if not home_npcs:
                    home_npcs = await conn.fetch("""
                        SELECT overall_rating FROM european_npc_players
                        WHERE team_id = $1 AND retired = FALSE
                    """, home_team_id)

                away_npcs = await conn.fetch("""
                    SELECT overall_rating FROM npc_players
                    WHERE team_id = $1 AND retired = FALSE
                """, away_team_id)
                
                if not away_npcs:
                    away_npcs = await conn.fetch("""
                        SELECT overall_rating FROM european_npc_players
                        WHERE team_id = $1 AND retired = FALSE
                    """, away_team_id)
            else:
                home_npcs = await conn.fetch("""
                    SELECT overall_rating FROM npc_players
                    WHERE team_id = $1 AND retired = FALSE
                """, home_team_id)

                away_npcs = await conn.fetch("""
                    SELECT overall_rating FROM npc_players
                    WHERE team_id = $1 AND retired = FALSE
                """, away_team_id)

            home_rating = sum(p['overall_rating'] for p in home_npcs) / len(home_npcs) if home_npcs else 75
            away_rating = sum(p['overall_rating'] for p in away_npcs) / len(away_npcs) if away_npcs else 75

            if home_rating >= 85:
                home_modifier = 25
            elif home_rating >= 80:
                home_modifier = 20
            elif home_rating >= 75:
                home_modifier = 15
            elif home_rating >= 70:
                home_modifier = 10
            elif home_rating >= 65:
                home_modifier = 5
            else:
                home_modifier = 0

            if away_rating >= 85:
                away_modifier = 25
            elif away_rating >= 80:
                away_modifier = 20
            elif away_rating >= 75:
                away_modifier = 15
            elif away_rating >= 70:
                away_modifier = 10
            elif away_rating >= 65:
                away_modifier = 5
            else:
                away_modifier = 0

            home_advantage = 5

            home_strength = home_rating + home_modifier + home_advantage
            away_strength = away_rating + away_modifier

            home_goals = 0
            away_goals = 0

            num_chances = random.randint(8, 14)

            for _ in range(num_chances):
                if random.random() < (home_strength / 400):
                    home_goals += 1

                if random.random() < (away_strength / 400):
                    away_goals += 1

            home_goals = min(home_goals, 6)
            away_goals = min(away_goals, 6)

            if random.random() < 0.05:
                home_goals = min(home_goals + random.randint(0, 2), 8)
                away_goals = min(away_goals + random.randint(0, 2), 8)

            return {
                'home_score': home_goals,
                'away_score': away_goals,
                'home_team': home_team['team_name'],
                'away_team': away_team['team_name']
            }


# ═══════════════════════════════════════════════════════════════
# ✅ BUTTON CLASSES WITH SKIP & AFK FUNCTIONALITY + SHOT PLACEMENT
# ═══════════════════════════════════════════════════════════════

class EnhancedActionView(discord.ui.View):
    def __init__(self, available_actions, user_id, timeout=30, show_afk_button=False, match_engine=None):
        super().__init__(timeout=timeout)
        self.chosen_action = None
        self.owner_user_id = user_id
        self.skipped = False
        self.match_engine = match_engine

        emoji_map = {
            'shoot': '🎯', 'pass': '🎪', 'dribble': '🪄', 'tackle': '🛡️', 'cross': '📤',
            'clearance': '🚀', 'through_ball': '⚡', 'save': '🧤', 'interception': '👀',
            'block': '🧱', 'cut_inside': '↩️', 'key_pass': '🔑', 'long_ball': '📡',
            'overlap': '🏃', 'claim_cross': '✊', 'distribution': '🎯', 'hold_up_play': '💪',
            'run_in_behind': '🏃', 'press_defender': '⚡', 'track_back': '🔙',
            'press': '⚡', 'cover': '🛡️', 'track_runner': '🏃', 'sweep': '🧹', 'header': '🎯'
        }

        # Add action buttons (first row)
        for action in available_actions[:5]:
            button = ActionButton(action, emoji_map.get(action, '⚽'))
            self.add_item(button)

        # Add skip button (second row) - ALWAYS visible
        skip_button = SkipTurnButton()
        self.add_item(skip_button)

        # Add AFK button (second row) - ONLY if player has timed out before
        if show_afk_button:
            afk_button = MarkAFKButton()
            self.add_item(afk_button)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class ActionButton(discord.ui.Button):
    def __init__(self, action, emoji):
        label = action.replace('_', ' ').title()
        super().__init__(
            label=label,
            emoji=emoji,
            style=discord.ButtonStyle.primary,
            row=0
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
        self.view.skipped = False
        for item in self.view.children:
            item.disabled = True
        await interaction.edit_original_response(view=self.view)
        self.view.stop()


class SkipTurnButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Skip Turn (Auto)",
            emoji="⏭️",
            style=discord.ButtonStyle.secondary,
            row=1
        )

    async def callback(self, interaction: discord.Interaction):
        match_id = getattr(self.view, 'match_id', None)

        if not match_id:
            await interaction.response.send_message(
                "❌ Error: Match context not found!",
                ephemeral=True
            )
            return

        # Check if clicker is a participant
        async with db.pool.acquire() as conn:
            participant = await conn.fetchrow("""
                SELECT user_id, team_id FROM match_participants 
                WHERE match_id = $1 AND user_id = $2
            """, match_id, interaction.user.id)

        if not participant:
            await interaction.response.send_message(
                "❌ Only players in this match can skip turns!",
                ephemeral=True
            )
            return

        # Just skip immediately
        await interaction.response.defer()

        # Select best action
        available_actions = [item.action for item in self.view.children if isinstance(item, ActionButton)]
        if available_actions:
            self.view.chosen_action = available_actions[0]
            self.view.skipped = True

        # Disable buttons
        for item in self.view.children:
            item.disabled = True

        try:
            await interaction.edit_original_response(view=self.view)
        except discord.errors.NotFound:
            pass
        except Exception as e:
            print(f"⚠️ Failed to edit interaction: {e}")

        # Public feedback
        skipper_member = interaction.guild.get_member(interaction.user.id)
        skipper_name = skipper_member.display_name if skipper_member else "Player"

        turn_owner_id = self.view.owner_user_id
        turn_owner_member = interaction.guild.get_member(turn_owner_id)
        turn_owner_name = turn_owner_member.display_name if turn_owner_member else "Player"

        if interaction.user.id == turn_owner_id:
            skip_msg = (
                f"⏭️ **{skipper_name}** skipped their turn\n"
                f"Auto-selected: **{self.view.chosen_action.upper()}**"
            )
        else:
            skip_msg = (
                f"⏭️ **{skipper_name}** skipped **{turn_owner_name}**'s turn\n"
                f"Auto-selected: **{self.view.chosen_action.upper()}**"
            )

        await interaction.followup.send(skip_msg, ephemeral=False)

        self.view.stop()


class MarkAFKButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Mark AFK",
            emoji="💤",
            style=discord.ButtonStyle.danger,
            row=1
        )

    async def callback(self, interaction: discord.Interaction):
        match_id = getattr(self.view, 'match_id', None)
        turn_owner_id = self.view.owner_user_id

        if not match_id:
            await interaction.response.send_message("❌ Error: Match context not found!", ephemeral=True)
            return

        # Check if clicker is opponent
        async with db.pool.acquire() as conn:
            skipper = await conn.fetchrow("""
                SELECT team_id FROM match_participants 
                WHERE match_id = $1 AND user_id = $2
            """, match_id, interaction.user.id)

            turn_owner = await conn.fetchrow("""
                SELECT team_id FROM match_participants 
                WHERE match_id = $1 AND user_id = $2
            """, match_id, turn_owner_id)

        if not skipper or not turn_owner:
            await interaction.response.send_message("❌ Error: Players not found!", ephemeral=True)
            return

        if skipper['team_id'] == turn_owner['team_id']:
            await interaction.response.send_message("❌ You can only mark opponents as AFK!", ephemeral=True)
            return

        # Mark player as AFK
        if self.view.match_engine:
            if match_id not in self.view.match_engine.afk_players:
                self.view.match_engine.afk_players[match_id] = set()
            self.view.match_engine.afk_players[match_id].add(turn_owner_id)

        await interaction.response.defer()

        # Disable buttons
        for item in self.view.children:
            item.disabled = True

        try:
            await interaction.edit_original_response(view=self.view)
        except:
            pass

        # Public announcement
        turn_owner_member = interaction.guild.get_member(turn_owner_id)
        turn_owner_name = turn_owner_member.display_name if turn_owner_member else "player"

        await interaction.followup.send(
            f"💤 **{turn_owner_name} marked as AFK**\n"
            f"All remaining turns will auto-play with recommended actions.",
            ephemeral=False
        )

        # Auto-select this turn
        available_actions = [item.action for item in self.view.children if isinstance(item, ActionButton)]
        if available_actions:
            self.view.chosen_action = available_actions[0]
            self.view.skipped = True

        self.view.stop()


# ✅ NEW: Shot Placement View and Buttons
class ShotPlacementView(discord.ui.View):
    """Interactive view for shot placement selection"""

    def __init__(self, player, keeper, adjusted_stats, shot_placement_config, timeout=15):
        super().__init__(timeout=timeout)
        self.chosen_placement = None
        self.player = player
        self.keeper = keeper
        self.adjusted_stats = adjusted_stats
        self.config = shot_placement_config

        # Add all 5 placement buttons
        for placement_key in ['left_corner', 'right_corner', 'top_center', 'low_center', 'power_shot']:
            button = ShotPlacementButton(placement_key, shot_placement_config[placement_key])
            self.add_item(button)

    async def on_timeout(self):
        # Auto-select safest option if timeout
        self.chosen_placement = 'low_center'
        for item in self.children:
            item.disabled = True


class ShotPlacementButton(discord.ui.Button):
    """Individual shot placement button"""

    def __init__(self, placement_key, config):
        super().__init__(
            label=config['name'],
            emoji=config['emoji'],
            style=config['style'],
            custom_id=placement_key
        )
        self.placement_key = placement_key
        self.config = config

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.chosen_placement = self.placement_key
        for item in self.view.children:
            item.disabled = True
        await interaction.edit_original_response(view=self.view)
        self.view.stop()


match_engine = Nonefetchrow("""
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
                away_team = await conn.
