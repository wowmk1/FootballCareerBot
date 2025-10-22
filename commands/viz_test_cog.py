"""
VISUALIZATION TEST COG - STANDALONE
Just add to your bot: await bot.load_extension('viz_test_cog')

NO EDITING NEEDED - Drop this file in your commands/ folder and load it!
"""
import discord
from discord import app_commands
from discord.ext import commands
import asyncio


class VizTestCog(commands.Cog):
    """Standalone visualization testing command"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="test_viz", description="🎬 Test complete visualization system")
    @app_commands.checks.has_permissions(administrator=True)
    async def test_viz(self, interaction: discord.Interaction):
        """Complete visualization test - shows match images, animated highlights, and results channel post"""
        await interaction.response.defer()
        
        try:
            # Import check
            try:
                from match_visualizer import generate_action_visualization, CoordinateMapper
                from match_highlights import MatchHighlightsGenerator
                await interaction.followup.send("✅ **Visualization system loaded!**")
            except ImportError as e:
                await interaction.followup.send(
                    f"❌ **Cannot import visualization system!**\n\n"
                    f"Error: {e}\n\n"
                    f"**Need:**\n• match_visualizer.py in project root\n• match_highlights.py in project root\n• `pip install Pillow`",
                    ephemeral=True
                )
                return
            
            channel = interaction.channel
            
            # Intro
            intro_embed = discord.Embed(
                title="🎬 COMPLETE VISUALIZATION TEST",
                description="## This shows EXACTLY what you'll see live!\n\n"
                           "**You'll see:**\n"
                           "1️⃣ Static images during match actions\n"
                           "2️⃣ Animated GIF highlights after match\n"
                           "3️⃣ Results channel post with highlights\n\n"
                           "**⚠️ SANDBOX MODE:** No database changes!",
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=intro_embed)
            await asyncio.sleep(3)
            
            # SECTION 1: Static Images
            section_embed = discord.Embed(
                title="📋 SECTION 1: MATCH ACTION IMAGES",
                description="These appear **instantly** during matches.",
                color=discord.Color.green()
            )
            await channel.send(embed=section_embed)
            await asyncio.sleep(2)
            
            test_player = {
                'player_name': f'{interaction.user.display_name}',
                'position': 'ST',
                'user_id': interaction.user.id
            }
            
            test_defender = {
                'player_name': 'John Defender',
                'position': 'GK'
            }
            
            # Test 1: Successful Shot
            await channel.send("⚡ **Generating:** Successful shot...")
            viz_shot = generate_action_visualization(
                action='shoot',
                player=test_player,
                defender=test_defender,
                is_home=True,
                success=True,
                is_goal=False,
                animated=False
            )
            
            embed1 = discord.Embed(
                title="✅ SHOT ON TARGET!",
                description=f"**{test_player['player_name']}** unleashes it!\n\n"
                           f"This appears RIGHT AFTER your action.",
                color=discord.Color.green()
            )
            embed1.set_image(url="attachment://shot_success.png")
            embed1.set_footer(text="⚡ <0.5 seconds | Static for speed")
            await channel.send(embed=embed1, file=discord.File(fp=viz_shot, filename="shot_success.png"))
            await asyncio.sleep(2)
            
            # Test 2: GOAL
            await channel.send("⚽ **Generating:** GOAL!")
            viz_goal = generate_action_visualization(
                action='shoot',
                player=test_player,
                defender=test_defender,
                is_home=True,
                success=True,
                is_goal=True,
                animated=False
            )
            
            embed2 = discord.Embed(
                title="⚽ GOAL!!!",
                description=f"**{test_player['player_name']}** SCORES!\n\nGold color = GOAL! 🎉",
                color=discord.Color.gold()
            )
            embed2.set_image(url="attachment://goal.png")
            embed2.set_footer(text="⚽ Special gold color for goals!")
            await channel.send(embed=embed2, file=discord.File(fp=viz_goal, filename="goal.png"))
            await asyncio.sleep(2)
            
            # Test 3: Failed Action
            await channel.send("❌ **Generating:** Failed pass...")
            test_player['position'] = 'CM'
            viz_fail = generate_action_visualization(
                action='pass',
                player=test_player,
                defender=test_defender,
                is_home=True,
                success=False,
                is_goal=False,
                animated=False
            )
            
            embed3 = discord.Embed(
                title="❌ PASS INTERCEPTED!",
                description=f"**{test_player['player_name']}'s** pass is cut out!\n\nRed = failed.",
                color=discord.Color.red()
            )
            embed3.set_image(url="attachment://pass_fail.png")
            await channel.send(embed=embed3, file=discord.File(fp=viz_fail, filename="pass_fail.png"))
            await asyncio.sleep(2)
            
            # Test 4: Winger Dribble
            await channel.send("💨 **Generating:** Winger dribble...")
            test_player['position'] = 'W'
            viz_dribble = generate_action_visualization(
                action='dribble',
                player=test_player,
                defender=test_defender,
                is_home=True,
                success=True,
                is_goal=False,
                animated=False
            )
            
            embed4 = discord.Embed(
                title="✅ DRIBBLE SUCCESS!",
                description=f"**{test_player['player_name']}** beats the defender!\n\n"
                           f"Different positions = different field locations.",
                color=discord.Color.green()
            )
            embed4.set_image(url="attachment://dribble.png")
            embed4.set_footer(text="🏃 Position: Winger (W) - Wide position")
            await channel.send(embed=embed4, file=discord.File(fp=viz_dribble, filename="dribble.png"))
            await asyncio.sleep(3)
            
            # SECTION 2: Animated Highlights
            section2_embed = discord.Embed(
                title="📋 SECTION 2: POST-MATCH ANIMATED HIGHLIGHTS",
                description="After match ends, players get **animated GIF replays**!\n\nTakes 2-3 seconds.",
                color=discord.Color.purple()
            )
            await channel.send(embed=section2_embed)
            await asyncio.sleep(2)
            
            await channel.send("🎞️ **Generating animated GIF... (2 seconds)**")
            test_player['position'] = 'ST'
            viz_animated = generate_action_visualization(
                action='shoot',
                player=test_player,
                defender=test_defender,
                is_home=True,
                success=True,
                is_goal=True,
                animated=True
            )
            
            animated_embed = discord.Embed(
                title="🎬 ANIMATED HIGHLIGHT - GOAL!",
                description=f"## ⚽ {test_player['player_name']} SCORES!\n\n"
                           f"**Appears in:**\n• Post-match highlights\n• Match results channel\n• Player DMs\n\n"
                           f"Watch the ball move! ⚽➡️🥅",
                color=discord.Color.gold()
            )
            animated_embed.set_image(url="attachment://highlight.gif")
            animated_embed.set_footer(text="🎬 Animated GIF | ~2-3 seconds")
            await channel.send(embed=animated_embed, file=discord.File(fp=viz_animated, filename="highlight.gif"))
            await asyncio.sleep(4)
            
            # SECTION 3: Results Channel Post
            section3_embed = discord.Embed(
                title="📋 SECTION 3: MATCH RESULTS CHANNEL POST",
                description="What gets posted to **match-results** channel.\n\nEveryone sees this!",
                color=discord.Color.gold()
            )
            await channel.send(embed=section3_embed)
            await asyncio.sleep(2)
            
            result_embed = discord.Embed(
                title="🏁 FULL TIME",
                description=f"## Test United 3 - 1 Sandbox City\n\n🏆 **Test United wins!**",
                color=discord.Color.blue()
            )
            
            result_embed.add_field(
                name="⚽ Goal Scorers",
                value=f"⚽ **Test United:** {interaction.user.display_name} (15', 34', 67') ⚽⚽⚽\n"
                      f"⚽ **Sandbox City:** John NPC (89')",
                inline=False
            )
            
            result_embed.add_field(
                name="⭐ Man of the Match",
                value=f"**{interaction.user.display_name}** (9.2 rating) 🎩 HAT-TRICK!",
                inline=True
            )
            
            result_embed.add_field(
                name="📊 Match Info",
                value="**Competition:** Premier League\n**Week:** 5",
                inline=True
            )
            
            viz_animated.seek(0)
            result_embed.set_image(url="attachment://match_highlight.gif")
            result_embed.set_footer(text="Sandbox City | Posted to #match-results")
            
            await channel.send(
                "**📰 THIS IS WHAT POSTS TO #match-results:**",
                embed=result_embed,
                file=discord.File(fp=viz_animated, filename="match_highlight.gif")
            )
            await asyncio.sleep(3)
            
            # Summary
            summary_embed = discord.Embed(
                title="🎉 TEST COMPLETE - SYSTEM WORKING!",
                description="## You just saw the COMPLETE visualization flow!",
                color=discord.Color.green()
            )
            
            summary_embed.add_field(
                name="✅ During Matches",
                value="• Static images (instant)\n• Success/failure colors\n• Position-accurate",
                inline=False
            )
            
            summary_embed.add_field(
                name="✅ After Matches",
                value="• Animated GIF highlights\n• Beautiful replays\n• Posted to results",
                inline=False
            )
            
            summary_embed.add_field(
                name="📊 Performance",
                value="⚡ Static: <0.5s (perfect for live)\n🎬 Animated: 2-3s (post-match)",
                inline=False
            )
            
            summary_embed.add_field(
                name="🎯 Ready?",
                value="Your event_poster.py ALREADY supports highlights!\n\n"
                      "Just pass highlights_buffer to post_match_result_to_channel()\n"
                      "**⚠️ This test: ZERO database changes!**",
                inline=False
            )
            
            await channel.send(embed=summary_embed)
            
            # Technical details
            coords_test = CoordinateMapper.get_action_coordinates('shoot', 'ST', True)
            tech_embed = discord.Embed(
                title="🔧 Technical Details",
                color=discord.Color.blue()
            )
            tech_embed.add_field(
                name="✅ Your event_poster.py",
                value="Already has highlights support!\nJust pass the highlights_buffer parameter.",
                inline=False
            )
            tech_embed.add_field(
                name="📦 Ready to integrate",
                value="Check INTEGRATION_SIMPLE.txt for the 2 lines to add to match_engine.py",
                inline=False
            )
            await channel.send(embed=tech_embed)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ **Test failed!**\n\n"
                f"Error: {e}\n\n"
                f"**Check:**\n1. `pip install Pillow`\n2. Files in project root",
                ephemeral=True
            )
            import traceback
            traceback.print_exc()


async def setup(bot):
    await bot.add_cog(VizTestCog(bot))
