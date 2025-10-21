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
# 🎬 TENOR GIF API (keeping from previous version)
# ============================================

TENOR_API_KEY = config.TENOR_API_KEY if hasattr(config, 'TENOR_API_KEY') else None

FALLBACK_GIFS = {
    'intense': ['https://media.giphy.com/media/3o7TKqm1mNujcBPSpy/giphy.gif'],
    'skill': ['https://media.giphy.com/media/l0HlNQ03J5JxX6lva/giphy.gif'],
    'cardio': ['https://media.giphy.com/media/3o6ZsZdNs3yE5l6hWM/giphy.gif'],
    'defending': ['https://media.giphy.com/media/3o7btYXD7vNS0BkVZC/giphy.gif'],
    'shooting': ['https://media.giphy.com/media/3o7TKPATxjC8vBZFUA/giphy.gif'],
    'success': ['https://media.giphy.com/media/g9582DNuQppxC/giphy.gif'],
}

TENOR_SEARCH_TERMS = {
    'intense': ['football training gym', 'soccer workout', 'athlete training hard'],
    'skill': ['football skills training', 'soccer dribbling practice'],
    'cardio': ['football sprint training', 'soccer running drills'],
    'defending': ['football defending training', 'soccer tackle practice'],
    'shooting': ['football shooting practice', 'soccer goal scoring'],
    'success': ['football celebration', 'soccer goal celebration']
}

async def fetch_tenor_gif(search_term, limit=10):
    if not TENOR_API_KEY:
        return None
    try:
        url = f"https://tenor.googleapis.com/v2/search"
        params = {'q': search_term, 'key': TENOR_API_KEY, 'limit': limit, 'media_filter': 'gif'}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('results'):
                        result = random.choice(data['results'])
                        return result['media_formats']['gif']['url']
        return None
    except:
        return None

async def get_training_gif(stat_trained, success_level='normal'):
    if success_level == 'success':
        category = 'success'
    else:
        gif_map = {'pace': 'cardio', 'physical': 'intense', 'shooting': 'shooting',
                   'dribbling': 'skill', 'passing': 'skill', 'defending': 'defending'}
        category = gif_map.get(stat_trained, 'intense')
    
    if TENOR_API_KEY:
        search_term = random.choice(TENOR_SEARCH_TERMS[category])
        gif_url = await fetch_tenor_gif(search_term)
        if gif_url:
            return gif_url
    
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
            description="Here's what you can expect from this training session:",
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
        
        # Secondary stats
        secondary_stats = [(s, g) for s, g in expected_gains.items() if s != self.selected_stat]
        if secondary_stats:
            secondary_text = "These stats also improve during this training:\n\n"
            for sec_stat, (min_g, max_g, _) in secondary_stats:
                if max_g > 0:
                    secondary_text += f"• **{sec_stat.capitalize()}**: +{min_g}-{max_g} points\n"
            
            embed.add_field(
                name="💡 BONUS: Related Stats",
                value=secondary_text,
                inline=False
            )
        
        # Explanation
        relationships_text = {
            'shooting': "Shooting practice includes:\n• Shot power & strength (Physical)\n• Close control in box (Dribbling)\n• Getting into positions (Pace)\n• Striking technique (Passing)",
            'pace': "Speed training includes:\n• Cardio & explosive power (Physical)\n• Ball control at speed (Dribbling)\n• Tracking/recovery runs (Defending)\n• Quick transitions (Passing)",
            'physical': "Strength training improves:\n• Explosive acceleration (Pace)\n• Winning physical battles (Defending)\n• Shot power (Shooting)\n• Long passing power (Passing)",
            'dribbling': "Dribbling drills improve:\n• Quick feet & agility (Pace)\n• Ball control for passing (Passing)\n• Close control for shots (Shooting)\n• Balance & core strength (Physical)",
            'passing': "Passing practice enhances:\n• Receiving & ball control (Dribbling)\n• Striking technique (Shooting)\n• Stamina for quality (Physical)\n• Positioning awareness (Defending)",
            'defending': "Defensive training builds:\n• Tackling strength & stamina (Physical)\n• Tracking & recovery speed (Pace)\n• Playing out from back (Passing)\n• Carrying ball forward (Dribbling)"
        }
        
        if self.selected_stat in relationships_text:
            embed.add_field(
                name="📋 Why These Stats?",
                value=relationships_text[self.selected_stat],
                inline=False
            )
        
        embed.set_footer(text="✅ Training is realistic - related attributes improve naturally!")
        
        await interaction.response.edit_message(embed=embed, view=None)
        await asyncio.sleep(2)  # Let them read it
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

        # [Keep all cooldown checking code from previous version]
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

        embed = discord.Embed(
            title="💪 Training Complete!",
            description=f"Focused on **{selected_stat.capitalize()}** training!",
            color=discord.Color.gold() if actual_gains else discord.Color.orange()
        )
        
        embed.set_image(url=result_gif)

        # Show primary gains
        if selected_stat in actual_gains:
            primary_text = f"⭐ **+{actual_gains[selected_stat]} {selected_stat.capitalize()}** "
            primary_text += f"({player[selected_stat]} → **{updated_stats[selected_stat]}**)\n"
            
            if updated_stats[selected_stat] >= 90 and player[selected_stat] < 90:
                primary_text += "🔥 **WORLD CLASS!**"
            elif updated_stats[selected_stat] >= 80 and player[selected_stat] < 80:
                primary_text += "⚡ **ELITE!**"
            
            embed.add_field(name="🎯 Primary Focus", value=primary_text, inline=False)

        # Show secondary gains
        secondary_gains = {s: g for s, g in actual_gains.items() if s != selected_stat}
        if secondary_gains:
            sec_text = "Related stats improved from training:\n\n"
            for sec_stat, sec_gain in secondary_gains.items():
                sec_text += f"• **+{sec_gain} {sec_stat.capitalize()}** ({player[sec_stat]} → {updated_stats[sec_stat]})\n"
            
            embed.add_field(name="💡 Bonus Improvements", value=sec_text, inline=False)

        if not actual_gains:
            embed.add_field(name="📈 Results", value="No improvements this session. Keep training!", inline=False)

        if new_overall > player['overall_rating']:
            embed.add_field(
                name="⭐ Overall Rating",
                value=f"{player['overall_rating']} → **{new_overall}** (+{new_overall - player['overall_rating']})",
                inline=True
            )

        embed.add_field(name="🔥 Streak", value=f"**{new_streak} days**", inline=True)

        if newly_unlocked_traits:
            traits_text = ""
            for trait_id, trait_data in newly_unlocked_traits:
                traits_text += f"{trait_data['emoji']} **{trait_data['name']}**\n"
            embed.add_field(name="🎯 NEW TRAITS!", value=traits_text, inline=False)

        embed.set_footer(text=f"✨ Total gains: +{sum(actual_gains.values())} across {len(actual_gains)} stats | Realistic training!")

        await interaction.edit_original_response(embed=embed, view=None)


async def setup(bot):
    await bot.add_cog(TrainingCommands(bot))
