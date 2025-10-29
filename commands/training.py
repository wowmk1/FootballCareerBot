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
import os


# ============================================
# 🎯 REALISTIC TRAINING STAT RELATIONSHIPS
# ============================================

def get_training_stat_relationships():
    """
    Defines which secondary stats improve when training a primary stat.
    Returns percentages for FRACTIONAL accumulation (NO RNG!)
    
    Based on realistic football training:
    - What movements/skills are involved in each type of training?
    - Which attributes naturally develop together?
    - Position-specific training logic
    
    Format: {
        'primary_stat': {
            'secondary_stat': fractional_percentage (0.0-1.0),
        }
    }
    """
    return {
        'shooting': {
            'physical': 0.50,
            'dribbling': 0.30,
            'pace': 0.20,
            'passing': 0.10,
        },
        'pace': {
            'physical': 0.60,
            'dribbling': 0.35,
            'defending': 0.20,
            'passing': 0.10,
        },
        'physical': {
            'pace': 0.45,
            'defending': 0.40,
            'shooting': 0.25,
            'passing': 0.15,
        },
        'dribbling': {
            'pace': 0.40,
            'passing': 0.40,
            'shooting': 0.25,
            'physical': 0.15,
        },
        'passing': {
            'dribbling': 0.45,
            'shooting': 0.30,
            'physical': 0.20,
            'defending': 0.15,
        },
        'defending': {
            'physical': 0.55,
            'pace': 0.35,
            'passing': 0.20,
            'dribbling': 0.10,
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
    
    # Apply position efficiency to total points
    efficiency = position_efficiency.get(selected_stat, 100) / 100.0
    adjusted_points = int(total_points * efficiency)
    adjusted_points = max(1, adjusted_points)  # At least 1 point
    
    # Main focus stat - scale with adjusted points
    # Off-position (50%): 0-1 points
    # Secondary (75%): 1-2 points  
    # Primary (100%): 1-2 points
    # Expert (120%): 2-3 points
    if adjusted_points <= 1:
        primary_min = 0
        primary_max = 1
    elif adjusted_points <= 2:
        primary_min = 1
        primary_max = 2
    else:
        primary_min = max(1, int(adjusted_points * 0.7))
        primary_max = max(2, int(adjusted_points * 1.2))
    
    expected_gains[selected_stat] = (primary_min, primary_max, True)
    
    # Secondary stats get percentage of adjusted points (as fractional)
    if selected_stat in relationships:
        for secondary_stat, percentage in relationships[selected_stat].items():
            secondary_points = adjusted_points * percentage  # Keep as float for fractional
            if secondary_points > 0:
                sec_min = max(0, int(secondary_points * 0.8))
                sec_max = int(secondary_points * 1.2)
                expected_gains[secondary_stat] = (sec_min, sec_max, False)
    
    return expected_gains


# ============================================
# 🎬 GIPHY GIF API - FOOTBALL ONLY!
# ============================================

# Check multiple sources for API key
GIPHY_API_KEY = None
if hasattr(config, 'GIPHY_API_KEY') and config.GIPHY_API_KEY:
    GIPHY_API_KEY = config.GIPHY_API_KEY
    print("✅ Giphy API key loaded from config.py")
elif os.getenv('GIPHY_API_KEY'):
    GIPHY_API_KEY = os.getenv('GIPHY_API_KEY')
    print("✅ Giphy API key loaded from environment variable")
else:
    print("⚠️ No Giphy API key found - using fallback GIFs only")

# ✅ CURATED FOOTBALL GIF URLS - No API needed!
FOOTBALL_GIFS = {
    'intense': [
        'https://media.giphy.com/media/3oKIPqsXYcdjcBcXL2/giphy.gif',
        'https://media.giphy.com/media/l0HlBO7eyXzSZkJri/giphy.gif',
        'https://media.giphy.com/media/xUOwGhOrYP0jP6iAy4/giphy.gif',
    ],
    'skill': [
        'https://media.giphy.com/media/l0HlNQ03J5JxX6lva/giphy.gif',
        'https://media.giphy.com/media/26BRuo6sLetdllPAQ/giphy.gif',
        'https://media.giphy.com/media/3o7TKMt1VVNkHV2PaE/giphy.gif',
    ],
    'cardio': [
        'https://media.giphy.com/media/xT9IgN8YKRhByRBzZm/giphy.gif',
        'https://media.giphy.com/media/l0HlHFRbmaZtBRhXG/giphy.gif',
        'https://media.giphy.com/media/xT9IgN8YKRhByRBzZm/giphy.gif',
    ],
    'defending': [
        'https://media.giphy.com/media/3o7TKwmnDgQb5jemjK/giphy.gif',
        'https://media.giphy.com/media/xT9IgNxKAAT2h7oE1i/giphy.gif',
        'https://media.giphy.com/media/3o7TKwmnDgQb5jemjK/giphy.gif',
    ],
    'shooting': [
        'https://media.giphy.com/media/3o7TKRn9HVJ8Ezn98c/giphy.gif',
        'https://media.giphy.com/media/3o7TKMeCOV3oXSb5bq/giphy.gif',
        'https://media.giphy.com/media/3o7TKRn9HVJ8Ezn98c/giphy.gif',
    ],
    'success': [
        'https://media.giphy.com/media/26BRBKqUiq586bRVm/giphy.gif',
        'https://media.giphy.com/media/5GoVLqeAOo6PK/giphy.gif',
        'https://media.giphy.com/media/g9582DNuQppxC/giphy.gif',
    ],
}

GIPHY_SEARCH_TERMS = {
    'intense': [
        'man utd soccer indoor training',
        'soccer serious',
        'soccer amazing skills',
        'juve soccer strength',
        'professional football soccer gym'
    ],
    'skill': [
        'messi dribbling barcelona',
        'neymar skills psg',
        'ronaldinho soccer',
        'hazard dribbling chelsea',
        'football skill moves'
    ],
    'cardio': [
        'mbappe',
        'running for soccer',
        'soccer running player',
        'ryan giggs',
        'paul scholes'
    ],
    'defending': [
        'van dijk defending',
        'ramos tackle madrid',
        'soccer tackle',
        'chiellini juventus tackle',
        'rudiger'
    ],
    'shooting': [
        'ronaldo free kick',
        'messi goal barcelona',
        'premier league goal',
        'champions league goal',
        'football shooting training'
    ],
    'success': [
        'messi world cup celebration',
        'ronaldo siuu celebration',
        'champions league celebration',
        'football trophy celebration',
        'premier league celebration'
    ]
}

async def fetch_giphy_gif(search_term, limit=5):
    """Fetch a GIF from Giphy API using specific search term"""
    if not GIPHY_API_KEY:
        return None
    
    try:
        url = "https://api.giphy.com/v1/gifs/search"
        params = {
            'api_key': GIPHY_API_KEY,
            'q': search_term,
            'limit': limit,
            'rating': 'g',
            'lang': 'en'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('data'):
                        gif = random.choice(data['data'])
                        return gif['images']['original']['url']
        
        return None
    
    except Exception as e:
        print(f"⚠️ Giphy API error for '{search_term}': {e}")
        return None


async def get_training_gif(stat_trained, success_level='normal'):
    """Get appropriate training GIF"""
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
    
    # Try API first
    if GIPHY_API_KEY and category in GIPHY_SEARCH_TERMS:
        search_term = random.choice(GIPHY_SEARCH_TERMS[category])
        gif_url = await fetch_giphy_gif(search_term, limit=5)
        if gif_url:
            return gif_url
    
    # Fallback to curated list
    return random.choice(FOOTBALL_GIFS[category])


# ============================================
# 📊 FRACTIONAL STAT HELPERS
# ============================================

def create_fractional_progress_bar(fractional_value, length=10):
    """
    Create a visual progress bar showing fractional progress.
    
    Example: 0.73 → ███████▓░░ 73%
    """
    filled = int(fractional_value * length)
    bar = "█" * filled + "░" * (length - filled)
    percentage = int(fractional_value * 100)
    return f"{bar} {percentage}%"


def format_fractional_display(stat_name, fractional_value, stat_emoji):
    """Format a single stat's fractional progress for display"""
    progress_bar = create_fractional_progress_bar(fractional_value, length=10)
    remaining = 1.0 - fractional_value
    
    if fractional_value >= 0.75:
        status = f"🔥 Almost there! {remaining:.2f} more"
    elif fractional_value >= 0.50:
        status = f"⚡ Halfway! {remaining:.2f} more"
    elif fractional_value >= 0.25:
        status = f"💪 Building... {remaining:.2f} more"
    else:
        status = f"📊 {remaining:.2f} more to +1"
    
    return f"{stat_emoji} **{stat_name}**: {progress_bar}\n    └ {status}"


async def apply_training_with_fractional_gains(player, selected_stat, base_total_points, position_efficiency):
    """
    Apply training with GUARANTEED fractional gains for secondary stats.
    No more RNG for secondary stats - just predictable, accumulating progress!
    
    Returns:
        dict: {
            'actual_gains': {stat: gain_amount},
            'fractional_gains': {stat: fractional_amount_added},
            'fractional_conversions': {stat: converted_amount},
            'new_fractional_values': {stat: new_fractional_value},
            'new_overall': int,
            'updated_stats': {stat: new_value}
        }
    """
    
    # Get current fractional values from database
    current_fractionals = {
        'pace': float(player.get('pace_fractional', 0.0)),
        'shooting': float(player.get('shooting_fractional', 0.0)),
        'passing': float(player.get('passing_fractional', 0.0)),
        'dribbling': float(player.get('dribbling_fractional', 0.0)),
        'defending': float(player.get('defending_fractional', 0.0)),
        'physical': float(player.get('physical_fractional', 0.0))
    }
    
    # Apply position efficiency to get adjusted points
    efficiency = position_efficiency[selected_stat] / 100.0
    adjusted_points = int(base_total_points * efficiency)
    adjusted_points = max(1, adjusted_points)
    
    # Randomness (same as original)
    if random.random() < 0.15:
        adjusted_points = max(1, adjusted_points - 1)
    elif random.random() < 0.10:
        adjusted_points += 1
    
    # === PRIMARY STAT: Full points with potential-based success rate ===
    actual_gains = {}
    current = player[selected_stat]
    current_potential = player['potential']
    distance_from_potential = current_potential - current
    
    # Same success rates as original code
    if distance_from_potential <= 0:
        if current < current_potential + 3:
            successful_gains = sum(1 for _ in range(adjusted_points) if random.random() < 0.10)
        else:
            successful_gains = 0
    elif distance_from_potential <= 5:
        successful_gains = sum(1 for _ in range(adjusted_points) if random.random() < 0.30)
    elif distance_from_potential <= 10:
        successful_gains = sum(1 for _ in range(adjusted_points) if random.random() < 0.50)
    else:
        successful_gains = sum(1 for _ in range(adjusted_points) if random.random() < 0.70)
    
    new_value = min(99, current + successful_gains)
    actual_gain = new_value - current
    
    if actual_gain > 0:
        actual_gains[selected_stat] = actual_gain
    
    # === SECONDARY STATS: FRACTIONAL ACCUMULATION (NO RNG!) ===
    relationships = get_training_stat_relationships()
    fractional_gains = {}
    fractional_conversions = {}
    new_fractional_values = current_fractionals.copy()
    
    if selected_stat in relationships:
        for secondary_stat, percentage in relationships[selected_stat].items():
            # Calculate fractional gain (GUARANTEED, no RNG)
            fractional_gain = adjusted_points * percentage
            
            # Add to current fractional value
            new_fractional = current_fractionals[secondary_stat] + fractional_gain
            
            # Check if we can convert to full point
            conversions = 0
            temp_stat_value = player[secondary_stat]  # ✅ Initialize with current value
            while new_fractional >= 1.0 and temp_stat_value < 99:
                new_fractional -= 1.0
                conversions += 1
                temp_stat_value += 1
            
            # Store results
            fractional_gains[secondary_stat] = fractional_gain
            new_fractional_values[secondary_stat] = round(new_fractional, 2)
            
            if conversions > 0:
                fractional_conversions[secondary_stat] = conversions
                # Add to actual gains
                if secondary_stat in actual_gains:
                    actual_gains[secondary_stat] += conversions
                else:
                    actual_gains[secondary_stat] = conversions
    
    # Calculate new overall
    updated_stats = {stat: player[stat] for stat in ['pace', 'shooting', 'passing', 'dribbling', 'defending', 'physical']}
    for stat, gain in actual_gains.items():
        updated_stats[stat] = min(99, player[stat] + gain)
    
    new_overall = sum(updated_stats.values()) // 6
    
    return {
        'actual_gains': actual_gains,
        'fractional_gains': fractional_gains,
        'fractional_conversions': fractional_conversions,
        'new_fractional_values': new_fractional_values,
        'new_overall': new_overall,
        'updated_stats': updated_stats
    }


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
        
        stat_abbrev = {
            'pace': 'PAC', 'shooting': 'SHO', 'passing': 'PAS',
            'dribbling': 'DRI', 'defending': 'DEF', 'physical': 'PHY'
        }
        
        for stat in ['pace', 'shooting', 'passing', 'dribbling', 'defending', 'physical']:
            efficiency = position_efficiency.get(stat, 100)
            
            # Calculate expected gains with base points
            expected_gains = calculate_expected_gains(stat, self.total_points, position_efficiency, player)
            
            # Build label showing actual expected gains
            primary_gain = expected_gains[stat]
            current_val = self.player[stat]
            
            # Show the stat with expected gains
            label = f"{stat.capitalize()} ({current_val}) +{primary_gain[0]}-{primary_gain[1]}"
            
            # Get secondary stats for this
            secondary_stat_names = [s for s in expected_gains.keys() if s != stat]
            secondary_abbrevs = [stat_abbrev[s] for s in secondary_stat_names]
            
            if secondary_abbrevs:
                secondary_display = "/".join(secondary_abbrevs[:3])
                if len(secondary_abbrevs) > 3:
                    secondary_display += "..."
                label += f" → {secondary_display}"
            
            # Efficiency description with CLEAR warnings
            if efficiency >= 120:
                description = "⭐ EXPERT +20% | Perfect for your position!"
            elif efficiency >= 110:
                description = "✓ Primary +10% | Great for your position"
            elif efficiency >= 100:
                description = "○ Primary | Good for your position"
            elif efficiency >= 75:
                description = "△ Secondary -25% | Not ideal"
            else:
                description = "✗ Off-Position -50% | Very reduced gains!"
            
            options.append(
                discord.SelectOption(
                    label=label,
                    description=description,
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
        
        # Show detailed preview
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
        
        # Show position efficiency warning if off-position
        efficiency = self.position_efficiency[self.selected_stat]
        if efficiency < 100:
            if efficiency >= 75:
                embed.description += f"\n\n⚠️ **Secondary Stat (-25%)** - Not your position's specialty"
            else:
                embed.description += f"\n\n❌ **Off-Position (-50%)** - Training outside your role gives reduced gains!"
        elif efficiency > 100:
            if efficiency >= 120:
                embed.description += f"\n\n⭐ **Expert (+20%)** - Perfect for your position!"
            else:
                embed.description += f"\n\n✓ **Primary Stat (+10%)** - Good for your position"
        
        # Main training focus
        primary = expected_gains[self.selected_stat]
        embed.add_field(
            name=f"🎯 MAIN FOCUS: {self.selected_stat.capitalize()}",
            value=f"Expected: **+{primary[0]}-{primary[1]} points**\n"
                  f"Current: {self.player[self.selected_stat]} → ~{self.player[self.selected_stat] + primary[1]}",
            inline=False
        )
        
        # Secondary stats (FRACTIONAL)
        secondary_stats = [(s, g) for s, g in expected_gains.items() if s != self.selected_stat]
        if secondary_stats:
            secondary_text = "**These stats improve automatically (fractional progress):**\n\n"
            for sec_stat, (min_g, max_g, _) in secondary_stats:
                if max_g > 0:
                    current = self.player[sec_stat]
                    # Show fractional amounts
                    secondary_text += f"💡 **{sec_stat.capitalize()}**: +{min_g:.1f}-{max_g:.1f} fractional\n"
                    secondary_text += f"    └ Accumulates toward +1 full point!\n"
            
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
        
        embed.set_footer(text="✅ Fractional stats accumulate - guaranteed progress every session! | Starting in 5 seconds...")
        
        await interaction.response.edit_message(embed=embed, view=None)
        await asyncio.sleep(5)
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
        """Realistic training with fractional multi-stat improvements"""

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

        base_total_points = int((base_points + streak_bonus) * age_multiplier * morale_multiplier * league_modifier)
        base_total_points = max(1, base_total_points)

        # Show selection screen
        embed = discord.Embed(
            title=f"💪 {player['player_name']} - Training Session",
            description=f"**{player['position']}** • Age {player['age']} • **{player['overall_rating']}** OVR → ⭐ **{player['potential']}** POT\n\n"
                       f"✨ **NEW:** Fractional stats - guaranteed progress on secondary attributes!",
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
                  "**Your position affects how effective training is:**\n"
                  f"• {player['position']} training their EXPERT stats: +20% gains\n"
                  f"• Training PRIMARY stats: Normal/+10% gains\n"
                  f"• Training off-position stats: -25% to -50% gains\n\n"
                  "**NEW: Fractional Progress**\n"
                  "Secondary stats now accumulate fractional progress (0.1, 0.5, etc)\n"
                  "When fractional reaches 1.0 → converts to +1 full stat point!",
            inline=False
        )
        
        # ADD DETAILED BREAKDOWN OF WHAT EACH STAT IMPROVES
        stat_relationships = get_training_stat_relationships()
        relationships_guide = "**📋 What Each Stat Improves:**\n\n"
        relationships_guide += "⚡ **Pace** → Physical, Dribbling, Defending, Passing\n"
        relationships_guide += "🎯 **Shooting** → Physical, Dribbling, Pace, Passing\n"
        relationships_guide += "🎨 **Passing** → Dribbling, Shooting, Physical, Defending\n"
        relationships_guide += "⚽ **Dribbling** → Pace, Passing, Shooting, Physical\n"
        relationships_guide += "🛡️ **Defending** → Physical, Pace, Passing, Dribbling\n"
        relationships_guide += "💪 **Physical** → Pace, Defending, Shooting, Passing"
        
        embed.add_field(
            name="✨ Multi-Stat Training Guide",
            value=relationships_guide,
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

        # === APPLY TRAINING WITH FRACTIONAL SYSTEM ===
        selected_stat = view.selected_stat
        
        result = await apply_training_with_fractional_gains(
            player=player,
            selected_stat=selected_stat,
            base_total_points=base_total_points,
            position_efficiency=position_efficiency
        )
        
        actual_gains = result['actual_gains']
        fractional_gains = result['fractional_gains']
        fractional_conversions = result['fractional_conversions']
        new_fractional_values = result['new_fractional_values']
        new_overall = result['new_overall']
        updated_stats = result['updated_stats']

        # Check for 30-day streak milestone
        potential_boost = 0
        current_potential = player['potential']
        if new_streak == 30 and player['training_streak'] < 30:
            potential_boost = 3
            current_potential += potential_boost

        # === UPDATE DATABASE ===
        async with db.pool.acquire() as conn:
            # Build dynamic update query
            update_parts = []
            update_values = []
            param_count = 1
            
            # Update actual stats
            for stat, new_val in updated_stats.items():
                if new_val != player[stat]:
                    update_parts.append(f"{stat} = ${param_count}")
                    update_values.append(new_val)
                    param_count += 1
            
            # Update fractional values
            for stat, frac_val in new_fractional_values.items():
                update_parts.append(f"{stat}_fractional = ${param_count}")
                update_values.append(frac_val)
                param_count += 1
            
            # Update overall, streak, last_training
            update_parts.append(f"overall_rating = ${param_count}")
            update_values.append(new_overall)
            param_count += 1
            
            update_parts.append(f"training_streak = ${param_count}")
            update_values.append(new_streak)
            param_count += 1
            
            update_parts.append(f"last_training = ${param_count}")
            update_values.append(datetime.now().isoformat())
            param_count += 1
            
            if potential_boost > 0:
                update_parts.append(f"potential = ${param_count}")
                update_values.append(current_potential)
                param_count += 1
            
            # Add user_id for WHERE clause
            update_values.append(player['user_id'])
            
            # Execute update
            set_clause = ", ".join(update_parts)
            await conn.execute(
                f"UPDATE players SET {set_clause} WHERE user_id = ${param_count}",
                *update_values
            )

            await conn.execute('''
                INSERT INTO training_history (user_id, stat_gains, streak_bonus, overall_before, overall_after)
                VALUES ($1, $2, $3, $4, $5)
            ''', interaction.user.id, str(actual_gains), new_streak >= 7, player['overall_rating'], new_overall)

        from utils.form_morale_system import update_player_morale
        await update_player_morale(interaction.user.id, 'training')

        from utils.traits_system import check_trait_unlocks
        newly_unlocked_traits = await check_trait_unlocks(interaction.user.id, self.bot)

        # === RESULTS SCREEN WITH FRACTIONAL PROGRESS ===
        success_level = 'success' if sum(actual_gains.values()) >= 3 or new_overall > player['overall_rating'] else 'normal'
        result_gif = await get_training_gif(selected_stat, success_level)

        if not actual_gains:
            title = "💪 Training Complete!"
            description = "Hard work and dedication!\n⚠️ **Tough session today! Gains reduced.**\n\n*But fractional progress was still added!*"
            color = discord.Color.orange()
        elif sum(actual_gains.values()) >= 4:
            title = "💪 Training Complete!"
            description = "Hard work and dedication!"
            color = discord.Color.gold()
        else:
            title = "💪 Training Complete!"
            description = "Hard work and dedication!"
            color = discord.Color.green()
        
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_image(url=result_gif)

        # Progress to next OVR
        if new_overall < 99:
            next_ovr = new_overall + 1
            total_stats = sum(updated_stats.values())
            needed_for_next = (next_ovr * 6) - total_stats
            progress = max(0, min(100, ((6 - needed_for_next) / 6) * 100))
            
            progress_bar_length = 20
            filled = int(progress / 100 * progress_bar_length)
            progress_bar = "█" * filled + "░" * (progress_bar_length - filled)
            
            embed.add_field(
                name=f"📊 Progress to {next_ovr} OVR",
                value=f"{progress_bar} **{int(progress)}%**",
                inline=False
            )

        # Stat gains
        if actual_gains:
            gains_text = ""
            for stat, gain in actual_gains.items():
                is_primary = stat == selected_stat
                emoji = "⭐" if is_primary else "💡"
                new_val = updated_stats[stat]
                old_val = player[stat]
                
                milestone = ""
                if new_val >= 90 and old_val < 90:
                    milestone = " 🔥 **WORLD CLASS!**"
                elif new_val >= 80 and old_val < 80:
                    milestone = " ⚡ **ELITE!**"
                elif new_val >= 70 and old_val < 70:
                    milestone = " ✨ **PROFESSIONAL!**"
                
                # Show if this came from fractional conversion
                if stat in fractional_conversions:
                    gains_text += f"{emoji} **+{gain} {stat.capitalize()}** (fractional converted!)★{milestone}\n"
                else:
                    gains_text += f"{emoji} **+{gain} {stat.capitalize()}**{milestone}\n"
            
            past_potential = any(updated_stats[stat] >= player['potential'] for stat in actual_gains.keys())
            if past_potential:
                gains_text += "\n✨ **Pushing beyond limits!**"
        else:
            gains_text = "⚠️ No full stat gains - but fractional progress added below!"

        embed.add_field(name="📈 Stat Gains", value=gains_text, inline=False)

        # === NEW: FRACTIONAL PROGRESS SECTION ===
        stat_emojis = {
            'pace': '⚡', 'shooting': '🎯', 'passing': '🎨',
            'dribbling': '⚽', 'defending': '🛡️', 'physical': '💪'
        }
        
        fractional_display = "**Secondary Stats Building Up:**\n\n"
        has_fractional = False
        
        for stat in ['pace', 'shooting', 'passing', 'dribbling', 'defending', 'physical']:
            if stat == selected_stat:
                continue  # Skip primary stat
            
            frac_val = new_fractional_values[stat]
            
            if frac_val > 0.01:  # Only show if there's progress
                has_fractional = True
                fractional_display += format_fractional_display(
                    stat.capitalize(),
                    frac_val,
                    stat_emojis[stat]
                ) + "\n\n"
        
        if has_fractional:
            embed.add_field(
                name="📊 Fractional Progress (Next +1 Points)",
                value=fractional_display.strip(),
                inline=False
            )
        
        # Show which stats got fractional gains THIS session
        if fractional_gains:
            this_session_text = "**Added this session:**\n"
            for stat, gain_amount in fractional_gains.items():
                this_session_text += f"{stat_emojis[stat]} {stat.capitalize()}: +{gain_amount:.2f}\n"
            
            embed.add_field(
                name="✨ Fractional Gains (This Session)",
                value=this_session_text,
                inline=False
            )

        # Progress to 30-day streak
        if new_streak < 30:
            streak_progress = new_streak / 30
            progress_bar_filled = int(streak_progress * 20)
            streak_progress_bar = "█" * progress_bar_filled + "░" * (20 - progress_bar_filled)
            embed.add_field(
                name="🎯 Progress to 30-Day Streak",
                value=f"{streak_progress_bar} **{new_streak}/30 days**\nUnlock: **+3 Potential** permanently!",
                inline=False
            )

        if potential_boost > 0:
            embed.add_field(
                name="🌟 30-DAY MILESTONE REACHED!",
                value=f"**+{potential_boost} POTENTIAL!** New max: {current_potential}",
                inline=False
            )

        # Trait unlocks
        if newly_unlocked_traits:
            traits_text = ""
            for trait_id, trait_data in newly_unlocked_traits:
                traits_text += f"{trait_data['emoji']} **{trait_data['name']}** unlocked!\n"
            embed.add_field(name="🎯 NEW TRAITS UNLOCKED!", value=traits_text, inline=False)

        # League comparison
        async with db.pool.acquire() as conn:
            league_avg = await conn.fetchrow("""
                SELECT AVG(overall_rating) as avg_rating
                FROM players
                WHERE league = $1 AND retired = FALSE
            """, player.get('league', 'Championship'))
            
            if league_avg and league_avg['avg_rating']:
                avg = float(league_avg['avg_rating'])
                diff = new_overall - avg
                comparison = "above" if diff >= 0 else "below"
                
                embed.add_field(
                    name="📊 League Comparison",
                    value=f"**You:** {new_overall} | **League Avg:** {avg:.1f}\nYou are **{abs(diff):.1f} OVR {comparison}** average",
                    inline=False
                )

        # Two-column layout
        left_col = ""
        right_col = ""

        # Left: Streak & Morale
        left_col += f"🔥 **Streak**\n{new_streak} days\n\n"
        
        if morale_multiplier != 1.0:
            emoji = "😊" if morale_multiplier > 1.0 else "😕"
            bonus_text = f"+{int((morale_multiplier - 1.0) * 100)}%" if morale_multiplier > 1.0 else f"{int((morale_multiplier - 1.0) * 100)}%"
            left_col += f"{emoji} **Morale Bonus**\n{morale_desc}\n**{bonus_text}** training gains!"

        # Right: Potential Progress
        distance = current_potential - new_overall
        if distance > 0:
            right_col += f"🎯 **Potential Progress**\n**{distance} OVR** from potential ({current_potential})\n"
            right_col += f"Estimated: ~{distance * 3} sessions\n\n"
        else:
            over_by = new_overall - player['potential']
            right_col += f"🚀 **Beyond Potential!**\n**+{over_by} OVR** above base!\n\n"

        # Career & Next Session
        years_left = config.RETIREMENT_AGE - player['age']
        right_col += f"⏳ **Career Time**\n{years_left} years left | Age {player['age']}\n\n"
        right_col += f"⏰ **Next Session**\n{config.TRAINING_COOLDOWN_HOURS}h"

        if left_col:
            embed.add_field(name="\u200b", value=left_col, inline=True)
        if right_col:
            embed.add_field(name="\u200b", value=right_col, inline=True)

        # Footer
        league_name = player.get('league', 'Championship')
        efficiency = position_efficiency[selected_stat] / 100.0
        embed.set_footer(text=f"Age: {age_multiplier:.1f}x | Morale: {morale_multiplier:.1f}x | {league_name}: {league_modifier}x | Position: {efficiency:.1f}x")

        await interaction.edit_original_response(embed=embed, view=None)


async def setup(bot):
    await bot.add_cog(TrainingCommands(bot))
