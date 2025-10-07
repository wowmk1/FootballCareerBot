# Add this to bot.py or create a new utils/event_poster.py file

import discord
from database import db

async def post_match_result_to_channel(bot, guild, fixture, home_score, away_score):
    """Post match result to match-results channel"""
    try:
        results_channel = discord.utils.get(guild.text_channels, name="match-results")
        if not results_channel:
            return
        
        home_team = await db.get_team(fixture['home_team_id'])
        away_team = await db.get_team(fixture['away_team_id'])
        
        if not home_team or not away_team:
            return
        
        # Determine result emoji
        if home_score > away_score:
            result = "🟢 HOME WIN"
            color = discord.Color.green()
        elif away_score > home_score:
            result = "🔴 AWAY WIN"
            color = discord.Color.red()
        else:
            result = "🟡 DRAW"
            color = discord.Color.gold()
        
        embed = discord.Embed(
            title=f"{result} - Week {fixture['week_number']}",
            description=f"## {home_team['team_name']} **{home_score} - {away_score}** {away_team['team_name']}",
            color=color
        )
        
        embed.add_field(name="Competition", value=fixture['competition'], inline=True)
        embed.add_field(name="League", value=fixture['league'], inline=True)
        
        # Add team crests
        from utils.football_data_api import get_team_crest_url
        home_crest = get_team_crest_url(fixture['home_team_id'])
        away_crest = get_team_crest_url(fixture['away_team_id'])
        
        if home_crest:
            embed.set_thumbnail(url=home_crest)
        
        # Get player participants and their ratings
        async with db.pool.acquire() as conn:
            participants = await conn.fetch(
                """SELECT mp.*, p.player_name 
                   FROM match_participants mp
                   JOIN players p ON mp.user_id = p.user_id
                   WHERE mp.match_id IN (
                       SELECT match_id FROM active_matches WHERE fixture_id = $1
                   )
                   ORDER BY mp.match_rating DESC""",
                fixture['fixture_id']
            )
        
        if participants:
            ratings_text = ""
            for p in participants[:3]:
                emoji = "🌟" if p['match_rating'] >= 8 else "⭐" if p['match_rating'] >= 7 else "✅"
                ratings_text += f"{emoji} {p['player_name']}: **{p['match_rating']:.1f}/10**\n"
            
            embed.add_field(name="⭐ Player Ratings", value=ratings_text, inline=False)
        
        await results_channel.send(embed=embed)
        print(f"✅ Posted result: {home_team['team_name']} {home_score}-{away_score} {away_team['team_name']}")
        
    except Exception as e:
        print(f"❌ Error posting match result: {e}")


async def post_transfer_news_to_channel(bot, guild, transfer_info):
    """Post transfer news to transfer-news channel"""
    try:
        transfer_channel = discord.utils.get(guild.text_channels, name="transfer-news")
        if not transfer_channel:
            return
        
        from_team = await db.get_team(transfer_info['from_team']) if transfer_info['from_team'] != 'free_agent' else None
        to_team = await db.get_team(transfer_info['to_team'])
        
        from_name = from_team['team_name'] if from_team else "Free Agency"
        to_name = to_team['team_name'] if to_team else "Unknown"
        
        # Determine transfer type
        if transfer_info['fee'] > 0:
            transfer_type = "💼 TRANSFER"
            color = discord.Color.blue()
        else:
            transfer_type = "🆓 FREE TRANSFER"
            color = discord.Color.green()
        
        embed = discord.Embed(
            title=f"{transfer_type} CONFIRMED",
            description=f"## {transfer_info['player_name']}\n**{from_name}** ➡️ **{to_name}**",
            color=color
        )
        
        if transfer_info['fee'] > 0:
            embed.add_field(name="💰 Transfer Fee", value=f"**£{transfer_info['fee']:,}**", inline=True)
        
        embed.add_field(
            name="💼 Contract",
            value=f"£{transfer_info['wage']:,}/week\n{transfer_info['contract_length']} years",
            inline=True
        )
        
        # Add team crest
        from utils.football_data_api import get_team_crest_url
        to_crest = get_team_crest_url(transfer_info['to_team'])
        if to_crest:
            embed.set_thumbnail(url=to_crest)
        
        await transfer_channel.send(embed=embed)
        print(f"✅ Posted transfer: {transfer_info['player_name']} to {to_name}")
        
    except Exception as e:
        print(f"❌ Error posting transfer news: {e}")


