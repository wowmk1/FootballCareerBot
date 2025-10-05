import os

# Discord Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
BOT_PREFIX = os.getenv('BOT_PREFIX', '/')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')

# Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'football.db')

# Game Configuration
MATCHES_PER_WEEK = 3  # Monday, Wednesday, Saturday
TRAINING_COOLDOWN_HOURS = int(os.getenv('TRAINING_COOLDOWN_HOURS', '24'))
MAX_PLAYERS = int(os.getenv('MAX_PLAYERS', '100'))
CURRENT_SEASON = "2027/28"
SEASON_TOTAL_WEEKS = 38

# Player Configuration
RETIREMENT_AGE = 40
STARTING_AGE = 18

# Match Days Configuration
MATCH_WINDOW_HOURS = 2  # How long players have to play their matches
MATCH_START_HOUR = 20  # 8 PM (24-hour format)
MATCH_DAYS = [0, 2, 5]  # Monday=0, Wednesday=2, Saturday=5
MATCH_DAY_NAMES = {0: "Monday", 2: "Wednesday", 5: "Saturday"}

# DnD Match Configuration
MATCH_EVENTS_PER_GAME = 8  # Key moments per match
AUTO_ROLL_TIMEOUT = 10  # Seconds before auto-roll
MATCH_DURATION_MINUTES = 15  # Average match length
PLAYER_JOIN_WAIT_MINUTES = 5  # Wait time for opponent to join

# Difficulty Classes (DC) for actions
DC_EASY = 10
DC_MEDIUM = 15
DC_HARD = 20
DC_VERY_HARD = 25

# Action Types
ACTION_SHOOT = "shoot"
ACTION_PASS = "pass"
ACTION_DRIBBLE = "dribble"
ACTION_DEFEND = "defend"
ACTION_SAVE = "save"

# Training Configuration
BASE_STAT_GAIN = 2
STREAK_BONUS_THRESHOLD = 3
STREAK_BONUS_AMOUNT = 1
DECAY_START_DAYS = 4
DECAY_RATE = 1

# Environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')

# Validation
if not DISCORD_TOKEN:
    raise ValueError("❌ DISCORD_TOKEN not found! Set it in Railway variables.")

print("✅ Config loaded successfully")
print(f"📊 Environment: {ENVIRONMENT}")
print(f"⚽ Matches per week: {MATCHES_PER_WEEK}")
print(f"🎲 Match events per game: {MATCH_EVENTS_PER_GAME}")
print(f"⏱️ Match window: {MATCH_WINDOW_HOURS} hours")
print(f"⏰ Match start time: {MATCH_START_HOUR}:00")
print(f"🏋️ Training cooldown: {TRAINING_COOLDOWN_HOURS}h")
