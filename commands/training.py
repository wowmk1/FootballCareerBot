import discord
from discord import app_commands
from discord.ext import commands
from database import db
import random
from datetime import datetime, timedelta
import config
import asyncio


class TrainingCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="train", description="Train to improve your stats (once per day)")
    async def train(self, interaction: discord.Interaction):
        """Realistic daily training with slower, meaningful progression"""

        # CRITICAL: Defer immediately to prevent timeout
        await interaction.response.defer()

        player = await db.get_player(interaction.user.id)

        if not player:
            await interaction.followup.send(
                "You haven't created a player yet! Use `/start` to begin.",
                ephemeral=True
            )
            return

        if player['retired']:
            await interaction.followup.send(
                "Your player has retired! Use `/start` to create a new player.",
                ephemeral=True
            )
            return

        if player['injury_weeks'] and player['injury_weeks'] > 0:
            await interaction.followup.send(
                f"You're injured! Rest for **{player['injury_weeks']} more weeks** before training.",
                ephemeral=True
            )
            return

        # Check cooldown
        streak_broken = False
        if player['last_training']:
            last_train = datetime.fromisoformat(player['last_training'])
            time_diff = datetime.now() - last_train

            if time_diff < timedelta(hours=config.TRAINING_COOLDOWN_HOURS):
                # Calculate exact time remaining
                next_train = last_train + timedelta(hours=config.TRAINING_COOLDOWN_HOURS)
                time_until = next_train - datetime.now()

                hours_left = int(time_until.total_seconds() // 3600)
                minutes_left = int((time_until.total_seconds() % 3600) // 60)

                # Format next training time
                next_train_formatted = next_train.strftime('%I:%M %p')
                today_or_tomorrow = "today" if next_train.date() == datetime.now().date() else "tomorrow"

                embed = discord.Embed(
                    title="⏰ Training on Cooldown",
                    description=f"You trained recently and need rest!",
                    color=discord.Color.orange()
                )

                embed.add_field(
                    name="⏱️ Time Remaining",
                    value=f"**{hours_left}h {minutes_left}m**",
                    inline=True
                )

                embed.add_field(
                    name="🕐 Next Training",
                    value=f"**{next_train_formatted}** {today_or_tomorrow}",
                    inline=True
                )

                embed.add_field(
                    name="🔥 Current Streak",
                    value=f"**{player['training_streak']} days**\n*Don't break it!*",
                    inline=False
                )

                embed.set_footer(text="💡 Train daily to maintain your streak and gain bonus points!")

                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # 48h grace period for streaks
            if time_diff > timedelta(hours=48):
                streak_broken = True

        # REALISTIC PROGRESSION with MORALE BONUS
        age_multiplier = 1.0
        if player['age'] <= 21:
            age_multiplier = 1.2
        elif player['age'] <= 25:
            age_multiplier = 1.0
        elif player['age'] <= 30:
            age_multiplier = 0.8
        elif player['age'] <= 35:
            age_multiplier = 0.5
        else:
            age_multiplier = 0.3

        # MORALE AFFECTS TRAINING GAINS
        from utils.form_morale_system import get_morale_training_modifier
        morale_multiplier = get_morale_training_modifier(player['morale'])

        # ⭐ OPTION A: Reduced base gain from 2 to 1
        base_points = 1  # CHANGED FROM 2

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
            streak_bonus = 1
        if new_streak >= 30:
            streak_bonus = 2

        # MAJOR BONUS: 30+ day streak gives +3 potential
        potential_boost = 0
        if new_streak == 30:
            potential_boost = 3
            async with db.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE players SET potential = potential + 3 WHERE user_id = $1",
                    interaction.user.id
                )

        # Apply ALL multipliers
        total_points = int((base_points + streak_bonus) * age_multiplier * morale_multiplier)
        total_points = max(1, total_points)

        # FIX #25: Add randomness to training
        bad_day_message = ""
        surprise_stat = None
        
        # 15% chance of "bad training day" (reduced gains)
        if random.random() < 0.15:
            total_points = max(1, total_points - 1)
            bad_day_message = "\n⚠️ **Tough session today!** Gains reduced."
        
        # 10% chance of unexpected stat gain
        unexpected_bonus = False
        if random.random() < 0.10:
            unexpected_bonus = True

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
            if random.random() < 0.75:
                stat = random.choice(primary_stats)
            else:
                stat = random.choice(all_stats)

            stat_gains[stat] = stat_gains.get(stat, 0) + 1

        # Add unexpected stat gain
        if unexpected_bonus:
            surprise_stat = random.choice(all_stats)
            stat_gains[surprise_stat] = stat_gains.get(surprise_stat, 0) + 1

        # Apply stat gains with diminishing returns
        update_parts = []
        update_values = []
        actual_gains = {}

        current_potential = player['potential'] + potential_boost

        for stat, gain in stat_gains.items():
            current = player[stat]
            distance_from_potential = current_potential - current

            if distance_from_potential <= 0:
                if current < current_potential + 3:
                    successful_gains = sum(1 for _ in range(gain) if random.random() < 0.2)
                    capped_value = min(99, current + successful_gains)
                else:
                    capped_value = current
            elif distance_from_potential <= 5:
                successful_gains = sum(1 for _ in range(gain) if random.random() < 0.5)
                capped_value = min(99, min(current + successful_gains, current_potential + 3))
            elif distance_from_potential <= 10:
                successful_gains = sum(1 for _ in range(gain) if random.random() < 0.7)
                capped_value = min(99, min(current + successful_gains, current_potential + 3))
            else:
                successful_gains = sum(1 for _ in range(gain) if random.random() < 0.9)
                capped_value = min(99, min(current + successful_gains, current_potential + 3))

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
                set_clause = ", ".join([f"{part} = ${i + 1}" for i, part in enumerate(update_parts)])
                set_clause += f", overall_rating = ${len(update_parts) + 1}"
                set_clause += f", training_streak = ${len(update_parts) + 2}"
                set_clause += f", last_training = ${len(update_parts) + 3}"

                all_values = update_values + [new_overall, new_streak, datetime.now().isoformat(), interaction.user.id]

                await conn.execute(
                    f"UPDATE players SET {set_clause} WHERE user_id = ${len(update_parts) + 4}",
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

        # SMALL MORALE BOOST FROM TRAINING
        from utils.form_morale_system import update_player_morale
        await update_player_morale(interaction.user.id, 'training')

        # FIX #18: Enhanced Training Feedback
        from utils.form_morale_system import get_morale_description
        morale_desc = get_morale_description(player['morale'])

        # Calculate progress to next level
        progress_to_next = 100 - ((new_overall % 10) * 10) if new_overall < 99 else 0
        progress_bar_length = 20
        filled = int((100 - progress_to_next) / 100 * progress_bar_length)
        progress_bar = "█" * filled + "░" * (progress_bar_length - filled)

        embed = discord.Embed(
            title="💪 Training Complete!",
            description=f"Hard work and dedication!" + streak_lost_message + bad_day_message,
            color=discord.Color.gold()
        )

        # Progress to next OVR
        if new_overall < 99:
            next_ovr = new_overall + 1
            embed.add_field(
                name=f"📊 Progress to {next_ovr} OVR",
                value=f"{progress_bar} {100 - progress_to_next}%",
                inline=False
            )

        # Show gains with highlights and milestones
        if actual_gains:
            gains_text = ""
            for stat, gain in actual_gains.items():
                is_primary = stat in primary_stats
                emoji = "⭐" if is_primary else "•"
                
                # Highlight milestone gains
                new_val = player[stat] + gain
                milestone = ""
                if new_val >= 90 and player[stat] < 90:
                    milestone = " 🔥 **WORLD CLASS!**"
                elif new_val >= 80 and player[stat] < 80:
                    milestone = " ⚡ **ELITE!**"
                
                gains_text += f"{emoji} +{gain} {stat.capitalize()}{milestone}\n"

            past_potential = any(player[stat] >= player['potential'] for stat in actual_gains.keys())
            if past_potential:
                gains_text += "\n✨ **Pushing beyond limits!**"
        else:
            gains_text = "Tough session! Keep working - gains will come."

        embed.add_field(name="📈 Stat Gains", value=gains_text, inline=False)

        # Show surprise development
        if surprise_stat and actual_gains.get(surprise_stat, 0) > 0:
            embed.add_field(
                name="💡 Surprise Development",
                value=f"Unexpected improvement in {surprise_stat}!",
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
                          f"You are {abs(diff):.1f} OVR {comparison} average",
                    inline=False
                )

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

        if potential_boost > 0:
            embed.add_field(
                name="🌟 30-DAY MILESTONE!",
                value=f"**+{potential_boost} POTENTIAL!** New max: {current_potential}",
                inline=False
            )

        distance = current_potential - new_overall
        if distance > 0:
            embed.add_field(
                name="🎯 Potential Progress",
                value=f"**{distance} OVR** from potential ({current_potential})\n"
                      f"Estimated: ~{distance * 6} sessions (~{distance * 6} days)",
                inline=False
            )
        else:
            over_by = new_overall - player['potential']
            embed.add_field(
                name="🚀 Beyond Potential!",
                value=f"**+{over_by} OVR** above base potential!",
                inline=False
            )

        years_left = config.RETIREMENT_AGE - player['age']
        embed.add_field(
            name="⏳ Career Time",
            value=f"**{years_left} years** left | Age: {player['age']}",
            inline=True
        )

        embed.add_field(
            name="⏰ Next Session",
            value=f"**{config.TRAINING_COOLDOWN_HOURS}h**",
            inline=True
        )

        embed.set_footer(text=f"Age: {age_multiplier}x | Morale: {morale_multiplier}x | Slower gains = more rewarding!")

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(TrainingCommands(bot))
