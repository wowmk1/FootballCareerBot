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
    
    # Secondary stats get percentage of adjusted points
    if selected_stat in relationships:
        for secondary_stat, percentage in relationships[selected_stat].items():
            secondary_points = int(adjusted_points * percentage)
            if secondary_points > 0:
                sec_min = max(0, secondary_points - 1)
                sec_max = secondary_points + 1
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
# Each category has multiple verified working GIFs
FOOTBALL_GIFS = {
    'intense': [
        'https://media.giphy.com/media/3oKIPqsXYcdjcBcXL2/giphy.gif',  # Ronaldo gym
        'https://media.giphy.com/media/l0HlBO7eyXzSZkJri/giphy.gif',  # Training drill
        'https://media.giphy.com/media/xUOwGhOrYP0jP6iAy4/giphy.gif',  # Weights
    ],
    'skill': [
        'https://media.giphy.com/media/l0HlNQ03J5JxX6lva/giphy.gif',  # Messi dribble
        'https://media.giphy.com/media/26BRuo6sLetdllPAQ/giphy.gif',  # Ball control
        'https://media.giphy.com/media/3o7TKMt1VVNkHV2PaE/giphy.gif',  # Skill move
    ],
    'cardio': [
        'https://media.giphy.com/media/xT9IgN8YKRhByRBzZm/giphy.gif',  # Running
        'https://media.giphy.com/media/l0HlHFRbmaZtBRhXG/giphy.gif',  # Sprint drill
        'https://media.giphy.com/media/xT9IgN8YKRhByRBzZm/giphy.gif',  # Cardio
    ],
    'defending': [
        'https://media.giphy.com/media/3o7TKwmnDgQb5jemjK/giphy.gif',  # Tackle
        'https://media.giphy.com/media/xT9IgNxKAAT2h7oE1i/giphy.gif',  # Defense
        'https://media.giphy.com/media/3o7TKwmnDgQb5jemjK/giphy.gif',  # Block
    ],
    'shooting': [
        'https://media.giphy.com/media/3o7TKRn9HVJ8Ezn98c/giphy.gif',  # Goal
        'https://media.giphy.com/media/3o7TKMeCOV3oXSb5bq/giphy.gif',  # Shot
        'https://media.giphy.com/media/3o7TKRn9HVJ8Ezn98c/giphy.gif',  # Strike
    ],
    'success': [
        'https://media.giphy.com/media/26BRBKqUiq586bRVm/giphy.gif',  # Celebration
        'https://media.giphy.com/media/5GoVLqeAOo6PK/giphy.gif',  # Victory
        'https://media.giphy.com/media/g9582DNuQppxC/giphy.gif',  # Win
    ],
}

# ✅ IMPROVED SOCCER-SPECIFIC SEARCH TERMS - Top 5 only per category
# Focused on most reliable terms that return quality football content
GIPHY_SEARCH_TERMS = {
    'intense': [
        'cristiano ronaldo gym training',
        'premier league training session',
        'football fitness workout',
        'soccer strength training',
        'professional football gym'
    ],
    'skill': [
        'messi dribbling barcelona',
        'neymar skills psg',
        'ronaldinho football tricks',
        'hazard dribbling chelsea',
        'football skill moves'
    ],
    'cardio': [
        'mbappe running speed',
        'football sprint training',
        'soccer speed drill',
        'rashford sprint drill',
        'football cardio workout'
    ],
    'defending': [
        'van dijk defending',
        'ramos tackle madrid',
        'football defensive drill',
        'chiellini juventus tackle',
        'soccer defending training'
    ],
    'shooting': [
        'manchester real ronaldo free kick goal',
        'messi goal barcelona',
        'premier league player goal',
        'champions league goal',
        'football shooting training'
    ],
    'success': [
        'messi world cup celebration',
        'ronaldo siuu celebration',
        'champions league celebration',
        'football trophy celebration',
        'premier league champions'
    ]
}

