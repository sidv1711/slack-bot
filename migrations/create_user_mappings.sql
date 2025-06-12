-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create user_mappings table
CREATE TABLE IF NOT EXISTS user_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slack_user_id TEXT NOT NULL,
    propelauth_user_id TEXT NOT NULL,
    slack_team_id TEXT NOT NULL,
    slack_email TEXT,
    propelauth_email TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraints
    UNIQUE(slack_team_id, slack_user_id),
    UNIQUE(propelauth_user_id)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_user_mappings_slack_lookup 
ON user_mappings(slack_user_id, slack_team_id);

CREATE INDEX IF NOT EXISTS idx_user_mappings_propelauth_lookup 
ON user_mappings(propelauth_user_id);

CREATE INDEX IF NOT EXISTS idx_user_mappings_email_lookup 
ON user_mappings(slack_email, propelauth_email);

-- Add RLS (Row Level Security) policies
ALTER TABLE user_mappings ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Allow read access to authenticated users" ON user_mappings;
DROP POLICY IF EXISTS "Allow write access to service role" ON user_mappings;

-- Create policy to allow read access to authenticated users
CREATE POLICY "Allow read access to authenticated users"
ON user_mappings FOR SELECT
TO authenticated
USING (true);

-- Create policy to allow insert/update for service role only
CREATE POLICY "Allow write access to service role"
ON user_mappings FOR ALL
TO service_role
USING (true)
WITH CHECK (true); 