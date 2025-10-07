"""
Form and Morale System
Form: Based on recent match performances
Morale: Affected by results, transfers, contract situation
"""

from database import db

async def update_player_form(user_id: int, match_rating: float):
    """Update player form based on match performance"""
    player = await db.get_player(user_id)
    if not player:
        return
    
    current_form = player['form']
    
    # Form change based on rating
    if match_rating >= 8.0:
        form_change = 10  # Excellent performance
    elif match_rating >= 7.0:
        form_change = 5   # Good performance
    elif match_rating >= 6.0:
        form_change = 0   # Average performance
    elif match_rating >= 5.0:
        form_change = -5  # Poor performance
    else:
        form_change = -10 # Very poor performance
    
    new_form = max(0, min(100, current_form + form_change))
    
    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE players SET form = $1 WHERE user_id = $2",
            new_form, user_id
        )
    
    return new_form

async def update_player_morale(user_id: int, event_type: str, value: int = 0):
    """Update player morale based on events
    
    event_type: 'win', 'loss', 'draw', 'goal', 'transfer', 'contract_expiring', 'training'
    """
    player = await db.get_player(user_id)
    if not player:
        return
    
    current_morale = player['morale']
    
    morale_changes = {
        'win': 5,
        'loss': -5,
        'draw': 0,
        'goal': 3,
        'assist': 2,
        'transfer_accepted': 10,
        'transfer_rejected': -3,
        'contract_expiring': -5,
        'new_contract': 8,
        'training': 1,
        'injury': -10
    }
    
    morale_change = morale_changes.get(event_type, 0)
    new_morale = max(0, min(100, current_morale + morale_change))
    
    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE players SET morale = $1 WHERE user_id = $2",
            new_morale, user_id
        )
    
    return new_morale

def get_form_modifier(form: int):
    """Get stat modifier based on form
    
    Form 80-100: +5 to all stats
    Form 60-79: +2 to all stats
    Form 40-59: 0 modifier
    Form 20-39: -2 to all stats
    Form 0-19: -5 to all stats
    """
    if form >= 80:
        return 5
    elif form >= 60:
        return 2
    elif form >= 40:
        return 0
    elif form >= 20:
        return -2
    else:
        return -5

def get_morale_training_modifier(morale: int):
    """Get training gains modifier based on morale
    
    High morale = better training
    """
    if morale >= 80:
        return 1.3  # 30% bonus
    elif morale >= 60:
        return 1.15  # 15% bonus
    elif morale >= 40:
        return 1.0  # Normal
    elif morale >= 20:
        return 0.85  # 15% penalty
    else:
        return 0.7  # 30% penalty

def get_form_description(form: int):
    """Get form description for display"""
    if form >= 80:
        return "🔥 Excellent"
    elif form >= 60:
        return "✅ Good"
    elif form >= 40:
        return "📊 Average"
    elif form >= 20:
        return "📉 Poor"
    else:
        return "❄️ Very Poor"

def get_morale_description(morale: int):
    """Get morale description for display"""
    if morale >= 80:
        return "😊 Delighted"
    elif morale >= 60:
        return "🙂 Happy"
    elif morale >= 40:
        return "😐 Content"
    elif morale >= 20:
        return "😕 Unhappy"
    else:
        return "😢 Miserable"
