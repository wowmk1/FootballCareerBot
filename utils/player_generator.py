import random
from data.player_names import FIRST_NAMES, LAST_NAMES

def generate_random_player_name():
    """Generate a random player name from expanded database"""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return f"{first} {last}"

def calculate_regen_rating(league: str, position: str):
    """Calculate rating for a regen player based on league"""
    if league == "Premier League":
        base = random.randint(70, 80)
    elif league == "Championship":
        base = random.randint(62, 72)
    else:  # League One
        base = random.randint(55, 65)
    
    if position == "GK":
        base += random.randint(-2, 2)
    elif position in ["ST", "W", "CAM"]:
        base += random.randint(-1, 3)
    
    return min(85, max(50, base))
