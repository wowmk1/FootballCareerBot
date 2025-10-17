import os

# Discord Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
BOT_PREFIX = os.getenv('BOT_PREFIX', '/')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')

# Season Configuration
CURRENT_SEASON = "2027/28"
SEASON_TOTAL_WEEKS = 38
MATCHES_PER_WEEK = 1  # 1 real-life day = 1 game week (Mon/Wed/Sat)

# Match Configuration
MATCH_WINDOW_HOURS = 2
MATCH_START_HOUR = 15  # 3PM EST
MATCH_EVENTS_PER_GAME_MIN = 18  # Minimum key moments
MATCH_EVENTS_PER_GAME_MAX = 25  # Maximum key moments

# Player Configuration
STARTING_AGE = 18
RETIREMENT_AGE = 38
BASE_STAT_GAIN = 2
STREAK_BONUS_THRESHOLD = 7
STREAK_BONUS_AMOUNT = 1

# Training Configuration
TRAINING_COOLDOWN_HOURS = 24

# Transfer Configuration
TRANSFER_WINDOW_WEEKS = [15, 16, 17, 30, 31, 32]  # Two transfer windows per season
TRANSFER_OFFERS_PER_WINDOW = 3  # Number of offers a player receives

# Notification Configuration
NOTIFY_MATCH_WINDOW = True
NOTIFY_TRAINING_READY = True
NOTIFY_TRANSFER_OFFERS = True

# Training effectiveness by league (better facilities = better training)
TRAINING_EFFECTIVENESS_BY_LEAGUE = {
    'Premier League': 1.2,     # Better facilities = 20% bonus
    'Championship': 1.0,        # Standard
    'League One': 0.85,         # Worse facilities = 15% penalty
    'League Two': 0.7           # Much worse facilities
}

# ===== EUROPEAN COMPETITIONS =====
CHAMPIONS_LEAGUE_TEAMS = 32
EUROPA_LEAGUE_TEAMS = 32
CHAMPIONS_LEAGUE_MATCH_DAY = 2  # Wednesday (FIXED from 1)
EUROPA_LEAGUE_MATCH_DAY = 3     # Thursday
EUROPEAN_MATCH_START_HOUR = 15  # 3 PM

GROUP_STAGE_WEEKS = [3, 6, 9, 12, 18, 21]
KNOCKOUT_R16_WEEKS = [24, 27]
KNOCKOUT_QF_WEEKS = [30, 33]
KNOCKOUT_SF_WEEKS = [36, 39]
KNOCKOUT_FINAL_WEEK = 42

EUROPEAN_MATCH_WEEKS = GROUP_STAGE_WEEKS + KNOCKOUT_R16_WEEKS + KNOCKOUT_QF_WEEKS + KNOCKOUT_SF_WEEKS + [KNOCKOUT_FINAL_WEEK]

CL_QUALIFICATION_POSITIONS = {
    'Premier League': [1, 2, 3, 4],
    'Championship': [],
    'League One': []
}

EL_QUALIFICATION_POSITIONS = {
    'Premier League': [5, 6],
    'Championship': [],
    'League One': []
}

print("✅ Config loaded successfully")
print(f"📊 Environment: production")
print(f"⚽ Match schedule: Mon/Wed/Sat (1 game week per real day)")
print(f"🎲 Match events per game: {MATCH_EVENTS_PER_GAME_MIN}-{MATCH_EVENTS_PER_GAME_MAX}")
print(f"⏱️ Match window: {MATCH_WINDOW_HOURS} hours")
print(f"⏰ Match start time: {MATCH_START_HOUR}:00")
print(f"🏋️ Training cooldown: {TRAINING_COOLDOWN_HOURS}h")
print(f"👴 Retirement age: {RETIREMENT_AGE}")
print(f"🏆 European match weeks: {EUROPEAN_MATCH_WEEKS}")
