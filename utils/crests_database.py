"""
Static Team Crests Database
Uses reliable Wikipedia/Wikimedia Commons URLs
No API needed - these are permanent public domain images
"""

# Premier League Team Crests
PREMIER_LEAGUE_CRESTS = {
    'arsenal': 'https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg',
    'aston_villa': 'https://upload.wikimedia.org/wikipedia/en/f/f9/Aston_Villa_FC_crest_%282016%29.svg',
    'bournemouth': 'https://upload.wikimedia.org/wikipedia/en/e/e5/AFC_Bournemouth_%282013%29.svg',
    'brentford': 'https://upload.wikimedia.org/wikipedia/en/2/2a/Brentford_FC_crest.svg',
    'brighton': 'https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_%26_Hove_Albion_logo.svg',
    'chelsea': 'https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg',
    'crystal_palace': 'https://upload.wikimedia.org/wikipedia/en/a/a2/Crystal_Palace_FC_logo_%282022%29.svg',
    'everton': 'https://upload.wikimedia.org/wikipedia/en/7/7c/Everton_FC_logo.svg',
    'fulham': 'https://upload.wikimedia.org/wikipedia/en/e/eb/Fulham_FC_%28shield%29.svg',
    'liverpool': 'https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg',
    'man_city': 'https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg',
    'man_united': 'https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg',
    'newcastle': 'https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg',
    'nottm_forest': 'https://upload.wikimedia.org/wikipedia/en/e/e5/Nottingham_Forest_F.C._logo.svg',
    'tottenham': 'https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg',
    'west_ham': 'https://upload.wikimedia.org/wikipedia/en/c/c2/West_Ham_United_FC_logo.svg',
    'wolves': 'https://upload.wikimedia.org/wikipedia/en/f/fc/Wolverhampton_Wanderers.svg',
    'leicester': 'https://upload.wikimedia.org/wikipedia/en/2/2d/Leicester_City_crest.svg',
    'southampton': 'https://upload.wikimedia.org/wikipedia/en/c/c9/FC_Southampton.svg',
    'ipswich': 'https://upload.wikimedia.org/wikipedia/en/4/43/Ipswich_Town.svg',
}

# Championship Team Crests
CHAMPIONSHIP_CRESTS = {
    'leeds': 'https://upload.wikimedia.org/wikipedia/en/5/54/Leeds_United_F.C._logo.svg',
    'burnley': 'https://upload.wikimedia.org/wikipedia/en/6/6d/Burnley_F.C._Logo.svg',
    'sheff_united': 'https://upload.wikimedia.org/wikipedia/en/9/9c/Sheffield_United_FC_logo.svg',
    'luton': 'https://upload.wikimedia.org/wikipedia/en/8/8b/Luton_Town_logo.svg',
    'middlesbrough': 'https://upload.wikimedia.org/wikipedia/en/2/2c/Middlesbrough_FC_crest.svg',
    'norwich': 'https://upload.wikimedia.org/wikipedia/en/8/8c/Norwich_City.svg',
    'coventry': 'https://upload.wikimedia.org/wikipedia/en/9/94/Coventry_City_FC_logo.svg',
    'west_brom': 'https://upload.wikimedia.org/wikipedia/en/8/8b/West_Bromwich_Albion.svg',
    'millwall': 'https://upload.wikimedia.org/wikipedia/en/8/8f/Millwall_F.C._logo.svg',
    'blackburn': 'https://upload.wikimedia.org/wikipedia/en/0/0f/Blackburn_Rovers.svg',
    'preston': 'https://upload.wikimedia.org/wikipedia/en/8/82/Preston_North_End_FC.svg',
    'bristol_city': 'https://upload.wikimedia.org/wikipedia/en/f/f5/Bristol_City_crest.svg',
    'cardiff': 'https://upload.wikimedia.org/wikipedia/en/3/3c/Cardiff_City_crest.svg',
    'swansea': 'https://upload.wikimedia.org/wikipedia/en/f/f9/Swansea_City_AFC_logo.svg',
    'stoke': 'https://upload.wikimedia.org/wikipedia/en/2/29/Stoke_City_FC.svg',
    'hull': 'https://upload.wikimedia.org/wikipedia/en/5/54/Hull_City_A.F.C._logo.svg',
    'qpr': 'https://upload.wikimedia.org/wikipedia/en/3/31/Queens_Park_Rangers_crest.svg',
    'sunderland': 'https://upload.wikimedia.org/wikipedia/en/7/77/Sunderland_AFC_logo.svg',
    'watford': 'https://upload.wikimedia.org/wikipedia/en/e/e2/Watford.svg',
    'plymouth': 'https://upload.wikimedia.org/wikipedia/en/a/a8/Plymouth_Argyle_F.C._logo.svg',
    'derby': 'https://upload.wikimedia.org/wikipedia/en/4/4a/Derby_County_crest.svg',
    'portsmouth': 'https://upload.wikimedia.org/wikipedia/en/3/38/Portsmouth_FC_crest.svg',
    'sheff_wed': 'https://upload.wikimedia.org/wikipedia/en/8/88/Sheffield_Wednesday_badge.svg',
    'oxford': 'https://upload.wikimedia.org/wikipedia/en/b/b4/Oxford_United_FC_logo.svg',
}

