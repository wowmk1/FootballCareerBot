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
                   LIMIT 8""",  # ✅ REDUCED from 12
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
                
                # ✅ NEW SECTION 1: LEAGUE STANDINGS
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
                
                # ✅ NEW SECTION 2: TOP SCORERS
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
                
                # ✅ NEW SECTION 3: TRANSFER WINDOW STATUS
                import config
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
                
                # ✅ MODIFIED: TOP NEWS HEADLINES (Reduced to 5)
                category_emojis = {
                    'player_news': '⭐',
                    'league_news': '🏆',
                    'match_news': '⚽',
                    'transfer_news': '💼',
                    'injury_news': '🤕'
                }
                
                news_text = ""
                for news in news_items[:5]:  # ✅ Only 5 headlines
                    emoji = category_emojis.get(news['category'], '📌')
                    news_text += f"{emoji} {news['headline']}\n"
                
                embed.add_field(
                    name="📰 Top Headlines",
                    value=news_text,
                    inline=False
                )
                
                # ✅ NEW SECTION 4: UPCOMING FIXTURES
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