async def post_weekly_news_digest(bot, guild):
    """Post weekly news digest to news-feed channel"""
    try:
        news_channel = discord.utils.get(guild.text_channels, name="news-feed")
        if not news_channel:
            return
        
        state = await db.get_game_state()
        current_week = state['current_week']
        
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM news 
                   WHERE week_number = $1 
                   ORDER BY importance DESC, created_at DESC 
                   LIMIT 10""",
                current_week
            )
            news_items = [dict(row) for row in rows]
        
        if not news_items:
            return
        
        embed = discord.Embed(
            title=f"📰 Week {current_week} News Digest",
            description=f"**Season {state['current_season']}**\nTop stories from this week",
            color=discord.Color.blue()
        )
        
        category_emojis = {
            'player_news': '⭐',
            'league_news': '🏆',
            'match_news': '⚽',
            'transfer_news': '💼',
            'injury_news': '🤕'
        }
        
        for news in news_items[:8]:
            emoji = category_emojis.get(news['category'], '📌')
            
            # Truncate long content
            content = news['content'][:200]
            if len(news['content']) > 200:
                content += "..."
            
            embed.add_field(
                name=f"{emoji} {news['headline']}",
                value=content,
                inline=False
            )
        
        embed.set_footer(text=f"Use /news for personalized feed")
        
        await news_channel.send(embed=embed)
        print(f"✅ Posted weekly news digest for Week {current_week}")
        
    except Exception as e:
        print(f"❌ Error posting news digest: {e}")


# Modify the match engine's end_match function to auto-post results
# Add this at the end of end_match in match_engine.py:

async def end_match_with_posting(self, match_id, fixture, channel, home_score, away_score, participants):
    """End match and post results to all servers"""
    # ... existing end_match code ...
    
    # After all the existing code, add:
    
    # Post to all guilds
    for guild in self.bot.guilds:
        try:
            await post_match_result_to_channel(self.bot, guild, fixture, home_score, away_score)
        except Exception as e:
            print(f"Could not post result to {guild.name}: {e}")


# Modify accept_transfer_offer in transfer_window_manager.py
# After successful transfer, add:

async def accept_transfer_with_posting(user_id, offer_id, bot):
    """Accept transfer and post to channels"""
    # ... existing accept logic ...
    
    # After successful transfer:
    transfer_info = {
        'player_name': result['player_name'],
        'from_team': result['old_team_id'],
        'to_team': result['new_team_id'],
        'fee': result['fee'],
        'wage': result['wage'],
        'contract_length': result['contract_length']
    }
    
    # Post to all guilds
    for guild in bot.guilds:
        try:
            await post_transfer_news_to_channel(bot, guild, transfer_info)
        except Exception as e:
            print(f"Could not post transfer to {guild.name}: {e}")


# Add this to season_manager.py in the open_match_window function
# Replace the existing weekly news posting with:

async def open_match_window(bot=None):
    """Open match window for current week"""
    # ... existing code ...
    
    # POST WEEKLY NEWS TO CHANNELS
    if bot:
        try:
            for guild in bot.guilds:
                await post_weekly_news_digest(bot, guild)
            print(f"✅ Posted weekly news to all servers")
        except Exception as e:
            print(f"⚠️ Could not post weekly news: {e}")


# INTEGRATION INSTRUCTIONS:
# 1. Add this file as utils/event_poster.py
# 2. Import in match_engine.py: from utils.event_poster import post_match_result_to_channel
# 3. Import in transfer_window_manager.py: from utils.event_poster import post_transfer_news_to_channel
# 4. Import in season_manager.py: from utils.event_poster import post_weekly_news_digest
# 5. Call the functions in the appropriate places as shown above
