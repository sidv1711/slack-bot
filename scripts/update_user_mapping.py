#!/usr/bin/env python3
"""Update the user mapping to use the new PropelAuth user ID."""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append('src')

async def update_user_mapping():
    """Update the user mapping in the database."""
    
    load_dotenv()
    
    # Configuration
    slack_user_id = 'U08T1DTEMJT'  # Your Slack user ID from the logs
    team_id = 'T070WU1A37D'  # Your team ID from the logs
    old_propelauth_user_id = '<UUID>'
    new_propelauth_user_id = '<UUID>'
    
    print("🔄 Updating User Mapping")
    print("=" * 40)
    print(f"👤 Slack User: {slack_user_id}")
    print(f"🏢 Team: {team_id}")
    print(f"🔄 Old PropelAuth User: {old_propelauth_user_id}")
    print(f"✨ New PropelAuth User: {new_propelauth_user_id}")
    print()
    
    try:
        # Import required modules
        from src.services.database_service import DatabaseService
        from src.auth.supabase_store import SupabaseUserMappingStore
        from src.config.settings import Settings
        
        # Initialize settings and services
        settings = Settings()
        db_service = DatabaseService()
        user_mapping_store = SupabaseUserMappingStore(settings)
        
        print("📡 Connected to database")
        
        # Check current mapping
        print("🔍 Checking current mapping...")
        current_mapping = await user_mapping_store.get_by_slack_id(slack_user_id, team_id)
        
        if current_mapping:
            print(f"✅ Found current mapping:")
            print(f"   📊 Current PropelAuth User: {current_mapping.propelauth_user_id}")
            print(f"   📊 Slack User: {current_mapping.slack_user_id}")
            print(f"   📊 Team: {current_mapping.slack_team_id}")
            
            # Update the mapping by creating a new one with updated PropelAuth user ID
            print(f"\n🔄 Updating PropelAuth user ID...")
            
            # Create updated mapping object
            from src.models.user_mapping import UserMapping
            from datetime import datetime
            
            updated_mapping = UserMapping(
                slack_user_id=current_mapping.slack_user_id,
                propelauth_user_id=new_propelauth_user_id,  # New user ID
                slack_team_id=current_mapping.slack_team_id,
                slack_email=current_mapping.slack_email,
                propelauth_email=current_mapping.propelauth_email,
                created_at=current_mapping.created_at,
                updated_at=datetime.utcnow()
            )
            
            # Save the updated mapping (will update existing record)
            await user_mapping_store.save_mapping(updated_mapping)
            print("🎉 ✅ Mapping updated successfully!")
            print(f"✨ New PropelAuth User ID: {new_propelauth_user_id}")
            
        else:
            print("❌ No current mapping found")
            print("🆕 Creating new mapping...")
            
            # Create new mapping
            new_mapping = await user_mapping_store.create(
                slack_user_id=slack_user_id,
                team_id=team_id,
                propelauth_user_id=new_propelauth_user_id
            )
            
            if new_mapping:
                print("🎉 ✅ New mapping created successfully!")
                print(f"✨ PropelAuth User ID: {new_propelauth_user_id}")
            else:
                print("❌ Failed to create mapping")
        
        # Verify the update
        print(f"\n🔍 Verifying updated mapping...")
        verified_mapping = await user_mapping_store.get_by_slack_id(slack_user_id, team_id)
        
        if verified_mapping and verified_mapping.propelauth_user_id == new_propelauth_user_id:
            print("🎉 ✅ Verification successful!")
            print(f"📊 Verified PropelAuth User: {verified_mapping.propelauth_user_id}")
            print("\n🚀 Ready to test the bot with the new user mapping!")
            return True
        else:
            print("❌ Verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Error updating user mapping: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(update_user_mapping())
    if success:
        print("\n🎯 NEXT STEPS:")
        print("1. Rebuild the Docker containers with new PropelAuth configuration")
        print("2. Test the /test-executions command")
        print("3. Verify access token creation works")
    else:
        print("\n❌ Fix the user mapping issue before proceeding") 