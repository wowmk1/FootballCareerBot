"""
Football-Data.org API Integration
Now uses local crest cache to avoid API calls and rate limits
"""

import aiohttp
import json
import os
from datetime import datetime, timedelta

API_KEY = os.getenv('FOOTBALL_DATA_API_KEY', 'YOUR_API_KEY_HERE')
BASE_URL = 'https://api.football-data.org/v4'

# Cache file (for future API-fetched data if needed)
CACHE_FILE = 'data/crest_cache.json'
CACHE_DURATION_DAYS = 30


class FootballDataAPI:
    def __init__(self):
        self.cache = self.load_cache()
        self.last_request_time = None
        self.request_count = 0
    
    def load_cache(self):
        """Load cached crest URLs from file (legacy support)"""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    
                    # Check if cache is expired
                    cached_date = datetime.fromisoformat(data.get('cached_at', '2020-01-01'))
                    if datetime.now() - cached_date < timedelta(days=CACHE_DURATION_DAYS):
                        return data
        except:
            pass
        
        return {'teams': {}, 'competitions': {}, 'cached_at': datetime.now().isoformat()}
    
    def save_cache(self):
        """Save cache to file"""
        os.makedirs('data', exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def get_team_crest(self, team_id):
        """Get cached crest URL for a team (legacy method)"""
        team_data = self.cache['teams'].get(team_id, {})
        return team_data.get('crest', '')
    
    def get_competition_logo(self, competition_code):
        """Get competition logo URL (legacy method)"""
        return self.cache['competitions'].get(competition_code, {}).get('logo', '')


# Global instance
football_api = FootballDataAPI()


async def cache_all_crests():
    """
    Initialize crest system - now uses local cache
    No API calls needed!
    """
    try:
        from data.team_crests import get_all_cached_teams
        cached_count = len(get_all_cached_teams())
        print(f"✅ Using local crest cache ({cached_count} teams)")
        print(f"   All Championship clubs included!")
    except Exception as e:
        print(f"⚠️ Could not load crest cache: {e}")
        print("   Bot will work with placeholder crests")


def get_team_crest_url(team_id):
    """
    Get crest URL for a team (use in embeds)
    Uses local cache - no API calls!
    """
    try:
        from data.team_crests import get_team_crest_url as get_cached_crest
        return get_cached_crest(team_id)
    except Exception as e:
        print(f"⚠️ Error getting crest for {team_id}: {e}")
        # Fallback placeholder
        return f"https://ui-avatars.com/api/?name={team_id.replace('_', '+')}&background=0f3460&color=fff&size=128&bold=true"


def get_competition_logo_url(competition_name):
    """
    Get competition logo URL
    """
    try:
        from data.team_crests import get_competition_logo
        return get_competition_logo(competition_name)
    except:
        return ''
