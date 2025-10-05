import random

FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
    "Thomas", "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven",
    "Paul", "Andrew", "Joshua", "Kenneth", "George", "Kevin", "Brian", "Edward",
    "Ryan", "Jacob", "Gary", "Nicholas", "Eric", "Jonathan", "Stephen", "Larry",
    "Jack", "Harry", "Charlie", "Oliver", "Oscar", "Alfie", "Noah", "George",
    "Connor", "Lewis", "Jake", "Callum", "Ben", "Luke", "Alex", "Max", "Sam",
    "Adam", "Aaron", "Adrian", "Alan", "Albert", "Alexander", "Andre", "Angel",
    "Antonio", "Arthur", "Austin", "Benjamin", "Blake", "Brandon", "Brett", "Bruce",
    "Carlos", "Carl", "Chad", "Charles", "Christian", "Cody", "Cole", "Colin"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White",
    "Harris", "Clark", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Green", "Baker", "Adams", "Nelson", "Carter", "Mitchell",
    "Roberts", "Turner", "Phillips", "Campbell", "Parker", "Evans", "Edwards", "Collins",
    "Stewart", "Morris", "Murphy", "Cook", "Rogers", "Morgan", "Peterson", "Cooper",
    "Reed", "Bailey", "Bell", "Gomez", "Kelly", "Howard", "Ward", "Cox", "Diaz",
    "Richardson", "Wood", "Watson", "Brooks", "Bennett", "Gray", "James", "Reyes"
]

def generate_random_player_name():
    """Generate a random player name for regens"""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return f"{first} {last}"

def calculate_regen_rating(league: str, position: str):
    """Calculate rating for a regen player based on league"""
    if league == "Premier League":
        base = random.randint(70, 80)
    elif league == "Championship":
        base = random.randint(62, 72)
    else:  # League One
        base = random.randint(55, 65)
    
    if position == "GK":
        base += random.randint(-2, 2)
    elif position in ["ST", "W", "CAM"]:
        base += random.randint(-1, 3)
    
    return min(85, max(50, base))
