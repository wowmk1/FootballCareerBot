import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select
from database import db
import random
from datetime import datetime, timedelta
import config
import asyncio
import aiohttp


# ============================================
# 🎯 REALISTIC TRAINING STAT RELATIONSHIPS
# ============================================

def get_training_stat_relationships():
    """
    Defines which secondary stats improve when training a primary stat.
    
    Based on realistic football training:
    - What movements/skills are involved in each type of training?
    - Which attributes naturally develop together?
    - Position-specific training logic
    
    Format: {
        'primary_stat': {
            'secondary_stat': percentage (0.0-1.0),
        }
    }
    """
    return {
        'shooting': {
            # Shooting practice involves: Running to positions, shot power, close control, technique
            'physical': 0.50,   # Shot power, holding off defenders, stamina from repetitions
            'dribbling': 0.30,  # Close control in box, receiving ball before shooting
            'pace': 0.20,       # Getting into scoring positions quickly
            'passing': 0.10,    # Striking technique transfers (both about hitting the ball)
        },
        'pace': {
            # Sprint training involves: Cardio, explosive movements, agility, sometimes with ball
            'physical': 0.60,   # Cardio conditioning and explosive power (VERY connected!)
            'dribbling': 0.35,  # Speed dribbling, ball control at pace
            'defending': 0.20,  # Tracking runs, recovery speed (especially for defenders)
            'passing': 0.10,    # Quick transitions, passing on the move
        },
        'physical': {
            # Strength/stamina training: Gym work, endurance, physical battles, power
            'pace': 0.45,       # Explosive power improves acceleration/sprint speed
            'defending': 0.40,  # Strength for tackles, winning physical battles
            'shooting': 0.25,   # Shot power from leg/core strength
            'passing': 0.15,    # Long passing power, driven passes
        },
        'dribbling': {
            # Dribbling drills: Close control, agility, ball manipulation, turns
            'pace': 0.40,       # Agility and quick feet improve acceleration
            'passing': 0.40,    # Ball control = better passing technique
            'shooting': 0.25,   # Close control before shooting, dribbling to shoot
            'physical': 0.15,   # Balance and core strength for tight turns
        },
        'passing': {
            # Passing practice: Technique, vision, weight of pass, distribution
            'dribbling': 0.45,  # Receiving and controlling = dribbling improvement
            'shooting': 0.30,   # Both require striking technique (hitting the ball)
            'physical': 0.20,   # Stamina for maintaining quality, power for long passes
            'defending': 0.15,  # Vision and positioning awareness (reading the game)
        },
        'defending': {
            # Defensive training: Tackling, positioning, 1v1s, physical battles
            'physical': 0.55,   # Tackling strength, winning duels, stamina
            'pace': 0.35,       # Tracking runners, recovery speed, jockeying
            'passing': 0.20,    # Playing out from back after winning possession
            'dribbling': 0.10,  # Carrying ball forward after winning it (modern defenders)
        }
    }


def calculate_expected_gains(selected_stat, total_points, position_efficiency, player):
    """
    Calculate expected gains for primary + secondary stats
    
    Returns:
        dict: {stat: (min_gain, max_gain, is_primary)}
    """
    relationships = get_training_stat_relationships()
    expected_gains = {}
    
    # Primary stat gets all points
    primary_min = max(1, int(total_points * 0.7))  # 70% success rate
    primary_max = max(2, int(total_points * 1.2))  # Up to 120% with luck
    expected_gains[selected_stat] = (primary_min, primary_max, True)
    
    # Secondary stats get percentage of points
    if selected_stat in relationships:
        for secondary_stat, percentage in relationships[selected_stat].items():
            # Secondary gains are reduced
            secondary_points = int(total_points * percentage)
            if secondary_points > 0:
                sec_min = max(0, secondary_points - 1)
                sec_max = secondary_points + 1
                expected_gains[secondary_stat] = (sec_min, sec_max, False)
    
    return expected_gains


# ============================================
# 🎬 GIPHY GIF API (Better than Tenor!)
# ============================================

GIPHY_API_KEY = config.GIPHY_API_KEY if hasattr(config, 'GIPHY_API_KEY') else None

FALLBACK_GIFS = {
    'intense': ['https://media.giphy.com/media/3o7TKqm1mNujcBPSpy/giphy.gif'],
    'skill': ['https://media.giphy.com/media/l0HlNQ03J5JxX6lva/giphy.gif'],
    'cardio': ['https://media.giphy.com/media/3o6ZsZdNs3yE5l6hWM/giphy.gif'],
    'defending': ['https://media.giphy.com/media/3o7btYXD7vNS0BkVZC/giphy.gif'],
    'shooting': ['https://media.giphy.com/media/3o7TKPATxjC8vBZFUA/giphy.gif'],
    'success': ['https://media.giphy.com/media/g9582DNuQppxC/giphy.gif'],
}

