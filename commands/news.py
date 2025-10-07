import discord
from discord import app_commands
from discord.ext import commands
from database import db

class NewsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="news", description="View your personalized news feed")
    async def news(self, interaction: discord.Interaction):
        """View news feed"""
        
        player = await db.get_player(interaction.user.id)
        
        if player:
            news_items = await db.get_recent_news(interaction.user.id, limit=10)
        else:
            news_items = await db.get_recent_news(None, limit=10)
        
        if not news_items:
            await interaction.response.send_message(
                "📰 No news yet! Start your career with `/start` to generate news.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="📰 Football News Feed",
            description="Latest updates from around the league",
            color=discord.Color.blue()
        )
        
        category_emojis = {
            'player_news': '⭐',
            'league_news': '🏆',
            'match_news': '⚽',
            'transfer_news': '💼',
            'injury_news': '🤕',
        }
        
        for news in news_items[:8]:
            emoji = category_emojis.get(news['category'], '📌')
            
            created = news['created_at']
            if isinstance(created, str):
                time_str = created[:10]
            else:
                time_str = created.strftime('%Y-%m-%d')
            
            embed.add_field(
                name=f"{emoji} {news['headline']}",
                value=f"{news['content']}\n*Week {news['week_number']} • {time_str}*",
                inline=False
            )
        
        state = await db.get_game_state()
        embed.set_footer(text=f"Season {state['current_season']} • Week {state['current_week']}")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(NewsCommands(bot))
