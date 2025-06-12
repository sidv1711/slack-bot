-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create slack_installations table
CREATE TABLE IF NOT EXISTS slack_installations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    app_id TEXT NOT NULL,
    enterprise_id TEXT,
    team_id TEXT NOT NULL,
    bot_token TEXT NOT NULL,
    bot_id TEXT NOT NULL,
    bot_scopes TEXT NOT NULL,
    user_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraints
    UNIQUE(team_id)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_slack_installations_team_lookup 
ON slack_installations(team_id);

CREATE INDEX IF NOT EXISTS idx_slack_installations_enterprise_lookup 
ON slack_installations(enterprise_id);

-- Add RLS (Row Level Security) policies
ALTER TABLE slack_installations ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Allow read access to authenticated users" ON slack_installations;
DROP POLICY IF EXISTS "Allow write access to service role" ON slack_installations;
DROP POLICY IF EXISTS "Allow service role full access" ON slack_installations;

-- Create policy to allow read access to authenticated users
CREATE POLICY "Allow read access to authenticated users"
ON slack_installations FOR SELECT
TO authenticated
USING (true);

-- Create policy to allow full access for service role
CREATE POLICY "Allow service role full access"
ON slack_installations
TO service_role
USING (true)
WITH CHECK (true); 