# ✅ SOCCER-SPECIFIC SEARCH TERMS (Avoids American football & memes!)
# Uses player names, league names, and technical terms for accurate results
GIPHY_SEARCH_TERMS = {
    'intense': [
        'premier league training ground',
        'soccer gym workout professional',
        'champions league fitness training',
        'manchester united training carrington',
        'juventus training session',
        'cristiano ronaldo manchester united gym',
        'paul pogba juventus training',
        'bruno fernandes training'
    ],
    'skill': [
        'messi dribbling skills',
        'neymar skill compilation',
        'ronaldinho magic tricks',
        'marcus rashford skills',
        'antony manchester united tricks',
        'paulo dybala juventus skills',
        'federico chiesa dribbling',
        'del piero magic'
    ],
    'cardio': [
        'soccer sprint training drill',
        'kylian mbappe running',
        'premier league fitness test',
        'manchester united sprint drill',
        'rashford speed training',
        'juventus fitness test',
        'dusan vlahovic running',
        'garnacho sprint'
    ],
    'defending': [
        'virgil van dijk defending',
        'sergio ramos tackle',
        'soccer defensive training drill',
        'lisandro martinez tackle',
        'varane manchester united defending',
        'chiellini juventus defending',
        'bonucci tackle',
        'bremer defending'
    ],
    'shooting': [
        'lionel messi free kick',
        'cristiano ronaldo bicycle kick',
        'premier league striker goal',
        'bruno fernandes goal',
        'rashford free kick',
        'manchester united goal celebration',
        'vlahovic goal juventus',
        'chiesa goal celebration'
    ],
    'success': [
        'messi world cup celebration 2022',
        'ronaldo siuu celebration',
        'champions league trophy celebration',
        'manchester united treble celebration',
        'cristiano ronaldo manchester united celebration',
        'juventus scudetto celebration',
        'del piero celebration',
        'bruno fernandes goal celebration'
    ]
}

