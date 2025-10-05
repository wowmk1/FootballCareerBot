import os

# Discord Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
BOT_PREFIX = os.getenv('BOT_PREFIX', '/')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')

# Season Configuration
CURRENT_SEASON = "2027/28"
SEASON_TOTAL_WEEKS = 38
MATCHES_PER_WEEK = 3  # Mon, Wed, Sat

# Match Configuration
MATCH_WINDOW_HOURS = 2
MATCH_START_HOUR = 15  # 3PM EST (was 20:00)
MATCH_EVENTS_PER_GAME_MIN = 6  # Minimum key moments
MATCH_EVENTS_PER_GAME_MAX = 10  # Maximum key moments

# Player Configuration
STARTING_AGE = 18
RETIREMENT_AGE = 38  # Changed from 40
BASE_STAT_GAIN = 2
STREAK_BONUS_THRESHOLD = 7
STREAK_BONUS_AMOUNT = 1

# Training Configuration
TRAINING_COOLDOWN_HOURS = 24

# Transfer Configuration
TRANSFER_WINDOW_WEEKS = [4, 5, 6, 20, 21, 22]  # Two transfer windows per season
TRANSFER_OFFERS_PER_WINDOW = 3  # Number of offers a player receives

# Notification Configuration
NOTIFY_MATCH_WINDOW = True
NOTIFY_TRAINING_READY = True
NOTIFY_TRANSFER_OFFERS = True

print("✅ Config loaded successfully")
print(f"📊 Environment: production")
print(f"⚽ Matches per week: {MATCHES_PER_WEEK}")
print(f"🎲 Match events per game: {MATCH_EVENTS_PER_GAME_MIN}-{MATCH_EVENTS_PER_GAME_MAX}")
print(f"⏱️ Match window: {MATCH_WINDOW_HOURS} hours")
print(f"⏰ Match start time: {MATCH_START_HOUR}:00")
print(f"🏋️ Training cooldown: {TRAINING_COOLDOWN_HOURS}h")
print(f"👴 Retirement age: {RETIREMENT_AGE}")
