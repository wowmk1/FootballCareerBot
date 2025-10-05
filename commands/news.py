import discord
from discord import app_commands
from discord.ext import commands
from database import db
from datetime import datetime

class NewsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="news", description="View your personalized news feed")
    async def news(self, interaction: discord.Interaction):
        """View news feed"""
        
        player = await db.get_player(interaction.user.id)
        
        if not player:
            await interaction.response.send_message(
                "❌ You haven't created a player yet! Use `/start` to begin.",
                ephemeral=True
            )
            return
        
        news_items = await db.get_recent_news(interaction.user.id, limit=10)
        
        if not news_items:
            embed = discord.Embed(
                title="📰 Your News Feed",
                description="Welcome to your career! News about your matches, transfers, and achievements will appear here.",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="💡 Stay Active!",
                value=(
                    "• Train daily to improve\n"
                    "• Sign for a club\n"
                    "• Play matches\n"
                    "• Complete achievements\n\n"
                    "Your story starts now!"
                ),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title="📰 Your Football News",
            description=f"Latest updates for **{player['player_name']}**:",
            color=discord.Color.blue()
        )
        
        categories = {
            'match_news': '⚽ Match Reports',
            'transfer_news': '💼 Transfer News',
            'player_news': '📈 Player Updates',
            'league_news': '🏆 League News',
            'achievement': '🏅 Achievements'
        }
        
        news_by_category = {}
        for item in news_items:
            category = item['category'] or 'general'
            if category not in news_by_category:
                news_by_category[category] = []
            news_by_category[category].append(item)
        
        total_shown = 0
        for category, items in news_by_category.items():
            if total_shown >= 5:
                break
            
            category_name = categories.get(category, '📰 News')
            news_text = []
            
            for item in items[:3]:
                try:
                    created = datetime.fromisoformat(item['created_at'])
                    time_ago = self._time_ago(created)
                except:
                    time_ago = "recently"
                
                week_info = f"Week {item['week_number']}" if item['week_number'] else ""
                news_text.append(f"**{item['headline']}**\n_{time_ago}_ {week_info}")
                total_shown += 1
            
            if news_text:
                embed.add_field(
                    name=category_name,
                    value="\n\n".join(news_text),
                    inline=False
                )
        
        embed.set_footer(text="News updates automatically as you play!")
        
        await interaction.response.send_message(embed=embed)
    
    def _time_ago(self, dt):
        """Convert datetime to 'X ago' format"""
        now = datetime.now()
        diff = now - dt
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours}h ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days}d ago"
        else:
            weeks = int(seconds / 604800)
            return f"{weeks}w ago"

async def setup(bot):
    await bot.add_cog(NewsCommands(bot))
