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

print("✅ Config loaded successfully")
print(f"📊 Environment: production")
print(f"⚽ Match schedule: Mon/Wed/Sat (1 game week per real day)")
print(f"🎲 Match events per game: {MATCH_EVENTS_PER_GAME_MIN}-{MATCH_EVENTS_PER_GAME_MAX}")
print(f"⏱️ Match window: {MATCH_WINDOW_HOURS} hours")
print(f"⏰ Match start time: {MATCH_START_HOUR}:00")
print(f"🏋️ Training cooldown: {TRAINING_COOLDOWN_HOURS}h")
print(f"👴 Retirement age: {RETIREMENT_AGE}")

# Training effectiveness by league (better facilities = better training)
TRAINING_EFFECTIVENESS_BY_LEAGUE = {
    'Premier League': 1.2,     # Better facilities = 20% bonus
    'Championship': 1.0,        # Standard
    'League One': 0.85,         # Worse facilities = 15% penalty
    'League Two': 0.7           # Much worse facilities
}
