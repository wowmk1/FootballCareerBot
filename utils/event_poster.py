"""
Event Poster - PREMIUM MULTI-EMBED NEWS SYSTEM WITH BEAUTIFUL CRESTS
Posts beautiful, themed news embeds to Discord channels with side-by-side team crests
"""
import discord
from database import db
import config
from io import BytesIO
from PIL import Image
import aiohttp


async def generate_crests_image(home_crest_url, away_crest_url):
    """
    Generate combined image with both team crests side by side
    Matches the European commands style
    
    Args:
        home_crest_url: URL for home team crest
        away_crest_url: URL for away team crest
    
    Returns:
        BytesIO buffer with PNG image, or None if failed
    """
    try:
        async with aiohttp.ClientSession() as session:
            home_img_bytes = None
            away_img_bytes = None
            
            # Download home crest
            if home_crest_url:
                try:
                    async with session.get(home_crest_url, timeout=aiohttp.ClientTimeout(total=5)) as r:
                        if r.status == 200:
                            home_img_bytes = await r.read()
                except Exception as e:
                    print(f"  ⚠️ Could not fetch home crest: {e}")
            
            # Download away crest
            if away_crest_url:
                try:
                    async with session.get(away_crest_url, timeout=aiohttp.ClientTimeout(total=5)) as r:
                        if r.status == 200:
                            away_img_bytes = await r.read()
                except Exception as e:
                    print(f"  ⚠️ Could not fetch away crest: {e}")
        
        # Create combined image
        size = (100, 100)  # Size for each crest
        padding = 40  # Space between crests
        width = size[0] * 2 + padding
        height = size[1]
        
        # Create transparent background
        img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        
        # Add home crest (left side)
        if home_img_bytes:
            try:
                home = Image.open(BytesIO(home_img_bytes)).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
                img.paste(home, (0, 0), home)
            except Exception as e:
                print(f"  ⚠️ Could not process home crest: {e}")
        
        # Add away crest (right side)
        if away_img_bytes:
            try:
                away = Image.open(BytesIO(away_img_bytes)).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
                img.paste(away, (size[0] + padding, 0), away)
            except Exception as e:
                print(f"  ⚠️ Could not process away crest: {e}")
        
        # Save to buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        print(f"  ❌ Error generating crests image: {e}")
        return None


