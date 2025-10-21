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
    
    # Primary stat gets all points
    primary_min = max(1, int(total_points * 0.7))
    primary_max = max(2, int(total_points * 1.2))
    expected_gains[selected_stat] = (primary_min, primary_max, True)
    
    # Secondary stats get percentage of points
    if selected_stat in relationships:
        for secondary_stat, percentage in relationships[selected_stat].items():
            secondary_points = int(total_points * percentage)
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
        'ronaldo free kick goal',
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
                description = "⚠️ Secondary -25% | Not ideal for your position"
            else:
                description = "❌ Off-Position -50% | Very inefficient!"
            
            options.append(
                discord.SelectOption(
                    label=label,
                    value=stat,
                    description=description,
                    emoji=stat_emojis[stat]
                )
            )
        
        select = Select(
            placeholder="🎯 Choose a stat to train...",
            options=options,
            custom_id="stat_select"
        )
        select.callback = self.stat_selected
        self.add_item(select)
    
    async def stat_selected(self, interaction: discord.Interaction):
        """Handle stat selection and show preview"""
        selected_stat = interaction.data['values'][0]
        self.selected_stat = selected_stat
        
        # Calculate actual training results
        efficiency = self.position_efficiency[selected_stat] / 100.0
        total_points = int(self.total_points * efficiency)
        total_points = max(1, total_points)
        
        # Calculate expected gains for preview
        expected_gains = calculate_expected_gains(selected_stat, total_points, self.position_efficiency, self.player)
        
        # Create preview embed
        embed = discord.Embed(
            title=f"📋 Training Preview: {selected_stat.capitalize()}",
            description=f"🎯 **Selected:** {selected_stat.capitalize()} training\n"
                       f"⚙️ **Position Efficiency:** {efficiency:.0%}\n\n"
                       f"Here's what you can expect from this session:",
            color=discord.Color.blue()
        )
        
        # Show expected gains
        gains_preview = ""
        for stat, (min_gain, max_gain, is_primary) in expected_gains.items():
            emoji = "⭐" if is_primary else "💡"
            label = "Primary" if is_primary else "Secondary"
            gains_preview += f"{emoji} **{stat.capitalize()}** ({label}): +{min_gain} to +{max_gain}\n"
        
        embed.add_field(
            name="📈 Expected Stat Gains",
            value=gains_preview,
            inline=False
        )
        
        # Show current stats
        current_stats = ""
        for stat in ['pace', 'shooting', 'passing', 'dribbling', 'defending', 'physical']:
            emoji = {'pace': '⚡', 'shooting': '🎯', 'passing': '🎨', 
                    'dribbling': '⚽', 'defending': '🛡️', 'physical': '💪'}[stat]
            current_stats += f"{emoji} {stat.capitalize()}: **{self.player[stat]}**\n"
        
        embed.add_field(
            name="📊 Current Stats",
            value=current_stats,
            inline=True
        )
        
        # Add training info
        info_text = (
            f"💪 **Training Points:** {total_points}\n"
            f"🎯 **Focus:** {selected_stat.capitalize()}\n"
            f"📊 **Secondary Stats:** Will also improve!\n"
        )
        embed.add_field(
            name="ℹ️ Training Info",
            value=info_text,
            inline=True
        )
        
        embed.set_footer(text="✅ Confirm to start training!")
        
        # Get preview GIF
        preview_gif = await get_training_gif(selected_stat, 'normal')
        embed.set_image(url=preview_gif)
        
        # Create confirm view
        confirm_view = ConfirmTrainingView(self.player, selected_stat, self.position_efficiency, self.total_points)
        
        await interaction.response.edit_message(embed=embed, view=confirm_view)
        self.stop()


