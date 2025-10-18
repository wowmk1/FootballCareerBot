"""
Event Poster - Posts game events to Discord channels
"""
import discord
from database import db
import config


async def post_transfer_news_to_channel(bot, guild, transfer_info):
    """
    Post a transfer announcement to the transfer-news channel
    
    Args:
        bot: Discord bot instance
        guild: Discord guild
        transfer_info: Dict with keys: player_name, from_team, to_team, fee, wage, contract_length
    """
    try:
        # Find transfer-news channel, fallback to general
        news_channel = discord.utils.get(guild.text_channels, name="transfer-news")
        if not news_channel:
            news_channel = discord.utils.get(guild.text_channels, name="general")
        
        if not news_channel:
            print(f"  ❌ No suitable channel found in {guild.name}")
            return
        
        # Determine if this is a new player announcement
        is_new_player = transfer_info.get('is_new_player', False)
        
        if is_new_player:
            # New player joining the game
            embed = discord.Embed(
                title="🆕 NEW PLAYER JOINS!",
                description=f"**{transfer_info['player_name']}** has entered the league!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📋 Player Details",
                value=f"**Position:** {transfer_info.get('position', 'Unknown')}\n"
                      f"**Age:** {transfer_info.get('age', 18)}\n"
                      f"**Rating:** {transfer_info.get('overall', 'N/A')} OVR → ⭐ {transfer_info.get('potential', 'N/A')} POT",
                inline=True
            )
            
            embed.add_field(
                name="⚽ First Club",
                value=f"**{transfer_info['to_team']}**\n"
                      f"£{transfer_info['wage']:,}/week\n"
                      f"{transfer_info['contract_length']} year contract",
                inline=True
            )
            
            # Mention the user if provided
            if transfer_info.get('user'):
                embed.set_footer(text=f"Welcome {transfer_info['user'].name}!")
            
        else:
            # Regular transfer
            embed = discord.Embed(
                title="💼 TRANSFER CONFIRMED",
                description=f"**{transfer_info['player_name']}** is on the move!",
                color=discord.Color.gold()
            )
            
            transfer_type = "Free Transfer" if transfer_info['fee'] == 0 else f"£{transfer_info['fee']:,}"
            
            embed.add_field(
                name="📋 Transfer Details",
                value=f"**From:** {transfer_info['from_team']}\n"
                      f"**To:** {transfer_info['to_team']}\n"
                      f"**Fee:** {transfer_type}",
                inline=False
            )
            
            embed.add_field(
                name="💰 Contract",
                value=f"**Wage:** £{transfer_info['wage']:,}/week\n"
                      f"**Length:** {transfer_info['contract_length']} years",
                inline=False
            )
        
        await news_channel.send(embed=embed)
        print(f"  ✅ Posted transfer news to {guild.name}")
        
    except Exception as e:
        print(f"  ❌ Error posting transfer news to {guild.name}: {e}")
        import traceback
        traceback.print_exc()


async def post_new_player_announcement(bot, guild, transfer_info):
    """
    Post announcement for a brand new player joining the game
    This is a wrapper that calls post_transfer_news_to_channel with is_new_player flag
    """
    transfer_info['is_new_player'] = True
    await post_transfer_news_to_channel(bot, guild, transfer_info)


async def post_match_result_to_channel(bot, guild, fixture, home_score, away_score):
    """
    Post match result to match-results channel
    
    Args:
        bot: Discord bot instance
        guild: Discord guild
        fixture: Fixture dict with home_team_id, away_team_id, week_number
        home_score: Home team score
        away_score: Away team score
    """
    try:
        # Find match-results channel, fallback to general
        results_channel = discord.utils.get(guild.text_channels, name="match-results")
        if not results_channel:
            results_channel = discord.utils.get(guild.text_channels, name="general")
        
        if not results_channel:
            print(f"  ❌ No suitable channel found in {guild.name}")
            return
        
        # Get team info
        home_team = await db.get_team(fixture['home_team_id'])
        away_team = await db.get_team(fixture['away_team_id'])
        
        if not home_team or not away_team:
            return
        
        # Determine result emoji
        if home_score > away_score:
            result_emoji = "🏆"
            result_text = f"**{home_team['team_name']}** wins!"
        elif away_score > home_score:
            result_emoji = "🏆"
            result_text = f"**{away_team['team_name']}** wins!"
        else:
            result_emoji = "🤝"
            result_text = "Draw!"
        
        embed = discord.Embed(
            title=f"{result_emoji} FULL TIME",
            description=f"## {home_team['team_name']} {home_score} - {away_score} {away_team['team_name']}\n\n{result_text}",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📊 Match Info",
            value=f"**Competition:** {fixture.get('competition', 'League')}\n"
                  f"**Week:** {fixture['week_number']}",
            inline=False
        )
        
        # Add team crests if available
        from utils.football_data_api import get_team_crest_url
        home_crest = get_team_crest_url(fixture['home_team_id'])
        if home_crest:
            embed.set_thumbnail(url=home_crest)
        
        await results_channel.send(embed=embed)
        print(f"  ✅ Posted match result to {guild.name}")
        
    except Exception as e:
        print(f"  ❌ Error posting match result to {guild.name}: {e}")
        import traceback
        traceback.print_exc()


