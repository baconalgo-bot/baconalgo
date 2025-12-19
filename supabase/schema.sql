-- Create signals table
CREATE TABLE signals (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    direction VARCHAR(4) NOT NULL,
    entry DECIMAL(10, 2) NOT NULL,
    stop DECIMAL(10, 2) NOT NULL,
    target DECIMAL(10, 2) NOT NULL,
    tech_score INTEGER NOT NULL,
    social_score INTEGER NOT NULL,
    total_score INTEGER NOT NULL,
    rsi DECIMAL(5, 2),
    volume_ratio DECIMAL(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX idx_signals_created_at ON signals(created_at DESC);
CREATE INDEX idx_signals_total_score ON signals(total_score DESC);
CREATE INDEX idx_signals_symbol ON signals(symbol);

-- Enable Row Level Security
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;

-- Allow public read
CREATE POLICY "Public read access" ON signals
    FOR SELECT USING (true);

-- Only authenticated users can insert
CREATE POLICY "Authenticated insert" ON signals
    FOR INSERT TO authenticated
    WITH CHECK (true);
