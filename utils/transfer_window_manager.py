"""
Transfer Window Manager - Handles transfer window logic and offer generation
Place this file in: utils/transfer_window_manager.py
"""

from database import db
import random
import config
from datetime import datetime

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
            print(f"🔓 Transfer window OPENED for Week {current_week}")
            await generate_weekly_offers_for_all_players()
        else:
            print(f"🔒 Transfer window CLOSED after Week {current_week}")
            await expire_all_pending_offers()
    
    return is_open

async def generate_weekly_offers_for_all_players():
    """Generate new offers for all active players at start of week"""
    async with db.pool.acquire() as conn:
        players = await conn.fetch(
            "SELECT * FROM players WHERE retired = FALSE AND team_id != 'free_agent'"
        )
    
    state = await db.get_game_state()
    current_week = state['current_week']
    
    for player_row in players:
        player = dict(player_row)
        
        # Skip if player already transferred this window
        if player.get('last_transfer_window') == get_current_transfer_window(current_week):
            continue
        
        # Generate 2-4 offers
        num_offers = random.randint(2, 4)
        await generate_offers_for_player(player, current_week, num_offers)
    
    print(f"✅ Generated weekly offers for {len(players)} players")

async def generate_offers_for_player(player: dict, current_week: int, num_offers: int = 3):
    """Generate transfer offers for a specific player"""
    
    rating = player['overall_rating']
    potential = player['potential']
    user_id = player['user_id']
    
    # Check for previous offers this window
    async with db.pool.acquire() as conn:
        previous_offers = await conn.fetch(
            """SELECT * FROM transfer_offers 
               WHERE user_id = $1 AND offer_week >= $2 
               ORDER BY created_at DESC""",
            user_id, 
            current_week - 2  # Look back 2 weeks in current window
        )
        previous_offers = [dict(row) for row in previous_offers]
    
    interested_teams = []
    
    # Get teams from appropriate leagues
    if rating >= 75 or potential >= 82:
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM teams WHERE league = $1 ORDER BY RANDOM() LIMIT 4",
                'Premier League'
            )
            interested_teams.extend([dict(row) for row in rows])
    
    if rating >= 65 or potential >= 72:
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM teams WHERE league = $1 ORDER BY RANDOM() LIMIT 4",
                'Championship'
            )
            interested_teams.extend([dict(row) for row in rows])
    
    if rating >= 55:
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM teams WHERE league = $1 ORDER BY RANDOM() LIMIT 4",
                'League One'
            )
            interested_teams.extend([dict(row) for row in rows])
    
    # Remove current team
    interested_teams = [t for t in interested_teams if t['team_id'] != player['team_id']]
    
    if not interested_teams:
        return []
    
    # Mix: 40% chance to re-offer from previously rejected teams
    teams_to_offer = []
    rejected_team_ids = [o['team_id'] for o in previous_offers if o['status'] == 'rejected']
    
    for _ in range(num_offers):
        if rejected_team_ids and random.random() < 0.4:
            # Return with improved offer
            team_id = random.choice(rejected_team_ids)
            team = next((t for t in interested_teams if t['team_id'] == team_id), None)
            if team:
                # Find previous offer
                prev_offer = next((o for o in previous_offers if o['team_id'] == team_id), None)
                if prev_offer:
                    team['is_improved'] = True
                    team['previous_offer_id'] = prev_offer['offer_id']
                    team['previous_wage'] = prev_offer['wage_offer']
                teams_to_offer.append(team)
        else:
            # New team
            available = [t for t in interested_teams if t not in teams_to_offer]
            if available:
                team = random.choice(available)
                team['is_improved'] = False
                teams_to_offer.append(team)
    
    # Add current club renewal offer if contract expiring
    if player['contract_years'] <= 1:
        current_team = await db.get_team(player['team_id'])
        if current_team:
            current_team['is_renewal'] = True
            current_team['is_improved'] = False
            teams_to_offer.append(current_team)
    
    # Create offers in database
    created_offers = []
    async with db.pool.acquire() as conn:
        for team in teams_to_offer[:num_offers + 1]:  # +1 for potential renewal
            base_wage = player['overall_rating'] * 1000
            
            # Performance bonus
            performance_bonus = 0
            if player['season_rating'] >= 7.5:
                performance_bonus = int(base_wage * 0.2)
            if player['season_goals'] >= 10:
                performance_bonus += int(base_wage * 0.15)
            
            # League wage multipliers
            if team['league'] == 'Premier League':
                wage_offer = int((base_wage + performance_bonus) * random.uniform(1.5, 2.5))
            elif team['league'] == 'Championship':
                wage_offer = int((base_wage + performance_bonus) * random.uniform(0.8, 1.2))
            else:
                wage_offer = int((base_wage + performance_bonus) * random.uniform(0.4, 0.7))
            
            # Improved offer bonus
            if team.get('is_improved'):
                wage_offer = int(team['previous_wage'] * 1.15)  # 15% increase
                offer_type = 'improved'
                previous_offer_id = team['previous_offer_id']
            elif team.get('is_renewal'):
                wage_offer = int(player['contract_wage'] * 1.1)  # 10% raise
                offer_type = 'renewal'
                previous_offer_id = None
            else:
                offer_type = 'standard'
                previous_offer_id = None
            
            contract_length = random.randint(2, 4)
            
            # Create offer
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

