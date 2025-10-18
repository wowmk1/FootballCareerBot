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

# Match Configuration - DOMESTIC
MATCH_WINDOW_HOURS = 2
MATCH_START_HOUR = 15  # 3PM EST
MATCH_EVENTS_PER_GAME_MIN = 18
MATCH_EVENTS_PER_GAME_MAX = 25

# Match Configuration - EUROPEAN
EUROPEAN_MATCH_START_HOUR = 12  # 12PM EST (Noon)
EUROPEAN_MATCH_END_HOUR = 14    # 2PM EST
EUROPEAN_WINDOW_HOURS = 2

# Player Configuration
STARTING_AGE = 18
RETIREMENT_AGE = 38
BASE_STAT_GAIN = 2
STREAK_BONUS_THRESHOLD = 7
STREAK_BONUS_AMOUNT = 1

# Training Configuration
TRAINING_COOLDOWN_HOURS = 24

# Transfer Configuration
TRANSFER_WINDOW_WEEKS = [15, 16, 17, 30, 31, 32]
TRANSFER_OFFERS_PER_WINDOW = 3

# Notification Configuration
NOTIFY_MATCH_WINDOW = True
NOTIFY_TRAINING_READY = True
NOTIFY_TRANSFER_OFFERS = True

# Training effectiveness by league
TRAINING_EFFECTIVENESS_BY_LEAGUE = {
    'Premier League': 1.2,
    'Championship': 1.0,
    'League One': 0.85,
    'League Two': 0.7
}

# ===== EUROPEAN COMPETITIONS =====
CHAMPIONS_LEAGUE_TEAMS = 32
EUROPA_LEAGUE_TEAMS = 32

# European Competition Weeks (FIXED to fit within 38-week season)
GROUP_STAGE_WEEKS = [3, 6, 9, 12, 15, 18]       # 6 group stage matchdays (weeks 3-18)
KNOCKOUT_R16_WEEKS = [21, 24]                    # Round of 16 (2 legs, weeks 21-24)
KNOCKOUT_QF_WEEKS = [27, 30]                     # Quarter-Finals (2 legs, weeks 27-30)
KNOCKOUT_SF_WEEKS = [33, 36]                     # Semi-Finals (2 legs, weeks 33-36)
KNOCKOUT_FINAL_WEEK = 38                         # Final (single match, week 38 - LAST WEEK!)

# All European match weeks combined
EUROPEAN_MATCH_WEEKS = GROUP_STAGE_WEEKS + KNOCKOUT_R16_WEEKS + KNOCKOUT_QF_WEEKS + KNOCKOUT_SF_WEEKS + [KNOCKOUT_FINAL_WEEK]

# Qualification positions
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
print(f"🏆 European windows: 12-2 PM on Mon/Wed/Sat during European weeks")
print(f"⚽ Domestic windows: 3-5 PM on Mon/Wed/Sat (always)")
print(f"🎲 Match events per game: {MATCH_EVENTS_PER_GAME_MIN}-{MATCH_EVENTS_PER_GAME_MAX}")
print(f"⏱️ Match window: {MATCH_WINDOW_HOURS} hours")
print(f"⏰ Domestic start time: {MATCH_START_HOUR}:00")
print(f"⏰ European start time: {EUROPEAN_MATCH_START_HOUR}:00")
print(f"🏋️ Training cooldown: {TRAINING_COOLDOWN_HOURS}h")
print(f"👴 Retirement age: {RETIREMENT_AGE}")
print(f"🏆 European match weeks: {EUROPEAN_MATCH_WEEKS}")
print(f"🏆 CL/EL Final: Week {KNOCKOUT_FINAL_WEEK} (final week of season!)")
