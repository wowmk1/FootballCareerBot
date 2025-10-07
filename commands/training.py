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
        """Enhanced daily training with 3x gains and streak bonuses"""
        
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
        
        # Check cooldown with 48h grace period for streaks
        streak_broken = False
        if player['last_training']:
            last_train = datetime.fromisoformat(player['last_training'])
            time_diff = datetime.now() - last_train
            
            if time_diff < timedelta(hours=config.TRAINING_COOLDOWN_HOURS):
                hours_left = config.TRAINING_COOLDOWN_HOURS - (time_diff.seconds // 3600)
                minutes_left = (config.TRAINING_COOLDOWN_HOURS * 60) - (time_diff.seconds // 60)
                
                if hours_left > 0:
                    await interaction.response.send_message(
                        f"⏰ Train again in **{hours_left}h {minutes_left % 60}m**!\n"
                        f"Training available every {config.TRAINING_COOLDOWN_HOURS}h.",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        f"⏰ Train again in **{minutes_left}m**!",
                        ephemeral=True
                    )
                return
            
            # 48h grace period for streaks
            if time_diff > timedelta(hours=48):
                streak_broken = True
        
        # ENHANCED: 3x gains for 3-week compression + age modifiers
        age_multiplier = 1.0
        if player['age'] >= 30:
            age_multiplier = 0.9  # Less penalty for veterans
        elif player['age'] >= 35:
            age_multiplier = 0.7
        
        # Base gain is 6 (3x original 2) to account for compressed time
        base_gain = int(6 * age_multiplier)
        
        # Handle streak
        if streak_broken:
            new_streak = 1
            streak_lost_message = f"\n⚠️ **Streak broken!** Missed a day. Starting fresh."
        else:
            new_streak = player['training_streak'] + 1
            streak_lost_message = ""
        
        # Streak bonuses
        streak_bonus = 0
        if new_streak >= 7:
            streak_bonus = 2  # +2 for weekly streak
        if new_streak >= 30:
            streak_bonus = 5  # +5 for monthly dedication
        
        # MAJOR BONUS: 30+ day streak gives +5 max potential permanently
        potential_boost = 0
        if new_streak == 30:
            potential_boost = 5
            async with db.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE players SET potential = potential + 5 WHERE user_id = $1",
                    interaction.user.id
                )
        
        total_points = base_gain + streak_bonus
        
        # Position-focused training
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
            if random.random() < 0.75:  # 75% chance for primary stats
                stat = random.choice(primary_stats)
            else:
                stat = random.choice(all_stats)
            
            stat_gains[stat] = stat_gains.get(stat, 0) + 1
        
        # Apply stat gains with improved potential system
        update_parts = []
        update_values = []
        actual_gains = {}
        
        current_potential = player['potential'] + potential_boost
        
        for stat, gain in stat_gains.items():
            current = player[stat]
            
            # Growth past potential (easier now)
            if current >= current_potential:
                # 50% chance to gain 1 point even past potential (max +5 above)
                if current < current_potential + 5 and random.random() < 0.5:
                    capped_value = current + 1
                    actual_gain = 1
                else:
                    capped_value = current
                    actual_gain = 0
            else:
                # Normal growth
                capped_value = min(current + gain, min(99, current_potential))
                actual_gain = capped_value - current
            
            if actual_gain > 0:
                update_parts.append(stat)
                update_values.append(capped_value)
                actual_gains[stat] = actual_gain
        
        # Calculate new overall
        new_overall = (
            (player['pace'] + actual_gains.get('pace', 0)) +
            (player['shooting'] + actual_gains.get('shooting', 0)) +
            (player['passing'] + actual_gains.get('passing', 0)) +
            (player['dribbling'] + actual_gains.get('dribbling', 0)) +
            (player['defending'] + actual_gains.get('defending', 0)) +
            (player['physical'] + actual_gains.get('physical', 0))
        ) // 6
        
        # Update database
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
        
        # Build response embed
        embed = discord.Embed(
            title="💪 Training Complete!",
            description="Dedication pays off!" + streak_lost_message,
            color=discord.Color.gold()
        )
        
        if actual_gains:
            gains_text = "\n".join([
                f"{'⭐' if stat in primary_stats else '•'} +{gain} {stat.capitalize()}"
                for stat, gain in actual_gains.items()
            ])
            
            past_potential = any(player[stat] >= player['potential'] for stat in actual_gains.keys())
            if past_potential:
                gains_text += "\n\n✨ **Exceeding potential!**"
        else:
            gains_text = "Hard session, no visible gains. Keep pushing!"
        
        embed.add_field(name="📈 Stat Gains", value=gains_text, inline=False)
        
        if new_overall > player['overall_rating']:
            embed.add_field(
                name="⭐ Overall Rating",
                value=f"{player['overall_rating']} → **{new_overall}** (+{new_overall - player['overall_rating']})",
                inline=True
            )
        
        embed.add_field(
            name="🔥 Streak",
            value=f"**{new_streak} days**",
            inline=True
        )
        
        if streak_bonus > 0:
            embed.add_field(
                name="🎁 Streak Bonus",
                value=f"+{streak_bonus} extra points!",
                inline=True
            )
        
        if potential_boost > 0:
            embed.add_field(
                name="🌟 30-DAY MILESTONE!",
                value=f"**+5 POTENTIAL!** New max: {current_potential}",
                inline=False
            )
        
        # Show progression
        if new_overall < current_potential:
            gap = current_potential - new_overall
            embed.add_field(
                name="🎯 Potential Progress",
                value=f"**{gap} OVR** from potential ({current_potential})",
                inline=False
            )
        elif new_overall == current_potential:
            embed.add_field(
                name="✅ Potential Reached!",
                value=f"Can still grow **+5 OVR** with consistency!",
                inline=False
            )
        else:
            embed.add_field(
                name="🚀 Beyond Potential!",
                value=f"**{new_overall - player['potential']} OVR** above base potential!",
                inline=False
            )
        
        years_left = config.RETIREMENT_AGE - player['age']
        embed.add_field(
            name="⏳ Career Time",
            value=f"**{years_left} years** until retirement",
            inline=True
        )
        
        embed.add_field(
            name="⏰ Next Session",
            value=f"**{config.TRAINING_COOLDOWN_HOURS}h**",
            inline=True
        )
        
        motivational_messages = [
            "Consistency builds champions!",
            "Every session counts!",
            "You're getting stronger!",
            "Keep the momentum!",
            "Hard work never lies!",
            "Champions are made in training!",
        ]
        
        if new_streak >= 7:
            motivational_messages.append("🔥 WEEK STREAK! Unstoppable!")
        if new_streak >= 30:
            motivational_messages.append("⚡ MONTH STREAK! Legendary dedication!")
        
        embed.set_footer(text=random.choice(motivational_messages))
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(TrainingCommands(bot))