async def accept_transfer_offer(user_id: int, offer_id: int):
    """Accept a transfer offer and update player"""
    async with db.pool.acquire() as conn:
        # Get offer details
        offer_row = await conn.fetchrow(
            "SELECT * FROM transfer_offers WHERE offer_id = $1 AND user_id = $2",
            offer_id, user_id
        )
        
        if not offer_row:
            return None, "Offer not found"
        
        offer = dict(offer_row)
        
        if offer['status'] != 'pending':
            return None, "Offer is no longer available"
        
        # Get player and team info
        player = await db.get_player(user_id)
        new_team = await db.get_team(offer['team_id'])
        old_team = await db.get_team(player['team_id']) if player['team_id'] != 'free_agent' else None
        
        # Check if player already transferred this window
        state = await db.get_game_state()
        current_window = get_current_transfer_window(state['current_week'])
        
        if player.get('last_transfer_window') == current_window:
            return None, "You've already transferred this window"
        
        # Calculate transfer fee
        if old_team and player['team_id'] != 'free_agent':
            base_fee = player['overall_rating'] * 1000000
            transfer_fee = int(base_fee * random.uniform(0.5, 1.5))
        else:
            transfer_fee = 0
        
        # Update player
        await conn.execute('''
            UPDATE players 
            SET team_id = $1, league = $2, contract_wage = $3, contract_years = $4,
                last_transfer_window = $5, transfers_this_season = transfers_this_season + 1
            WHERE user_id = $6
        ''',
            offer['team_id'], new_team['league'], offer['wage_offer'], 
            offer['contract_length'], current_window, user_id
        )
        
        # Mark offer as accepted
        await conn.execute(
            "UPDATE transfer_offers SET status = 'accepted' WHERE offer_id = $1",
            offer_id
        )
        
        # Reject all other pending offers for this player
        await conn.execute(
            "UPDATE transfer_offers SET status = 'rejected' WHERE user_id = $1 AND offer_id != $2 AND status = 'pending'",
            user_id, offer_id
        )
        
        # Record transfer in transfers table
        await conn.execute('''
            INSERT INTO transfers (user_id, from_team, to_team, fee, wage, contract_length, transfer_type)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''',
            user_id, player['team_id'], offer['team_id'], transfer_fee,
            offer['wage_offer'], offer['contract_length'],
            'free_transfer' if transfer_fee == 0 else 'transfer'
        )
        
        # Add news
        old_team_name = old_team['team_name'] if old_team else 'free agency'
        
        await db.add_news(
            f"TRANSFER: {player['player_name']} joins {new_team['team_name']}!",
            f"{player['player_name']} completes move from {old_team_name} to {new_team['team_name']} "
            f"{'for £' + f'{transfer_fee:,}' if transfer_fee > 0 else ''}on a {offer['contract_length']}-year deal.",
            "transfer_news",
            user_id,
            8,
            state['current_week']
        )
        
        return {
            'player_name': player['player_name'],
            'old_team': old_team_name,
            'new_team': new_team['team_name'],
            'fee': transfer_fee,
            'wage': offer['wage_offer'],
            'contract_length': offer['contract_length']
        }, None

async def reject_transfer_offer(user_id: int, offer_id: int):
    """Reject a single transfer offer"""
    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE transfer_offers SET status = 'rejected' WHERE offer_id = $1 AND user_id = $2",
            offer_id, user_id
        )
    return True

async def reject_all_offers(user_id: int):
    """Reject all pending offers for a player"""
    async with db.pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE transfer_offers SET status = 'rejected' WHERE user_id = $1 AND status = 'pending'",
            user_id
        )
    return True

async def expire_all_pending_offers():
    """Expire all pending offers at end of transfer window"""
    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE transfer_offers SET status = 'expired' WHERE status = 'pending'"
        )
    print("✅ All pending offers expired")

def get_current_transfer_window(week: int) -> int:
    """Get transfer window ID based on week number"""
    if week in config.TRANSFER_WINDOW_WEEKS[:3]:  # Weeks 4-6
        return 1  # January window
    elif week in config.TRANSFER_WINDOW_WEEKS[3:]:  # Weeks 20-22
        return 2  # Summer window
    return 0  # No window

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
                value="At the end of this week",
                inline=False
            )
            embed.set_footer(text="Use /offers to view • /accept_offer to sign • /reject_all to decline")
            await user.send(embed=embed)
            print(f"✅ Sent offer notification to user {user_id}")
    except Exception as e:
        print(f"❌ Could not send notification to user {user_id}: {e}")
