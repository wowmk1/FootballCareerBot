"""
Migration script - Adds current_match_of_week to database, then starts bot
"""
import asyncio
import asyncpg
import os
import subprocess
import sys

DATABASE_URL = os.getenv('DATABASE_URL')

async def add_match_counter():
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found")
        return False
    
    try:
        print("🔄 Connecting to database...")
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected")
        
        print("📋 Adding current_match_of_week column...")
        await conn.execute("""
            ALTER TABLE game_state 
            ADD COLUMN IF NOT EXISTS current_match_of_week INTEGER DEFAULT 0
        """)
        print("  ✅ Added current_match_of_week column")
        
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
    print("RUNNING DATABASE MIGRATION")
    print("=" * 60)
    
    result = asyncio.run(add_match_counter())
    
    if result:
        print("\n✅ Database migrated successfully!")
    else:
        print("\n⚠️ Migration had issues, but continuing...")
    
    print("\n" + "=" * 60)
    print("STARTING BOT")
    print("=" * 60 + "\n")
    
    subprocess.run([sys.executable, "bot.py"])
