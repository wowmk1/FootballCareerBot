"""
Event Poster - PREMIUM MULTI-EMBED NEWS SYSTEM
Posts beautiful, themed news embeds to Discord channels
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
    ✅ UPDATED: Removed top single club section, added crests to both teams in scoreline
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
                    
                    # ✅ UPDATED: Simple title and scoreline with crests in description
                    scoreline = f"{result['home_name']} {result['home_score']} - {result['away_score']} {result['away_name']}"
                    
                    embed = discord.Embed(
                        title=f"{comp_emoji} {comp_name}",
                        description=f"## {scoreline}\n\n{result_emoji} {winner_text}",
                        color=comp_color
                    )
                    
                    # Competition logo as thumbnail
                    if comp_logo:
                        embed.set_thumbnail(url=comp_logo)
                    
                    # ✅ NEW: Set home team crest as author icon (left side)
                    if home_crest:
                        embed.set_author(
                            name=result['home_name'],
                            icon_url=home_crest
                        )
                    
                    # ✅ NEW: Set away team crest as footer icon (bottom)
                    if away_crest:
                        embed.set_footer(
                            text=result['away_name'],
                            icon_url=away_crest
                        )
                    
                    # Match info - 3 columns in first row
                    embed.add_field(
                        name="📊 Status",
                        value="✅ Full Time",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="🎭 Stage",
                        value=stage_text,
                        inline=True
                    )
                    
                    embed.add_field(
                        name="📅 Week",
                        value=f"3",
                        inline=True
                    )
                    
                    # Goal scorers would go here if tracked
                    total_goals = result['home_score'] + result['away_score']
                    if total_goals >= 4:
                        embed.add_field(
                            name="⚽ Goals",
                            value=f"🔥 **{total_goals} goal thriller!**",
                            inline=False
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
    🆕 PREMIUM MULTI-EMBED WEEKLY NEWS DIGEST
    Posts 5-7 separate themed embeds for comprehensive coverage
    """
    try:
        state = await db.get_game_state()
        
        # Post to all guilds
        for guild in bot.guilds:
            try:
                news_channel = discord.utils.get(guild.text_channels, name="news-feed")
                if not news_channel:
                    news_channel = discord.utils.get(guild.text_channels, name="general")
                
                if not news_channel:
                    continue
                
                # ═══════════════════════════════════════════════════════
                # 📰 HEADER MESSAGE
                # ═══════════════════════════════════════════════════════
                header_msg = (
                    f"# 📰 WEEK {week_number} REVIEW\n"
                    f"**Season {state['current_season']} • {config.SEASON_TOTAL_WEEKS - week_number} weeks remaining**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                )
                await news_channel.send(header_msg)
                
                embeds_to_send = []
                
                # ═══════════════════════════════════════════════════════
                # 1️⃣ MATCH OF THE WEEK (Biggest upset or highest scoring)
                # ═══════════════════════════════════════════════════════
                async with db.pool.acquire() as conn:
                    motw = await conn.fetchrow("""
                        SELECT f.*,
                               ht.team_name as home_name,
                               at.team_name as away_name,
                               (f.home_score + f.away_score) as total_goals
                        FROM fixtures f
                        JOIN teams ht ON f.home_team_id = ht.team_id
                        JOIN teams at ON f.away_team_id = at.team_id
                        WHERE f.week_number = $1 AND f.played = TRUE
                        ORDER BY total_goals DESC, ABS(f.home_score - f.away_score) DESC
                        LIMIT 1
                    """, week_number)
                    
                    if motw:
                        from utils.football_data_api import get_team_crest_url
                        home_crest = get_team_crest_url(motw['home_team_id'])
                        away_crest = get_team_crest_url(motw['away_team_id'])
                        
                        motw_embed = discord.Embed(
                            title="🏆 MATCH OF THE WEEK",
                            description=f"## {motw['home_name']} **{motw['home_score']}** - **{motw['away_score']}** {motw['away_name']}",
                            color=discord.Color.gold()
                        )
                        
                        if home_crest:
                            motw_embed.set_thumbnail(url=home_crest)
                        
                        # Get goal scorers from match_events if available
                        goal_scorers = await conn.fetch("""
                            SELECT player_name, team_id, event_type
                            FROM match_events
                            WHERE fixture_id = $1 
                              AND event_type IN ('goal', 'penalty_goal')
                            ORDER BY minute
                        """, motw['fixture_id'])
                        
                        if goal_scorers:
                            home_scorers = [g['player_name'] for g in goal_scorers if g['team_id'] == motw['home_team_id']]
                            away_scorers = [g['player_name'] for g in goal_scorers if g['team_id'] == motw['away_team_id']]
                            
                            scorers_text = ""
                            if home_scorers:
                                scorers_text += f"⚽ **{motw['home_name']}:** {', '.join(home_scorers)}\n"
                            if away_scorers:
                                scorers_text += f"⚽ **{motw['away_name']}:** {', '.join(away_scorers)}\n"
                            
                            if scorers_text:
                                motw_embed.add_field(
                                    name="⚽ Goal Scorers",
                                    value=scorers_text,
                                    inline=False
                                )
                        
                        # Add context
                        if motw['total_goals'] >= 5:
                            motw_embed.add_field(
                                name="🔥 Goal Fest!",
                                value=f"**{motw['total_goals']} goals** in an absolute thriller!",
                                inline=True
                            )
                        
                        # Check for MOTM
                        motm = await conn.fetchrow("""
                            SELECT player_name, rating
                            FROM match_participants
                            WHERE fixture_id = $1 AND motm = TRUE
                            LIMIT 1
                        """, motw['fixture_id'])
                        
                        if motm:
                            motw_embed.add_field(
                                name="⭐ Man of the Match",
                                value=f"**{motm['player_name']}** ({motm['rating']:.1f} rating)",
                                inline=True
                            )
                        
                        if motw['home_score'] > motw['away_score']:
                            winner = motw['home_name']
                            result_emoji = "🏆"
                        elif motw['away_score'] > motw['home_score']:
                            winner = motw['away_name']
                            result_emoji = "🏆"
                        else:
                            winner = "Both teams share"
                            result_emoji = "🤝"
                        
                        motw_embed.add_field(
                            name=f"{result_emoji} Result",
                            value=f"**{winner}** the points in Week {week_number}'s standout fixture",
                            inline=False
                        )
                        
                        if away_crest:
                            motw_embed.set_footer(text=motw['away_name'], icon_url=away_crest)
                        
                        embeds_to_send.append(transfer_embed)
                
                elif state['current_week'] + 1 in config.TRANSFER_WINDOW_WEEKS:
                    transfer_embed = discord.Embed(
                        title="💼 TRANSFER WINDOW PREVIEW",
                        description="**Window opens next week!**",
                        color=discord.Color.gold()
                    )
                    
                    transfer_embed.add_field(
                        name="⚠️ Next Week",
                        value=f"Transfer window opens in **Week {state['current_week'] + 1}**\nPrepare for offers!",
                        inline=False
                    )
                    
                    embeds_to_send.append(transfer_embed)
                
                # ═══════════════════════════════════════════════════════
                # 7️⃣ UPCOMING FIXTURES
                # ═══════════════════════════════════════════════════════
                from utils.season_manager import get_next_match_window
                try:
                    next_window = get_next_match_window()
                    day_name = next_window.strftime('%A')
                    time_str = next_window.strftime('%I:%M %p EST')
                    
                    fixtures_embed = discord.Embed(
                        title="📅 UPCOMING FIXTURES",
                        description=f"**Week {state['current_week']} Match Day**",
                        color=discord.Color.green()
                    )
                    
                    fixtures_embed.add_field(
                        name="⏰ Next Match Window",
                        value=f"**{day_name}**\nKickoff at **{time_str}**",
                        inline=True
                    )
                    
                    # European check
                    if state['current_week'] in config.EUROPEAN_MATCH_WEEKS:
                        fixtures_embed.add_field(
                            name="🏆 European Week",
                            value="CL/EL matches at **12 PM**\nDomestic at **3 PM**",
                            inline=True
                        )
                    else:
                        fixtures_embed.add_field(
                            name="⚽ Domestic Only",
                            value="League matches at **3 PM**",
                            inline=True
                        )
                    
                    embeds_to_send.append(fixtures_embed)
                
                except Exception as e:
                    print(f"  ⚠️ Could not get next window: {e}")
                
                # ═══════════════════════════════════════════════════════
                # SEND ALL EMBEDS
                # ═══════════════════════════════════════════════════════
                if embeds_to_send:
                    # Send in batches of 10 (Discord limit)
                    for i in range(0, len(embeds_to_send), 10):
                        batch = embeds_to_send[i:i+10]
                        await news_channel.send(embeds=batch)
                    
                    print(f"  ✅ Posted {len(embeds_to_send)} premium news embeds to {guild.name}")
                else:
                    print(f"  ⚠️ No news content generated for {guild.name}")
                
            except Exception as e:
                print(f"  ❌ Could not post news to {guild.name}: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error in weekly news digest: {e}")
        import traceback
        traceback.print_exc()


async def post_european_champions(bot, season):
    """
    🏆 POST EUROPEAN CHAMPIONS ANNOUNCEMENT
    Called at end of season when CL/EL finals are complete
    """
    try:
        async with db.pool.acquire() as conn:
            # Get CL winner
            cl_winner = await conn.fetchrow("""
                SELECT k.winner_team_id,
                       COALESCE(t.team_name, et.team_name) as team_name
                FROM european_knockout k
                LEFT JOIN teams t ON k.winner_team_id = t.team_id
                LEFT JOIN european_teams et ON k.winner_team_id = et.team_id
                WHERE k.competition = 'CL' AND k.stage = 'final' 
                  AND k.season = $1 AND k.winner_team_id IS NOT NULL
            """, season)
            
            # Get EL winner
            el_winner = await conn.fetchrow("""
                SELECT k.winner_team_id,
                       COALESCE(t.team_name, et.team_name) as team_name
                FROM european_knockout k
                LEFT JOIN teams t ON k.winner_team_id = t.team_id
                LEFT JOIN european_teams et ON k.winner_team_id = et.team_id
                WHERE k.competition = 'EL' AND k.stage = 'final' 
                  AND k.season = $1 AND k.winner_team_id IS NOT NULL
            """, season)
        
        if not cl_winner and not el_winner:
            print("  ⚠️ No European champions found")
            return
        
        from utils.football_data_api import get_team_crest_url, get_competition_logo
        
        # Post to all guilds
        for guild in bot.guilds:
            try:
                news_channel = discord.utils.get(guild.text_channels, name='european-news')
                if not news_channel:
                    news_channel = discord.utils.get(guild.text_channels, name='news-feed')
                if not news_channel:
                    news_channel = discord.utils.get(guild.text_channels, name='general')
                
                if not news_channel:
                    continue
                
                embeds = []
                
                # Champions League Winner
                if cl_winner:
                    cl_logo = get_competition_logo('Champions League')
                    winner_crest = get_team_crest_url(cl_winner['winner_team_id'])
                    
                    cl_embed = discord.Embed(
                        title="⭐ CHAMPIONS LEAGUE WINNERS",
                        description=f"# 🏆 {cl_winner['team_name'].upper()} 🏆\n\n**Champions of Europe {season}**",
                        color=discord.Color.blue()
                    )
                    
                    if cl_logo:
                        cl_embed.set_thumbnail(url=cl_logo)
                    if winner_crest:
                        cl_embed.set_image(url=winner_crest)
                    
                    cl_embed.add_field(
                        name="🎉 Glory",
                        value=f"**{cl_winner['team_name']}** are crowned Champions League winners!",
                        inline=False
                    )
                    
                    cl_embed.set_footer(text=f"Season {season} • The pinnacle of European football")
                    embeds.append(cl_embed)
                
                # Europa League Winner
                if el_winner:
                    el_logo = get_competition_logo('Europa League')
                    winner_crest = get_team_crest_url(el_winner['winner_team_id'])
                    
                    el_embed = discord.Embed(
                        title="🌟 EUROPA LEAGUE WINNERS",
                        description=f"# 🏆 {el_winner['team_name'].upper()} 🏆\n\n**Europa League Champions {season}**",
                        color=discord.Color.gold()
                    )
                    
                    if el_logo:
                        el_embed.set_thumbnail(url=el_logo)
                    if winner_crest:
                        el_embed.set_image(url=winner_crest)
                    
                    el_embed.add_field(
                        name="🎉 Triumph",
                        value=f"**{el_winner['team_name']}** claim Europa League glory!",
                        inline=False
                    )
                    
                    el_embed.set_footer(text=f"Season {season} • European excellence")
                    embeds.append(el_embed)
                
                if embeds:
                    header = f"# 🏆 EUROPEAN CHAMPIONS CROWNED - {season} 🏆\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                    await news_channel.send(header)
                    await news_channel.send(embeds=embeds)
                    print(f"  ✅ Posted European champions to {guild.name}")
                
            except Exception as e:
                print(f"  ❌ Could not post champions to {guild.name}: {e}")
    
    except Exception as e:
        print(f"❌ Error posting European champions: {e}")
        import traceback
        traceback.print_exc()


async def post_match_day_preview(bot, week_number):
    """
    📋 POST MATCH DAY PREVIEW
    Called when match window opens - shows key fixtures
    """
    try:
        state = await db.get_game_state()
        
        async with db.pool.acquire() as conn:
            # Get most exciting fixtures (involving top teams)
            key_fixtures = await conn.fetch("""
                SELECT f.*, 
                       ht.team_name as home_name,
                       ht.points as home_points,
                       at.team_name as away_name,
                       at.points as away_points
                FROM fixtures f
                JOIN teams ht ON f.home_team_id = ht.team_id
                JOIN teams at ON f.away_team_id = at.team_id
                WHERE f.week_number = $1 AND f.played = FALSE
                ORDER BY (ht.points + at.points) DESC
                LIMIT 5
            """, week_number)
        
        if not key_fixtures:
            return
        
        for guild in bot.guilds:
            try:
                news_channel = discord.utils.get(guild.text_channels, name='match-previews')
                if not news_channel:
                    news_channel = discord.utils.get(guild.text_channels, name='news-feed')
                if not news_channel:
                    news_channel = discord.utils.get(guild.text_channels, name='general')
                
                if not news_channel:
                    continue
                
                preview_embed = discord.Embed(
                    title="⚽ MATCH DAY PREVIEW",
                    description=f"**Week {week_number} • Key Fixtures**",
                    color=discord.Color.green()
                )
                
                fixtures_text = ""
                for fixture in key_fixtures:
                    fixtures_text += (
                        f"🏟️ **{fixture['home_name']}** vs **{fixture['away_name']}**\n"
                        f"   {fixture['home_points']} pts vs {fixture['away_points']} pts\n\n"
                    )
                
                preview_embed.add_field(
                    name="🔥 Top Matches",
                    value=fixtures_text,
                    inline=False
                )
                
                # European check
                if week_number in config.EUROPEAN_MATCH_WEEKS:
                    preview_embed.add_field(
                        name="🏆 European Action",
                        value="Champions League & Europa League matches today!\n**12:00 PM - 2:00 PM EST**",
                        inline=False
                    )
                
                preview_embed.add_field(
                    name="🎮 Play Your Match",
                    value="Use `/play_match` when the window opens!",
                    inline=False
                )
                
                preview_embed.set_footer(text=f"Season {state['current_season']} • Week {week_number}")
                
                await news_channel.send(embed=preview_embed)
                print(f"  ✅ Posted match day preview to {guild.name}")
                
            except Exception as e:
                print(f"  ❌ Could not post preview to {guild.name}: {e}")
    
    except Exception as e:
        print(f"❌ Error posting match day preview: {e}")
        import traceback
        traceback.print_exc()


async def post_season_finale_preview(bot):
    """
    🎬 POST SEASON FINALE PREVIEW
    Called before final week - shows title race, relegation battle, European race
    """
    try:
        state = await db.get_game_state()
        
        async with db.pool.acquire() as conn:
            pl_standings = await conn.fetch("""
                SELECT team_name, points, played,
                       (goals_for - goals_against) as gd
                FROM teams
                WHERE league = 'Premier League'
                ORDER BY points DESC, gd DESC
            """)
        
        if not pl_standings or len(pl_standings) < 20:
            return
        
        for guild in bot.guilds:
            try:
                news_channel = discord.utils.get(guild.text_channels, name='news-feed')
                if not news_channel:
                    news_channel = discord.utils.get(guild.text_channels, name='general')
                
                if not news_channel:
                    continue
                
                # Header
                header = (
                    f"# 🎬 SEASON FINALE PREVIEW\n"
                    f"**The final day approaches...**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                )
                await news_channel.send(header)
                
                embeds = []
                
                # Title Race
                title_race_embed = discord.Embed(
                    title="🏆 TITLE RACE",
                    description="**Who will be crowned champions?**",
                    color=discord.Color.gold()
                )
                
                title_text = ""
                for i, team in enumerate(pl_standings[:3], 1):
                    emoji = ["🥇", "🥈", "🥉"][i-1]
                    title_text += f"{emoji} **{team['team_name']}** - {team['points']} pts (GD: {team['gd']:+d})\n"
                
                title_race_embed.add_field(
                    name="Top 3",
                    value=title_text,
                    inline=False
                )
                
                embeds.append(title_race_embed)
                
                # European Race
                euro_embed = discord.Embed(
                    title="🌟 EUROPEAN RACE",
                    description="**Battle for Europe**",
                    color=discord.Color.blue()
                )
                
                euro_text = ""
                for i, team in enumerate(pl_standings[3:7], 4):
                    if i <= 4:
                        zone = "CL" if i <= 4 else "EL"
                        euro_text += f"{i}. **{team['team_name']}** - {team['points']} pts ({zone})\n"
                    else:
                        euro_text += f"{i}. **{team['team_name']}** - {team['points']} pts (EL)\n"
                
                euro_embed.add_field(
                    name="Positions 4-7",
                    value=euro_text,
                    inline=False
                )
                
                embeds.append(euro_embed)
                
                # Relegation Battle
                rel_embed = discord.Embed(
                    title="🔴 RELEGATION BATTLE",
                    description="**Who will go down?**",
                    color=discord.Color.red()
                )
                
                rel_text = ""
                for i, team in enumerate(pl_standings[-4:], len(pl_standings)-3):
                    status = "⚠️ DANGER" if i >= len(pl_standings) - 2 else "⚠️ SAFE"
                    rel_text += f"{i}. **{team['team_name']}** - {team['points']} pts {status}\n"
                
                rel_embed.add_field(
                    name="Bottom 4",
                    value=rel_text,
                    inline=False
                )
                
                embeds.append(rel_embed)
                
                await news_channel.send(embeds=embeds)
                print(f"  ✅ Posted season finale preview to {guild.name}")
                
            except Exception as e:
                print(f"  ❌ Could not post finale preview to {guild.name}: {e}")
    
    except Exception as e:
        print(f"❌ Error posting season finale: {e}")
        import traceback
        traceback.print_exc()d.append(motw_embed)
                
                # ═══════════════════════════════════════════════════════
                # 2️⃣ PREMIER LEAGUE TABLE WATCH
                # ═══════════════════════════════════════════════════════
                async with db.pool.acquire() as conn:
                    pl_standings = await conn.fetch("""
                        SELECT team_name, points, played, won, drawn, lost,
                               goals_for, goals_against,
                               (goals_for - goals_against) as gd
                        FROM teams
                        WHERE league = 'Premier League'
                        ORDER BY points DESC, gd DESC, goals_for DESC
                    """)
                    
                    if pl_standings:
                        table_embed = discord.Embed(
                            title="📊 PREMIER LEAGUE TABLE",
                            description="**Current Standings**",
                            color=discord.Color.purple()
                        )
                        
                        # Top 4 (Champions League)
                        top4_text = ""
                        for i, team in enumerate(pl_standings[:4], 1):
                            emoji = ["🥇", "🥈", "🥉", "4️⃣"][i-1]
                            top4_text += f"{emoji} **{team['team_name']}** - {team['points']} pts\n"
                            top4_text += f"   {team['won']}W {team['drawn']}D {team['lost']}L • GD {team['gd']:+d}\n"
                        
                        table_embed.add_field(
                            name="🏆 Champions League Zone",
                            value=top4_text,
                            inline=False
                        )
                        
                        # 5th-6th (Europa League)
                        if len(pl_standings) >= 6:
                            europa_text = ""
                            for i, team in enumerate(pl_standings[4:6], 5):
                                europa_text += f"{i}. **{team['team_name']}** - {team['points']} pts\n"
                            
                            table_embed.add_field(
                                name="🌟 Europa League Zone",
                                value=europa_text,
                                inline=False
                            )
                        
                        # Bottom 3 (Relegation)
                        if len(pl_standings) >= 20:
                            rel_text = ""
                            for i, team in enumerate(pl_standings[-3:], len(pl_standings)-2):
                                rel_text += f"{i}. **{team['team_name']}** - {team['points']} pts ⚠️\n"
                            
                            table_embed.add_field(
                                name="🔴 Relegation Zone",
                                value=rel_text,
                                inline=False
                            )
                        
                        table_embed.set_footer(text=f"Week {week_number} Standings")
                        embeds_to_send.append(table_embed)
                
                # ═══════════════════════════════════════════════════════
                # 3️⃣ PLAYER SPOTLIGHT (Top scorers + assists)
                # ═══════════════════════════════════════════════════════
                async with db.pool.acquire() as conn:
                    top_players = await conn.fetch("""
                        SELECT p.player_name, p.season_goals, p.season_assists, 
                               p.season_motm, t.team_name
                        FROM players p
                        LEFT JOIN teams t ON p.team_id = t.team_id
                        WHERE p.retired = FALSE AND p.team_id != 'free_agent'
                          AND (p.season_goals > 0 OR p.season_assists > 0 OR p.season_motm > 0)
                        ORDER BY p.season_goals DESC, p.season_assists DESC
                        LIMIT 5
                    """)
                    
                    if top_players:
                        player_embed = discord.Embed(
                            title="⭐ PLAYER SPOTLIGHT",
                            description="**Season Leaders**",
                            color=discord.Color.orange()
                        )
                        
                        scorers_text = ""
                        for i, player in enumerate(top_players, 1):
                            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
                            scorers_text += (
                                f"{medal} **{player['player_name']}** ({player['team_name']})\n"
                                f"   ⚽ {player['season_goals']}G • 🎯 {player['season_assists']}A"
                            )
                            if player['season_motm'] > 0:
                                scorers_text += f" • 🏅 {player['season_motm']} MOTM"
                            scorers_text += "\n"
                        
                        player_embed.add_field(
                            name="👟 Top Performers",
                            value=scorers_text,
                            inline=False
                        )
                        
                        embeds_to_send.append(player_embed)
                
                # ═══════════════════════════════════════════════════════
                # 4️⃣ HOT & COLD (Form guide)
                # ═══════════════════════════════════════════════════════
                async with db.pool.acquire() as conn:
                    # Teams with 3+ wins in last 5 weeks (if tracked)
                    hot_teams = await conn.fetch("""
                        SELECT team_name, points, won
                        FROM teams
                        WHERE league = 'Premier League' AND won >= 3
                        ORDER BY points DESC
                        LIMIT 3
                    """)
                    
                    cold_teams = await conn.fetch("""
                        SELECT team_name, points, lost
                        FROM teams
                        WHERE league = 'Premier League' AND lost >= 3
                        ORDER BY points ASC
                        LIMIT 3
                    """)
                    
                    if hot_teams or cold_teams:
                        form_embed = discord.Embed(
                            title="🔥 FORM GUIDE",
                            description="**Hot & Cold Teams**",
                            color=discord.Color.red()
                        )
                        
                        if hot_teams:
                            hot_text = ""
                            for team in hot_teams:
                                hot_text += f"🔥 **{team['team_name']}** - {team['won']} wins\n"
                            
                            form_embed.add_field(
                                name="📈 On Fire",
                                value=hot_text,
                                inline=True
                            )
                        
                        if cold_teams:
                            cold_text = ""
                            for team in cold_teams:
                                cold_text += f"❄️ **{team['team_name']}** - {team['lost']} losses\n"
                            
                            form_embed.add_field(
                                name="📉 Struggling",
                                value=cold_text,
                                inline=True
                            )
                        
                        embeds_to_send.append(form_embed)
                
                # ═══════════════════════════════════════════════════════
                # 5️⃣ EUROPEAN SPOTLIGHT (if European week)
                # ═══════════════════════════════════════════════════════
                if week_number in config.EUROPEAN_MATCH_WEEKS:
                    async with db.pool.acquire() as conn:
                        euro_count = await conn.fetchval("""
                            SELECT COUNT(*) FROM european_fixtures
                            WHERE week_number = $1 AND played = TRUE
                        """, week_number)
                        
                        if euro_count and euro_count > 0:
                            euro_embed = discord.Embed(
                                title="🏆 EUROPEAN SPOTLIGHT",
                                description=f"**Week {week_number} European Action**",
                                color=discord.Color.blue()
                            )
                            
                            # Get English teams in Europe
                            english_results = await conn.fetch("""
                                SELECT f.*, 
                                       COALESCE(ht.team_name, eht.team_name) as home_name,
                                       COALESCE(at.team_name, eat.team_name) as away_name,
                                       t.team_name as english_team
                                FROM european_fixtures f
                                LEFT JOIN teams ht ON f.home_team_id = ht.team_id
                                LEFT JOIN teams at ON f.away_team_id = at.team_id
                                LEFT JOIN european_teams eht ON f.home_team_id = eht.team_id
                                LEFT JOIN european_teams eat ON f.away_team_id = eat.team_id
                                LEFT JOIN teams t ON (f.home_team_id = t.team_id OR f.away_team_id = t.team_id)
                                WHERE f.week_number = $1 AND f.played = TRUE
                                  AND t.league = 'Premier League'
                                LIMIT 5
                            """, week_number)
                            
                            if english_results:
                                results_text = ""
                                for match in english_results:
                                    comp = "⭐" if match['competition'] == 'CL' else "🌟"
                                    results_text += (
                                        f"{comp} **{match['home_name']}** {match['home_score']}-{match['away_score']} "
                                        f"**{match['away_name']}**\n"
                                    )
                                
                                euro_embed.add_field(
                                    name="🏴󠁧󠁢󠁥󠁮󠁧󠁿 English Clubs",
                                    value=results_text,
                                    inline=False
                                )
                            
                            euro_embed.add_field(
                                name="📊 European Matches",
                                value=f"**{euro_count}** matches played across CL & EL",
                                inline=False
                            )
                            
                            embeds_to_send.append(euro_embed)
                
                # ═══════════════════════════════════════════════════════
                # 6️⃣ TRANSFER WINDOW STATUS
                # ═══════════════════════════════════════════════════════
                if state['current_week'] in config.TRANSFER_WINDOW_WEEKS:
                    transfer_embed = discord.Embed(
                        title="💼 TRANSFER WINDOW OPEN",
                        description="**The market is active!**",
                        color=discord.Color.green()
                    )
                    
                    transfer_embed.add_field(
                        name="🟢 Status",
                        value="Transfer window is **OPEN**\nClubs are making moves!",
                        inline=False
                    )
                    
                    transfer_embed.add_field(
                        name="📋 For Players",
                        value="Use `/offers` to see which clubs want to sign you!",
                        inline=False
                    )
                    
                    embeds_to_sen
