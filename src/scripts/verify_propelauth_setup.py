#!/usr/bin/env python3
"""Comprehensive PropelAuth setup verification."""

import httpx
import asyncio
from propelauth_fastapi import init_auth

async def verify_propelauth_setup():
    """Verify PropelAuth staging setup comprehensively."""
    
    staging_url = 'https://233768343.propelauthtest.com'
    api_key = '<HEX_SECRET><HEX_SECRET>'
    user_id = '<UUID>'
    
    print("🔧 PropelAuth Setup Verification")
    print("=" * 50)
    print(f"📍 Staging URL: {staging_url}")
    print(f"🔑 API Key Length: {len(api_key)} characters")
    print(f"🔑 API Key Preview: {api_key[:30]}...")
    print(f"👤 User ID: {user_id}")
    print()
    
    # Step 1: Test if staging URL is accessible
    print("1️⃣ Testing Staging URL Accessibility...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{staging_url}/.well-known/openid-configuration", timeout=10)
            if response.status_code == 200:
                print("✅ Staging URL is accessible")
                config = response.json()
                print(f"   Issuer: {config.get('issuer')}")
            else:
                print(f"❌ Staging URL returned {response.status_code}")
    except Exception as e:
        print(f"❌ Staging URL not accessible: {e}")
    print()
    
    # Step 2: Test PropelAuth initialization 
    print("2️⃣ Testing PropelAuth Client Initialization...")
    try:
        auth = init_auth(staging_url, api_key)
        print("✅ PropelAuth client initialized successfully")
    except Exception as e:
        print(f"❌ PropelAuth initialization failed: {e}")
        print()
        print("🔍 POSSIBLE CAUSES:")
        print("   • Wrong Backend API Key (check Backend Integration page)")
        print("   • Using Test environment key for Staging")
        print("   • Using Frontend API Key instead of Backend API Key")
        print("   • API Key not created in correct environment")
        print()
        print("🛠️ SOLUTION STEPS:")
        print("   1. Go to: https://233768343.propelauthtest.com")
        print("   2. Navigate to: Backend Integration")
        print("   3. Ensure you're in STAGING environment (not Test)")
        print("   4. Create New API Key or copy existing Backend API Key")
        print("   5. The key should be ~128+ characters long")
        return
    print()
    
    # Step 3: Test user lookup
    print("3️⃣ Testing User Lookup...")
    try:
        user = auth.fetch_user_metadata_by_user_id(user_id)
        if user:
            print(f"✅ User found: {user}")
        else:
            print("⚠️ User exists but returns None (this can be normal)")
    except Exception as e:
        print(f"❌ User lookup failed: {e}")
    print()
    
    # Step 4: Test access token creation
    print("4️⃣ Testing Access Token Creation...")
    try:
        token_response = auth.create_access_token(
            user_id=user_id,
            duration_in_minutes=60
        )
        print("🎉 ✅ ACCESS TOKEN CREATION SUCCESSFUL!")
        print(f"🎫 Token Length: {len(token_response.access_token)} characters")
        print(f"🎫 Token Preview: {token_response.access_token[:50]}...")
        print()
        print("🎯 RESULT: PropelAuth access token API is working perfectly!")
        print("✅ Ready to update .env file and rebuild bot")
        
    except Exception as e:
        print(f"❌ Access token creation failed: {e}")
        print()
        print("🔍 This usually means the user doesn't exist in staging")
        print("🛠️ Either create the user in staging or use a different user ID")

if __name__ == "__main__":
    asyncio.run(verify_propelauth_setup()) 