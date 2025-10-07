"""
Database Migration Script for Railway/GitHub Deployment
Automatically runs necessary database changes
Safe to run multiple times (checks before applying changes)
"""

import asyncio
import asyncpg
import os
import sys

DATABASE_URL = os.getenv('DATABASE_URL')

async def run_migrations():
    """Run all database migrations"""
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment variables")
        return False
    
    try:
        print("🔄 Connecting to database...")
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database")
        
        # Migration 1: Check if is_regen column exists
        print("\n📋 Migration 1: Checking is_regen column...")
        result = await conn.fetchrow("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'npc_players' AND column_name = 'is_regen'
        """)
        
        if not result:
            print("  Adding is_regen column...")
            await conn.execute("""
                ALTER TABLE npc_players 
                ADD COLUMN is_regen BOOLEAN DEFAULT FALSE
            """)
            print("  ✅ Added is_regen column")
        else:
            print("  ✅ is_regen column already exists")
        
        # Migration 2: Check if form and morale have proper defaults
        print("\n📋 Migration 2: Checking form and morale columns...")
        
        result = await conn.fetchrow("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'players' AND column_name = 'form'
        """)
        
        if result:
            # Ensure all players have form values
            await conn.execute("""
                UPDATE players 
                SET form = 50 
                WHERE form IS NULL OR form = 0
            """)
            print("  ✅ Form values normalized")
        
        result = await conn.fetchrow("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'players' AND column_name = 'morale'
        """)
        
        if result:
            # Ensure all players have morale values
            await conn.execute("""
                UPDATE players 
                SET morale = 75 
                WHERE morale IS NULL OR morale = 0
            """)
            print("  ✅ Morale values normalized")
        
        # Migration 3: Add indexes for performance if missing
        print("\n📋 Migration 3: Adding performance indexes...")
        
        indexes = [
            ('idx_npc_is_regen', 'CREATE INDEX IF NOT EXISTS idx_npc_is_regen ON npc_players(is_regen)'),
            ('idx_npc_retired', 'CREATE INDEX IF NOT EXISTS idx_npc_retired ON npc_players(retired)'),
            ('idx_npc_team_retired', 'CREATE INDEX IF NOT EXISTS idx_npc_team_retired ON npc_players(team_id, retired)'),
            ('idx_transfers_npc', 'CREATE INDEX IF NOT EXISTS idx_transfers_npc ON transfers(npc_id)'),
            ('idx_transfers_date', 'CREATE INDEX IF NOT EXISTS idx_transfers_date ON transfers(transfer_date DESC)'),
        ]
        
        for index_name, index_sql in indexes:
            await conn.execute(index_sql)
            print(f"  ✅ {index_name}")
        
        # Migration 4: Verify critical tables exist
        print("\n📋 Migration 4: Verifying critical tables...")
        
        tables = ['players', 'teams', 'npc_players', 'fixtures', 'transfers', 
                 'match_participants', 'active_matches', 'game_state']
        
        for table in tables:
            result = await conn.fetchrow("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = $1
                )
            """, table)
            
            if result['exists']:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} - MISSING! Database may need full initialization")
        
        # Migration 5: Count data for verification
        print("\n📋 Data Verification:")
        
        result = await conn.fetchrow("SELECT COUNT(*) as count FROM teams")
        print(f"  Teams: {result['count']}")
        
        result = await conn.fetchrow("SELECT COUNT(*) as count FROM npc_players WHERE retired = FALSE")
        print(f"  Active NPC Players: {result['count']}")
        
        result = await conn.fetchrow("SELECT COUNT(*) as count FROM npc_players WHERE is_regen = TRUE")
        print(f"  Regen Players: {result['count']}")
        
        result = await conn.fetchrow("SELECT COUNT(*) as count FROM players WHERE retired = FALSE")
        print(f"  Active User Players: {result['count']}")
        
        await conn.close()
        print("\n✅ All migrations completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE MIGRATION SCRIPT")
    print("=" * 60)
    
    result = asyncio.run(run_migrations())
    
    if result:
        print("\n🎉 Database is ready!")
        sys.exit(0)
    else:
        print("\n⚠️ Migration had issues. Check errors above.")
        sys.exit(1)
