"""
Add MOTM column to match_participants table
Run this once: python add_match_participants_motm.py
"""
import asyncio
import asyncpg
import os

DATABASE_URL = os.getenv('DATABASE_URL')

async def add_motm_column():
    """Add motm BOOLEAN column to match_participants table"""
    
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
            WHERE table_name = 'match_participants' AND column_name = 'motm'
        """)
        
        if not result:
            print("📋 Adding motm column to match_participants...")
            await conn.execute("""
                ALTER TABLE match_participants 
                ADD COLUMN motm BOOLEAN DEFAULT FALSE
            """)
            print("  ✅ Added motm column")
        else:
            print("  ✅ motm column already exists")
        
        # Set default values for existing records
        await conn.execute("""
            UPDATE match_participants 
            SET motm = FALSE 
            WHERE motm IS NULL
        """)
        
        print("✅ All existing match participants updated with motm = FALSE")
        
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
    print("ADD MATCH_PARTICIPANTS MOTM COLUMN MIGRATION")
    print("=" * 60)
    
    result = asyncio.run(add_motm_column())
    
    if result:
        print("\n✅ Database is ready!")
    else:
        print("\n⚠️ Migration had issues.")
