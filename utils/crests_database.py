"""
Static Team Crests Database
REALISTIC VERSION - Only Premier League crests work reliably
Championship/League One will show league logo instead
"""

# Premier League - Official CDN (100% WORKING!)
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

# Championship - Empty for now (Discord doesn't support most CDNs)
# Users will see the league logo instead
CHAMPIONSHIP_CRESTS = {
    'leeds': '',
    'burnley': '',
    'sheff_united': '',
    'luton': '',
    'middlesbrough': '',
    'norwich': '',
    'coventry': '',
    'west_brom': '',
    'millwall': '',
    'blackburn': '',
    'preston': '',
    'bristol_city': '',
    'cardiff': '',
    'swansea': '',
    'stoke': '',
    'hull': '',
    'qpr': '',
    'sunderland': '',
    'watford': '',
    'plymouth': '',
    'derby': '',
    'portsmouth': '',
    'sheff_wed': '',
    'oxford': '',
}

# League One - Empty for now
LEAGUE_ONE_CRESTS = {
    'barnsley': '',
    'bolton': '',
    'charlton': '',
    'wycombe': '',
    'peterborough': '',
    'lincoln': '',
    'exeter': '',
    'burton': '',
    'cambridge': '',
    'shrewsbury': '',
    'northampton': '',
    'stevenage': '',
    'rotherham': '',
    'reading': '',
    'bristol_rovers': '',
    'leyton_orient': '',
    'blackpool': '',
    'mansfield': '',
    'crawley': '',
    'stockport': '',
    'wrexham': '',
    'huddersfield': '',
    'birmingham': '',
    'wigan': '',
}

# Combine all crests
ALL_TEAM_CRESTS = {
    **PREMIER_LEAGUE_CRESTS,
    **CHAMPIONSHIP_CRESTS,
    **LEAGUE_ONE_CRESTS
}

# Competition Logos - Use simple emoji/text fallback
COMPETITION_LOGOS = {
    'Premier League': 'https://resources.premierleague.com/premierleague/photo/2023/10/26/d9e3bc11-e0a9-46c1-ac28-b5d2fb09bf37/PL-Lion-Mono-Digital.png',
    'Championship': '',  # Will show text only
    'League One': '',
    'FA Cup': '',
    'EFL Cup': '',
}

def get_team_crest_url(team_id: str) -> str:
    """
    Get crest URL for a team
    Only Premier League teams have working crests
    
    Args:
        team_id: Team identifier (e.g., 'man_city', 'arsenal')
    
    Returns:
        Direct URL to team crest image, or empty string if not found
    """
    return ALL_TEAM_CRESTS.get(team_id, '')

def get_competition_logo_url(competition: str) -> str:
    """
    Get logo URL for a competition
    Only Premier League has working logo
    
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
    print(f"   - Premier League: {stats['premier_league']} (WORKING)")
    print(f"   - Championship: {stats['championship']} (disabled)")
    print(f"   - League One: {stats['league_one']} (disabled)")
    print(f"   ⚠️ Only Premier League crests work in Discord embeds")
