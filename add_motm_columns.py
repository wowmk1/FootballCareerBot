"""
Add MOTM columns to players table
Run this once: python add_motm_columns.py
"""
import asyncio
import asyncpg
import os

DATABASE_URL = os.getenv('DATABASE_URL')

async def add_motm_columns():
    """Add season_motm and career_motm columns to players table"""
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found")
        return False
    
    try:
        print("🔄 Connecting to database...")
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected")
        
        # Check if columns exist
        result = await conn.fetchrow("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'players' AND column_name = 'season_motm'
        """)
        
        if not result:
            print("📋 Adding season_motm column...")
            await conn.execute("""
                ALTER TABLE players 
                ADD COLUMN season_motm INTEGER DEFAULT 0
            """)
            print("  ✅ Added season_motm")
        else:
            print("  ✅ season_motm already exists")
        
        result = await conn.fetchrow("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'players' AND column_name = 'career_motm'
        """)
        
        if not result:
            print("📋 Adding career_motm column...")
            await conn.execute("""
                ALTER TABLE players 
                ADD COLUMN career_motm INTEGER DEFAULT 0
            """)
            print("  ✅ Added career_motm")
        else:
            print("  ✅ career_motm already exists")
        
        # Set default values for existing players
        await conn.execute("""
            UPDATE players 
            SET season_motm = 0 
            WHERE season_motm IS NULL
        """)
        
        await conn.execute("""
            UPDATE players 
            SET career_motm = 0 
            WHERE career_motm IS NULL
        """)
        
        print("✅ All existing players updated with MOTM = 0")
        
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
    print("ADD MOTM COLUMNS MIGRATION")
    print("=" * 60)
    
    result = asyncio.run(add_motm_columns())
    
    if result:
        print("\n✅ Database is ready!")
    else:
        print("\n⚠️ Migration had issues.")
