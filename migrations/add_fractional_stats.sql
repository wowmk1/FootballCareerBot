-- ============================================
-- FRACTIONAL STAT TRACKING FOR MULTI-STAT TRAINING
-- ============================================
-- Purpose: Allow secondary stats to accumulate fractional progress
-- Example: Training shooting gives +0.5 physical each session
--          After 2 sessions: 1.0 fractional = +1 actual stat point

-- Add fractional columns to players table
ALTER TABLE players
ADD COLUMN IF NOT EXISTS pace_fractional DECIMAL(5, 2) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS shooting_fractional DECIMAL(5, 2) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS passing_fractional DECIMAL(5, 2) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS dribbling_fractional DECIMAL(5, 2) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS defending_fractional DECIMAL(5, 2) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS physical_fractional DECIMAL(5, 2) DEFAULT 0.0;

-- Initialize all existing players to 0.0
UPDATE players
SET 
    pace_fractional = 0.0,
    shooting_fractional = 0.0,
    passing_fractional = 0.0,
    dribbling_fractional = 0.0,
    defending_fractional = 0.0,
    physical_fractional = 0.0
WHERE pace_fractional IS NULL;

-- Create index for performance (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_players_fractional_stats 
ON players(pace_fractional, shooting_fractional, passing_fractional, 
           dribbling_fractional, defending_fractional, physical_fractional);
