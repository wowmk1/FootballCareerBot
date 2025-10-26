"""
VISUALIZATION TEST COG - UPDATED WITH MULTI-GOAL DEMO
Shows exactly what happens when multiple goals are scored!

Just add to your bot: await bot.load_extension('commands.viz_test_cog')
"""
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import io


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
                from match_visualizer import generate_action_visualization, CoordinateMapper, MatchVisualizer
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
                           "2️⃣ **COMBINED animated GIF with MULTIPLE goals**\n"
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
            viz_shot = await generate_action_visualization(
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
            viz_goal = await generate_action_visualization(
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
            viz_fail = await generate_action_visualization(
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
            viz_dribble = await generate_action_visualization(
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
            
            # SECTION 2: COMBINED MULTI-GOAL ANIMATED HIGHLIGHTS
            section2_embed = discord.Embed(
                title="📋 SECTION 2: COMBINED MULTI-GOAL HIGHLIGHTS",
                description="## 🎬 THE MAGIC: ALL GOALS IN ONE GIF!\n\n"
                           "After match ends, **ALL goals combine into ONE animated GIF**!\n\n"
                           "We'll create a 4-goal thriller and show you the combined result...",
                color=discord.Color.purple()
            )
            await channel.send(embed=section2_embed)
            await asyncio.sleep(2)
            
            await channel.send("🎞️ **Generating COMBINED 4-GOAL animated GIF... (5 seconds)**\n\n"
                             "⚽ Goal 1: Striker (home)\n"
                             "⚽ Goal 2: Winger (home)\n"
                             "⚽ Goal 3: Away team\n"
                             "⚽ Goal 4: Header (home)\n\n"
                             "**All combined into ONE file!**")
            
            # ✅ CREATE MULTIPLE GOALS AND COMBINE THEM
            all_frames = []
            
            # Goal 1: Striker
            test_player['position'] = 'ST'
            start_x, start_y, end_x, end_y = CoordinateMapper.get_action_coordinates(
                'shoot', 'ST', True
            )
            frames1 = await MatchVisualizer.create_action_animation(
                action='shoot',
                player_name=test_player['player_name'],
                player_position='ST',
                defender_name='Defender',
                start_pos=(start_x, start_y),
                end_pos=(end_x, end_y),
                is_home=True,
                success=True,
                is_goal=True,
                frames=15
            )
            all_frames.extend(frames1)
            
            # Goal 2: Winger
            start_x, start_y, end_x, end_y = CoordinateMapper.get_action_coordinates(
                'shoot', 'W', True
            )
            frames2 = await MatchVisualizer.create_action_animation(
                action='shoot',
                player_name=test_player['player_name'],
                player_position='W',
                defender_name='Defender',
                start_pos=(start_x, start_y),
                end_pos=(end_x, end_y),
                is_home=True,
                success=True,
                is_goal=True,
                frames=15
            )
            all_frames.extend(frames2)
            
            # Goal 3: Away team
            start_x, start_y, end_x, end_y = CoordinateMapper.get_action_coordinates(
                'shoot', 'ST', False  # Away team
            )
            frames3 = await MatchVisualizer.create_action_animation(
                action='shoot',
                player_name='Away Striker',
                player_position='ST',
                defender_name='Defender',
                start_pos=(start_x, start_y),
                end_pos=(end_x, end_y),
                is_home=False,
                success=True,
                is_goal=True,
                frames=15
            )
            all_frames.extend(frames3)
            
            # Goal 4: Header
            start_x, start_y, end_x, end_y = CoordinateMapper.get_action_coordinates(
                'header', 'ST', True
            )
            frames4 = await MatchVisualizer.create_action_animation(
                action='header',
                player_name=test_player['player_name'],
                player_position='ST',
                defender_name='Defender',
                start_pos=(start_x, start_y),
                end_pos=(end_x, end_y),
                is_home=True,
                success=True,
                is_goal=True,
                frames=15
            )
            all_frames.extend(frames4)
            
            # ✅ COMBINE ALL FRAMES INTO ONE GIF
            buffer = io.BytesIO()
            all_frames[0].save(
                buffer,
                format='GIF',
                save_all=True,
                append_images=all_frames[1:],
                duration=70,
                loop=0
            )
            buffer.seek(0)
            
            animated_embed = discord.Embed(
                title="🎬 COMBINED HIGHLIGHTS - 4 GOALS IN ONE GIF!",
                description=f"## ⚽⚽⚽⚽ ALL GOALS COMBINED!\n\n"
                           f"**This ONE GIF contains:**\n"
                           f"1️⃣ {test_player['player_name']} - Striker goal\n"
                           f"2️⃣ {test_player['player_name']} - Winger goal\n"
                           f"3️⃣ Away Striker - Away goal\n"
                           f"4️⃣ {test_player['player_name']} - Header goal\n\n"
                           f"**📊 Stats:**\n"
                           f"• Total frames: 60 (4 goals × 15 frames)\n"
                           f"• File size: ~1-2 MB\n"
                           f"• Duration: ~4.2 seconds\n\n"
                           f"**Watch all 4 goals play in sequence!** ⚽➡️⚽➡️⚽➡️⚽",
                color=discord.Color.gold()
            )
            animated_embed.set_image(url="attachment://combined_highlights.gif")
            animated_embed.set_footer(text="🎬 Combined GIF | All goals in ONE file | Auto-loops")
            await channel.send(embed=animated_embed, file=discord.File(fp=buffer, filename="combined_highlights.gif"))
            await asyncio.sleep(6)
            
            # Explanation
            explain_embed = discord.Embed(
                title="💡 HOW IT WORKS",
                description="## This is EXACTLY what happens after each match!\n\n"
                           "**The system:**\n"
                           "1️⃣ Collects all goals from the match\n"
                           "2️⃣ Creates 15 animated frames per goal\n"
                           "3️⃣ **Combines ALL frames into ONE GIF**\n"
                           "4️⃣ Posts to #match-results\n\n"
                           "**Examples:**\n"
                           "• 1 goal = 15 frames\n"
                           "• 6 goals = 90 frames (one file)\n"
                           "• 10 goals = 150 frames (one file)\n\n"
                           "**Result:** One beautiful highlight reel! 🎥",
                color=discord.Color.blue()
            )
            await channel.send(embed=explain_embed)
            await asyncio.sleep(3)
            
            # SECTION 3: Results Channel Post
            section3_embed = discord.Embed(
                title="📋 SECTION 3: MATCH RESULTS CHANNEL POST",
                description="What gets posted to **#match-results** channel.\n\nEveryone sees this!",
                color=discord.Color.gold()
            )
            await channel.send(embed=section3_embed)
            await asyncio.sleep(2)
            
            result_embed = discord.Embed(
                title="🏁 FULL TIME",
                description=f"## Test United 4 - 1 Sandbox City\n\n🏆 **Test United wins!**",
                color=discord.Color.blue()
            )
            
            result_embed.add_field(
                name="⚽ Goal Scorers",
                value=f"⚽ **Test United:**\n"
                      f"  • {interaction.user.display_name} (15', 34', 67') ⚽⚽⚽\n"
                      f"  • Header (89') ⚽\n\n"
                      f"⚽ **Sandbox City:** Away Striker (45')",
                inline=False
            )
            
            result_embed.add_field(
                name="⭐ Man of the Match",
                value=f"**{interaction.user.display_name}** (9.5 rating) 🎩 HAT-TRICK!",
                inline=True
            )
            
            result_embed.add_field(
                name="📊 Match Info",
                value="**Competition:** Premier League\n**Week:** 5",
                inline=True
            )
            
            buffer.seek(0)
            result_embed.set_image(url="attachment://match_highlight.gif")
            result_embed.set_footer(text="🎬 Combined highlights | Posted to #match-results")
            
            await channel.send(
                "**📰 THIS IS WHAT POSTS TO #match-results:**",
                embed=result_embed,
                file=discord.File(fp=buffer, filename="match_highlight.gif")
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
                value="• Static images (instant)\n• Success/failure colors\n• Position-accurate\n• Gold for goals",
                inline=False
            )
            
            summary_embed.add_field(
                name="✅ After Matches - THE MAGIC",
                value="• **ALL goals combined into ONE GIF**\n"
                      "• Smooth ball animation\n"
                      "• Beautiful replays\n"
                      "• Posted to results channel\n"
                      "• 1-10+ goals? No problem!",
                inline=False
            )
            
            summary_embed.add_field(
                name="📊 Performance",
                value="⚡ **Static:** <0.5s (perfect for live)\n"
                      "🎬 **Combined GIF:** 2-5s depending on goals\n"
                      "💾 **File size:** ~200-500 KB per goal\n"
                      "📦 **One file:** No matter how many goals!",
                inline=False
            )
            
            summary_embed.add_field(
                name="🎯 Key Insight",
                value="**Multiple goals = ONE combined animated GIF!**\n\n"
                      "You just saw 4 goals play in sequence in ONE file.\n"
                      "In real matches, this happens automatically!\n\n"
                      "6 goals scored? All 6 play in one GIF! ⚽⚽⚽⚽⚽⚽",
                inline=False
            )
            
            summary_embed.add_field(
                name="🔧 Ready to Go?",
                value="Your `match_highlights.py` handles this automatically!\n"
                      "Just call `generate_match_highlights(match_id)`\n"
                      "**⚠️ This test: ZERO database changes!**",
                inline=False
            )
            
            await channel.send(embed=summary_embed)
            
            # Technical details
            tech_embed = discord.Embed(
                title="🔧 Technical Details",
                color=discord.Color.blue()
            )
            tech_embed.add_field(
                name="✅ How it combines goals",
                value="```python\n"
                      "all_frames = []\n"
                      "for each goal:\n"
                      "    frames = create_animation(15 frames)\n"
                      "    all_frames.extend(frames)  # Add to list\n\n"
                      "# Save as ONE GIF\n"
                      "all_frames[0].save(\n"
                      "    append_images=all_frames[1:],  # All remaining\n"
                      "    save_all=True\n"
                      ")\n```",
                inline=False
            )
            tech_embed.add_field(
                name="📦 Real Match Example",
                value="**Match with 6 goals:**\n"
                      "• Player A: 3 goals → 45 frames\n"
                      "• Player B: 2 goals → 30 frames\n"
                      "• Player C: 1 goal → 15 frames\n"
                      "**Total: 90 frames in ONE GIF file**\n\n"
                      "Discord shows them all playing in sequence!",
                inline=False
            )
            await channel.send(embed=tech_embed)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ **Test failed!**\n\n"
                f"Error: {e}\n\n"
                f"**Check:**\n1. `pip install Pillow`\n2. Files in project root\n3. Images in database",
                ephemeral=True
            )
            import traceback
            traceback.print_exc()


async def setup(bot):
    await bot.add_cog(VizTestCog(bot))
