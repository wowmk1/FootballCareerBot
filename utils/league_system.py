"""
League System - Promotions and Relegations
Handles end-of-season league movements
"""
import logging
from database import db
import discord

logger = logging.getLogger(__name__)


async def process_promotions_relegations(bot=None):
    """
    Process promotions and relegations at end of season
    - Top 2 Championship → Premier League
    - Bottom 3 Premier League → Championship
    - Top 2 League One → Championship
    - Bottom 3 Championship → League One
    """
    logger.info("\n" + "="*60)
    logger.info("🔄 PROCESSING PROMOTIONS & RELEGATIONS")
    logger.info("="*60)
    
    try:
        async with db.pool.acquire() as conn:
            # Get final league tables
            pl_table = await conn.fetch("""
                SELECT team_id, team_name, position, points 
                FROM teams 
                WHERE league = 'Premier League' 
                ORDER BY points DESC, (goals_for - goals_against) DESC, goals_for DESC
            """)
            
            champ_table = await conn.fetch("""
                SELECT team_id, team_name, position, points 
                FROM teams 
                WHERE league = 'Championship' 
                ORDER BY points DESC, (goals_for - goals_against) DESC, goals_for DESC
            """)
            
            l1_table = await conn.fetch("""
                SELECT team_id, team_name, position, points 
                FROM teams 
                WHERE league = 'League One' 
                ORDER BY points DESC, (goals_for - goals_against) DESC, goals_for DESC
            """)
            
            # ===== PREMIER LEAGUE RELEGATIONS (Bottom 3) =====
            if len(pl_table) >= 3:
                relegated_from_pl = [dict(row) for row in pl_table[-3:]]
                
                for team in relegated_from_pl:
                    await conn.execute("""
                        UPDATE teams SET league = 'Championship' WHERE team_id = $1
                    """, team['team_id'])
                    
                    # Update player leagues
                    await conn.execute("""
                        UPDATE players SET league = 'Championship' WHERE team_id = $1
                    """, team['team_id'])
                    
                    logger.info(f"  ⬇️ RELEGATED: {team['team_name']} (PL → Championship)")
                    
                    await db.add_news(
                        f"RELEGATED: {team['team_name']} drop to Championship",
                        f"{team['team_name']} finished bottom 3 with {team['points']} points and are relegated.",
                        "league_news",
                        None,
                        9
                    )
            
            # ===== CHAMPIONSHIP PROMOTIONS (Top 2) =====
            if len(champ_table) >= 2:
                promoted_from_champ = [dict(row) for row in champ_table[:2]]
                
                for team in promoted_from_champ:
                    await conn.execute("""
                        UPDATE teams SET league = 'Premier League' WHERE team_id = $1
                    """, team['team_id'])
                    
                    # Update player leagues
                    await conn.execute("""
                        UPDATE players SET league = 'Premier League' WHERE team_id = $1
                    """, team['team_id'])
                    
                    logger.info(f"  ⬆️ PROMOTED: {team['team_name']} (Championship → PL)")
                    
                    await db.add_news(
                        f"PROMOTED: {team['team_name']} reach Premier League!",
                        f"{team['team_name']} finished top 2 with {team['points']} points and are promoted to the Premier League!",
                        "league_news",
                        None,
                        10
                    )
            
            # ===== CHAMPIONSHIP RELEGATIONS (Bottom 3) =====
            if len(champ_table) >= 3:
                relegated_from_champ = [dict(row) for row in champ_table[-3:]]
                
                for team in relegated_from_champ:
                    await conn.execute("""
                        UPDATE teams SET league = 'League One' WHERE team_id = $1
                    """, team['team_id'])
                    
                    # Update player leagues
                    await conn.execute("""
                        UPDATE players SET league = 'League One' WHERE team_id = $1
                    """, team['team_id'])
                    
                    logger.info(f"  ⬇️ RELEGATED: {team['team_name']} (Championship → L1)")
                    
                    await db.add_news(
                        f"RELEGATED: {team['team_name']} drop to League One",
                        f"{team['team_name']} are relegated to League One.",
                        "league_news",
                        None,
                        7
                    )
            
            # ===== LEAGUE ONE PROMOTIONS (Top 2) =====
            if len(l1_table) >= 2:
                promoted_from_l1 = [dict(row) for row in l1_table[:2]]
                
                for team in promoted_from_l1:
                    await conn.execute("""
                        UPDATE teams SET league = 'Championship' WHERE team_id = $1
                    """, team['team_id'])
                    
                    # Update player leagues
                    await conn.execute("""
                        UPDATE players SET league = 'Championship' WHERE team_id = $1
                    """, team['team_id'])
                    
                    logger.info(f"  ⬆️ PROMOTED: {team['team_name']} (L1 → Championship)")
                    
                    await db.add_news(
                        f"PROMOTED: {team['team_name']} reach Championship!",
                        f"{team['team_name']} are promoted to the Championship!",
                        "league_news",
                        None,
                        8
                    )
            
            logger.info("="*60)
            logger.info("✅ PROMOTIONS & RELEGATIONS COMPLETE")
            logger.info("="*60 + "\n")
            
            # Send notification to bot channels
            if bot:
                try:
                    for guild in bot.guilds:
                        channel = discord.utils.get(guild.text_channels, name="match-results")
                        if not channel:
                            channel = discord.utils.get(guild.text_channels, name="general")
                        
                        if channel:
                            embed = discord.Embed(
                                title="📊 SEASON COMPLETE - PROMOTIONS & RELEGATIONS",
                                description="The season has ended! Here are the movements:",
                                color=discord.Color.gold()
                            )
                            
                            if len(pl_table) >= 3:
                                relegated_pl_names = "\n".join([f"⬇️ {row['team_name']}" for row in pl_table[-3:]])
                                embed.add_field(
                                    name="🔴 Relegated from Premier League",
                                    value=relegated_pl_names,
                                    inline=False
                                )
                            
                            if len(champ_table) >= 2:
                                promoted_champ_names = "\n".join([f"⬆️ {row['team_name']}" for row in champ_table[:2]])
                                embed.add_field(
                                    name="🟢 Promoted to Premier League",
                                    value=promoted_champ_names,
                                    inline=False
                                )
                            
                            await channel.send(embed=embed)
                except Exception as e:
                    logger.warning(f"Could not post promotion/relegation notification: {e}")
    
    except Exception as e:
        logger.error(f"❌ Error processing promotions/relegations: {e}", exc_info=True)
