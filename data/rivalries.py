"""
Club Rivalries - Derby matches give bonus rewards
"""

RIVALRIES = {
    # Premier League Derbies
    ('man_united', 'man_city'): {'name': 'Manchester Derby', 'intensity': 10},
    ('liverpool', 'man_united'): {'name': 'North West Derby', 'intensity': 10},
    ('arsenal', 'tottenham'): {'name': 'North London Derby', 'intensity': 10},
    ('chelsea', 'arsenal'): {'name': 'London Derby', 'intensity': 8},
    ('chelsea', 'tottenham'): {'name': 'London Derby', 'intensity': 8},
    ('liverpool', 'everton'): {'name': 'Merseyside Derby', 'intensity': 10},
    ('newcastle', 'sunderland'): {'name': 'Tyne-Wear Derby', 'intensity': 9},
    
    # Championship Derbies
    ('leeds', 'sheff_united'): {'name': 'Yorkshire Derby', 'intensity': 8},
    ('bristol_city', 'cardiff'): {'name': 'Severnside Derby', 'intensity': 7},
    ('millwall', 'qpr'): {'name': 'South London Derby', 'intensity': 7},
}

def get_rivalry(team1_id: str, team2_id: str):
    """Check if match is a rivalry"""
    key1 = (team1_id, team2_id)
    key2 = (team2_id, team1_id)
    
    return RIVALRIES.get(key1) or RIVALRIES.get(key2)

def get_rivalry_bonuses(intensity: int):
    """Get bonuses for winning a rivalry match"""
    return {
        'morale_boost': intensity // 2,  # 4-5 morale for high intensity
        'form_boost': intensity,  # 8-10 form for high intensity
        'rating_multiplier': 1.2  # 20% bonus to match rating
    }
