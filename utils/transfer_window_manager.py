"""
Transfer Window Manager - Handles transfer window logic and offer generation
FIXED VERSION - Now accepts bot parameter in generate_offers_for_player
"""

from database import db
import random
import config
from datetime import datetime
from utils.event_poster import post_transfer_news_to_channel

async def is_transfer_window_open(current_week: int) -> bool:
    """Check if we're in a transfer window"""
    return current_week in config.TRANSFER_WINDOW_WEEKS

async def check_and_update_transfer_window():
    """Check if transfer window status changed and update game state"""
    state = await db.get_game_state()
    current_week = state['current_week']
    is_open = await is_transfer_window_open(current_week)
    
    # Update game state if status changed
    if state.get('transfer_window_active') != is_open:
        await db.update_game_state(transfer_window_active=is_open)
        
        if is_open:
            print(f"Transfer window OPENED for Week {current_week}")
        else:
            print(f"Transfer window CLOSED after Week {current_week}")
            await expire_all_pending_offers()
            await cleanup_old_offers(current_week)
    
    return is_open

async def process_weekly_transfer_offers(bot=None):
    """
    FIRST WEEK ONLY: Called when transfer window opens
    Generates new offers for all active players
    """
    state = await db.get_game_state()
    current_week = state['current_week']
    
    # Only run during transfer windows
    if not await is_transfer_window_open(current_week):
        print(f"Week {current_week}: Transfer window closed, skipping offer generation")
        return
    
    print(f"\n=== Week {current_week}: Generating Initial Transfer Offers ===")
    
    # Get all active players
    async with db.pool.acquire() as conn:
        players = await conn.fetch("""
            SELECT user_id, player_name, overall_rating, potential, 
                   team_id, contract_wage, contract_years, age,
                   season_rating, season_goals
            FROM players
            WHERE retired = FALSE
        """)
    
    offers_generated = 0
    players_with_offers = 0
    
    for player_row in players:
        player = dict(player_row)
        user_id = player['user_id']
        
        # Generate 1-3 offers based on player quality
        num_offers = calculate_num_offers(player)
        
        if num_offers == 0:
            print(f"  {player['player_name']}: Not generating offers (rating too low or other factors)")
            continue
        
        # CRITICAL FIX: Pass bot parameter
        created_offers = await generate_offers_for_player(player, current_week, num_offers, bot=bot)
        
        if created_offers:
            offers_generated += len(created_offers)
            players_with_offers += 1
            print(f"  {player['player_name']}: Generated {len(created_offers)} offers")
            
            # Send notification to player
            if bot:
                await send_offer_notification(bot, user_id, len(created_offers))
        else:
            print(f"  {player['player_name']}: Failed to generate offers")
    
    print(f"\n=== Transfer Offers Complete ===")
    print(f"Generated {offers_generated} offers for {players_with_offers} players")
    
    return offers_generated

async def generate_offers_for_eligible_players(bot=None):
    """
    SUBSEQUENT WEEKS: Generate offers ONLY for players who:
    1. Have NO pending offers (declined all or never got any)
    2. Have NOT accepted a transfer this window
    """
    state = await db.get_game_state()
    current_week = state['current_week']
    current_window = get_current_transfer_window(current_week)
    
    print(f"\n=== Week {current_week}: Checking for Eligible Players ===")
    
    # Get all active players
    async with db.pool.acquire() as conn:
        all_players = await conn.fetch("""
            SELECT user_id, player_name, overall_rating, potential, 
                   team_id, contract_wage, contract_years, age,
                   season_rating, season_goals, last_transfer_window
            FROM players
            WHERE retired = FALSE
        """)
    
    offers_generated = 0
    players_with_offers = 0
    
    for player_row in all_players:
        player = dict(player_row)
        user_id = player['user_id']
        
        # SKIP if player already transferred this window
        if player.get('last_transfer_window') == current_window:
            continue
        
        # Check if player has pending offers
        pending_offers = await get_pending_offers(user_id)
        
        if pending_offers:
            # Player already has offers waiting - skip
            continue
        
        # Check if player ACCEPTED an offer this window
        async with db.pool.acquire() as conn:
            accepted_this_window = await conn.fetchrow("""
                SELECT offer_id FROM transfer_offers
                WHERE user_id = $1 
                AND status = 'accepted'
                AND offer_week >= $2
            """, user_id, min(config.TRANSFER_WINDOW_WEEKS[:3]) if current_window == 1 else min(config.TRANSFER_WINDOW_WEEKS[3:]))
        
        if accepted_this_window:
            # Player accepted a transfer this window - no more offers
            continue
        
        # ELIGIBLE: Generate new offers
        print(f"  ✅ {player['player_name']}: Eligible for new offers")
        
        # Generate 1-3 offers for this player
        num_offers = calculate_num_offers(player)
        
        if num_offers == 0:
            continue
        
        # CRITICAL FIX: Pass bot parameter
        created_offers = await generate_offers_for_player(player, current_week, num_offers, bot=bot)
        
        if created_offers:
            offers_generated += len(created_offers)
            players_with_offers += 1
            print(f"  💼 {player['player_name']}: Generated {len(created_offers)} new offers")
            
            # Send notification to player if bot is available
            if bot:
                await send_offer_notification(bot, user_id, len(created_offers))
    
    print(f"\n=== Eligible Player Offers Complete ===")
    print(f"Generated {offers_generated} offers for {players_with_offers} players")
    
    return offers_generated