async def post_transfer_news_to_channel(bot, guild, transfer_info):
    """
    Post a transfer announcement to the transfer-news channel WITH CLUB CRESTS
    
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
        
        from utils.football_data_api import get_team_crest_url
        
        if is_new_player:
            # New player joining the game
            to_crest = get_team_crest_url(transfer_info.get('to_team_id'))
            
            embed = discord.Embed(
                title="🆕 NEW PLAYER JOINS!",
                description=f"**{transfer_info['player_name']}** has entered the league!",
                color=discord.Color.green()
            )
            
            # Set author with new player club
            if to_crest:
                embed.set_author(name=transfer_info['to_team'], icon_url=to_crest)
            else:
                embed.set_author(name=transfer_info['to_team'])
            
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
                embed.set_footer(text=f"Welcome {transfer_info['user'].name}! 🎉")
            
            await news_channel.send(embed=embed)
            
        else:
            # Regular transfer with both club crests
            from_crest = get_team_crest_url(transfer_info.get('from_team_id'))
            to_crest = get_team_crest_url(transfer_info.get('to_team_id'))
            
            embed = discord.Embed(
                title="💼 TRANSFER CONFIRMED",
                description=f"**{transfer_info['player_name']}** is on the move!",
                color=discord.Color.gold()
            )
            
            # Set author with from team
            if from_crest:
                embed.set_author(name=f"From: {transfer_info['from_team']}", icon_url=from_crest)
            
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
            
            # Generate combined crests image
            if from_crest or to_crest:
                crests_buffer = await generate_crests_image(from_crest, to_crest)
                if crests_buffer:
                    file = discord.File(fp=crests_buffer, filename="transfer_crests.png")
                    embed.set_image(url="attachment://transfer_crests.png")
                    
                    # Set footer with to team
                    if to_crest:
                        embed.set_footer(text=f"New club: {transfer_info['to_team']}", icon_url=to_crest)
                    else:
                        embed.set_footer(text=f"New club: {transfer_info['to_team']}")
                    
                    await news_channel.send(embed=embed, file=file)
                    print(f"  ✅ Posted transfer news with crests to {guild.name}")
                    return
            
            # Fallback without image
            if to_crest:
                embed.set_footer(text=f"New club: {transfer_info['to_team']}", icon_url=to_crest)
            
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


async def post_match_result_to_channel(bot, guild, fixture, home_score, away_score, highlights_buffer=None):
    """
    Post match result to match-results channel WITH BEAUTIFUL CRESTS
    
    Args:
        bot: Discord bot instance
        guild: Discord guild
        fixture: Fixture dict with home_team_id, away_team_id, week_number
        home_score: Home team score
        away_score: Away team score
        highlights_buffer: Optional BytesIO buffer with animated highlights GIF
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
        
        from utils.football_data_api import get_team_crest_url
        
        home_crest = get_team_crest_url(fixture['home_team_id'])
        away_crest = get_team_crest_url(fixture['away_team_id'])
        
        # Determine result emoji and text
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
        
        # Set author with home team crest
        if home_crest:
            embed.set_author(name=home_team['team_name'], icon_url=home_crest)
        
        # Get goal scorers if available - FIXED: JOIN with players table
        async with db.pool.acquire() as conn:
            goal_scorers = await conn.fetch("""
                SELECT p.player_name, p.team_id, me.event_type, me.minute
                FROM match_events me
                JOIN players p ON me.user_id = p.user_id
                WHERE me.fixture_id = $1 
                  AND me.event_type IN ('goal', 'penalty_goal')
                ORDER BY me.minute
            """, fixture.get('fixture_id'))
            
            if goal_scorers:
                home_scorers = [f"{g['player_name']} ({g['minute']}')" for g in goal_scorers if g['team_id'] == fixture['home_team_id']]
                away_scorers = [f"{g['player_name']} ({g['minute']}')" for g in goal_scorers if g['team_id'] == fixture['away_team_id']]
                
                scorers_text = ""
                if home_scorers:
                    scorers_text += f"⚽ **{home_team['team_name']}:** {', '.join(home_scorers)}\n"
                if away_scorers:
                    scorers_text += f"⚽ **{away_team['team_name']}:** {', '.join(away_scorers)}\n"
                
                if scorers_text:
                    embed.add_field(
                        name="⚽ Goal Scorers",
                        value=scorers_text,
                        inline=False
                    )
            
            # Check for MOTM - FIXED: match_participants uses match_id, not fixture_id
            # First get the match_id from active_matches
            match_id = await conn.fetchval("""
                SELECT match_id FROM active_matches WHERE fixture_id = $1
            """, fixture.get('fixture_id'))
            
            if match_id:
                motm = await conn.fetchrow("""
                    SELECT p.player_name, mp.rating
                    FROM match_participants mp
                    JOIN players p ON mp.user_id = p.user_id
                    WHERE mp.match_id = $1 AND mp.motm = TRUE
                    LIMIT 1
                """, match_id)
                
                if motm:
                    embed.add_field(
                        name="⭐ Man of the Match",
                        value=f"**{motm['player_name']}** ({motm['rating']:.1f} rating)",
                        inline=True
                    )
        
        embed.add_field(
            name="📊 Match Info",
            value=f"**Competition:** {fixture.get('competition', 'League')}\n"
                  f"**Week:** {fixture['week_number']}",
            inline=True
        )
        
        # Prepare files to send
        files_to_send = []
        
        # Add highlights GIF if provided
        if highlights_buffer:
            highlights_file = discord.File(fp=highlights_buffer, filename="match_highlights.gif")
            files_to_send.append(highlights_file)
            embed.set_image(url="attachment://match_highlights.gif")
        # Otherwise use combined crests image
        elif home_crest or away_crest:
            crests_buffer = await generate_crests_image(home_crest, away_crest)
            if crests_buffer:
                crests_file = discord.File(fp=crests_buffer, filename="match_crests.png")
                files_to_send.append(crests_file)
                embed.set_image(url="attachment://match_crests.png")
        
        # Set footer with away team
        if away_crest:
            embed.set_footer(text=away_team['team_name'], icon_url=away_crest)
        
        # Send with all files
        if files_to_send:
            await results_channel.send(embed=embed, files=files_to_send)
            print(f"  ✅ Posted match result with {'highlights' if highlights_buffer else 'crests'} to {guild.name}")
        else:
            await results_channel.send(embed=embed)
            print(f"  ✅ Posted match result to {guild.name}")
        
    except Exception as e:
        print(f"  ❌ Error posting match result to {guild.name}: {e}")
        import traceback
        traceback.print_exc()


