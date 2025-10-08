"""
Simple Crests Loader - No API Required
Uses static Wikipedia URLs stored in crests_database.py
FIXED VERSION - Ensures clean URLs
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
    Get team crest URL with better fallback handling
    FIXED: Returns clean string with no hidden characters
    """
    if not team_id or team_id in ['free_agent', 'retired', None]:
        return ""
    
    # Direct mapping first
    url = get_crest(team_id)

    # If not found, try converting team name format
    if not url:
        # Try underscore version (e.g., "man-city" -> "man_city")
        converted_id = team_id.replace('-', '_')
        url = get_crest(converted_id)

        if not url:
            print(f"⚠️ No crest mapping for: {team_id}")
            return ""

    # Force clean string and strip any whitespace/hidden chars
    clean_url = str(url).strip()
    
    return clean_url if clean_url else ""


def get_competition_logo(competition: str) -> str:
    """
    Get competition logo URL
    FIXED: Returns clean string
    """
    if not competition:
        return ""
    
    url = get_logo(competition)
    
    # Clean the URL
    clean_url = str(url).strip() if url else ""
    
    return clean_url


# Backwards compatibility
football_api = None

# For easy imports
__all__ = ['cache_all_crests', 'get_team_crest_url', 'get_competition_logo']
