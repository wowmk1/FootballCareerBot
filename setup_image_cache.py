"""
Image Cache Setup Script
Run this once to create the database table and cache images from Imgur
"""
import asyncio
import asyncpg
import requests
import io
from PIL import Image
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')

# Image URLs
IMAGE_URLS = {
    'stadium': 'https://i.imgur.com/7kJf34C.jpeg',
    'player_home': 'https://i.imgur.com/9KXzzpq.png',
    'player_away': 'https://i.imgur.com/5pTYlbS.png',
    'defender_home': 'https://i.imgur.com/GgpU26d.png',
    'defender_away': 'https://i.imgur.com/Z8pibql.png',
    'goalie_home': 'https://i.imgur.com/4j6Vnva.png',
    'goalie_away': 'https://i.imgur.com/LcaDRG1.png',
    'ball': 'https://i.imgur.com/39woCj8.png'
}


async def create_table(conn):
    """Create the image_cache table"""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS image_cache (
            image_key VARCHAR(50) PRIMARY KEY,
            image_data BYTEA NOT NULL,
            image_format VARCHAR(10) NOT NULL,
            width INTEGER NOT NULL,
            height INTEGER NOT NULL,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_size INTEGER NOT NULL
        )
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_image_cache_last_accessed 
        ON image_cache(last_accessed)
    """)
    
    print("✅ Table 'image_cache' created successfully!")


def download_image(url):
    """Download image from URL"""
    print(f"  Downloading: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    # Load image
    img = Image.open(io.BytesIO(response.content))
    
    # Convert to bytes
    buffer = io.BytesIO()
    img_format = img.format or 'PNG'
    img.save(buffer, format=img_format)
    image_bytes = buffer.getvalue()
    
    return {
        'data': image_bytes,
        'format': img_format,
        'width': img.width,
        'height': img.height,
        'size': len(image_bytes)
    }


async def cache_image(conn, key, url):
    """Download and cache a single image"""
    try:
        # Check if already cached
        existing = await conn.fetchrow(
            "SELECT image_key FROM image_cache WHERE image_key = $1",
            key
        )
        
        if existing:
            print(f"  ⏭️  '{key}' already cached, skipping...")
            return True
        
        # Download image
        img_data = download_image(url)
        
        # Insert into database
        await conn.execute("""
            INSERT INTO image_cache 
            (image_key, image_data, image_format, width, height, file_size)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, key, img_data['data'], img_data['format'], 
            img_data['width'], img_data['height'], img_data['size'])
        
        print(f"  ✅ Cached '{key}' ({img_data['size'] // 1024} KB)")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to cache '{key}': {e}")
        return False


async def setup_image_cache():
    """Main setup function"""
    print("=" * 60)
    print("IMAGE CACHE SETUP")
    print("=" * 60)
    
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL not found in environment variables!")
        print("   Make sure your .env file contains DATABASE_URL")
        return
    
    print(f"\n📦 Connecting to database...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database!")
        
        # Create table
        print("\n📋 Creating table...")
        await create_table(conn)
        
        # Cache all images
        print(f"\n🖼️  Caching {len(IMAGE_URLS)} images from Imgur...")
        success_count = 0
        
        for key, url in IMAGE_URLS.items():
            if await cache_image(conn, key, url):
                success_count += 1
        
        # Show summary
        print("\n" + "=" * 60)
        print(f"✅ SETUP COMPLETE!")
        print(f"   Successfully cached: {success_count}/{len(IMAGE_URLS)} images")
        
        # Show cache stats
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_images,
                SUM(file_size) as total_size,
                AVG(file_size) as avg_size
            FROM image_cache
        """)
        
        print(f"   Total cache size: {stats['total_size'] // 1024} KB")
        print(f"   Average image size: {stats['avg_size'] // 1024} KB")
        print("=" * 60)
        
        await conn.close()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 Starting image cache setup...\n")
    asyncio.run(setup_image_cache())
    print("\n✅ You can now use the visualizer with database caching!")
    print("   Images will load instantly from PostgreSQL instead of Imgur.\n")
