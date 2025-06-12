#!/usr/bin/env python3
from supabase import create_client

supabase_url = 'https://bupugtkjjavkbtdoujab.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ1cHVndGtqamF2a2J0ZG91amFiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDI1MjY0NTAsImV4cCI6MjAxODEwMjQ1MH0.2axcezVrcW2LkPy1pbKVP1UjU4WD3-Nq3FDeieIzU4E'

try:
    supabase = create_client(supabase_url, supabase_key)
    
    # Check specific user mapping
    result = supabase.table('user_mappings').select('*').eq('slack_user_id', 'U08T1DTEMJT').execute()
    print(f'Found {len(result.data)} user mappings for U08T1DTEMJT')
    
    if result.data:
        for mapping in result.data:
            print(f'  Slack: {mapping.get("slack_user_id")} -> PropelAuth: {mapping.get("propelauth_user_id")}')
            print(f'  Team: {mapping.get("slack_team_id")}')
            print(f'  Created: {mapping.get("created_at")}')
    else:
        print('❌ No user mapping found')
        
    # Check all user mappings
    all_result = supabase.table('user_mappings').select('*').execute()
    print(f'Total user mappings in table: {len(all_result.data)}')
    
    # Test table permissions
    print('Testing table permissions...')
    try:
        test_insert = {
            'slack_user_id': 'TEST123',
            'slack_team_id': 'TEST123', 
            'propelauth_user_id': 'test-user',
            'propelauth_email': 'test@test.com'
        }
        insert_result = supabase.table('user_mappings').insert(test_insert).execute()
        print('✅ Insert permission: OK')
        
        # Clean up test record
        supabase.table('user_mappings').delete().eq('slack_user_id', 'TEST123').execute()
    except Exception as e:
        print(f'❌ Insert permission: {e}')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc() 