def calculate_num_offers(player: dict) -> int:
    """
    Calculate how many offers a player should receive based on their attributes
    Returns 0-3
    """
    rating = player['overall_rating']
    potential = player['potential']
    age = player['age']
    season_rating = player.get('season_rating', 6.5)
    
    # Base number of offers
    if rating >= 80:
        base_offers = 3
    elif rating >= 75:
        base_offers = 3
    elif rating >= 70:
        base_offers = 2
    elif rating >= 65:
        base_offers = 2
    elif rating >= 60:
        base_offers = 1
    else:
        base_offers = 1
    
    # Bonus for high potential young players
    if potential >= 80 and age <= 23:
        base_offers = min(3, base_offers + 1)
    
    # Bonus for good form
    if season_rating >= 7.5:
        base_offers = min(3, base_offers + 1)
    
    # Penalty for poor form
    if season_rating < 6.0:
        base_offers = max(0, base_offers - 1)
    
    # Penalty for very old players
    if age >= 33:
        base_offers = max(0, base_offers - 1)
    
    # Add some randomness
    return max(0, base_offers + random.randint(-1, 0))

# CRITICAL FIX: Added bot=None parameter
async def generate_offers_for_player(player: dict, current_week: int, num_offers: int = 3, bot=None):
    """Generate transfer offers for a specific player"""
    
    rating = player['overall_rating']
    potential = player['potential']
    user_id = player['user_id']
    
    # Check for previous offers this window (for improved offers)
    async with db.pool.acquire() as conn:
        previous_offers = await conn.fetch(
            """SELECT * FROM transfer_offers 
               WHERE user_id = $1 AND offer_week >= $2 
               ORDER BY created_at DESC""",
            user_id, 
            current_week - 2
        )
        previous_offers = [dict(row) for row in previous_offers]
    
    interested_teams = []
    
    # Get teams from appropriate leagues based on player rating
    if rating >= 75 or potential >= 82:
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM teams WHERE league = $1 ORDER BY RANDOM() LIMIT 5",
                'Premier League'
            )
            interested_teams.extend([dict(row) for row in rows])
    
    if rating >= 65 or potential >= 72:
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM teams WHERE league = $1 ORDER BY RANDOM() LIMIT 5",
                'Championship'
            )
            interested_teams.extend([dict(row) for row in rows])
    
    if rating >= 55:
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM teams WHERE league = $1 ORDER BY RANDOM() LIMIT 5",
                'League One'
            )
            interested_teams.extend([dict(row) for row in rows])
    
    # Remove current team from interested teams
    interested_teams = [t for t in interested_teams if t['team_id'] != player['team_id']]
    
    if not interested_teams:
        print(f"    No interested teams found for {player['player_name']}")
        return []
    
    # Strategy: Mix of new offers and improved offers from rejected teams
    teams_to_offer = []
    rejected_team_ids = [o['team_id'] for o in previous_offers if o['status'] == 'rejected']
    
    # 40% chance per slot to make an improved offer from a previously rejected team
    for _ in range(num_offers):
        if rejected_team_ids and random.random() < 0.4:
            # Make an improved offer
            team_id = random.choice(rejected_team_ids)
            team = next((t for t in interested_teams if t['team_id'] == team_id), None)
            if team:
                prev_offer = next((o for o in previous_offers if o['team_id'] == team_id), None)
                if prev_offer:
                    team['is_improved'] = True
                    team['previous_offer_id'] = prev_offer['offer_id']
                    team['previous_wage'] = prev_offer['wage_offer']
                    teams_to_offer.append(team)
                    rejected_team_ids.remove(team_id)  # Don't offer from same team twice
        else:
            # Make a standard new offer
            available = [t for t in interested_teams if t not in teams_to_offer]
            if available:
                team = random.choice(available)
                team['is_improved'] = False
                teams_to_offer.append(team)
    
    # Always add current club renewal offer if contract is expiring
    if player['contract_years'] <= 1 and player['team_id'] != 'free_agent':
        current_team = await db.get_team(player['team_id'])
        if current_team:
            current_team['is_renewal'] = True
            current_team['is_improved'] = False
            teams_to_offer.append(current_team)
            print(f"    Added renewal offer from current club: {current_team['team_name']}")
    
    # Create offers in database
    created_offers = []
    async with db.pool.acquire() as conn:
        for team in teams_to_offer[:num_offers + 1]:  # +1 to allow for renewal offer
            # IMPROVED WAGE CALCULATION - exponential growth
            base_wage = (player['overall_rating'] ** 2) * 10
            
            # Performance bonus
            performance_bonus = 0
            if player.get('season_rating', 6.5) >= 7.5:
                performance_bonus = int(base_wage * 0.2)
            if player.get('season_goals', 0) >= 10:
                performance_bonus += int(base_wage * 0.15)
            
            # League wage multipliers
            if team['league'] == 'Premier League':
                wage_offer = int((base_wage + performance_bonus) * random.uniform(1.5, 2.5))
            elif team['league'] == 'Championship':
                wage_offer = int((base_wage + performance_bonus) * random.uniform(0.8, 1.2))
            elif team['league'] == 'League One':
                wage_offer = int((base_wage + performance_bonus) * random.uniform(0.4, 0.7))
            else:  # League Two
                wage_offer = int((base_wage + performance_bonus) * random.uniform(0.2, 0.4))
            
            # Ensure minimum wage
            wage_offer = max(wage_offer, 1000)
            
            # Handle special offer types
            if team.get('is_improved'):
                # Improved offers are 15-25% higher than previous
                wage_offer = int(team['previous_wage'] * random.uniform(1.15, 1.25))
                offer_type = 'improved'
                previous_offer_id = team['previous_offer_id']
            elif team.get('is_renewal'):
                # Renewal offers are 10-20% higher than current wage
                wage_offer = int(player['contract_wage'] * random.uniform(1.1, 1.2))
                offer_type = 'renewal'
                previous_offer_id = None
            else:
                offer_type = 'standard'
                previous_offer_id = None
            
            # Contract length (2-4 years, with young players getting longer contracts)
            if player['age'] <= 23:
                contract_length = random.randint(3, 4)
            elif player['age'] >= 32:
                contract_length = random.randint(1, 2)
            else:
                contract_length = random.randint(2, 4)
            
            # Insert offer into database
            result = await conn.fetchrow('''
                INSERT INTO transfer_offers (
                    user_id, team_id, wage_offer, contract_length,
                    offer_week, expires_week, offer_type, previous_offer_id,
                    performance_bonus, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING offer_id
            ''',
                user_id, team['team_id'], wage_offer, contract_length,
                current_week, current_week, offer_type, previous_offer_id,
                performance_bonus, 'pending'
            )
            
            created_offers.append({
                'offer_id': result['offer_id'],
                'team_id': team['team_id'],
                'team_name': team['team_name'],
                'wage_offer': wage_offer,
                'contract_length': contract_length,
                'offer_type': offer_type
            })
            
            print(f"    Created {offer_type} offer: {team['team_name']} - £{wage_offer:,}/wk")
    
    # CRITICAL FIX: Send notification if bot is available
    if bot and created_offers:
        await send_offer_notification(bot, user_id, len(created_offers))
    
    return created_offers

