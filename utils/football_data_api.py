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
    384: 'millwall',
    59: 'blackburn',
    1081: 'preston',
    387: 'bristol_city',
    715: 'cardiff',
    72: 'swansea',
    70: 'stoke',
    322: 'hull',
    69: 'qpr',
    71: 'sunderland',
    346: 'watford',
    1081: 'plymouth',
    342: 'derby',
    1044: 'portsmouth',
    345: 'sheff_wed',
    334: 'oxford',
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
                        try:
                            error_text = await response.text()
                            print(f"Response: {error_text[:200]}")
                        except:
                            pass
                        return []
        except Exception as e:
            print(f"❌ Exception fetching teams: {e}")
            return []
    
    async def cache_team_crests(self):
        """Cache all team crests from Premier League and Championship"""
        
        if not API_KEY or API_KEY == 'YOUR_API_KEY_HERE':
            print("⚠️ FOOTBALL_DATA_API_KEY not set in environment variables")
            print("   Matches will work without crests")
            return False
        
        print("🔄 Fetching team crests from Football-Data.org...")
        
        teams_cached = 0
        
        # Fetch Premier League teams
        print("📥 Fetching Premier League teams...")
        pl_teams = await self.fetch_competition_teams(COMPETITIONS['PL'])
        
        for team in pl_teams:
            team_id = team.get('id')
            if team_id in TEAM_MAPPING:
                our_team_id = TEAM_MAPPING[team_id]
                crest_url = team.get('crest', '')
                
                self.cache['teams'][our_team_id] = {
                    'name': team.get('name'),
                    'crest': crest_url,
                    'short_name': team.get('shortName'),
                    'tla': team.get('tla')
                }
                print(f"  ✅ {team.get('name')} → {our_team_id}")
                teams_cached += 1
        
        # Fetch Championship teams
        print("📥 Fetching Championship teams...")
        champ_teams = await self.fetch_competition_teams(COMPETITIONS['ELC'])
        
        for team in champ_teams:
            team_id = team.get('id')
            if team_id in TEAM_MAPPING:
                our_team_id = TEAM_MAPPING[team_id]
                crest_url = team.get('crest', '')
                
                self.cache['teams'][our_team_id] = {
                    'name': team.get('name'),
                    'crest': crest_url,
                    'short_name': team.get('shortName'),
                    'tla': team.get('tla')
                }
                print(f"  ✅ {team.get('name')} → {our_team_id}")
                teams_cached += 1
        
        if teams_cached > 0:
            # Update cache timestamp
            self.cache['cached_at'] = datetime.now().isoformat()
            
            # Save to file
            self.save_cache()
            
            print(f"🎉 Successfully cached {teams_cached} team crests!")
            return True
        else:
            print("⚠️ No teams were cached - check API key and network connection")
            return False
    
    def get_team_crest(self, team_id):
        """Get cached crest URL for a team"""
        team_data = self.cache['teams'].get(team_id, {})
        crest_url = team_data.get('crest', '')
        
        # Some debugging
        if not crest_url and team_id not in ['free_agent', 'retired']:
            print(f"⚠️ No crest found for team: {team_id}")
        
        return crest_url
    
    def get_competition_logo(self, competition_code):
        """Get competition logo URL"""
        return self.cache['competitions'].get(competition_code, {}).get('logo', '')

# Global instance
football_api = FootballDataAPI()

async def cache_all_crests():
    """Cache all crests on bot startup"""
    try:
        # Check if API key is set
        if not API_KEY or API_KEY == 'YOUR_API_KEY_HERE':
            print("⚠️ Football-Data.org API key not set")
            print("   Set FOOTBALL_DATA_API_KEY environment variable in Railway")
            print("   Get free key at: https://www.football-data.org/")
            print("   Matches will work without crests")
            return
        
        # Check if cache is fresh
        cached_date = datetime.fromisoformat(football_api.cache.get('cached_at', '2020-01-01'))
        if datetime.now() - cached_date < timedelta(days=CACHE_DURATION_DAYS):
            print(f"✅ Using cached crests ({len(football_api.cache['teams'])} teams)")
            return
        
        # Fetch and cache
        success = await football_api.cache_team_crests()
        if success:
            print("✅ Team crests cached successfully")
        else:
            print("⚠️ Could not cache crests - bot will work without them")
    
    except Exception as e:
        print(f"⚠️ Error caching crests: {e}")
        print("   Bot will work without crests")

def get_team_crest_url(team_id):
    """Get crest URL for a team (use in embeds)"""
    return football_api.get_team_crest(team_id)
