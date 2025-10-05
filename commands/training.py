import discord
from discord import app_commands
from discord.ext import commands
from database import db
import random
from datetime import datetime, timedelta
import config

class TrainingCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="train", description="Train to improve your stats (once per day)")
    async def train(self, interaction: discord.Interaction):
        """Daily training"""
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.response.send_message(
                "You haven't created a player yet! Use `/start` to begin.",
                ephemeral=True
            )
            return
        
        if player['retired']:
            await interaction.response.send_message(
                "Your player has retired! Use `/start` to create a new player.",
                ephemeral=True
            )
            return
        
        if player['injury_weeks'] and player['injury_weeks'] > 0:
            await interaction.response.send_message(
                f"You're injured! Rest for **{player['injury_weeks']} more weeks** before training.",
                ephemeral=True
            )
            return
        
        # IMPROVED: Check streak with grace period
        streak_broken = False
        if player['last_training']:
            last_train = datetime.fromisoformat(player['last_training'])
            time_diff = datetime.now() - last_train
            
            if time_diff < timedelta(hours=config.TRAINING_COOLDOWN_HOURS):
                hours_left = config.TRAINING_COOLDOWN_HOURS - (time_diff.seconds // 3600)
                minutes_left = (config.TRAINING_COOLDOWN_HOURS * 60) - (time_diff.seconds // 60)
                
                if hours_left > 0:
                    await interaction.response.send_message(
                        f"You can train again in **{hours_left}h {minutes_left % 60}m**!\n\n"
                        f"Training is available every {config.TRAINING_COOLDOWN_HOURS} hours.",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        f"You can train again in **{minutes_left}m**!",
                        ephemeral=True
                    )
                return
            
            # IMPROVED: Grace period for streaks (48 hours = 1 day grace)
            if time_diff > timedelta(hours=48):
                streak_broken = True
        
        age_multiplier = 1.0
        if player['age'] >= 30:
            age_multiplier = 0.8
        elif player['age'] >= 35:
            age_multiplier = 0.5
        
        base_gain = int(config.BASE_STAT_GAIN * age_multiplier)
        
        # Handle streak
        if streak_broken:
            new_streak = 1
            streak_lost_message = f"\n**Streak broken!** You missed a day. Starting fresh at 1 day."
        else:
            new_streak = player['training_streak'] + 1
            streak_lost_message = ""
        
        streak_bonus = 0
        if new_streak >= config.STREAK_BONUS_THRESHOLD:
            streak_bonus = config.STREAK_BONUS_AMOUNT
        
        total_points = base_gain + streak_bonus
        
        position_focus = {
            'ST': ['shooting', 'physical', 'pace'],
            'W': ['pace', 'dribbling', 'shooting'],
            'CAM': ['passing', 'dribbling', 'shooting'],
            'CM': ['passing', 'physical', 'defending'],
            'CDM': ['defending', 'physical', 'passing'],
            'FB': ['pace', 'defending', 'physical'],
            'CB': ['defending', 'physical', 'passing'],
            'GK': ['defending', 'physical']
        }
        
        primary_stats = position_focus.get(player['position'], ['pace', 'shooting', 'passing'])
        all_stats = ['pace', 'shooting', 'passing', 'dribbling', 'defending', 'physical']
        
        stat_gains = {}
        for _ in range(total_points):
            if random.random() < 0.7:
                stat = random.choice(primary_stats)
            else:
                stat = random.choice(all_stats)
            
            stat_gains[stat] = stat_gains.get(stat, 0) + 1
        
        update_parts = []
        update_values = []
        actual_gains = {}
        
        # IMPROVED: Allow growth past potential with diminishing returns
        for stat, gain in stat_gains.items():
            current = player[stat]
            potential = player['potential']
            
            # If at or above potential, harder to improve
            if current >= potential:
                # 33% chance to gain 1 point even past potential (max +2 above potential)
                if current < potential + 2 and random.random() < 0.33:
                    capped_value = current + 1
                    actual_gain = 1
                else:
                    capped_value = current
                    actual_gain = 0
            else:
                # Normal growth below potential
                capped_value = min(current + gain, min(99, potential))
                actual_gain = capped_value - current
            
            if actual_gain > 0:
                update_parts.append(stat)
                update_values.append(capped_value)
                actual_gains[stat] = actual_gain
        
        new_overall = (
            (player['pace'] + actual_gains.get('pace', 0)) +
            (player['shooting'] + actual_gains.get('shooting', 0)) +
            (player['passing'] + actual_gains.get('passing', 0)) +
            (player['dribbling'] + actual_gains.get('dribbling', 0)) +
            (player['defending'] + actual_gains.get('defending', 0)) +
            (player['physical'] + actual_gains.get('physical', 0))
        ) // 6
        
        async with db.pool.acquire() as conn:
            if update_parts:
                set_clause = ", ".join([f"{part} = ${i+1}" for i, part in enumerate(update_parts)])
                set_clause += f", overall_rating = ${len(update_parts)+1}"
                set_clause += f", training_streak = ${len(update_parts)+2}"
                set_clause += f", last_training = ${len(update_parts)+3}"
                
                all_values = update_values + [new_overall, new_streak, datetime.now().isoformat(), interaction.user.id]
                
                await conn.execute(
                    f"UPDATE players SET {set_clause} WHERE user_id = ${len(update_parts)+4}",
                    *all_values
                )
            else:
                await conn.execute(
                    "UPDATE players SET training_streak = $1, last_training = $2 WHERE user_id = $3",
                    new_streak, datetime.now().isoformat(), interaction.user.id
                )
            
            await conn.execute('''
                INSERT INTO training_history (user_id, stat_gains, streak_bonus, overall_before, overall_after)
                VALUES ($1, $2, $3, $4, $5)
            ''',
                interaction.user.id,
                str(actual_gains),
                streak_bonus > 0,
                player['overall_rating'],
                new_overall
            )
        
        embed = discord.Embed(
            title="Training Session Complete!",
            description="Great work today! Your dedication is paying off." + streak_lost_message,
            color=discord.Color.gold()
        )
        
        if actual_gains:
            gains_text = "\n".join([
                f"{'⭐' if stat in primary_stats else '•'} +{gain} {stat.capitalize()}"
                for stat, gain in actual_gains.items()
            ])
            
            # Check if any gains were past potential
            past_potential = any(player[stat] >= player['potential'] for stat in actual_gains.keys())
            if past_potential:
                gains_text += "\n\n**Exceeding expectations!** (Past potential)"
        else:
            # Check if at absolute cap
            if new_overall >= player['potential'] + 2:
                gains_text = "**Maximum reached!** You've exceeded your potential limit."
            else:
                gains_text = "Hard training, but no gains today. Keep pushing!"
        
        embed.add_field(name="Stat Gains", value=gains_text, inline=False)
        
        if new_overall > player['overall_rating']:
            embed.add_field(
                name="Overall Rating",
                value=f"{player['overall_rating']} → **{new_overall}** (+{new_overall - player['overall_rating']})",
                inline=True
            )
        else:
            embed.add_field(name="Overall Rating", value=f"**{new_overall}**", inline=True)
        
        embed.add_field(name="Training Streak", value=f"**{new_streak}** days", inline=True)
        
        if streak_bonus:
            embed.add_field(
                name="Streak Bonus",
                value=f"+{streak_bonus} extra stat point!",
                inline=True
            )
        
        if player['age'] >= 30:
            embed.add_field(
                name="Age Factor",
                value=f"Training gains reduced due to age ({player['age']}). Veterans improve slower!",
                inline=False
            )
        
        # Show progress to potential
        if new_overall < player['potential']:
            gap = player['potential'] - new_overall
            embed.add_field(
                name="Potential Progress",
                value=f"**{gap} OVR** away from potential ({player['potential']})",
                inline=False
            )
        elif new_overall == player['potential']:
            embed.add_field(
                name="Potential Reached!",
                value=f"You've reached your potential! You can still grow **+2 OVR** with hard work.",
                inline=False
            )
        else:
            embed.add_field(
                name="Beyond Potential!",
                value=f"**{new_overall - player['potential']} OVR** above potential! Exceptional dedication!",
                inline=False
            )
        
        years_left = config.RETIREMENT_AGE - player['age']
        if years_left <= 5:
            embed.add_field(
                name="Career Time Left",
                value=f"**{years_left} years** until retirement (age {config.RETIREMENT_AGE})",
                inline=False
            )
        
        embed.add_field(
            name="Next Training",
            value=f"Available in **{config.TRAINING_COOLDOWN_HOURS}h**",
            inline=False
        )
        
        messages = [
            "Consistency is key!",
            "Keep pushing your limits!",
            "Hard work beats talent!",
            "You're getting stronger!",
            "Focus and determination!",
            "Champions are made in training!",
        ]
        
        if new_streak >= 7:
            messages.append("A WEEK STREAK! Incredible dedication!")
        if new_streak >= 30:
            messages.append("30 DAYS! You're a training machine!")
        
        embed.set_footer(text=random.choice(messages))
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(TrainingCommands(bot))
