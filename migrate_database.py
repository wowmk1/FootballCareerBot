"""
Full Database Migration Script for FootballCareerBot
Creates league_table, transfer_offers, and adds transfer columns
Run this once to setup the database
"""
import asyncio
import asyncpg
import config
import sys

async def run_migration():
    try:
        print("Connecting to database...")
        conn = await asyncpg.connect(config.DATABASE_URL)

        print("Running migration...")

        # ---------------------------
        # 1. Create league_table
        # ---------------------------
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS league_table (
            id SERIAL PRIMARY KEY,
            season INT NOT NULL,
            team_id TEXT NOT NULL,
            played INT DEFAULT 0,
            won INT DEFAULT 0,
            drawn INT DEFAULT 0,
            lost INT DEFAULT 0,
            goals_for INT DEFAULT 0,
            goals_against INT DEFAULT 0,
            points INT DEFAULT 0
        );
        """)
        print("✅ Created league_table")

        # ---------------------------
        # 2. Add transfer columns to players table
        # ---------------------------
        await conn.execute("""
            ALTER TABLE players ADD COLUMN IF NOT EXISTS last_transfer_window INTEGER;
        """)
        print("✅ Added last_transfer_window column to players")

        await conn.execute("""
            ALTER TABLE players ADD COLUMN IF NOT EXISTS transfers_this_season INTEGER DEFAULT 0;
        """)
        print("✅ Added transfers_this_season column to players")

        # ---------------------------
        # 3. Create transfer_offers table
        # ---------------------------
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

        # ---------------------------
        # 4. Add indexes for transfer_offers
        # ---------------------------
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

        # ---------------------------
        # 5. Add transfer_window_active to game_state
        # ---------------------------
        await conn.execute("""
            ALTER TABLE game_state ADD COLUMN IF NOT EXISTS transfer_window_active BOOLEAN DEFAULT FALSE;
        """)
        print("✅ Added transfer_window_active column to game_state")

        await conn.close()
        print("\n🎉 Full migration completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(run_migration())
    sys.exit(0 if result else 1)
