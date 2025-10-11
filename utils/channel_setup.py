"""
Automatic Channel Setup for New Servers
"""
import discord

async def setup_server_channels(guild: discord.Guild):
    """Auto-create required channels if they don't exist"""
    
    print(f"🔧 Setting up channels for {guild.name}...")
    
    # Check for category
    category = discord.utils.get(guild.categories, name="⚽ FOOTBALL BOT")
    if not category:
        category = await guild.create_category("⚽ FOOTBALL BOT")
        print(f"  ✅ Created category")
    
    # Required channels
    required_channels = {
        'match-results': 'Match results and summaries',
        'transfer-news': 'Player transfers and signings',
        'news-feed': 'Weekly news digests',
    }
    
    created = 0
    for channel_name, topic in required_channels.items():
        existing = discord.utils.get(guild.text_channels, name=channel_name)
        if not existing:
            await guild.create_text_channel(
                name=channel_name,
                category=category,
                topic=topic
            )
            created += 1
            print(f"  ✅ Created #{channel_name}")
        else:
            print(f"  ✅ #{channel_name} already exists")
    
    if created > 0:
        print(f"✅ Created {created} new channels")
    else:
        print(f"✅ All channels already exist")
    
    return True
