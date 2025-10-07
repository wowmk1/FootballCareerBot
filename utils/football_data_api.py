"""
Simple Crests Loader - No API Required
Uses static Wikipedia URLs stored in crests_database.py
"""

from utils.crests_database import (
    get_team_crest_url as get_crest,
    get_competition_logo_url as get_logo,
    get_crest_stats
)

async def cache_all_crests():
    """
    Initialize crest system (no API calls needed)
    Just prints confirmation that static crests are ready
    """
    stats = get_crest_stats()
    print(f"✅ Loaded {stats['total']} team crests (static)")
    print(f"   📊 Premier League: {stats['premier_league']} teams")
    print(f"   📊 Championship: {stats['championship']} teams")
    print(f"   📊 League One: {stats['league_one']} teams")
    print(f"   🏆 Competition logos: {stats['competitions']}")
    print(f"   🌐 Source: Wikimedia Commons (public domain)")

def get_team_crest_url(team_id: str) -> str:
    """
    Get team crest URL
    
    Args:
        team_id: Team ID (e.g., 'man_city', 'arsenal')
    
    Returns:
        Direct image URL or empty string
    """
    url = get_crest(team_id)
    if not url and team_id not in ['free_agent', 'retired']:
        print(f"⚠️ No crest for: {team_id}")
    return url

def get_competition_logo(competition: str) -> str:
    """
    Get competition logo URL
    
    Args:
        competition: Competition name (e.g., 'Premier League')
    
    Returns:
        Direct image URL or empty string
    """
    return get_logo(competition)

# Backwards compatibility
football_api = None

# For easy imports
__all__ = ['cache_all_crests', 'get_team_crest_url', 'get_competition_logo']