async def fetch_giphy_gif(search_term, limit=10):
    """
    Fetch GIF from Giphy API
    
    Args:
        search_term: Search query for Giphy
        limit: Number of results to fetch (will pick random from these)
    
    Returns:
        GIF URL or None if failed
    """
    if not GIPHY_API_KEY:
        return None
    
    try:
        url = "https://api.giphy.com/v1/gifs/search"
        params = {
            'api_key': GIPHY_API_KEY,
            'q': search_term,
            'limit': limit,
            'rating': 'g',  # Family friendly
            'lang': 'en'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('data') and len(data['data']) > 0:
                        # Pick random from results
                        result = random.choice(data['data'])
                        # Return the original GIF URL
                        return result['images']['original']['url']
        
        return None
    
    except Exception as e:
        print(f"Giphy API error: {e}")
        return None


async def get_training_gif(stat_trained, success_level='normal'):
    """
    Get appropriate training GIF based on what was trained
    Uses Giphy API with fallback to static GIFs
    """
    # Determine category
    if success_level == 'success':
        category = 'success'
    else:
        gif_map = {
            'pace': 'cardio',
            'physical': 'intense',
            'shooting': 'shooting',
            'dribbling': 'skill',
            'passing': 'skill',
            'defending': 'defending'
        }
        category = gif_map.get(stat_trained, 'intense')
    
    # Try Giphy API first
    if GIPHY_API_KEY:
        search_term = random.choice(GIPHY_SEARCH_TERMS[category])
        gif_url = await fetch_giphy_gif(search_term)
        
        if gif_url:
            return gif_url
    
    # Fallback to static GIFs
    return random.choice(FALLBACK_GIFS[category])


# ============================================
# 🎯 ENHANCED STAT SELECTION VIEW WITH PREVIEW
# ============================================
class StatTrainingView(View):
    def __init__(self, player, position_efficiency, total_points):
        super().__init__(timeout=60)
        self.player = player
        self.position_efficiency = position_efficiency
        self.selected_stat = None
        self.total_points = total_points
        
        options = []
        stat_emojis = {
            'pace': '⚡', 'shooting': '🎯', 'passing': '🎨',
            'dribbling': '⚽', 'defending': '🛡️', 'physical': '💪'
        }
        
        for stat in ['pace', 'shooting', 'passing', 'dribbling', 'defending', 'physical']:
            efficiency = position_efficiency.get(stat, 100)
            
            # Calculate expected gains for this stat
            expected_gains = calculate_expected_gains(stat, total_points, position_efficiency, player)
            
            # Build preview text
            primary_gain = expected_gains[stat]
            preview = f"+{primary_gain[0]}-{primary_gain[1]} {stat.capitalize()}"
            
            # Add secondary stats preview
            secondary_stats = [s for s in expected_gains.keys() if s != stat]
            if secondary_stats:
                preview += f" (+ {len(secondary_stats)} other stats)"
            
            # Efficiency label
            if efficiency >= 120:
                label_suffix = "⭐ EXPERT +20%"
            elif efficiency >= 110:
                label_suffix = "✓ Primary +10%"
            elif efficiency >= 100:
                label_suffix = "○ Primary"
            elif efficiency >= 75:
                label_suffix = "△ Secondary -25%"
            else:
                label_suffix = "✗ Off-Position -50%"
            
            current_val = self.player[stat]
            
            options.append(
                discord.SelectOption(
                    label=f"{stat.capitalize()} ({current_val}) - {preview}",
                    description=f"{label_suffix}",
                    emoji=stat_emojis[stat],
                    value=stat
                )
            )
        
        select = Select(
            placeholder="🎯 Choose which stat to focus on...",
            options=options,
            custom_id="stat_select"
        )
        select.callback = self.select_callback
        self.add_item(select)
    
    async def select_callback(self, interaction: discord.Interaction):
        self.selected_stat = interaction.data['values'][0]
        
        # Show detailed preview before confirming
        expected_gains = calculate_expected_gains(
            self.selected_stat, 
            self.total_points, 
            self.position_efficiency, 
            self.player
        )
        
        embed = discord.Embed(
            title=f"🎯 Training Focus: {self.selected_stat.capitalize()}",
            description="**Here's what will improve from this session:**",
            color=discord.Color.blue()
        )
        
        # Primary stat
        primary = expected_gains[self.selected_stat]
        embed.add_field(
            name=f"⭐ PRIMARY: {self.selected_stat.capitalize()}",
            value=f"Expected: **+{primary[0]}-{primary[1]} points**\n"
                  f"Current: {self.player[self.selected_stat]} → ~{self.player[self.selected_stat] + primary[1]}",
            inline=False
        )
        
        # Secondary stats - MORE VISIBLE!
        secondary_stats = [(s, g) for s, g in expected_gains.items() if s != self.selected_stat]
        if secondary_stats:
            secondary_text = "**These stats also improve automatically:**\n\n"
            for sec_stat, (min_g, max_g, _) in secondary_stats:
                if max_g > 0:
                    current = self.player[sec_stat]
                    secondary_text += f"💡 **{sec_stat.capitalize()}**: +{min_g}-{max_g} ({current} → ~{current + max_g})\n"
            
            embed.add_field(
                name="✨ BONUS: Related Stats Improve Too!",
                value=secondary_text,
                inline=False
            )
        
        # Explanation
        relationships_text = {
            'shooting': "**Why?** Shooting practice includes:\n• Shot power & strength (Physical)\n• Close control in box (Dribbling)\n• Getting into positions (Pace)\n• Striking technique (Passing)",
            'pace': "**Why?** Speed training includes:\n• Cardio & explosive power (Physical)\n• Ball control at speed (Dribbling)\n• Tracking/recovery runs (Defending)\n• Quick transitions (Passing)",
            'physical': "**Why?** Strength training improves:\n• Explosive acceleration (Pace)\n• Winning physical battles (Defending)\n• Shot power (Shooting)\n• Long passing power (Passing)",
            'dribbling': "**Why?** Dribbling drills improve:\n• Quick feet & agility (Pace)\n• Ball control for passing (Passing)\n• Close control for shots (Shooting)\n• Balance & core strength (Physical)",
            'passing': "**Why?** Passing practice enhances:\n• Receiving & ball control (Dribbling)\n• Striking technique (Shooting)\n• Stamina for quality (Physical)\n• Positioning awareness (Defending)",
            'defending': "**Why?** Defensive training builds:\n• Tackling strength & stamina (Physical)\n• Tracking & recovery speed (Pace)\n• Playing out from back (Passing)\n• Carrying ball forward (Dribbling)"
        }
        
        if self.selected_stat in relationships_text:
            embed.add_field(
                name="📋 Realistic Training Logic",
                value=relationships_text[self.selected_stat],
                inline=False
            )
        
        embed.set_footer(text="✅ Training is realistic - related attributes improve naturally! | Starting in 5 seconds...")
        
        await interaction.response.edit_message(embed=embed, view=None)
        await asyncio.sleep(5)  # Give them time to read! Changed from 2 to 5 seconds
        self.stop()


def get_position_efficiency(position):
    """Returns efficiency multipliers for each stat based on position"""
    efficiency_map = {
        'ST': {'shooting': 120, 'physical': 110, 'pace': 100, 'dribbling': 85, 'passing': 75, 'defending': 50},
        'W': {'pace': 120, 'dribbling': 110, 'shooting': 100, 'passing': 85, 'physical': 75, 'defending': 50},
        'CAM': {'passing': 120, 'dribbling': 110, 'shooting': 100, 'pace': 85, 'physical': 75, 'defending': 60},
        'CM': {'passing': 120, 'physical': 110, 'defending': 100, 'dribbling': 85, 'pace': 80, 'shooting': 70},
        'CDM': {'defending': 120, 'physical': 110, 'passing': 100, 'pace': 80, 'dribbling': 70, 'shooting': 50},
        'FB': {'pace': 120, 'defending': 110, 'physical': 100, 'passing': 85, 'dribbling': 75, 'shooting': 50},
        'CB': {'defending': 120, 'physical': 110, 'passing': 100, 'pace': 75, 'dribbling': 60, 'shooting': 50},
        'GK': {'defending': 120, 'physical': 110, 'passing': 75, 'pace': 60, 'dribbling': 50, 'shooting': 50}
    }
    return efficiency_map.get(position, {stat: 100 for stat in ['pace', 'shooting', 'passing', 'dribbling', 'defending', 'physical']})


# ============================================
# 💪 MAIN TRAINING COMMAND
# ============================================
class TrainingCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="train", description="Train to improve your stats (once per day)")
    async def train(self, interaction: discord.Interaction):
        """Realistic training with multi-stat improvements"""

        await interaction.response.defer()

        player = await db.get_player(interaction.user.id)

        if not player:
            await interaction.followup.send("You haven't created a player yet! Use `/start` to begin.", ephemeral=True)
            return

        if player['retired']:
            await interaction.followup.send("Your player has retired! Use `/start` to create a new player.", ephemeral=True)
            return

        if player['injury_weeks'] and player['injury_weeks'] > 0:
            await interaction.followup.send(f"You're injured! Rest for **{player['injury_weeks']} more weeks** before training.", ephemeral=True)
            return

        # Check cooldown and streak
        streak_broken = False
        if player['last_training']:
            last_train = datetime.fromisoformat(player['last_training'])
            time_diff = datetime.now() - last_train

            if time_diff < timedelta(hours=config.TRAINING_COOLDOWN_HOURS):
                next_train = last_train + timedelta(hours=config.TRAINING_COOLDOWN_HOURS)
                time_until = next_train - datetime.now()
                hours_left = int(time_until.total_seconds() // 3600)
                minutes_left = int((time_until.total_seconds() % 3600) // 60)
                next_train_formatted = next_train.strftime('%I:%M %p')
                today_or_tomorrow = "today" if next_train.date() == datetime.now().date() else "tomorrow"

                embed = discord.Embed(title="⏰ Training on Cooldown", description=f"You trained recently and need rest!", color=discord.Color.orange())
                embed.add_field(name="⏱️ Time Remaining", value=f"**{hours_left}h {minutes_left}m**", inline=True)
                embed.add_field(name="🕐 Next Training", value=f"**{next_train_formatted}** {today_or_tomorrow}", inline=True)
                embed.add_field(name="🔥 Current Streak", value=f"**{player['training_streak']} days**\n*Don't break it!*", inline=False)
                embed.set_footer(text="💡 Train daily to maintain your streak and gain bonus points!")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            if time_diff > timedelta(hours=48):
                streak_broken = True

        # Calculate training modifiers
        age_multiplier = 1.0
        if player['age'] <= 21:
            age_multiplier = 1.0
        elif player['age'] <= 25:
            age_multiplier = 0.9
        elif player['age'] <= 30:
            age_multiplier = 0.65
        elif player['age'] <= 35:
            age_multiplier = 0.55
        else:
            age_multiplier = 0.15

        from utils.form_morale_system import get_morale_training_modifier, get_morale_description
        morale_multiplier = get_morale_training_modifier(player['morale'])
        morale_desc = get_morale_description(player['morale'])

        league_modifier = config.TRAINING_EFFECTIVENESS_BY_LEAGUE.get(player.get('league', 'Championship'), 1.0)
        position_efficiency = get_position_efficiency(player['position'])

        # Calculate base training points
        base_points = 1
        if streak_broken:
            new_streak = 1
        else:
            new_streak = player['training_streak'] + 1

        streak_bonus = 0
        if new_streak >= 7:
            streak_bonus = 0.3
        if new_streak >= 30:
            streak_bonus = 0.7

        # Base total points (before position efficiency)
        base_total_points = int((base_points + streak_bonus) * age_multiplier * morale_multiplier * league_modifier)
        base_total_points = max(1, base_total_points)

        # Show selection screen
        embed = discord.Embed(
            title=f"💪 {player['player_name']} - Training Session",
            description=f"**{player['position']}** • Age {player['age']} • **{player['overall_rating']}** OVR → ⭐ **{player['potential']}** POT\n\n"
                       f"✨ **NEW:** Training now improves multiple related stats realistically!",
            color=discord.Color.blue()
        )
        
        training_prep_gif = await get_training_gif('physical', 'normal')
        embed.set_image(url=training_prep_gif)

        # Current stats
        stats_text = (
            f"⚡ **Pace:** {player['pace']}\n🎯 **Shooting:** {player['shooting']}\n"
            f"🎨 **Passing:** {player['passing']}\n⚽ **Dribbling:** {player['dribbling']}\n"
            f"🛡️ **Defending:** {player['defending']}\n💪 **Physical:** {player['physical']}"
        )
        embed.add_field(name="📊 Current Attributes", value=stats_text, inline=True)

        modifiers_text = (
            f"😊 **Morale:** {morale_multiplier:.1f}x\n👤 **Age:** {age_multiplier:.1f}x\n"
            f"🏟️ **Facilities:** {league_modifier}x\n🔥 **Streak:** {player['training_streak']} days"
        )
        embed.add_field(name="⚙️ Modifiers", value=modifiers_text, inline=True)

        embed.add_field(
            name="💡 How It Works",
            value="Training is realistic! When you focus on one stat, related attributes also improve.\n\n"
                  "**Example:** Training Shooting also improves:\n"
                  "• Physical (shot power/strength)\n"
                  "• Dribbling (close control)\n"
                  "• Pace (positioning)\n"
                  "• Passing (striking technique)\n\n"
                  "**Every stat** has 3-4 related improvements!",
            inline=False
        )

        if streak_broken:
            embed.add_field(name="⚠️ Streak Broken", value="You missed a training day! Starting fresh.", inline=False)

        embed.set_footer(text="Select your primary training focus - secondary stats will improve automatically!")

        view = StatTrainingView(player, position_efficiency, base_total_points)
        await interaction.followup.send(embed=embed, view=view)

        await view.wait()

        if not view.selected_stat:
            await interaction.followup.send("⏰ Training session timed out!", ephemeral=True)
            return

        # Apply training with multi-stat gains
        selected_stat = view.selected_stat
        efficiency = position_efficiency[selected_stat] / 100.0
        total_points = int(base_total_points * efficiency)
        total_points = max(1, total_points)

        # Randomness
        if random.random() < 0.15:
            total_points = max(1, total_points - 1)
        elif random.random() < 0.10:
            total_points += 1

        # Calculate gains for primary + secondary stats
        relationships = get_training_stat_relationships()
        actual_gains = {}

        # Apply primary stat gain
        current = player[selected_stat]
        current_potential = player['potential']
        distance_from_potential = current_potential - current

        if distance_from_potential <= 0:
            if current < current_potential + 3:
                successful_gains = sum(1 for _ in range(total_points) if random.random() < 0.10)
            else:
                successful_gains = 0
        elif distance_from_potential <= 5:
            successful_gains = sum(1 for _ in range(total_points) if random.random() < 0.30)
        elif distance_from_potential <= 10:
            successful_gains = sum(1 for _ in range(total_points) if random.random() < 0.50)
        else:
            successful_gains = sum(1 for _ in range(total_points) if random.random() < 0.70)

        new_value = min(99, current + successful_gains)
        actual_gain = new_value - current
        
        if actual_gain > 0:
            actual_gains[selected_stat] = actual_gain

        # Apply secondary stat gains
        if selected_stat in relationships:
            for secondary_stat, percentage in relationships[selected_stat].items():
                secondary_points = int(total_points * percentage)
                
                if secondary_points > 0:
                    sec_current = player[secondary_stat]
                    sec_distance = current_potential - sec_current
                    
                    # Secondary stats have slightly lower success rates
                    if sec_distance <= 0:
                        sec_gains = sum(1 for _ in range(secondary_points) if random.random() < 0.05)
                    elif sec_distance <= 5:
                        sec_gains = sum(1 for _ in range(secondary_points) if random.random() < 0.20)
                    elif sec_distance <= 10:
                        sec_gains = sum(1 for _ in range(secondary_points) if random.random() < 0.40)
                    else:
                        sec_gains = sum(1 for _ in range(secondary_points) if random.random() < 0.60)
                    
                    sec_new = min(99, sec_current + sec_gains)
                    sec_gain = sec_new - sec_current
                    
                    if sec_gain > 0:
                        actual_gains[secondary_stat] = sec_gain

        # Update all stats and calculate new overall
        updated_stats = {stat: player[stat] for stat in ['pace', 'shooting', 'passing', 'dribbling', 'defending', 'physical']}
        for stat, gain in actual_gains.items():
            updated_stats[stat] = player[stat] + gain

        new_overall = sum(updated_stats.values()) // 6

        # Check for 30-day streak milestone (potential boost)
        potential_boost = 0
        if new_streak == 30 and player['training_streak'] < 30:
            potential_boost = 3
            current_potential += potential_boost

        # Update database
        async with db.pool.acquire() as conn:
            if actual_gains:
                update_parts = []
                update_values = []
                for stat, new_val in updated_stats.items():
                    if new_val != player[stat]:
                        update_parts.append(stat)
                        update_values.append(new_val)
                
                if update_parts:
                    set_clause = ", ".join([f"{part} = ${i + 1}" for i, part in enumerate(update_parts)])
                    set_clause += f", overall_rating = ${len(update_parts) + 1}, training_streak = ${len(update_parts) + 2}, last_training = ${len(update_parts) + 3}"
                    
                    if potential_boost > 0:
                        set_clause += f", potential = ${len(update_parts) + 4}"
                        all_values = update_values + [new_overall, new_streak, datetime.now().isoformat(), current_potential, interaction.user.id]
                        await conn.execute(f"UPDATE players SET {set_clause} WHERE user_id = ${len(update_parts) + 5}", *all_values)
                    else:
                        all_values = update_values + [new_overall, new_streak, datetime.now().isoformat(), interaction.user.id]
                        await conn.execute(f"UPDATE players SET {set_clause} WHERE user_id = ${len(update_parts) + 4}", *all_values)
            else:
                await conn.execute("UPDATE players SET training_streak = $1, last_training = $2 WHERE user_id = $3",
                    new_streak, datetime.now().isoformat(), interaction.user.id)

            await conn.execute('''
                INSERT INTO training_history (user_id, stat_gains, streak_bonus, overall_before, overall_after)
                VALUES ($1, $2, $3, $4, $5)
            ''', interaction.user.id, str(actual_gains), streak_bonus > 0, player['overall_rating'], new_overall)

        from utils.form_morale_system import update_player_morale
        await update_player_morale(interaction.user.id, 'training')

        from utils.traits_system import check_trait_unlocks
        newly_unlocked_traits = await check_trait_unlocks(interaction.user.id, self.bot)

        # Show results
        success_level = 'success' if sum(actual_gains.values()) >= 3 or new_overall > player['overall_rating'] else 'normal'
        result_gif = await get_training_gif(selected_stat, success_level)

        # Determine description based on gains
        if not actual_gains:
            description = "Tough session today! Keep training - gains will come."
        elif sum(actual_gains.values()) >= 4:
            description = "Outstanding session! Hard work and dedication!"
        elif streak_broken:
            description = "Back to training after missing a day!"
        else:
            description = "Hard work and dedication!"
        
        # Add bad day message if applicable
        bad_day_message = ""
        if random.random() < 0.15 and sum(actual_gains.values()) < 3:
            bad_day_message = "\n⚠️ **Tough session today!** Gains reduced."
        
        embed = discord.Embed(
            title="💪 Training Complete!",
            description=description + bad_day_message,
            color=discord.Color.gold() if actual_gains else discord.Color.orange()
        )
        
        embed.set_image(url=result_gif)

        # Progress to next OVR
        if new_overall < 99:
            next_ovr = new_overall + 1
            # Calculate how close to next level
            total_stats = sum(updated_stats.values())
            needed_for_next = (next_ovr * 6) - total_stats
            progress = ((6 - needed_for_next) / 6) * 100 if needed_for_next < 6 else 0
            
            progress_bar_length = 20
            filled = int(progress / 100 * progress_bar_length)
            progress_bar = "█" * filled + "░" * (progress_bar_length - filled)
            
            embed.add_field(
                name=f"📊 Progress to {next_ovr} OVR",
                value=f"{progress_bar} {int(progress)}%",
                inline=False
            )

        # Show ALL stat gains with highlights
        if actual_gains:
            gains_text = ""
            for stat, gain in actual_gains.items():
                is_primary = stat == selected_stat
                emoji = "⭐" if is_primary else "💡"
                
                # Highlight milestone gains
                new_val = updated_stats[stat]
                old_val = player[stat]
                milestone = ""
                if new_val >= 90 and old_val < 90:
                    milestone = " 🔥 **WORLD CLASS!**"
                elif new_val >= 80 and old_val < 80:
                    milestone = " ⚡ **ELITE!**"
                elif new_val >= 70 and old_val < 70:
                    milestone = " ✨ **PROFESSIONAL!**"
                
                if is_primary:
                    gains_text += f"{emoji} **+{gain} {stat.capitalize()}** ({old_val} → {new_val}){milestone}\n"
                else:
                    gains_text += f"{emoji} +{gain} {stat.capitalize()} ({old_val} → {new_val}){milestone}\n"
            
            # Check if past potential
            past_potential = any(updated_stats[stat] >= player['potential'] for stat in actual_gains.keys())
            if past_potential:
                gains_text += "\n✨ **Pushing beyond limits!**"
        else:
            gains_text = "Tough session! Keep working - gains will come."

        embed.add_field(name="📈 Stat Gains", value=gains_text, inline=False)

        # Show trait unlocks if any
        if newly_unlocked_traits:
            traits_text = ""
            for trait_id, trait_data in newly_unlocked_traits:
                traits_text += f"{trait_data['emoji']} **{trait_data['name']}** unlocked!\n"
            
            embed.add_field(
                name="🎯 NEW TRAITS UNLOCKED!",
                value=traits_text,
                inline=False
            )

        # Progress bar to 30-day streak
        if new_streak < 30:
            streak_progress = new_streak / 30
            progress_bar_filled = int(streak_progress * 20)
            streak_progress_bar = "█" * progress_bar_filled + "░" * (20 - progress_bar_filled)
            embed.add_field(
                name="🎯 Progress to 30-Day Streak",
                value=f"{streak_progress_bar} **{new_streak}/30 days**\n"
                      f"Unlock: **+3 Potential** permanently!",
                inline=False
            )

        # 30-day milestone reward
        if potential_boost > 0:
            embed.add_field(
                name="🌟 30-DAY MILESTONE REACHED!",
                value=f"**+{potential_boost} POTENTIAL!** New max: {current_potential}",
                inline=False
            )

        # League comparison
        async with db.pool.acquire() as conn:
            league_avg = await conn.fetchrow("""
                SELECT AVG(overall_rating) as avg_rating
                FROM players
                WHERE league = $1 AND retired = FALSE
            """, player['league'])
            
            if league_avg and league_avg['avg_rating']:
                avg = float(league_avg['avg_rating'])
                diff = new_overall - avg
                comparison = "above" if diff > 0 else "below"
                
                embed.add_field(
                    name="📊 League Comparison",
                    value=f"You: **{new_overall}** | League Avg: **{avg:.1f}**\n"
                          f"You are **{abs(diff):.1f} OVR {comparison}** average",
                    inline=False
                )

        # Overall rating change
        if new_overall > player['overall_rating']:
            embed.add_field(
                name="⭐ Overall Rating",
                value=f"{player['overall_rating']} → **{new_overall}** (+{new_overall - player['overall_rating']})",
                inline=True
            )

        # Streak display
        embed.add_field(
            name="🔥 Streak",
            value=f"**{new_streak} days**",
            inline=True
        )

        # Show morale impact
        if morale_multiplier > 1.0:
            embed.add_field(
                name="😊 Morale Bonus",
                value=f"{morale_desc}\n**+{int((morale_multiplier - 1.0) * 100)}%** training gains!",
                inline=True
            )
        elif morale_multiplier < 1.0:
            embed.add_field(
                name="😕 Morale Penalty",
                value=f"{morale_desc}\n**{int((morale_multiplier - 1.0) * 100)}%** training gains",
                inline=True
            )

        # Potential progress
        distance = current_potential - new_overall
        if distance > 0:
            embed.add_field(
                name="🎯 Potential Progress",
                value=f"**{distance} OVR** from potential ({current_potential})\n"
                      f"Estimated: ~{distance * 3} focused sessions (~{distance * 3} days)",
                inline=False
            )
        else:
            over_by = new_overall - player['potential']
            embed.add_field(
                name="🚀 Beyond Potential!",
                value=f"**+{over_by} OVR** above base potential!",
                inline=False
            )

        # Career time
        years_left = config.RETIREMENT_AGE - player['age']
        embed.add_field(
            name="⏳ Career Time",
            value=f"**{years_left} years** left | Age: {player['age']}",
            inline=True
        )

        # Next session time
        embed.add_field(
            name="⏰ Next Session",
            value=f"**{config.TRAINING_COOLDOWN_HOURS}h**",
            inline=True
        )

        # Footer with all multipliers
        league_name = player.get('league', 'Championship')
        embed.set_footer(text=f"Age: {age_multiplier:.1f}x | Morale: {morale_multiplier:.1f}x | {league_name}: {league_modifier}x | Position: {efficiency:.1f}x")

        await interaction.edit_original_response(embed=embed, view=None)


# ============================================
# 🧪 SANDBOX TEST FUNCTION (NO DB CHANGES!)
# ============================================
async def test_training_sandbox(interaction: discord.Interaction):
    """
    Sandbox test of the training system - shows all screens without DB changes
    """
    import random
    
    # Create fake player data
    fake_player = {
        'user_id': interaction.user.id,
        'player_name': f"{interaction.user.display_name}'s Test Player",
        'overall_rating': 75,
        'pace': 78,
        'shooting': 72,
        'passing': 74,
        'dribbling': 76,
        'defending': 68,
        'physical': 73,
        'team_id': 'test_team',
        'league': 'Premier League',
        'position': 'CM',
        'age': 23,
        'energy': 85,
        'form': 0.80,
        'potential': 85,
        'morale': 75,
        'training_streak': 5,
        'retired': False,
        'injury_weeks': 0,
        'last_training': None
    }
    
    # Calculate sandbox modifiers
    age_multiplier = 1.0
    morale_multiplier = 1.1
    league_modifier = 1.2
    position_efficiency = get_position_efficiency(fake_player['position'])
    
    base_total_points = int((1 + 0) * age_multiplier * morale_multiplier * league_modifier)
    base_total_points = max(1, base_total_points)
    
    # Show initial selection screen
    embed = discord.Embed(
        title=f"🧪 SANDBOX TEST: {fake_player['player_name']}",
        description=f"**{fake_player['position']}** • Age {fake_player['age']} • **{fake_player['overall_rating']}** OVR → ⭐ **{fake_player['potential']}** POT\n\n"
                   f"✨ **Testing:** Multi-stat training system (no database changes)",
        color=discord.Color.purple()
    )
    
    training_prep_gif = await get_training_gif('physical', 'normal')
    embed.set_image(url=training_prep_gif)
    
    # Current stats
    stats_text = (
        f"⚡ **Pace:** {fake_player['pace']}\n🎯 **Shooting:** {fake_player['shooting']}\n"
        f"🎨 **Passing:** {fake_player['passing']}\n⚽ **Dribbling:** {fake_player['dribbling']}\n"
        f"🛡️ **Defending:** {fake_player['defending']}\n💪 **Physical:** {fake_player['physical']}"
    )
    embed.add_field(name="📊 Current Attributes", value=stats_text, inline=True)
    
    modifiers_text = (
        f"😊 **Morale:** {morale_multiplier:.1f}x\n👤 **Age:** {age_multiplier:.1f}x\n"
        f"🏟️ **Facilities:** {league_modifier}x\n🔥 **Streak:** {fake_player['training_streak']} days"
    )
    embed.add_field(name="⚙️ Modifiers", value=modifiers_text, inline=True)
    
    embed.add_field(
        name="🧪 Sandbox Mode",
        value="This is a TEST - no database changes!\n"
              "You'll see all screens: selection → preview → results",
        inline=False
    )
    
    embed.set_footer(text="🧪 TESTING MODE | Select a stat to see preview screen")
    
    view = StatTrainingView(fake_player, position_efficiency, base_total_points)
    await interaction.followup.send(embed=embed, view=view)
    
    await view.wait()
    
    if not view.selected_stat:
        await interaction.followup.send("⏰ Test timed out!", ephemeral=True)
        return
    
    # Simulate training results
    selected_stat = view.selected_stat
    efficiency = position_efficiency[selected_stat] / 100.0
    total_points = int(base_total_points * efficiency)
    total_points = max(1, total_points)
    
    # Calculate gains for primary + secondary stats
    relationships = get_training_stat_relationships()
    actual_gains = {}
    
    # Primary stat gain (simulated)
    primary_gain = random.randint(1, 3)
    actual_gains[selected_stat] = primary_gain
    
    # Secondary stat gains (simulated)
    if selected_stat in relationships:
        for secondary_stat, percentage in relationships[selected_stat].items():
            secondary_points = int(total_points * percentage)
            if secondary_points > 0 and random.random() < 0.7:
                sec_gain = random.randint(0, 2)
                if sec_gain > 0:
                    actual_gains[secondary_stat] = sec_gain
    
    # Update fake stats
    updated_stats = {stat: fake_player[stat] for stat in ['pace', 'shooting', 'passing', 'dribbling', 'defending', 'physical']}
    for stat, gain in actual_gains.items():
        updated_stats[stat] = fake_player[stat] + gain
    
    new_overall = sum(updated_stats.values()) // 6
    
    # Show results (mimicking real training results)
    success_level = 'success' if sum(actual_gains.values()) >= 3 else 'normal'
    result_gif = await get_training_gif(selected_stat, success_level)
    
    description = "🧪 **Sandbox Test Complete!**\n\nThis is how results look in real training!"
    if sum(actual_gains.values()) >= 4:
        description += "\n✨ Outstanding session!"
    
    embed = discord.Embed(
        title="🧪 SANDBOX RESULTS (Not Saved)",
        description=description,
        color=discord.Color.purple()
    )
    
    embed.set_image(url=result_gif)
    
    # Show stat gains
    gains_text = ""
    for stat, gain in actual_gains.items():
        is_primary = stat == selected_stat
        emoji = "⭐" if is_primary else "💡"
        old_val = fake_player[stat]
        new_val = updated_stats[stat]
        
        if is_primary:
            gains_text += f"{emoji} **+{gain} {stat.capitalize()}** ({old_val} → {new_val})\n"
        else:
            gains_text += f"{emoji} +{gain} {stat.capitalize()} ({old_val} → {new_val})\n"
    
    embed.add_field(name="📈 Stat Gains", value=gains_text, inline=False)
    
    # Overall change
    if new_overall > fake_player['overall_rating']:
        embed.add_field(
            name="⭐ Overall Rating",
            value=f"{fake_player['overall_rating']} → **{new_overall}** (+{new_overall - fake_player['overall_rating']})",
            inline=True
        )
    
    embed.add_field(
        name="🔥 Streak",
        value=f"**{fake_player['training_streak']} days**",
        inline=True
    )
    
    embed.add_field(
        name="✅ Test Summary",
        value="• Stat selection screen ✓\n"
              "• Preview with secondary stats ✓\n"
              "• Detailed results screen ✓\n"
              "• All GIFs working ✓\n\n"
              "**No database changes made!**",
        inline=False
    )
    
    embed.set_footer(text="🧪 SANDBOX TEST COMPLETE | Real training uses /train command")
    
    await interaction.edit_original_response(embed=embed, view=None)


async def setup(bot):
    await bot.add_cog(TrainingCommands(bot))