async def get_pending_offers(user_id: int):
    """Get all pending offers for a player"""
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT o.*, t.team_name, t.league 
               FROM transfer_offers o
               JOIN teams t ON o.team_id = t.team_id
               WHERE o.user_id = $1 AND o.status = 'pending'
               ORDER BY o.wage_offer DESC""",
            user_id
        )
        return [dict(row) for row in rows]

async def accept_transfer_offer(user_id: int, offer_id: int, bot=None):
    """Accept a transfer offer and update player"""
    async with db.pool.acquire() as conn:
        offer_row = await conn.fetchrow(
            "SELECT * FROM transfer_offers WHERE offer_id = $1 AND user_id = $2",
            offer_id, user_id
        )
        
        if not offer_row:
            return None, "Offer not found"
        
        offer = dict(offer_row)
        
        if offer['status'] != 'pending':
            return None, "Offer is no longer available"
        
        player = await db.get_player(user_id)
        new_team = await db.get_team(offer['team_id'])
        old_team = await db.get_team(player['team_id']) if player['team_id'] != 'free_agent' else None
        
        state = await db.get_game_state()
        current_window = get_current_transfer_window(state['current_week'])
        
        # Check if already transferred this window
        if player.get('last_transfer_window') == current_window:
            return None, "You've already transferred this window"
        
        # IMPROVED TRANSFER FEE CALCULATION
        if old_team and player['team_id'] != 'free_agent':
            base_fee = player['overall_rating'] * 100000
            age_modifier = 1.0
            if player['age'] < 23:
                age_modifier = 1.5
            elif player['age'] > 30:
                age_modifier = 0.6
            
            # Contract length affects fee
            contract_modifier = 1.0 + (player['contract_years'] * 0.1)
            
            transfer_fee = int(base_fee * age_modifier * contract_modifier * random.uniform(0.5, 1.5))
        else:
            transfer_fee = 0
        
        # Update player's team and contract
        await conn.execute('''
            UPDATE players 
            SET team_id = $1, league = $2, contract_wage = $3, contract_years = $4,
                last_transfer_window = $5, transfers_this_season = transfers_this_season + 1
            WHERE user_id = $6
        ''',
            offer['team_id'], new_team['league'], offer['wage_offer'], 
            offer['contract_length'], current_window, user_id
        )
        
        # Mark this offer as accepted
        await conn.execute(
            "UPDATE transfer_offers SET status = 'accepted' WHERE offer_id = $1",
            offer_id
        )
        
        # Reject all other pending offers
        await conn.execute(
            "UPDATE transfer_offers SET status = 'rejected' WHERE user_id = $1 AND offer_id != $2 AND status = 'pending'",
            user_id, offer_id
        )
        
        # Record transfer in history
        await conn.execute('''
            INSERT INTO transfers (user_id, from_team, to_team, fee, wage, contract_length, transfer_type)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''',
            user_id, player['team_id'], offer['team_id'], transfer_fee,
            offer['wage_offer'], offer['contract_length'],
            'free_transfer' if transfer_fee == 0 else 'transfer'
        )
        
        old_team_name = old_team['team_name'] if old_team else 'free agency'
        
        # Add news article
        await db.add_news(
            f"TRANSFER: {player['player_name']} joins {new_team['team_name']}!",
            f"{player['player_name']} completes move from {old_team_name} to {new_team['team_name']} "
            f"{'for £' + f'{transfer_fee:,}' if transfer_fee > 0 else 'on a free transfer'} on a {offer['contract_length']}-year deal.",
            "transfer_news",
            user_id,
            8,
            state['current_week']
        )
        
        result = {
            'player_name': player['player_name'],
            'old_team': old_team_name,
            'new_team': new_team['team_name'],
            'fee': transfer_fee,
            'wage': offer['wage_offer'],
            'contract_length': offer['contract_length']
        }
        
        # Post transfer news to all guilds
        if bot:
            transfer_info = {
                'player_name': player['player_name'],
                'from_team': old_team_name,
                'to_team': new_team['team_name'],
                'fee': transfer_fee,
                'wage': offer['wage_offer'],
                'contract_length': offer['contract_length']
            }
            
            for guild in bot.guilds:
                try:
                    await post_transfer_news_to_channel(bot, guild, transfer_info)
                except Exception as e:
                    print(f"Could not post transfer to {guild.name}: {e}")
        
        return result, None

async def reject_transfer_offer(user_id: int, offer_id: int):
    """Reject a single transfer offer"""
    async with db.pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE transfer_offers SET status = 'rejected' WHERE offer_id = $1 AND user_id = $2 AND status = 'pending'",
            offer_id, user_id
        )
        return result != "UPDATE 0"

async def reject_all_offers(user_id: int):
    """Reject all pending offers for a player"""
    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE transfer_offers SET status = 'rejected' WHERE user_id = $1 AND status = 'pending'",
            user_id
        )
    return True

async def expire_all_pending_offers():
    """Expire all pending offers at end of transfer window"""
    async with db.pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE transfer_offers SET status = 'expired' WHERE status = 'pending'"
        )
    print(f"All pending offers expired: {result}")

async def cleanup_old_offers(current_week: int):
    """Delete old transfer offers to prevent database bloat"""
    async with db.pool.acquire() as conn:
        result = await conn.execute(
            """DELETE FROM transfer_offers 
               WHERE offer_week < $1 AND status != 'accepted'""",
            current_week - 5
        )
    print(f"Cleaned up old transfer offers: {result}")

def get_current_transfer_window(week: int) -> int:
    """Get transfer window ID based on week number"""
    if week in config.TRANSFER_WINDOW_WEEKS[:3]:
        return 1  # Summer window
    elif week in config.TRANSFER_WINDOW_WEEKS[3:]:
        return 2  # Winter window
    return 0

async def send_offer_notification(bot, user_id: int, num_offers: int):
    """Send Discord DM notification about new offers"""
    try:
        user = await bot.fetch_user(user_id)
        if user:
            import discord
            embed = discord.Embed(
                title="📬 NEW TRANSFER OFFERS!",
                description=f"You have **{num_offers} new club offers** waiting for you!\n\n"
                           f"The transfer window is open. Use `/offers` to review them.",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="⏰ Offers Expire",
                value="At the end of this transfer window",
                inline=False
            )
            embed.add_field(
                name="⚡ Quick Actions",
                value="• `/offers` - View all offers\n"
                      "• `/player contract` - Check current contract",
                inline=False
            )
            embed.set_footer(text="Accept before window closes!")
            await user.send(embed=embed)
            print(f"✅ Sent offer notification to user {user_id}")
    except Exception as e:
        print(f"❌ Could not send notification to user {user_id}: {e}")

async def simulate_npc_transfers():
    """Simulate NPC player transfers between clubs during transfer windows"""
    
    print("\n=== Simulating NPC Transfers ===")
    
    # Get NPCs who might transfer (aged 18-33, not retired)
    async with db.pool.acquire() as conn:
        transfer_candidates = await conn.fetch("""
            SELECT n.*, t.league 
            FROM npc_players n
            LEFT JOIN teams t ON n.team_id = t.team_id
            WHERE n.retired = FALSE 
            AND n.age BETWEEN 18 AND 33
            AND n.overall_rating BETWEEN 55 AND 85
            AND n.team_id IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 20
        """)
    
    transfers_made = 0
    
    for candidate in transfer_candidates:
        # 25% chance to transfer
        if random.random() > 0.25:
            continue
        
        candidate = dict(candidate)
        current_league = candidate['league']
        rating = candidate['overall_rating']
        
        # Determine potential new leagues based on rating
        potential_leagues = []
        if rating >= 75:
            potential_leagues.append('Premier League')
        if rating >= 65:
            potential_leagues.append('Championship')
        if rating >= 55:
            potential_leagues.append('League One')
        
        # 50% chance of lateral move, 50% chance of up/down move
        if random.random() < 0.5 and current_league in potential_leagues:
            potential_leagues.remove(current_league)
        
        if not potential_leagues:
            continue
        
        target_league = random.choice(potential_leagues)
        
        # Find a random team in target league (not current team)
        async with db.pool.acquire() as conn:
            new_team = await conn.fetchrow("""
                SELECT team_id, team_name, league
                FROM teams
                WHERE league = $1 AND team_id != $2
                ORDER BY RANDOM()
                LIMIT 1
            """, target_league, candidate['team_id'])
        
        if not new_team:
            continue
        
        new_team = dict(new_team)
        
        # Calculate transfer fee
        base_fee = rating * 100000
        age_modifier = 1.0
        if candidate['age'] < 23:
            age_modifier = 1.3
        elif candidate['age'] > 30:
            age_modifier = 0.6
        
        fee = int(base_fee * age_modifier * random.uniform(0.3, 1.2))
        
        # Execute transfer
        async with db.pool.acquire() as conn:
            old_team = await conn.fetchrow(
                "SELECT team_name FROM teams WHERE team_id = $1",
                candidate['team_id']
            )
            
            await conn.execute("""
                UPDATE npc_players
                SET team_id = $1
                WHERE npc_id = $2
            """, new_team['team_id'], candidate['npc_id'])
            
            # Record in transfers table
            await conn.execute("""
                INSERT INTO transfers (
                    npc_id, from_team, to_team, fee, wage, 
                    contract_length, transfer_type
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, 
                candidate['npc_id'],
                candidate['team_id'],
                new_team['team_id'],
                fee,
                rating * 1000,
                random.randint(2, 4),
                'transfer' if fee > 0 else 'free_transfer'
            )
        
        # Add news
        old_team_name = old_team['team_name'] if old_team else 'Unknown'
        state = await db.get_game_state()
        await db.add_news(
            f"{candidate['player_name']} joins {new_team['team_name']}",
            f"{candidate['player_name']} ({rating} OVR) has transferred from {old_team_name} to {new_team['team_name']} "
            f"{'for £' + f'{fee:,}' if fee > 0 else 'on a free transfer'}.",
            "transfer_news",
            None,
            3,
            state['current_week']
        )
        
        transfers_made += 1
        print(f"  ✅ {candidate['player_name']} ({old_team_name} -> {new_team['team_name']}) £{fee:,}")
    
    print(f"=== Completed {transfers_made} NPC transfers ===\n")
    return transfers_made
