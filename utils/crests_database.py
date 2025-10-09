"""
Static Team Crests Database
Using GitHub CDN (luukhopman/football-logos) - Discord-compatible
These are official team logos hosted on GitHub
"""

# Base URL for GitHub raw content
GITHUB_BASE = "https://raw.githubusercontent.com/luukhopman/football-logos/main/logos"

# Premier League Team Crests - Official Premier League CDN
PREMIER_LEAGUE_CRESTS = {
    'arsenal': 'https://resources.premierleague.com/premierleague/badges/100/t3@2x.png',
    'aston_villa': 'https://resources.premierleague.com/premierleague/badges/100/t7@2x.png',
    'bournemouth': 'https://resources.premierleague.com/premierleague/badges/100/t91@2x.png',
    'brentford': 'https://resources.premierleague.com/premierleague/badges/100/t94@2x.png',
    'brighton': 'https://resources.premierleague.com/premierleague/badges/100/t36@2x.png',
    'chelsea': 'https://resources.premierleague.com/premierleague/badges/100/t8@2x.png',
    'crystal_palace': 'https://resources.premierleague.com/premierleague/badges/100/t31@2x.png',
    'everton': 'https://resources.premierleague.com/premierleague/badges/100/t11@2x.png',
    'fulham': 'https://resources.premierleague.com/premierleague/badges/100/t54@2x.png',
    'liverpool': 'https://resources.premierleague.com/premierleague/badges/100/t14@2x.png',
    'man_city': 'https://resources.premierleague.com/premierleague/badges/100/t43@2x.png',
    'man_united': 'https://resources.premierleague.com/premierleague/badges/100/t1@2x.png',
    'newcastle': 'https://resources.premierleague.com/premierleague/badges/100/t4@2x.png',
    'nottm_forest': 'https://resources.premierleague.com/premierleague/badges/100/t17@2x.png',
    'tottenham': 'https://resources.premierleague.com/premierleague/badges/100/t6@2x.png',
    'west_ham': 'https://resources.premierleague.com/premierleague/badges/100/t21@2x.png',
    'wolves': 'https://resources.premierleague.com/premierleague/badges/100/t39@2x.png',
    'leicester': 'https://resources.premierleague.com/premierleague/badges/100/t13@2x.png',
    'southampton': 'https://resources.premierleague.com/premierleague/badges/100/t20@2x.png',
    'ipswich': 'https://resources.premierleague.com/premierleague/badges/100/t40@2x.png',
}

# Championship - Using GitHub CDN (luukhopman/football-logos)
CHAMPIONSHIP_CRESTS = {
    'leeds': f'{GITHUB_BASE}/england-championship/Leeds%20United.png',
    'burnley': f'{GITHUB_BASE}/england-championship/Burnley.png',
    'sheff_united': f'{GITHUB_BASE}/england-championship/Sheffield%20United.png',
    'luton': f'{GITHUB_BASE}/england-championship/Luton%20Town.png',
    'middlesbrough': f'{GITHUB_BASE}/england-championship/Middlesbrough.png',
    'norwich': f'{GITHUB_BASE}/england-championship/Norwich%20City.png',
    'coventry': f'{GITHUB_BASE}/england-championship/Coventry%20City.png',
    'west_brom': f'{GITHUB_BASE}/england-championship/West%20Bromwich%20Albion.png',
    'millwall': f'{GITHUB_BASE}/england-championship/Millwall.png',
    'blackburn': f'{GITHUB_BASE}/england-championship/Blackburn%20Rovers.png',
    'preston': f'{GITHUB_BASE}/england-championship/Preston%20North%20End.png',
    'bristol_city': f'{GITHUB_BASE}/england-championship/Bristol%20City.png',
    'cardiff': f'{GITHUB_BASE}/england-championship/Cardiff%20City.png',
    'swansea': f'{GITHUB_BASE}/england-championship/Swansea%20City.png',
    'stoke': f'{GITHUB_BASE}/england-championship/Stoke%20City.png',
    'hull': f'{GITHUB_BASE}/england-championship/Hull%20City.png',
    'qpr': f'{GITHUB_BASE}/england-championship/Queens%20Park%20Rangers.png',
    'sunderland': f'{GITHUB_BASE}/england-championship/Sunderland.png',
    'watford': f'{GITHUB_BASE}/england-championship/Watford.png',
    'plymouth': f'{GITHUB_BASE}/england-championship/Plymouth%20Argyle.png',
    'derby': f'{GITHUB_BASE}/england-championship/Derby%20County.png',
    'portsmouth': f'{GITHUB_BASE}/england-championship/Portsmouth.png',
    'sheff_wed': f'{GITHUB_BASE}/england-championship/Sheffield%20Wednesday.png',
    'oxford': f'{GITHUB_BASE}/england-championship/Oxford%20United.png',
}

