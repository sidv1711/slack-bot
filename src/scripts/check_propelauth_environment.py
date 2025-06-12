#!/usr/bin/env python3
"""Check PropelAuth environment and configuration."""

import httpx
import asyncio

async def check_propelauth_environment():
    """Check which PropelAuth environment we're dealing with."""
    
    test_url = 'https://233768343.propelauthtest.com'
    staging_url_your_company = 'https://staging.example.com'  # Possible staging URL
    production_url = 'https://auth.example.com'
    
    api_key = '<HEX_SECRET><HEX_SECRET>'
    
    print("🔍 PropelAuth Environment Detection")
    print("=" * 50)
    print(f"🔑 API Key Length: {len(api_key)} characters")
    print(f"🔑 API Key Preview: {api_key[:30]}...")
    print()
    
    urls_to_check = [
        ("Test Environment", test_url),
        ("Staging Environment (your_company)", staging_url_your_company), 
        ("Production Environment", production_url)
    ]
    
    for env_name, url in urls_to_check:
        print(f"🧪 Testing {env_name}: {url}")
        
        try:
            # Check if URL is accessible
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/.well-known/openid-configuration", timeout=10)
                
                if response.status_code == 200:
                    config = response.json()
                    print(f"   ✅ URL accessible")
                    print(f"   📍 Issuer: {config.get('issuer')}")
                    
                    # Test backend API key with this URL
                    try:
                        from propelauth_fastapi import init_auth
                        auth = init_auth(url, api_key)
                        print(f"   ✅ Backend API key works with this environment!")
                        print(f"   🎯 THIS IS THE CORRECT ENVIRONMENT")
                        
                        # Test user lookup
                        try:
                            user_id = '<UUID>'
                            user = auth.fetch_user_metadata_by_user_id(user_id)
                            print(f"   👤 User {user_id} exists: {user is not None}")
                            
                            # Test access token creation
                            token_response = auth.create_access_token(
                                user_id=user_id,
                                duration_in_minutes=60
                            )
                            print(f"   🎫 Access token creation: SUCCESS")
                            print(f"   🎫 Token length: {len(token_response.access_token)} characters")
                            
                        except Exception as e:
                            print(f"   ❌ User/token test failed: {e}")
                            
                    except Exception as e:
                        print(f"   ❌ Backend API key doesn't work: {e}")
                        
                else:
                    print(f"   ❌ URL returned {response.status_code}")
                    
        except Exception as e:
            print(f"   ❌ URL not accessible: {e}")
            
        print()
    
    print("🔍 ANALYSIS:")
    print("• If Test Environment works: You're using TEST, not staging")
    print("• If Staging Environment works: You have proper staging setup")
    print("• If none work: API key might be for different environment")
    print()
    print("🛠️ NEXT STEPS:")
    print("1. Check PropelAuth dashboard environment switcher (top-right)")
    print("2. Verify you're getting API key from correct environment")
    print("3. Check 'Frontend Integration' page for correct Auth URL")

if __name__ == "__main__":
    asyncio.run(check_propelauth_environment()) 