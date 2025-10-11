# ============================================
# Add to bot.py after line 362
# ============================================

async def notify_match_window_closed(self, week_results):
    """Notify all guilds that match window has closed with results"""
    try:
        state = await db.get_game_state()
        
        for guild in self.guilds:
            channel = discord.utils.get(guild.text_channels, name="match-results")
            if not channel:
                channel = discord.utils.get(guild.text_channels, name="general")
            
            if channel:
                embed = discord.Embed(
                    title="🔴 MATCH WINDOW CLOSED",
                    description=f"**Week {state['current_week']}** is complete! Advancing to Week {state['current_week'] + 1}...",
                    color=discord.Color.red()
                )
                
                # Show match summary
                if week_results:
                    results_text = ""
                    for result in week_results[:5]:  # Show top 5
                        results_text += f"**{result['home_team_name']}** {result['home_score']} - {result['away_score']} **{result['away_team_name']}**\n"
                    
                    embed.add_field(
                        name="📊 Recent Results",
                        value=results_text,
                        inline=False
                    )
                
                embed.add_field(
                    name="📅 Next Match Window",
                    value="Check `/season` for schedule",
                    inline=False
                )
                
                embed.set_footer(text="Use /league table to see updated standings!")
                
                await channel.send(embed=embed)
                print(f"✅ Posted window closed notification to {guild.name}")
    except Exception as e:
        print(f"⚠️ Could not post window closed notification: {e}")


# ============================================
# REPLACE notify_match_window_open() in bot.py (lines 336-362)
# ============================================

async def notify_match_window_open(self):
    """Notify all guilds that match window is open"""
    try:
        state = await db.get_game_state()
        
        for guild in self.guilds:
            channel = discord.utils.get(guild.text_channels, name="match-results")
            if not channel:
                channel = discord.utils.get(guild.text_channels, name="general")
            
            if channel:
                embed = discord.Embed(
                    title="🟢 MATCH WINDOW OPEN!",
                    description=f"**Week {state['current_week']}** matches are now playable!\n\n"
                               f"Use `/play_match` to play your match!",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="⏰ Window Open",
                    value="**3:00 PM - 5:00 PM EST**\n2 hour window",
                    inline=True
                )
                
                embed.add_field(
                    name="⚡ Quick Commands",
                    value="`/play_match` - Play your match\n`/season` - Check schedule",
                    inline=True
                )
                
                # Get players in this server who have matches
                async with db.pool.acquire() as conn:
                    players = await conn.fetch("""
                        SELECT DISTINCT p.user_id, p.player_name, t.team_name
                        FROM players p
                        JOIN teams t ON p.team_id = t.team_id
                        WHERE p.retired = FALSE 
                        AND p.team_id != 'free_agent'
                        AND EXISTS (
                            SELECT 1 FROM fixtures f
                            WHERE (f.home_team_id = p.team_id OR f.away_team_id = p.team_id)
                            AND f.week_number = $1
                            AND f.played = FALSE
                        )
                    """, state['current_week'])
                
                # Mention players who need to play
                player_mentions = []
                for p in players:
                    member = guild.get_member(p['user_id'])
                    if member:
                        player_mentions.append(f"{member.mention} ({p['team_name']})")
                
                if player_mentions:
                    mentions_text = "\n".join(player_mentions[:10])  # Max 10
                    if len(player_mentions) > 10:
                        mentions_text += f"\n*...and {len(player_mentions) - 10} more*"
                    
                    embed.add_field(
                        name="👥 Players with Matches",
                        value=mentions_text,
                        inline=False
                    )
                
                embed.set_footer(text="Window closes at 5:00 PM EST!")
                
                await channel.send(embed=embed)
                print(f"✅ Posted match window notification to {guild.name}")
    except Exception as e:
        print(f"⚠️ Could not post match window notification: {e}")


# ============================================
# Add to season_manager.py in close_match_window() at line 173
# REPLACE the section after "Simulate all unplayed matches"
# ============================================

# After simulating unplayed matches:
if simulated_count > 0:
    print(f"⚽ Simulated {simulated_count} unplayed matches")

# Get all week results for notification
async with db.pool.acquire() as conn:
    results = await conn.fetch("""
        SELECT f.*, 
               t1.team_name as home_team_name,
               t2.team_name as away_team_name
        FROM fixtures f
        JOIN teams t1 ON f.home_team_id = t1.team_id
        JOIN teams t2 ON f.away_team_id = t2.team_id
        WHERE f.week_number = $1 AND f.played = TRUE
        ORDER BY f.fixture_id DESC
        LIMIT 10
    """, current_week)
    week_results = [dict(r) for r in results]

# Notify about window closing
if bot:
    await bot.notify_match_window_closed(week_results)

# Close window
await db.update_game_state(match_window_open=False)

print(f"✅ Match window CLOSED for Week {current_week}")