# League One - Using GitHub CDN (luukhopman/football-logos)
LEAGUE_ONE_CRESTS = {
    'barnsley': f'{GITHUB_BASE}/england-league-one/Barnsley.png',
    'bolton': f'{GITHUB_BASE}/england-league-one/Bolton%20Wanderers.png',
    'charlton': f'{GITHUB_BASE}/england-league-one/Charlton%20Athletic.png',
    'wycombe': f'{GITHUB_BASE}/england-league-one/Wycombe%20Wanderers.png',
    'peterborough': f'{GITHUB_BASE}/england-league-one/Peterborough%20United.png',
    'lincoln': f'{GITHUB_BASE}/england-league-one/Lincoln%20City.png',
    'exeter': f'{GITHUB_BASE}/england-league-one/Exeter%20City.png',
    'burton': f'{GITHUB_BASE}/england-league-one/Burton%20Albion.png',
    'cambridge': f'{GITHUB_BASE}/england-league-one/Cambridge%20United.png',
    'shrewsbury': f'{GITHUB_BASE}/england-league-one/Shrewsbury%20Town.png',
    'northampton': f'{GITHUB_BASE}/england-league-one/Northampton%20Town.png',
    'stevenage': f'{GITHUB_BASE}/england-league-one/Stevenage.png',
    'rotherham': f'{GITHUB_BASE}/england-league-one/Rotherham%20United.png',
    'reading': f'{GITHUB_BASE}/england-league-one/Reading.png',
    'bristol_rovers': f'{GITHUB_BASE}/england-league-one/Bristol%20Rovers.png',
    'leyton_orient': f'{GITHUB_BASE}/england-league-one/Leyton%20Orient.png',
    'blackpool': f'{GITHUB_BASE}/england-league-one/Blackpool.png',
    'mansfield': f'{GITHUB_BASE}/england-league-one/Mansfield%20Town.png',
    'crawley': f'{GITHUB_BASE}/england-league-one/Crawley%20Town.png',
    'stockport': f'{GITHUB_BASE}/england-league-one/Stockport%20County.png',
    'wrexham': f'{GITHUB_BASE}/england-league-one/Wrexham.png',
    'huddersfield': f'{GITHUB_BASE}/england-league-one/Huddersfield%20Town.png',
    'birmingham': f'{GITHUB_BASE}/england-league-one/Birmingham%20City.png',
    'wigan': f'{GITHUB_BASE}/england-league-one/Wigan%20Athletic.png',
}

# Combine all crests
ALL_TEAM_CRESTS = {
    **PREMIER_LEAGUE_CRESTS,
    **CHAMPIONSHIP_CRESTS,
    **LEAGUE_ONE_CRESTS
}

# Competition Logos
COMPETITION_LOGOS = {
    'Premier League': 'https://resources.premierleague.com/premierleague/photo/2023/10/26/d9e3bc11-e0a9-46c1-ac28-b5d2fb09bf37/PL-Lion-Mono-Digital.png',
    'Championship': 'https://media.api-sports.io/football/leagues/40.png',
    'League One': 'https://media.api-sports.io/football/leagues/41.png',
    'FA Cup': 'https://media.api-sports.io/football/leagues/45.png',
    'EFL Cup': 'https://media.api-sports.io/football/leagues/48.png',
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
