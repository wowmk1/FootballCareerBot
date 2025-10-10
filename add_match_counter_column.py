"""
Add current_match_of_week column - Run this once
"""
import asyncio
import asyncpg
import os

DATABASE_URL = os.getenv('DATABASE_URL')

async def add_match_counter():
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found")
        return False
    
    try:
        print("🔄 Connecting to database...")
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected")
        
        # Check if column exists
        result = await conn.fetchrow("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'game_state' AND column_name = 'current_match_of_week'
        """)
        
        if not result:
            print("📋 Adding current_match_of_week column...")
            await conn.execute("""
                ALTER TABLE game_state 
                ADD COLUMN current_match_of_week INTEGER DEFAULT 0
            """)
            print("  ✅ Added current_match_of_week")
        else:
            print("  ✅ current_match_of_week already exists")
        
        await conn.execute("""
            UPDATE game_state 
            SET current_match_of_week = 0 
            WHERE current_match_of_week IS NULL
        """)
        
        await conn.close()
        print("\n🎉 Migration complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ADD MATCH COUNTER COLUMN")
    print("=" * 60)
    
    result = asyncio.run(add_match_counter())
    
    if result:
        print("\n✅ Database is ready!")
    else:
        print("\n⚠️ Migration had issues.")
