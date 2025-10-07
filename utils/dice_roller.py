import random

def roll_d20():
    """Roll a 20-sided die"""
    return random.randint(1, 20)

def calculate_modifier(stat_value):
    """Calculate D&D style modifier from stat value
    
    Examples:
    - 50-59 = +5
    - 60-69 = +6
    - 70-79 = +7
    - 80-89 = +8
    - 90-99 = +9
    """
    return stat_value // 10

def get_difficulty_class(action):
    """Get the difficulty class for different actions
    
    DC 10 = Easy (70% chance with decent stats)
    DC 15 = Medium (50% chance)
    DC 20 = Hard (30% chance)
    """
    difficulty_classes = {
        'shoot': 15,      # Medium difficulty
        'pass': 12,       # Easier
        'dribble': 14,    # Medium-easy
        'tackle': 13,
        'save': 16,
        'header': 14
    }
    
    return difficulty_classes.get(action, 15)

def roll_with_advantage():
    """Roll two d20s and take the higher result"""
    roll1 = roll_d20()
    roll2 = roll_d20()
    return max(roll1, roll2)

def roll_with_disadvantage():
    """Roll two d20s and take the lower result"""
    roll1 = roll_d20()
    roll2 = roll_d20()
    return min(roll1, roll2)

def check_success(stat_value, difficulty_class, advantage=False, disadvantage=False):
    """Perform a complete skill check
    
    Args:
        stat_value: Player's stat (e.g., shooting = 85)
        difficulty_class: DC to beat (e.g., 15)
        advantage: Roll twice, take higher
        disadvantage: Roll twice, take lower
    
    Returns:
        dict with roll, modifier, total, success, and critical info
    """
    if advantage:
        roll = roll_with_advantage()
    elif disadvantage:
        roll = roll_with_disadvantage()
    else:
        roll = roll_d20()
    
    modifier = calculate_modifier(stat_value)
    total = roll + modifier
    success = total >= difficulty_class
    
    return {
        'roll': roll,
        'modifier': modifier,
        'total': total,
        'success': success,
        'critical_success': roll == 20,
        'critical_failure': roll == 1,
        'dc': difficulty_class
    }
