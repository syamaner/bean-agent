#!/usr/bin/env python3
"""
Test MCP SSE connection with detailed debugging
"""
import os
import requests
import asyncio
import traceback
from mcp.client.sse import sse_client
from mcp import ClientSession

# Auth0 Configuration (from environment variables)
# IMPORTANT: Set these as environment variables - do NOT hardcode credentials  
# Use: source ./set_env.sh
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "https://coffee-roasting-api")

if not all([AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET]):
    raise ValueError("AUTH0_DOMAIN, AUTH0_CLIENT_ID, and AUTH0_CLIENT_SECRET must be set. Run: source ./set_env.sh")

# MCP Server URLs
ROASTER_URL = os.getenv("services__roaster-control__http__0", "http://localhost:5002")
ROASTER_SSE_URL = ROASTER_URL + "/sse"


def get_auth0_token():
    """Get Auth0 M2M access token."""
    print(f"Requesting token from: https://{AUTH0_DOMAIN}/oauth/token")
    print(f"  Client ID: {AUTH0_CLIENT_ID}")
    print(f"  Audience: {AUTH0_AUDIENCE}")
    
    response = requests.post(
        f"https://{AUTH0_DOMAIN}/oauth/token",
        json={
            "client_id": AUTH0_CLIENT_ID,
            "client_secret": AUTH0_CLIENT_SECRET,
            "audience": AUTH0_AUDIENCE,
            "grant_type": "client_credentials"
        }
    )
    response.raise_for_status()
    token_data = response.json()
    print(f"✓ Token received: {token_data['access_token'][:50]}...")
    print(f"  Token type: {token_data.get('token_type')}")
    print(f"  Expires in: {token_data.get('expires_in')}s")
    return token_data["access_token"]


async def test_connection():
    """Test MCP SSE connection."""
    print("\n" + "="*60)
    print("Testing MCP SSE Connection")
    print("="*60)
    
    # Get token
    print("\n1. Getting Auth0 token...")
    token = get_auth0_token()
    
    # Test health endpoint first
    print(f"\n2. Testing health endpoint: {ROASTER_URL}/health")
    try:
        health_resp = requests.get(f"{ROASTER_URL}/health")
        print(f"   Status: {health_resp.status_code}")
        print(f"   Response: {health_resp.text[:200]}")
    except Exception as e:
        print(f"   ✗ Health check failed: {e}")
        return
    
    # Test SSE endpoint with token
    print(f"\n3. Testing SSE endpoint: {ROASTER_SSE_URL}")
    print(f"   Using token: {token[:50]}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        async with sse_client(ROASTER_SSE_URL, headers=headers) as (read, write):
            print("   ✓ SSE connection established!")
            
            async with ClientSession(read, write) as session:
                print("   ✓ MCP session created")
                
                # Initialize
                await session.initialize()
                print("   ✓ Session initialized")
                
                # List tools
                tools = await session.list_tools()
                print(f"   ✓ Available tools: {[t.name for t in tools.tools]}")
                
                print("\n✅ SUCCESS! MCP connection working properly")
                
    except Exception as e:
        print(f"\n   ✗ Connection failed: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        
        # Additional debugging
        print("\n--- Debug Info ---")
        print(f"URL: {ROASTER_SSE_URL}")
        print(f"Headers: Authorization: Bearer {token[:30]}...")
        print(f"Environment variables:")
        for key in os.environ:
            if 'service' in key.lower() or 'auth0' in key.lower():
                print(f"  {key}={os.environ[key]}")


if __name__ == "__main__":
    asyncio.run(test_connection())
