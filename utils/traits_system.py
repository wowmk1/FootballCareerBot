"""
Player Traits System - Unlock special abilities at milestones
"""
from database import db

AVAILABLE_TRAITS = {
    'clinical_finisher': {
        'name': 'Clinical Finisher',
        'description': '+5 shooting permanently',
        'unlock_requirement': {'career_goals': 50},
        'emoji': '🎯',
        'stat_boost': {'shooting': 5}
    },
    'speedster': {
        'name': 'Speedster',
        'description': '+5 pace permanently',
        'unlock_requirement': {'pace': 85, 'career_apps': 20},
        'emoji': '⚡',
        'stat_boost': {'pace': 5}
    },
    'playmaker': {
        'name': 'Playmaker',
        'description': '+5 passing permanently',
        'unlock_requirement': {'career_assists': 30},
        'emoji': '🎨',
        'stat_boost': {'passing': 5}
    },
    'iron_wall': {
        'name': 'Iron Wall',
        'description': '+5 defending permanently',
        'unlock_requirement': {'position': 'CB', 'season_apps': 20},
        'emoji': '🛡️',
        'stat_boost': {'defending': 5}
    },
    'training_machine': {
        'name': 'Training Machine',
        'description': '+1 point per training session',
        'unlock_requirement': {'training_streak': 30},
        'emoji': '💪',
        'bonus': 'training_boost'
    },
    'captain': {
        'name': 'Captain',
        'description': '+3 to all stats',
        'unlock_requirement': {'career_apps': 100, 'season_motm': 5},
        'emoji': '©️',
        'stat_boost': {'pace': 3, 'shooting': 3, 'passing': 3, 'dribbling': 3, 'defending': 3, 'physical': 3}
    }
}

async def check_trait_unlocks(user_id: int, bot=None):
    """Check if player has unlocked any new traits"""
    
    player = await db.get_player(user_id)
    if not player:
        return []
    
    # Get current traits
    async with db.pool.acquire() as conn:
        current_traits = await conn.fetch(
            "SELECT trait_id FROM player_traits WHERE user_id = $1",
            user_id
        )
        current_trait_ids = [t['trait_id'] for t in current_traits]
    
    newly_unlocked = []
    
    for trait_id, trait_data in AVAILABLE_TRAITS.items():
        # Skip if already unlocked
        if trait_id in current_trait_ids:
            continue
        
        # Check requirements
        requirements = trait_data['unlock_requirement']
        meets_requirements = True
        
        for req_key, req_value in requirements.items():
            if req_key == 'position':
                if player['position'] != req_value:
                    meets_requirements = False
            elif player.get(req_key, 0) < req_value:
                meets_requirements = False
        
        if meets_requirements:
            # UNLOCK TRAIT
            async with db.pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO player_traits (user_id, trait_id) VALUES ($1, $2)",
                    user_id, trait_id
                )
            
            # Apply stat boosts if any
            if 'stat_boost' in trait_data:
                async with db.pool.acquire() as conn:
                    set_clauses = []
                    for stat, boost in trait_data['stat_boost'].items():
                        set_clauses.append(f"{stat} = LEAST(99, {stat} + {boost})")
                    
                    if set_clauses:
                        await conn.execute(
                            f"UPDATE players SET {', '.join(set_clauses)} WHERE user_id = $1",
                            user_id
                        )
            
            newly_unlocked.append((trait_id, trait_data))
            print(f"  🎯 {player['player_name']} unlocked trait: {trait_data['name']}")
    
    # Send notifications
    if newly_unlocked and bot:
        for trait_id, trait_data in newly_unlocked:
            try:
                user = await bot.fetch_user(user_id)
                import discord
                embed = discord.Embed(
                    title=f"{trait_data['emoji']} NEW TRAIT UNLOCKED!",
                    description=f"**{trait_data['name']}**\n{trait_data['description']}",
                    color=discord.Color.gold()
                )
                embed.add_field(
                    name="✅ Requirement Met",
                    value="You've achieved a career milestone!",
                    inline=False
                )
                await user.send(embed=embed)
            except:
                pass
    
    return newly_unlocked
