"""
Helper function to generate combined team crest images
Creates a single PNG with both team crests side-by-side
"""

import aiohttp
from io import BytesIO
from PIL import Image


async def generate_combined_crests(home_url, away_url):
    """
    Generate a single image with both team crests side-by-side
    
    Args:
        home_url: URL to home team crest image
        away_url: URL to away team crest image
    
    Returns:
        BytesIO buffer with PNG image, or None if failed
    """
    print(f"🖼️ Generating crests: home={home_url}, away={away_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            home_img_bytes = None
            away_img_bytes = None
            
            # Fetch home team crest
            if home_url:
                try:
                    print(f"  Fetching home crest...")
                    async with session.get(home_url, timeout=aiohttp.ClientTimeout(total=5)) as r:
                        if r.status == 200:
                            home_img_bytes = await r.read()
                            print(f"  ✅ Home crest fetched: {len(home_img_bytes)} bytes")
                        else:
                            print(f"  ❌ Home crest failed: status {r.status}")
                except Exception as e:
                    print(f"  ❌ Failed to fetch home crest: {e}")
            
            # Fetch away team crest
            if away_url:
                try:
                    print(f"  Fetching away crest...")
                    async with session.get(away_url, timeout=aiohttp.ClientTimeout(total=5)) as r:
                        if r.status == 200:
                            away_img_bytes = await r.read()
                            print(f"  ✅ Away crest fetched: {len(away_img_bytes)} bytes")
                        else:
                            print(f"  ❌ Away crest failed: status {r.status}")
                except Exception as e:
                    print(f"  ❌ Failed to fetch away crest: {e}")
        
        # Create canvas for both crests
        size = (100, 100)
        padding = 40
        width = size[0] * 2 + padding
        height = size[1]
        img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        
        # Paste home team crest on left
        if home_img_bytes:
            try:
                home = Image.open(BytesIO(home_img_bytes)).convert("RGBA").resize(size)
                img.paste(home, (0, 0), home)
                print(f"  ✅ Home crest pasted")
            except Exception as e:
                print(f"  ❌ Failed to process home crest: {e}")
        
        # Paste away team crest on right
        if away_img_bytes:
            try:
                away = Image.open(BytesIO(away_img_bytes)).convert("RGBA").resize(size)
                img.paste(away, (size[0] + padding, 0), away)
                print(f"  ✅ Away crest pasted")
            except Exception as e:
                print(f"  ❌ Failed to process away crest: {e}")
        
        # Save to buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        print(f"  ✅ Combined crests image created: {buffer.tell()} bytes")
        return buffer
        
    except Exception as e:
        print(f"❌ Error generating combined crests: {e}")
        import traceback
        traceback.print_exc()
        return None
