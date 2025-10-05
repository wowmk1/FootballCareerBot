import asyncio
import asyncpg
import config

async def run_migration():
    conn = await asyncpg.connect(config.DATABASE_URL)
    
    print("Running migration...")
    
    # Add columns to players table
    await conn.execute("""
        ALTER TABLE players ADD COLUMN IF NOT EXISTS last_transfer_window INTEGER;
    """)
    print("✅ Added last_transfer_window column")
    
    await conn.execute("""
        ALTER TABLE players ADD COLUMN IF NOT EXISTS transfers_this_season INTEGER DEFAULT 0;
    """)
    print("✅ Added transfers_this_season column")
    
    # Create transfer_offers table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS transfer_offers (
            offer_id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            team_id TEXT NOT NULL,
            wage_offer INTEGER NOT NULL,
            contract_length INTEGER NOT NULL,
            offer_week INTEGER NOT NULL,
            expires_week INTEGER NOT NULL,
            offer_type TEXT DEFAULT 'standard',
            previous_offer_id INTEGER,
            performance_bonus INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("✅ Created transfer_offers table")
    
    # Create indexes
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_transfer_offers_user_status 
        ON transfer_offers(user_id, status);
    """)
    print("✅ Created index on user_id and status")
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_transfer_offers_week 
        ON transfer_offers(offer_week);
    """)
    print("✅ Created index on offer_week")
    
    # Add column to game_state
    await conn.execute("""
        ALTER TABLE game_state ADD COLUMN IF NOT EXISTS transfer_window_active BOOLEAN DEFAULT FALSE;
    """)
    print("✅ Added transfer_window_active column")
    
    await conn.close()
    print("\n🎉 Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_migration())