async def fetch_giphy_gif(search_term, limit=5):
    """
    Fetch a GIF from Giphy API using specific search term.
    Limit set to 5 to get only top quality results.
    
    Args:
        search_term: Specific search query (e.g., "messi dribbling")
        limit: Number of results to fetch (default 5 for top picks only)
    
    Returns:
        GIF URL string or None if failed
    """
    if not GIPHY_API_KEY:
        return None
    
    try:
        url = "https://api.giphy.com/v1/gifs/search"
        params = {
            'api_key': GIPHY_API_KEY,
            'q': search_term,
            'limit': limit,  # Only get top 5 picks
            'rating': 'g',
            'lang': 'en'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('data'):
                        # Pick random from top 5 results
                        gif = random.choice(data['data'])
                        return gif['images']['original']['url']
        
        return None
    
    except Exception as e:
        print(f"⚠️ Giphy API error for '{search_term}': {e}")
        return None


async def get_training_gif(stat_trained, success_level='normal'):
    """
    Get appropriate training GIF - tries API first with improved terms, 
    falls back to curated list if API fails.
    Only uses top 5 results from Giphy to avoid random gifs.
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
    
    # Try API first with improved search terms (top 5 only)
    if GIPHY_API_KEY and category in GIPHY_SEARCH_TERMS:
        search_term = random.choice(GIPHY_SEARCH_TERMS[category])
        gif_url = await fetch_giphy_gif(search_term, limit=5)
        if gif_url:
            return gif_url
    
    # Fallback to curated list
    return random.choice(FOOTBALL_GIFS[category])



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
            
            # Calculate expected gains (now position-adjusted!)
            expected_gains = calculate_expected_gains(stat, total_points, position_efficiency, player)
            
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
        
        # Secondary stats
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
                  "**Your position affects how effective training is:**\n"
                  f"• {player['position']} training their EXPERT stats: +20% gains\n"
                  f"• Training PRIMARY stats: Normal/+10% gains\n"
                  f"• Training off-position stats: -25% to -50% gains\n\n"
                  "**Example:** Strikers get +20% when training Shooting, but Defenders get -50%",
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
        current_potential = player['potential']  # Initialize here
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

        # Check for 30-day streak milestone
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

        # === RESULTS SCREEN - MATCH ORIGINAL DESIGN ===
        success_level = 'success' if sum(actual_gains.values()) >= 3 or new_overall > player['overall_rating'] else 'normal'
        result_gif = await get_training_gif(selected_stat, success_level)

        if not actual_gains:
            title = "💪 Training Complete!"
            description = "Hard work and dedication!\n⚠️ **Tough session today! Gains reduced.**"
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
                
                gains_text += f"{emoji} **+{gain} {stat.capitalize()}**{milestone}\n"
            
            past_potential = any(updated_stats[stat] >= player['potential'] for stat in actual_gains.keys())
            if past_potential:
                gains_text += "\n✨ **Pushing beyond limits!**"
        else:
            gains_text = "⚠️ No gains this session - keep training!"

        embed.add_field(name="📈 Stat Gains", value=gains_text, inline=False)

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
        embed.set_footer(text=f"Age: {age_multiplier:.1f}x | Morale: {morale_multiplier:.1f}x | {league_name}: {league_modifier}x | Position: {efficiency:.1f}x")

        await interaction.edit_original_response(embed=embed, view=None)


# ============================================
# 🧪 SANDBOX TEST FUNCTION
# ============================================
async def test_training_sandbox(interaction: discord.Interaction):
    """Sandbox test - shows all screens without DB changes"""
    import random
    
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
        'potential': 85,
        'morale': 75,
        'training_streak': 5,
        'retired': False,
        'injury_weeks': 0,
        'last_training': None
    }
    
    age_multiplier = 1.0
    morale_multiplier = 1.1
    league_modifier = 1.2
    position_efficiency = get_position_efficiency(fake_player['position'])
    
    base_total_points = int((1 + 0) * age_multiplier * morale_multiplier * league_modifier)
    base_total_points = max(1, base_total_points)
    
    embed = discord.Embed(
        title=f"🧪 SANDBOX TEST: {fake_player['player_name']}",
        description=f"**{fake_player['position']}** • Age {fake_player['age']} • **{fake_player['overall_rating']}** OVR → ⭐ **{fake_player['potential']}** POT\n\n"
                   f"✨ **Testing:** Multi-stat training (no database changes)",
        color=discord.Color.purple()
    )
    
    training_prep_gif = await get_training_gif('physical', 'normal')
    embed.set_image(url=training_prep_gif)
    
    stats_text = (
        f"⚡ Pace: {fake_player['pace']}\n🎯 Shooting: {fake_player['shooting']}\n"
        f"🎨 Passing: {fake_player['passing']}\n⚽ Dribbling: {fake_player['dribbling']}\n"
        f"🛡️ Defending: {fake_player['defending']}\n💪 Physical: {fake_player['physical']}"
    )
    embed.add_field(name="📊 Current Attributes", value=stats_text, inline=True)
    
    modifiers_text = (
        f"😊 Morale: {morale_multiplier:.1f}x\n👤 Age: {age_multiplier:.1f}x\n"
        f"🏟️ Facilities: {league_modifier}x\n🔥 Streak: {fake_player['training_streak']} days"
    )
    embed.add_field(name="⚙️ Modifiers", value=modifiers_text, inline=True)
    
    embed.add_field(
        name="🧪 Sandbox Mode",
        value="TEST - no database changes!\nYou'll see: selection → preview → results\n\n"
              f"**Your Position: {fake_player['position']}**\n"
              f"• Expert stats get +20% gains\n"
              f"• Primary stats get normal/+10% gains\n"
              f"• Off-position stats get -25% to -50% gains",
        inline=False
    )
    
    # ADD SAME RELATIONSHIP GUIDE AS REAL TRAINING
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
    
    embed.set_footer(text="🧪 TESTING | Select a stat")
    
    view = StatTrainingView(fake_player, position_efficiency, base_total_points)
    await interaction.followup.send(embed=embed, view=view)
    
    await view.wait()
    
    if not view.selected_stat:
        await interaction.followup.send("⏰ Test timed out!", ephemeral=True)
        return
    
    selected_stat = view.selected_stat
    efficiency = position_efficiency[selected_stat] / 100.0
    total_points = int(base_total_points * efficiency)
    total_points = max(1, total_points)
    
    relationships = get_training_stat_relationships()
    actual_gains = {}
    
    # Calculate primary gain based on total_points (respects position efficiency)
    # Off-position (1 point): 0-1 gain
    # Secondary (1-2 points): 1-2 gain
    # Primary (2 points): 1-2 gain
    # Expert (3 points): 2-3 gain
    if total_points <= 1:
        primary_gain = random.randint(0, 1)
    elif total_points == 2:
        primary_gain = random.randint(1, 2)
    else:
        primary_gain = random.randint(max(1, total_points - 1), min(3, total_points + 1))
    
    if primary_gain > 0:
        actual_gains[selected_stat] = primary_gain
    
    # Secondary stats (also scaled by position-adjusted total_points)
    if selected_stat in relationships:
        for secondary_stat, percentage in relationships[selected_stat].items():
            secondary_points = int(total_points * percentage)
            if secondary_points > 0 and random.random() < 0.7:
                sec_gain = random.randint(0, min(2, secondary_points))
                if sec_gain > 0:
                    actual_gains[secondary_stat] = sec_gain
    
    updated_stats = {stat: fake_player[stat] for stat in ['pace', 'shooting', 'passing', 'dribbling', 'defending', 'physical']}
    for stat, gain in actual_gains.items():
        updated_stats[stat] = fake_player[stat] + gain
    
    new_overall = sum(updated_stats.values()) // 6
    
    # === EXACT REPLICA OF REAL RESULTS SCREEN ===
    success_level = 'success' if sum(actual_gains.values()) >= 3 else 'normal'
    result_gif = await get_training_gif(selected_stat, success_level)
    
    if not actual_gains:
        title = "💪 Training Complete!"
        description = "Hard work and dedication!\n⚠️ **Tough session today! Gains reduced.**"
        color = discord.Color.orange()
    elif sum(actual_gains.values()) >= 4:
        title = "💪 Training Complete!"
        description = "Hard work and dedication!"
        color = discord.Color.gold()
    else:
        title = "💪 Training Complete!"
        description = "Hard work and dedication!"
        color = discord.Color.green()
    
    # Add sandbox indicator to title only
    embed = discord.Embed(
        title=f"{title} [🧪 SANDBOX TEST]",
        description=description,
        color=color
    )
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

    # Stat gains (EXACT SAME FORMAT)
    if actual_gains:
        gains_text = ""
        for stat, gain in actual_gains.items():
            is_primary = stat == selected_stat
            emoji = "⭐" if is_primary else "💡"
            new_val = updated_stats[stat]
            old_val = fake_player[stat]
            
            milestone = ""
            if new_val >= 90 and old_val < 90:
                milestone = " 🔥 **WORLD CLASS!**"
            elif new_val >= 80 and old_val < 80:
                milestone = " ⚡ **ELITE!**"
            elif new_val >= 70 and old_val < 70:
                milestone = " ✨ **PROFESSIONAL!**"
            
            gains_text += f"{emoji} **+{gain} {stat.capitalize()}**{milestone}\n"
        
        past_potential = any(updated_stats[stat] >= fake_player['potential'] for stat in actual_gains.keys())
        if past_potential:
            gains_text += "\n✨ **Pushing beyond limits!**"
    else:
        gains_text = "⚠️ No gains this session - keep training!"

    embed.add_field(name="📈 Stat Gains", value=gains_text, inline=False)

    # Progress to 30-day streak
    new_streak = fake_player['training_streak'] + 1
    if new_streak < 30:
        streak_progress = new_streak / 30
        progress_bar_filled = int(streak_progress * 20)
        streak_progress_bar = "█" * progress_bar_filled + "░" * (20 - progress_bar_filled)
        embed.add_field(
            name="🎯 Progress to 30-Day Streak",
            value=f"{streak_progress_bar} **{new_streak}/30 days**\nUnlock: **+3 Potential** permanently!",
            inline=False
        )

    # Simulated league comparison
    league_avg = 71.7  # Fake average
    diff = new_overall - league_avg
    comparison = "above" if diff >= 0 else "below"
    
    embed.add_field(
        name="📊 League Comparison",
        value=f"**You:** {new_overall} | **League Avg:** {league_avg:.1f}\nYou are **{abs(diff):.1f} OVR {comparison}** average",
        inline=False
    )

    # Two-column layout (EXACT SAME)
    left_col = ""
    right_col = ""

    # Left: Streak & Morale
    morale_multiplier = 1.1
    morale_desc = "Delighted"
    
    left_col += f"🔥 **Streak**\n{new_streak} days\n\n"
    left_col += f"😊 **Morale Bonus**\n{morale_desc}\n**+30%** training gains!"

    # Right: Potential Progress
    distance = fake_player['potential'] - new_overall
    if distance > 0:
        right_col += f"🎯 **Potential Progress**\n**{distance} OVR** from potential ({fake_player['potential']})\n"
        right_col += f"Estimated: ~{distance * 3} sessions\n\n"
    else:
        over_by = new_overall - fake_player['potential']
        right_col += f"🚀 **Beyond Potential!**\n**+{over_by} OVR** above base!\n\n"

    # Career & Next Session
    years_left = config.RETIREMENT_AGE - fake_player['age']
    right_col += f"⏳ **Career Time**\n{years_left} years left | Age {fake_player['age']}\n\n"
    right_col += f"⏰ **Next Session**\n{config.TRAINING_COOLDOWN_HOURS}h"

    if left_col:
        embed.add_field(name="\u200b", value=left_col, inline=True)
    if right_col:
        embed.add_field(name="\u200b", value=right_col, inline=True)

    # Footer (EXACT SAME)
    age_multiplier = 1.0
    league_modifier = 1.2
    embed.set_footer(text=f"🧪 SANDBOX TEST | Age: {age_multiplier:.1f}x | Morale: {morale_multiplier:.1f}x | {fake_player['league']}: {league_modifier}x | Position: {efficiency:.1f}x")
    
    await interaction.edit_original_response(embed=embed, view=None)


async def setup(bot):
    await bot.add_cog(TrainingCommands(bot))
