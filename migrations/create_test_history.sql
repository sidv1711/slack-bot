-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create test_history table
CREATE TABLE IF NOT EXISTS test_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_uid TEXT NOT NULL,
    execution_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('passed', 'failed', 'running', 'pending', 'skipped')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_test_history_test_uid_lookup 
ON test_history(test_uid);

CREATE INDEX IF NOT EXISTS idx_test_history_status_lookup 
ON test_history(status);

CREATE INDEX IF NOT EXISTS idx_test_history_execution_time_lookup 
ON test_history(execution_time DESC);

CREATE INDEX IF NOT EXISTS idx_test_history_composite_lookup 
ON test_history(test_uid, status, execution_time DESC);

-- Add RLS (Row Level Security) policies
ALTER TABLE test_history ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Allow read access to authenticated users" ON test_history;
DROP POLICY IF EXISTS "Allow write access to service role" ON test_history;

-- Create policy to allow read access to authenticated users
CREATE POLICY "Allow read access to authenticated users"
ON test_history FOR SELECT
TO authenticated
USING (true);

-- Create policy to allow write access for service role only
CREATE POLICY "Allow write access to service role"
ON test_history FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Insert some sample data for testing
INSERT INTO test_history (test_uid, execution_time, status, metadata) VALUES
    ('TEST_001', NOW() - INTERVAL '1 hour', 'passed', '{"duration": 45, "environment": "staging"}'),
    ('TEST_002', NOW() - INTERVAL '2 hours', 'failed', '{"duration": 120, "error": "timeout", "environment": "production"}'),
    ('TEST_003', NOW() - INTERVAL '3 hours', 'passed', '{"duration": 30, "environment": "staging"}'),
    ('TEST_001', NOW() - INTERVAL '1 day', 'failed', '{"duration": 90, "error": "assertion failed", "environment": "staging"}'),
    ('TEST_004', NOW() - INTERVAL '2 days', 'passed', '{"duration": 60, "environment": "production"}'),
    ('TEST_002', NOW() - INTERVAL '3 days', 'passed', '{"duration": 75, "environment": "staging"}'),
    ('TEST_005', NOW() - INTERVAL '4 days', 'running', '{"environment": "staging"}'),
    ('TEST_003', NOW() - INTERVAL '5 days', 'skipped', '{"reason": "dependency failure", "environment": "production"}'),
    ('TEST_006', NOW() - INTERVAL '6 days', 'passed', '{"duration": 25, "environment": "staging"}'),
    ('TEST_001', NOW() - INTERVAL '1 week', 'passed', '{"duration": 40, "environment": "production"}')
ON CONFLICT DO NOTHING; 