"""
Improved Crests System with Better Error Handling and Validation
"""

from utils.crests_database import (
    get_team_crest_url as get_crest_from_db,
    get_competition_logo_url as get_logo_from_db,
    get_crest_stats,
    get_all_available_teams
)
import re


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
    
    # Verify some critical crests load properly
    test_teams = ['man_city', 'arsenal', 'oxford', 'leeds']
    failed = []
    for team_id in test_teams:
        url = get_team_crest_url(team_id)
        if not url or not _validate_url(url):
            failed.append(team_id)
    
    if failed:
        print(f"   ⚠️ WARNING: Failed to load crests for: {', '.join(failed)}")
    else:
        print(f"   ✅ All test crests validated successfully")


def _validate_url(url: str) -> bool:
    """Validate that a URL is properly formatted"""
    if not url:
        return False
    
    # Check for valid URL pattern
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))


def _clean_url(url: str) -> str:
    """Clean and validate URL string"""
    if not url:
        return ""
    
    # Remove any whitespace, newlines, or hidden characters
    cleaned = url.strip()
    cleaned = ''.join(char for char in cleaned if ord(char) < 128 or char.isalnum())
    
    # Ensure it starts with http
    if cleaned and not cleaned.startswith('http'):
        return ""
    
    return cleaned


def get_team_crest_url(team_id: str) -> str:
    """
    Get team crest URL with validation and error handling
    
    Args:
        team_id: Team identifier (e.g., 'man_city', 'arsenal', 'oxford')
    
    Returns:
        Clean, validated URL string or empty string
    """
    # Handle None or invalid input
    if not team_id or not isinstance(team_id, str):
        return ""
    
    # Special cases
    if team_id.lower() in ['free_agent', 'retired', 'none', '']:
        return ""
    
    # Clean the team_id
    team_id = team_id.lower().strip()
    
    # Try to get URL from database
    url = get_crest_from_db(team_id)
    
    # If not found, try common variations
    if not url:
        # Try with underscores replaced by dashes
        alt_id = team_id.replace('_', '-')
        url = get_crest_from_db(alt_id)
        
        if not url:
            # Try with dashes replaced by underscores
            alt_id = team_id.replace('-', '_')
            url = get_crest_from_db(alt_id)
    
    # Validate and clean URL
    if url:
        cleaned_url = _clean_url(url)
        if _validate_url(cleaned_url):
            return cleaned_url
        else:
            print(f"⚠️ Invalid crest URL for {team_id}: {url[:50]}")
            return ""
    
    # URL not found
    available_teams = get_all_available_teams()
    if team_id not in available_teams:
        print(f"⚠️ Team not in crest database: {team_id}")
        print(f"   Available teams: {', '.join(available_teams[:10])}...")
    
    return ""


def get_competition_logo(competition: str) -> str:
    """
    Get competition logo URL with validation
    
    Args:
        competition: Competition name (e.g., 'Premier League')
    
    Returns:
        Clean, validated URL string or empty string
    """
    if not competition or not isinstance(competition, str):
        return ""
    
    # Get URL from database
    url = get_logo_from_db(competition)
    
    # Validate and clean
    if url:
        cleaned_url = _clean_url(url)
        if _validate_url(cleaned_url):
            return cleaned_url
        else:
            print(f"⚠️ Invalid competition logo URL: {url[:50]}")
            return ""
    
    return ""


def debug_crest(team_id: str) -> dict:
    """
    Debug helper to get detailed crest information
    
    Args:
        team_id: Team identifier
    
    Returns:
        Dictionary with debug information
    """
    raw_url = get_crest_from_db(team_id)
    cleaned_url = _clean_url(raw_url) if raw_url else ""
    is_valid = _validate_url(cleaned_url)
    
    return {
        'team_id': team_id,
        'raw_url': raw_url,
        'cleaned_url': cleaned_url,
        'is_valid': is_valid,
        'url_length': len(cleaned_url) if cleaned_url else 0,
        'has_hidden_chars': raw_url != cleaned_url if raw_url else False
    }


# Backwards compatibility
football_api = None

# Easy imports
__all__ = [
    'cache_all_crests',
    'get_team_crest_url',
    'get_competition_logo',
    'debug_crest'
]