async def post_european_results(bot, competition, week_number):
    """
    Post BEAUTIFUL European match results with rich embeds
    """
    comp_name = "Champions League" if competition == 'CL' else "Europa League"
    comp_emoji = "⭐" if competition == 'CL' else "🌟"
    comp_color = discord.Color.blue() if competition == 'CL' else discord.Color.gold()
    
    try:
        async with db.pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT f.*,
                       f.home_team_id,
                       f.away_team_id,
                       COALESCE(t1.team_name, et1.team_name) as home_name,
                       COALESCE(t2.team_name, et2.team_name) as away_name
                FROM european_fixtures f
                LEFT JOIN teams t1 ON f.home_team_id = t1.team_id
                LEFT JOIN teams t2 ON f.away_team_id = t2.team_id
                LEFT JOIN european_teams et1 ON f.home_team_id = et1.team_id
                LEFT JOIN european_teams et2 ON f.away_team_id = et2.team_id
                WHERE f.competition = $1 
                AND f.week_number = $2 
                AND f.played = TRUE
                ORDER BY f.home_score + f.away_score DESC
            """, competition, week_number)
        
        if not results:
            print(f"  📰 No {comp_name} results for Week {week_number}")
            return
        
        from utils.football_data_api import get_team_crest_url, get_competition_logo
        comp_logo = get_competition_logo(comp_name)
        
        # Post to all guilds
        for guild in bot.guilds:
            try:
                # Find appropriate channel
                news_channel = discord.utils.get(guild.text_channels, name='european-news')
                if not news_channel:
                    news_channel = discord.utils.get(guild.text_channels, name='news-feed')
                if not news_channel:
                    news_channel = discord.utils.get(guild.text_channels, name='general')
                
                if not news_channel:
                    continue
                
                # Create beautiful result embeds (max 10 per batch)
                embeds = []
                
                for result in results[:10]:
                    # Get crests
                    home_crest = get_team_crest_url(result['home_team_id'])
                    away_crest = get_team_crest_url(result['away_team_id'])
                    
                    # Determine result
                    if result['home_score'] > result['away_score']:
                        result_emoji = "🏆"
                        winner_text = f"**{result['home_name']} wins!**"
                    elif result['away_score'] > result['home_score']:
                        result_emoji = "🏆"
                        winner_text = f"**{result['away_name']} wins!**"
                    else:
                        result_emoji = "🤝"
                        winner_text = "**Draw!**"
                    
                    # Stage info
                    if result['stage'] == 'group':
                        stage_text = f"Group {result.get('group_name', '?')}"
                    else:
                        leg = f" - Leg {result['leg']}" if result.get('leg', 1) > 1 else ""
                        stage_text = f"{result['stage'].title()}{leg}"
                    
                    embed = discord.Embed(
                        title=f"{comp_emoji} {comp_name} - {stage_text}",
                        description=f"## {result['home_name']} **{result['home_score']} - {result['away_score']}** {result['away_name']}\n\n{result_emoji} {winner_text}",
                        color=comp_color
                    )
                    
                    # Competition logo
                    if comp_logo:
                        embed.set_thumbnail(url=comp_logo)
                    
                    # Home team crest as author
                    if home_crest:
                        embed.set_author(name=result['home_name'], icon_url=home_crest)
                    
                    # Away team crest as footer
                    if away_crest:
                        embed.set_footer(text=result['away_name'], icon_url=away_crest)
                    
                    # Match stats
                    embed.add_field(
                        name="📊 Match Info",
                        value=f"**Week:** {week_number}\n**Stage:** {stage_text}",
                        inline=True
                    )
                    
                    # Goal scorers would go here if tracked
                    total_goals = result['home_score'] + result['away_score']
                    if total_goals >= 4:
                        embed.add_field(
                            name="⚽ Goals",
                            value=f"🔥 **{total_goals} goal thriller!**",
                            inline=True
                        )
                    
                    embeds.append(embed)
                
                # Send header message
                header = f"## {comp_emoji} {comp_name} Results - Week {week_number}\n"
                header += f"**{len(results)} matches completed**"
                
                await news_channel.send(header)
                
                # Send embeds in batches
                for i in range(0, len(embeds), 10):
                    batch = embeds[i:i+10]
                    await news_channel.send(embeds=batch)
                
                print(f"  ✅ Posted beautiful {comp_name} results to {guild.name}")
                
            except Exception as e:
                print(f"  ❌ Could not post to {guild.name}: {e}")
    
    except Exception as e:
        print(f"❌ Error in post_european_results: {e}")
        import traceback
        traceback.print_exc()


async def post_weekly_news_digest(bot, week_number: int):
    """
    🆕 ENHANCED: Auto-post weekly news with standings, scorers, and fixtures
    """
    try:
        state = await db.get_game_state()
        
        # Get news from completed week
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM news 
                   WHERE week_number = $1 
                   ORDER BY importance DESC, created_at DESC 
                   LIMIT 8""",
                week_number
            )
            news_items = [dict(row) for row in rows]
        
        if not news_items:
            print(f"  📰 No news items for Week {week_number}")
            return
        
        # Post to all guilds
        for guild in bot.guilds:
            try:
                news_channel = discord.utils.get(guild.text_channels, name="news-feed")
                if not news_channel:
                    news_channel = discord.utils.get(guild.text_channels, name="general")
                
                if not news_channel:
                    continue
                
                embed = discord.Embed(
                    title=f"📰 Week {week_number} Review",
                    description=f"**Season {state['current_season']}**",
                    color=discord.Color.blue()
                )
                
                # ✅ SECTION 1: LEAGUE STANDINGS
                async with db.pool.acquire() as conn:
                    pl_top = await conn.fetch("""
                        SELECT team_name, points, played
                        FROM teams
                        WHERE league = 'Premier League'
                        ORDER BY points DESC, (goals_for - goals_against) DESC
                        LIMIT 3
                    """)
                    
                    if pl_top:
                        standings_text = "**Premier League Top 3:**\n"
                        for i, team in enumerate(pl_top, 1):
                            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                            standings_text += f"{emoji} {team['team_name']} - {team['points']} pts ({team['played']} played)\n"
                        
                        embed.add_field(
                            name="🏆 League Standings",
                            value=standings_text,
                            inline=False
                        )
                
                # ✅ SECTION 2: TOP SCORERS
                async with db.pool.acquire() as conn:
                    top_scorers = await conn.fetch("""
                        SELECT p.player_name, p.season_goals, t.team_name
                        FROM players p
                        LEFT JOIN teams t ON p.team_id = t.team_id
                        WHERE p.season_goals > 0 AND p.retired = FALSE
                        ORDER BY p.season_goals DESC
                        LIMIT 3
                    """)
                    
                    if top_scorers:
                        scorers_text = ""
                        for scorer in top_scorers:
                            scorers_text += f"⚽ {scorer['player_name']} ({scorer['team_name']}) - {scorer['season_goals']} goals\n"
                        
                        embed.add_field(
                            name="👟 Top Scorers",
                            value=scorers_text,
                            inline=False
                        )
                
                # ✅ SECTION 3: TRANSFER WINDOW STATUS
                if state['current_week'] in config.TRANSFER_WINDOW_WEEKS:
                    embed.add_field(
                        name="💼 Transfer Window",
                        value="🟢 **OPEN** - Use `/offers` to view club interest!",
                        inline=False
                    )
                elif state['current_week'] == 14 or state['current_week'] == 29:
                    embed.add_field(
                        name="💼 Transfer Window",
                        value="⚠️ **OPENS NEXT WEEK** - Prepare for offers!",
                        inline=False
                    )
                
                # ✅ SECTION 4: TOP NEWS HEADLINES
                category_emojis = {
                    'player_news': '⭐',
                    'league_news': '🏆',
                    'match_news': '⚽',
                    'transfer_news': '💼',
                    'injury_news': '🤕'
                }
                
                news_text = ""
                for news in news_items[:5]:
                    emoji = category_emojis.get(news['category'], '📌')
                    news_text += f"{emoji} {news['headline']}\n"
                
                embed.add_field(
                    name="📰 Top Headlines",
                    value=news_text,
                    inline=False
                )
                
                # ✅ SECTION 5: UPCOMING FIXTURES
                from utils.season_manager import get_next_match_window, EST
                try:
                    next_window = get_next_match_window()
                    day_name = next_window.strftime('%A')
                    time_str = next_window.strftime('%I:%M %p EST')
                    
                    embed.add_field(
                        name="📅 Next Match Day",
                        value=f"**{day_name}** at **{time_str}**\nWeek {state['current_week']} matches",
                        inline=False
                    )
                except:
                    pass
                
                # Footer
                embed.set_footer(text=f"Week {state['current_week']}/{config.SEASON_TOTAL_WEEKS} • Use /news for your personalized feed")
                
                await news_channel.send(embed=embed)
                print(f"  ✅ Posted enhanced digest to {guild.name}")
                
            except Exception as e:
                print(f"  ❌ Could not post news to {guild.name}: {e}")
        
    except Exception as e:
        print(f"❌ Error in weekly news digest: {e}")
        import traceback
        traceback.print_exc()