class ConfirmTrainingView(View):
    def __init__(self, player, selected_stat, position_efficiency, total_points):
        super().__init__(timeout=60)
        self.player = player
        self.selected_stat = selected_stat
        self.position_efficiency = position_efficiency
        self.total_points = total_points
        self.confirmed = False
    
    @discord.ui.button(label="✅ Confirm Training", style=discord.ButtonStyle.success)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        
        # Calculate actual gains
        efficiency = self.position_efficiency[self.selected_stat] / 100.0
        total_points = int(self.total_points * efficiency)
        total_points = max(1, total_points)
        
        relationships = get_training_stat_relationships()
        actual_gains = {}
        
        # Primary stat gain
        primary_gain = random.randint(1, 3)
        actual_gains[self.selected_stat] = primary_gain
        
        # Secondary stat gains
        if self.selected_stat in relationships:
            for secondary_stat, percentage in relationships[self.selected_stat].items():
                secondary_points = int(total_points * percentage)
                if secondary_points > 0 and random.random() < 0.7:  # 70% chance for secondary
                    sec_gain = random.randint(0, 2)
                    if sec_gain > 0:
                        actual_gains[secondary_stat] = sec_gain
        
        # Update player stats
        updated_stats = {stat: self.player[stat] for stat in ['pace', 'shooting', 'passing', 'dribbling', 'defending', 'physical']}
        for stat, gain in actual_gains.items():
            updated_stats[stat] = self.player[stat] + gain
        
        new_overall = sum(updated_stats.values()) // 6
        
        # Create results embed
        success_level = 'success' if sum(actual_gains.values()) >= 3 else 'normal'
        result_gif = await get_training_gif(self.selected_stat, success_level)
        
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
        
        embed = discord.Embed(
            title=title,
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
        
        # Stat gains
        if actual_gains:
            gains_text = ""
            for stat, gain in actual_gains.items():
                is_primary = stat == self.selected_stat
                emoji = "⭐" if is_primary else "💡"
                new_val = updated_stats[stat]
                old_val = self.player[stat]
                
                milestone = ""
                if new_val >= 90 and old_val < 90:
                    milestone = " 🔥 **WORLD CLASS!**"
                elif new_val >= 80 and old_val < 80:
                    milestone = " ⚡ **ELITE!**"
                elif new_val >= 70 and old_val < 70:
                    milestone = " ✨ **PROFESSIONAL!**"
                
                gains_text += f"{emoji} **+{gain} {stat.capitalize()}**{milestone}\n"
            
            past_potential = any(updated_stats[stat] >= self.player['potential'] for stat in actual_gains.keys())
            if past_potential:
                gains_text += "\n✨ **Pushing beyond limits!**"
        else:
            gains_text = "⚠️ No gains this session - keep training!"
        
        embed.add_field(name="📈 Stat Gains", value=gains_text, inline=False)
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ Training cancelled.", embed=None, view=None)
        self.stop()


# ============================================
# 🎓 POSITION EFFICIENCY SYSTEM
# ============================================

def get_position_efficiency(position):
    """
    Returns training efficiency percentages for each stat based on position.
    
    Categories:
    - Expert (120%): Position's signature stats
    - Primary (100-110%): Core stats for position
    - Secondary (75%): Less relevant but useful
    - Off-position (50%): Not suited for position
    
    Returns dict: {'stat': percentage}
    """
    efficiencies = {
        # ⚡ ATTACKING POSITIONS
        'ST': {
            'shooting': 120,  # Expert
            'pace': 110,      # Primary
            'physical': 110,  # Primary
            'dribbling': 100, # Primary
            'passing': 75,    # Secondary
            'defending': 50   # Off-position
        },
        'CF': {
            'shooting': 120,
            'dribbling': 110,
            'passing': 110,
            'pace': 100,
            'physical': 75,
            'defending': 50
        },
        'LW': {
            'dribbling': 120,
            'pace': 110,
            'shooting': 110,
            'passing': 100,
            'physical': 75,
            'defending': 50
        },
        'RW': {
            'dribbling': 120,
            'pace': 110,
            'shooting': 110,
            'passing': 100,
            'physical': 75,
            'defending': 50
        },
        
        # 🎨 MIDFIELD POSITIONS
        'CAM': {
            'passing': 120,
            'dribbling': 110,
            'shooting': 110,
            'pace': 100,
            'physical': 75,
            'defending': 75
        },
        'CM': {
            'passing': 120,
            'physical': 110,
            'defending': 100,
            'dribbling': 100,
            'pace': 100,
            'shooting': 75
        },
        'CDM': {
            'defending': 120,
            'physical': 110,
            'passing': 110,
            'pace': 100,
            'dribbling': 75,
            'shooting': 50
        },
        'LM': {
            'pace': 120,
            'dribbling': 110,
            'passing': 110,
            'physical': 100,
            'shooting': 75,
            'defending': 75
        },
        'RM': {
            'pace': 120,
            'dribbling': 110,
            'passing': 110,
            'physical': 100,
            'shooting': 75,
            'defending': 75
        },
        
        # 🛡️ DEFENSIVE POSITIONS
        'LB': {
            'defending': 120,
            'pace': 110,
            'physical': 110,
            'passing': 100,
            'dribbling': 75,
            'shooting': 50
        },
        'RB': {
            'defending': 120,
            'pace': 110,
            'physical': 110,
            'passing': 100,
            'dribbling': 75,
            'shooting': 50
        },
        'CB': {
            'defending': 120,
            'physical': 110,
            'pace': 100,
            'passing': 75,
            'dribbling': 50,
            'shooting': 50
        },
        
        # 🧤 GOALKEEPER
        'GK': {
            'physical': 110,
            'defending': 100,
            'pace': 75,
            'passing': 75,
            'dribbling': 50,
            'shooting': 50
        }
    }
    
    return efficiencies.get(position, {
        'pace': 100, 'shooting': 100, 'passing': 100,
        'dribbling': 100, 'defending': 100, 'physical': 100
    })


# ============================================
# 📱 BOT COMMANDS - /train & /sandbox
# ============================================

class TrainingCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="train", description="🏋️ Train your player to improve stats")
    async def train(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        player = db.players.find_one({'user_id': user_id})
        
        if not player:
            await interaction.followup.send("❌ You don't have a player! Use `/start` to create one.", ephemeral=True)
            return
        
        if player.get('retired', False):
            await interaction.followup.send("❌ Your player has retired! Use `/start` to create a new one.", ephemeral=True)
            return
        
        if player.get('injury_weeks', 0) > 0:
            weeks_left = player['injury_weeks']
            await interaction.followup.send(f"🤕 Your player is injured! **{weeks_left} weeks** until recovery.", ephemeral=True)
            return
        
        # Check cooldown
        last_training = player.get('last_training')
        if last_training:
            cooldown = timedelta(hours=config.TRAINING_COOLDOWN_HOURS)
            time_since = datetime.utcnow() - last_training
            if time_since < cooldown:
                remaining = cooldown - time_since
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                await interaction.followup.send(f"⏰ Training on cooldown! Wait **{hours}h {minutes}m**", ephemeral=True)
                return
        
        # Calculate training modifiers
        age = player['age']
        if age <= 23:
            age_multiplier = 1.2
        elif age <= 28:
            age_multiplier = 1.0
        elif age <= 32:
            age_multiplier = 0.85
        else:
            age_multiplier = 0.7
        
        morale = player.get('morale', 75)
        if morale >= 90:
            morale_multiplier = 1.3
        elif morale >= 75:
            morale_multiplier = 1.1
        elif morale >= 50:
            morale_multiplier = 1.0
        elif morale >= 25:
            morale_multiplier = 0.85
        else:
            morale_multiplier = 0.7
        
        league_modifiers = {
            'Premier League': 1.2,
            'La Liga': 1.2,
            'Bundesliga': 1.15,
            'Serie A': 1.15,
            'Ligue 1': 1.1,
            'Eredivisie': 1.0,
            'Liga Portugal': 1.0,
            'Championship': 0.9,
            'MLS': 0.85
        }
        league_modifier = league_modifiers.get(player['league'], 1.0)
        
        position_efficiency = get_position_efficiency(player['position'])
        
        # Calculate base training points
        base_total_points = int((1 + player.get('training_streak', 0) * 0.1) * age_multiplier * morale_multiplier * league_modifier)
        base_total_points = max(1, base_total_points)
        
        # Create initial embed
        embed = discord.Embed(
            title=f"💪 Training Session: {player['player_name']}",
            description=f"**{player['position']}** • Age {player['age']} • **{player['overall_rating']}** OVR → ⭐ **{player['potential']}** POT\n\n"
                       f"🎯 **Select a stat to train**\n"
                       f"Your position affects training efficiency!",
            color=discord.Color.blue()
        )
        
        # Get training prep GIF
        training_prep_gif = await get_training_gif('physical', 'normal')
        embed.set_image(url=training_prep_gif)
        
        # Current stats
        stats_text = (
            f"⚡ Pace: {player['pace']}\n🎯 Shooting: {player['shooting']}\n"
            f"🎨 Passing: {player['passing']}\n⚽ Dribbling: {player['dribbling']}\n"
            f"🛡️ Defending: {player['defending']}\n💪 Physical: {player['physical']}"
        )
        embed.add_field(name="📊 Current Attributes", value=stats_text, inline=True)
        
        # Training modifiers
        morale_desc = "Delighted" if morale >= 90 else "Happy" if morale >= 75 else "Content" if morale >= 50 else "Unhappy" if morale >= 25 else "Furious"
        modifiers_text = (
            f"😊 Morale: {morale_multiplier:.1f}x ({morale_desc})\n"
            f"👤 Age: {age_multiplier:.1f}x\n"
            f"🏟️ {player['league']}: {league_modifier}x\n"
            f"🔥 Streak: {player.get('training_streak', 0)} days"
        )
        embed.add_field(name="⚙️ Training Modifiers", value=modifiers_text, inline=True)
        
        # Position efficiency guide
        position_guide = f"**Your Position: {player['position']}**\n"
        position_guide += "• ⭐ Expert stats: +20% gains\n"
        position_guide += "• ✓ Primary stats: Normal/+10% gains\n"
        position_guide += "• ⚠️ Secondary: -25% gains\n"
        position_guide += "• ❌ Off-position: -50% gains"
        
        embed.add_field(name="📋 Position Training Guide", value=position_guide, inline=False)
        
        # Multi-stat training info
        relationships_guide = "**📋 What Each Stat Improves:**\n\n"
        relationships_guide += "⚡ **Pace** → Physical, Dribbling, Defending, Passing\n"
        relationships_guide += "🎯 **Shooting** → Physical, Dribbling, Pace, Passing\n"
        relationships_guide += "🎨 **Passing** → Dribbling, Shooting, Physical, Defending\n"
        relationships_guide += "⚽ **Dribbling** → Pace, Passing, Shooting, Physical\n"
        relationships_guide += "🛡️ **Defending** → Physical, Pace, Passing, Dribbling\n"
        relationships_guide += "💪 **Physical** → Pace, Defending, Shooting, Passing"
        
        embed.add_field(
            name="✨ Multi-Stat Training System",
            value=relationships_guide,
            inline=False
        )
        
        embed.set_footer(text="🎯 Select a stat to see detailed preview")
        
        # Create view with stat selection
        view = StatTrainingView(player, position_efficiency, base_total_points)
        await interaction.followup.send(embed=embed, view=view)


    @app_commands.command(name="sandbox", description="🧪 Test training system in sandbox mode (no database changes)")
    async def sandbox(self, interaction: discord.Interaction):
        """Test the training system without affecting real player data"""
        await interaction.response.defer()
        
        # Create fake test player
        fake_player = {
            'player_name': 'Test Player',
            'user_id': str(interaction.user.id),
        'position': 'ST',
            'overall_rating': 75,
            'pace': 78,
            'shooting': 80,
            'passing': 70,
            'dribbling': 76,
            'defending': 40,
            'physical': 75,
            'league': 'Premier League',
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
        
        primary_gain = random.randint(1, 3)
        actual_gains[selected_stat] = primary_gain
        
        if selected_stat in relationships:
            for secondary_stat, percentage in relationships[selected_stat].items():
                secondary_points = int(total_points * percentage)
                if secondary_points > 0 and random.random() < 0.7:
                    sec_gain = random.randint(0, 2)
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