async def post_european_results(bot, competition, week_number):
    """
    Post BEAUTIFUL European match results with rich embeds and CRESTS
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
                
                # Send header message
                header = f"## {comp_emoji} {comp_name} Results - Week {week_number}\n"
                header += f"**{len(results)} matches completed**"
                
                await news_channel.send(header)
                
                # Create beautiful result embeds (max 10 per batch)
                for idx, result in enumerate(results[:10]):
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
                    
                    # Competition logo as thumbnail
                    if comp_logo:
                        embed.set_thumbnail(url=comp_logo)
                    
                    # Home team crest as author
                    if home_crest:
                        embed.set_author(name=result['home_name'], icon_url=home_crest)
                    
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
                    
                    # Generate combined crests image
                    if home_crest or away_crest:
                        crests_buffer = await generate_crests_image(home_crest, away_crest)
                        if crests_buffer:
                            file = discord.File(fp=crests_buffer, filename=f"euro_crests_{idx}.png")
                            embed.set_image(url=f"attachment://euro_crests_{idx}.png")
                            
                            # Away team crest as footer
                            if away_crest:
                                embed.set_footer(text=result['away_name'], icon_url=away_crest)
                            
                            await news_channel.send(embed=embed, file=file)
                            continue
                    
                    # Fallback without image
                    if away_crest:
                        embed.set_footer(text=result['away_name'], icon_url=away_crest)
                    
                    await news_channel.send(embed=embed)
                
                print(f"  ✅ Posted beautiful {comp_name} results to {guild.name}")
                
            except Exception as e:
                print(f"  ❌ Could not post to {guild.name}: {e}")
    
    except Exception as e:
        print(f"❌ Error in post_european_results: {e}")
        import traceback
        traceback.print_exc()


async def post_weekly_news_digest(bot, week_number: int):
    """
    🆕 PREMIUM MULTI-EMBED WEEKLY NEWS DIGEST WITH CRESTS
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
                
                # Header message
                header_msg = (
                    f"# 📰 WEEK {week_number} REVIEW\n"
                    f"**Season {state['current_season']} • {config.SEASON_TOTAL_WEEKS - week_number} weeks remaining**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                )
                await news_channel.send(header_msg)
                
                embeds_to_send = []
                files_to_send = []
                
                # 1️⃣ MATCH OF THE WEEK
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
                            motw_embed.set_author(name=motw['home_name'], icon_url=home_crest)
                        
                        # FIXED: JOIN with players table for goal scorers
                        goal_scorers = await conn.fetch("""
                            SELECT p.player_name, p.team_id, me.event_type
                            FROM match_events me
                            JOIN players p ON me.user_id = p.user_id
                            WHERE me.fixture_id = $1 
                              AND me.event_type IN ('goal', 'penalty_goal')
                            ORDER BY me.minute
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
                        
                        if motw['total_goals'] >= 5:
                            motw_embed.add_field(
                                name="🔥 Goal Fest!",
                                value=f"**{motw['total_goals']} goals** in an absolute thriller!",
                                inline=True
                            )
                        
                        # FIXED: Get match_id first, then get MOTM
                        match_id = await conn.fetchval("""
                            SELECT match_id FROM active_matches WHERE fixture_id = $1
                        """, motw['fixture_id'])
                        
                        if match_id:
                            motm = await conn.fetchrow("""
                                SELECT p.player_name, mp.rating
                                FROM match_participants mp
                                JOIN players p ON mp.user_id = p.user_id
                                WHERE mp.match_id = $1 AND mp.motm = TRUE
                                LIMIT 1
                            """, match_id)
                            
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
                        
                        if home_crest or away_crest:
                            crests_buffer = await generate_crests_image(home_crest, away_crest)
                            if crests_buffer:
                                file = discord.File(fp=crests_buffer, filename="motw_crests.png")
                                motw_embed.set_image(url="attachment://motw_crests.png")
                                files_to_send.append(file)
                        
                        if away_crest:
                            motw_embed.set_footer(text=motw['away_name'], icon_url=away_crest)
                        
                        embeds_to_send.append(motw_embed)
                
                # 2️⃣ PREMIER LEAGUE TABLE
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
                        
                        if len(pl_standings) >= 6:
                            europa_text = ""
                            for i, team in enumerate(pl_standings[4:6], 5):
                                europa_text += f"{i}. **{team['team_name']}** - {team['points']} pts\n"
                            
                            table_embed.add_field(
                                name="🌟 Europa League Zone",
                                value=europa_text,
                                inline=False
                            )
                        
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
                
                # 3️⃣ PLAYER SPOTLIGHT
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
                
                # 4️⃣ HOT & COLD
                async with db.pool.acquire() as conn:
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
                
                # 5️⃣ EUROPEAN SPOTLIGHT
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
                
                # 6️⃣ TRANSFER WINDOW
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
                
                # 7️⃣ UPCOMING FIXTURES
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
                
                # SEND ALL EMBEDS
                if embeds_to_send:
                    for i, embed in enumerate(embeds_to_send):
                        if i < len(files_to_send):
                            await news_channel.send(embed=embed, file=files_to_send[i])
                        else:
                            await news_channel.send(embed=embed)
                    
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
    """
    try:
        async with db.pool.acquire() as conn:
            cl_winner = await conn.fetchrow("""
                SELECT k.winner_team_id,
                       COALESCE(t.team_name, et.team_name) as team_name
                FROM european_knockout k
                LEFT JOIN teams t ON k.winner_team_id = t.team_id
                LEFT JOIN european_teams et ON k.winner_team_id = et.team_id
                WHERE k.competition = 'CL' AND k.stage = 'final' 
                  AND k.season = $1 AND k.winner_team_id IS NOT NULL
            """, season)
            
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
                        cl_embed.set_author(name=f"🏆 {cl_winner['team_name']}", icon_url=winner_crest)
                    
                    cl_embed.add_field(
                        name="🎉 Glory",
                        value=f"**{cl_winner['team_name']}** are crowned Champions League winners!",
                        inline=False
                    )
                    
                    cl_embed.set_footer(text=f"Season {season} • The pinnacle of European football")
                    embeds.append(cl_embed)
                
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
                        el_embed.set_author(name=f"🏆 {el_winner['team_name']}", icon_url=winner_crest)
                    
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
                    for embed in embeds:
                        await news_channel.send(embed=embed)
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
    """
    try:
        state = await db.get_game_state()
        
        async with db.pool.acquire() as conn:
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
                
                header = (
                    f"# 🎬 SEASON FINALE PREVIEW\n"
                    f"**The final day approaches...**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                )
                await news_channel.send(header)
                
                embeds = []
                
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
                
                for embed in embeds:
                    await news_channel.send(embed=embed)
                print(f"  ✅ Posted season finale preview to {guild.name}")
                
            except Exception as e:
                print(f"  ❌ Could not post finale preview to {guild.name}: {e}")
    
    except Exception as e:
        print(f"❌ Error posting season finale: {e}")
        import traceback
        traceback.print_exc()
