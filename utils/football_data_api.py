"""
Football-Data.org API Integration - FIXED VERSION
Caches team crests and competition logos
Free tier: 10 calls per minute
"""

import aiohttp
import json
import os
from datetime import datetime, timedelta

# Get API key from environment
API_KEY = os.getenv('FOOTBALL_DATA_API_KEY')

BASE_URL = 'https://api.football-data.org/v4'

# Cache file
CACHE_FILE = 'data/crest_cache.json'
CACHE_DURATION_DAYS = 30

# Team ID mapping (football-data.org ID -> our team_id)
TEAM_MAPPING = {
    # Premier League
    57: 'arsenal',
    58: 'aston_villa',
    1044: 'bournemouth',
    402: 'brentford',
    397: 'brighton',
    61: 'chelsea',
    354: 'crystal_palace',
    62: 'everton',
    63: 'fulham',
    64: 'liverpool',
    65: 'man_city',
    66: 'man_united',
    67: 'newcastle',
    351: 'nottm_forest',
    73: 'tottenham',
    563: 'west_ham',
    76: 'wolves',
    338: 'leicester',
    340: 'southampton',
    349: 'ipswich',
    
    # Championship
    341: 'leeds',
    328: 'burnley',
    356: 'sheff_united',
    389: 'luton',
    343: 'middlesbrough',
    68: 'norwich',
    1076: 'coventry',
    74: 'west_brom',
    # Add more as needed
}

# Competition IDs
COMPETITIONS = {
    'PL': 2021,  # Premier League
    'ELC': 2016,  # Championship
}

class FootballDataAPI:
    def __init__(self):
        self.cache = self.load_cache()
        self.last_request_time = None
        self.request_count = 0
    
    def load_cache(self):
        """Load cached crest URLs"""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    
                    # Check if cache is expired
                    cached_date = datetime.fromisoformat(data.get('cached_at', '2020-01-01'))
                    if datetime.now() - cached_date < timedelta(days=CACHE_DURATION_DAYS):
                        print(f"✅ Loaded {len(data.get('teams', {}))} cached team crests")
                        return data
        except Exception as e:
            print(f"⚠️ Could not load cache: {e}")
        
        return {'teams': {}, 'competitions': {}, 'cached_at': datetime.now().isoformat()}
    
    def save_cache(self):
        """Save cache to file"""
        try:
            os.makedirs('data', exist_ok=True)
            with open(CACHE_FILE, 'w') as f:
                json.dump(self.cache, f, indent=2)
            print(f"✅ Saved cache with {len(self.cache['teams'])} teams")
        except Exception as e:
            print(f"⚠️ Could not save cache: {e}")
    
    async def rate_limit(self):
        """Enforce rate limiting (10 requests per minute)"""
        now = datetime.now()
        
        if self.last_request_time:
            time_diff = (now - self.last_request_time).total_seconds()
            
            # Reset counter after 60 seconds
            if time_diff >= 60:
                self.request_count = 0
                self.last_request_time = now
            elif self.request_count >= 10:
                # Wait for the minute to complete
                import asyncio
                wait_time = 60 - time_diff
                print(f"Rate limit reached, waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                self.request_count = 0
        
        self.last_request_time = datetime.now()
        self.request_count += 1
    
    async def fetch_competition_teams(self, competition_id):
        """Fetch all teams from a competition"""
        
        # Check if API key is available
        if not API_KEY or API_KEY == 'YOUR_API_KEY_HERE':
            print("⚠️ No API key configured for Football-Data.org")
            return []
        
        await self.rate_limit()
        
        headers = {'X-Auth-Token': API_KEY}
        url = f"{BASE_URL}/competitions/{competition_id}/teams"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        teams = data.get('teams', [])
                        print(f"✅ Fetched {len(teams)} teams from competition {competition_id}")
                        return teams
                    else:
                        print(f"❌ Error fetching teams: HTTP {response.status}")