# League One Team Crests
LEAGUE_ONE_CRESTS = {
    'barnsley': 'https://upload.wikimedia.org/wikipedia/en/c/c9/Barnsley_FC.svg',
    'bolton': 'https://upload.wikimedia.org/wikipedia/en/8/82/Bolton_Wanderers_FC_logo.svg',
    'charlton': 'https://upload.wikimedia.org/wikipedia/en/5/5c/Charlton_Athletic.svg',
    'wycombe': 'https://upload.wikimedia.org/wikipedia/en/f/fb/Wycombe_Wanderers_FC_logo.svg',
    'peterborough': 'https://upload.wikimedia.org/wikipedia/en/4/45/Peterborough_United.svg',
    'lincoln': 'https://upload.wikimedia.org/wikipedia/en/4/40/Lincoln_City_FC.svg',
    'exeter': 'https://upload.wikimedia.org/wikipedia/en/e/e0/Exeter_City_FC.svg',
    'burton': 'https://upload.wikimedia.org/wikipedia/en/5/53/Burton_Albion_FC_logo.svg',
    'cambridge': 'https://upload.wikimedia.org/wikipedia/en/5/5c/Cambridge_United_FC.svg',
    'shrewsbury': 'https://upload.wikimedia.org/wikipedia/en/7/76/Shrewsbury_Town_F.C._logo.svg',
    'northampton': 'https://upload.wikimedia.org/wikipedia/en/e/e8/Northampton_Town_FC.svg',
    'stevenage': 'https://upload.wikimedia.org/wikipedia/en/9/9f/Stevenage_FC_logo.svg',
    'rotherham': 'https://upload.wikimedia.org/wikipedia/en/c/c0/Rotherham_United_FC.svg',
    'reading': 'https://upload.wikimedia.org/wikipedia/en/1/11/Reading_FC.svg',
    'bristol_rovers': 'https://upload.wikimedia.org/wikipedia/en/4/47/Bristol_Rovers_F.C._logo.svg',
    'leyton_orient': 'https://upload.wikimedia.org/wikipedia/en/5/50/Leyton_Orient_FC.svg',
    'blackpool': 'https://upload.wikimedia.org/wikipedia/en/d/df/Blackpool_FC_logo.svg',
    'mansfield': 'https://upload.wikimedia.org/wikipedia/en/d/d2/Mansfield_Town_FC.svg',
    'crawley': 'https://upload.wikimedia.org/wikipedia/en/6/6d/Crawley_Town_FC_logo.svg',
    'stockport': 'https://upload.wikimedia.org/wikipedia/en/f/fc/Stockport_County_FC_logo.svg',
    'wrexham': 'https://upload.wikimedia.org/wikipedia/en/1/1f/Wrexham_AFC.svg',
    'huddersfield': 'https://upload.wikimedia.org/wikipedia/en/7/7d/Huddersfield_Town_A.F.C._logo.svg',
    'birmingham': 'https://upload.wikimedia.org/wikipedia/en/6/68/Birmingham_City_FC_logo.svg',
    'wigan': 'https://upload.wikimedia.org/wikipedia/en/4/43/Wigan_Athletic.svg',
}

# Combine all crests
ALL_TEAM_CRESTS = {
    **PREMIER_LEAGUE_CRESTS,
    **CHAMPIONSHIP_CRESTS,
    **LEAGUE_ONE_CRESTS
}

# Competition Logos
COMPETITION_LOGOS = {
    'Premier League': 'https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg',
    'Championship': 'https://upload.wikimedia.org/wikipedia/en/8/8f/EFL_Championship.svg',
    'League One': 'https://upload.wikimedia.org/wikipedia/en/f/f4/EFL_League_One.svg',
    'FA Cup': 'https://upload.wikimedia.org/wikipedia/en/5/5e/The_Emirates_FA_Cup_Logo.svg',
    'EFL Cup': 'https://upload.wikimedia.org/wikipedia/en/8/80/Carabao_Cup_Logo.svg',
}

def get_team_crest_url(team_id: str) -> str:
    """
    Get crest URL for a team
    
    Args:
        team_id: Team identifier (e.g., 'man_city', 'arsenal')
    
    Returns:
        Direct URL to team crest image, or empty string if not found
    """
    return ALL_TEAM_CRESTS.get(team_id, '')

def get_competition_logo_url(competition: str) -> str:
    """
    Get logo URL for a competition
    
    Args:
        competition: Competition name (e.g., 'Premier League')
    
    Returns:
        Direct URL to competition logo, or empty string if not found
    """
    return COMPETITION_LOGOS.get(competition, '')

def get_all_available_teams():
    """Get list of all teams with available crests"""
    return list(ALL_TEAM_CRESTS.keys())

def get_crest_stats():
    """Get statistics about available crests"""
    return {
        'total': len(ALL_TEAM_CRESTS),
        'premier_league': len(PREMIER_LEAGUE_CRESTS),
        'championship': len(CHAMPIONSHIP_CRESTS),
        'league_one': len(LEAGUE_ONE_CRESTS),
        'competitions': len(COMPETITION_LOGOS)
    }

# Print stats on import
if __name__ == '__main__':
    stats = get_crest_stats()
    print(f"✅ Loaded {stats['total']} team crests:")
    print(f"   - Premier League: {stats['premier_league']}")
    print(f"   - Championship: {stats['championship']}")
    print(f"   - League One: {stats['league_one']}")
    print(f"   - Competitions: {stats['competitions']}")
