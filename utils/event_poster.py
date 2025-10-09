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
        
        from_team_name = transfer_info['from_team']
        to_team_name = transfer_info['to_team']
        
        # Determine transfer type
        if transfer_info['fee'] > 0:
            transfer_type = "💼 TRANSFER"
            color = discord.Color.blue()
        else:
            transfer_type = "🆓 FREE TRANSFER"
            color = discord.Color.green()
        
        embed = discord.Embed(
            title=f"{transfer_type} CONFIRMED",
            description=f"## {transfer_info['player_name']}\n**{from_team_name}** ➡️ **{to_team_name}**",
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
        from data.teams import ALL_TEAMS
        
        # Find the team_id from team name
        to_team_id = None
        for team in ALL_TEAMS:
            if team['team_name'] == to_team_name:
                to_team_id = team['team_id']
                break
        
        if to_team_id:
            to_crest = get_team_crest_url(to_team_id)
            if to_crest:
                embed.set_thumbnail(url=to_crest)
        
        await transfer_channel.send(embed=embed)
        print(f"✅ Posted transfer: {transfer_info['player_name']} to {to_team_name}")
        
    except Exception as e:
        print(f"❌ Error posting transfer news: {e}")


async def post_new_player_announcement(bot, guild, player_info):
    """Post new player joining announcement to transfer-news channel"""
    try:
        transfer_channel = discord.utils.get(guild.text_channels, name="transfer-news")
        if not transfer_channel:
            return
        
        embed = discord.Embed(
            title="🆕 NEW PLAYER DEBUT!",
            description=f"## {player_info['player_name']}\n**{player_info['user'].display_name}** joins **{player_info['to_team']}**",
            color=discord.Color.green()
        )
        
        # Player stats
        embed.add_field(
            name="📊 Player Profile",
            value=f"**Position:** {player_info['position']}\n"
                  f"**Age:** {player_info['age']}\n"
                  f"**Rating:** {player_info['overall']} OVR\n"
                  f"**Potential:** ⭐ {player_info['potential']} POT",
            inline=True
        )
        
        # Contract details
        embed.add_field(
            name="💼 Contract",
            value=f"**£{player_info['wage']:,}/week**\n"
                  f"**{player_info['contract_length']} years**\n"
                  f"*Free transfer*",
            inline=True
        )
        
        # Add team crest
        from utils.football_data_api import get_team_crest_url
        from data.teams import ALL_TEAMS
        
        # Find the team_id from team name
        to_team_id = None
        for team in ALL_TEAMS:
            if team['team_name'] == player_info['to_team']:
                to_team_id = team['team_id']
                break
        
        if to_team_id:
            to_crest = get_team_crest_url(to_team_id)
            if to_crest:
                embed.set_thumbnail(url=to_crest)
        
        # Add user avatar
        embed.set_author(
            name=f"{player_info['user'].display_name} creates their player!",
            icon_url=player_info['user'].display_avatar.url if player_info['user'].display_avatar else None
        )
        
        embed.set_footer(text=f"🎮 Use /start to create your own player!")
        
        await transfer_channel.send(embed=embed)
        print(f"✅ Posted new player announcement: {player_info['player_name']} to {transfer_channel.guild.name}")
        
    except Exception as e:
        print(f"❌ Error posting new player announcement: {e}")


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
