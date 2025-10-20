"""
Safe NPC Stats Diagnostic Script
Run this to check what's wrong WITHOUT breaking anything
"""
import asyncio
from database import db

async def diagnose_npc_stats():
    """Check NPC stat integrity"""
    
    print("\n" + "="*70)
    print("🔍 NPC STATS DIAGNOSTIC")
    print("="*70)
    
    # 1. Check if NPCs have individual stats
    async with db.pool.acquire() as conn:
        # Sample a few Championship NPCs
        npcs = await conn.fetch("""
            SELECT 
                n.player_name,
                n.position,
                n.overall_rating,
                n.pace,
                n.shooting,
                n.passing,
                n.dribbling,
                n.defending,
                n.physical,
                t.team_name,
                t.league
            FROM npc_players n
            JOIN teams t ON n.team_id = t.team_id
            WHERE t.league = 'Championship' 
            AND n.retired = FALSE
            LIMIT 10
        """)
        
        if not npcs:
            print("❌ NO CHAMPIONSHIP NPCS FOUND!")
            return
        
        print(f"\n📊 Sample of {len(npcs)} Championship NPCs:\n")
        
        missing_stats = []
        
        for npc in npcs:
            print(f"\n{npc['player_name']} ({npc['position']}) - {npc['team_name']}")
            print(f"   Overall: {npc['overall_rating']}")
            
            # Check each stat
            stats = {
                'Pace': npc['pace'],
                'Shooting': npc['shooting'],
                'Passing': npc['passing'],
                'Dribbling': npc['dribbling'],
                'Defending': npc['defending'],
                'Physical': npc['physical']
            }
            
            has_missing = False
            for stat_name, value in stats.items():
                if value is None:
                    print(f"   ❌ {stat_name}: MISSING!")
                    has_missing = True
                else:
                    print(f"   ✅ {stat_name}: {value}")
            
            if has_missing:
                missing_stats.append(npc['player_name'])
        
        # 2. Test weighted stat calculation
        print("\n" + "="*70)
        print("🧪 TESTING WEIGHTED STAT CALCULATION")
        print("="*70)
        
        if npcs:
            test_npc = npcs[0]
            
            print(f"\nTest Subject: {test_npc['player_name']} ({test_npc['position']})")
            print(f"Defending: {test_npc['defending']}")
            print(f"Physical: {test_npc['physical']}")
            
            # Manual calculation
            if test_npc['defending'] and test_npc['physical']:
                manual_weighted = int((test_npc['defending'] * 0.7) + (test_npc['physical'] * 0.3))
                print(f"\n✅ Manual Weighted Calculation: {manual_weighted}")
                print(f"   Formula: (DEF * 0.7) + (PHY * 0.3)")
                print(f"   = ({test_npc['defending']} * 0.7) + ({test_npc['physical']} * 0.3)")
                print(f"   = {manual_weighted}")
            else:
                print("\n❌ Cannot calculate - stats are NULL!")
        
        # 3. Summary
        print("\n" + "="*70)
        print("📋 DIAGNOSTIC SUMMARY")
        print("="*70)
        
        if missing_stats:
            print(f"\n❌ PROBLEM FOUND:")
            print(f"   {len(missing_stats)} NPCs have missing individual stats!")
            print(f"   They only have overall_rating, not individual stats.")
            print(f"\n💡 SOLUTION:")
            print(f"   Need to run stat generation script to populate individual stats.")
        else:
            print(f"\n✅ ALL NPCs HAVE PROPER STATS!")
            print(f"   Problem must be elsewhere (display or calculation logic).")
        
        # 4. Check database schema
        print("\n" + "="*70)
        print("🗄️ DATABASE SCHEMA CHECK")
        print("="*70)
        
        columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'npc_players'
            AND column_name IN ('pace', 'shooting', 'passing', 'dribbling', 'defending', 'physical')
            ORDER BY column_name
        """)
        
        print("\nIndividual stat columns:")
        for col in columns:
            print(f"   ✅ {col['column_name']} ({col['data_type']})")
        
        if len(columns) < 6:
            print(f"\n❌ MISSING COLUMNS! Only found {len(columns)}/6")
            print("   Need to add missing stat columns to database.")

if __name__ == "__main__":
    asyncio.run(diagnose_npc_stats())
