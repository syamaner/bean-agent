#!/usr/bin/env python3
"""
Coffee Roasting AI Agent Demo
Uses OpenAI GPT-4 + MCP SSE Servers with Auth0

Requirements:
    pip install openai requests mcp httpx-sse

Usage:
    export OPENAI_API_KEY="your-key"
    python demo_agent.py
"""
import os
import asyncio
import requests
from openai import OpenAI
from mcp import ClientSession
from mcp.client.sse import sse_client

# Auth0 Configuration (from environment variables)
# IMPORTANT: Set these as environment variables - do NOT hardcode credentials
# Use: source ./set_env.sh
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "https://coffee-roasting-api")

if not all([AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET]):
    raise ValueError("AUTH0_DOMAIN, AUTH0_CLIENT_ID, and AUTH0_CLIENT_SECRET must be set. Run: source ./set_env.sh")

# MCP Server URLs (from Aspire service references)
# Aspire injects these as services__<service-name>__http__0 or https__0
ROASTER_SSE_URL = os.getenv("services__roaster-control__http__0", "http://localhost:5002") + "/sse"
DETECTION_SSE_URL = os.getenv("services__first-crack-detection__http__0", "http://localhost:5001") + "/sse"


def get_auth0_token():
    """Get Auth0 M2M access token."""
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
    return response.json()["access_token"]


async def demo_roast():
    """Run coffee roasting demo with AI agent."""
    import sys
    import logging
    
    # Configure logging to flush immediately
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, force=True)
    sys.stdout.reconfigure(line_buffering=True)
    
    print("🤖 Coffee Roasting AI Agent Demo", flush=True)
    print("=" * 60, flush=True)
    
    # Step 1: Get Auth0 token
    print("\n🔐 Step 1: Authenticating with Auth0...", flush=True)
    try:
        token = get_auth0_token()
        print(f"   ✓ Token acquired: {token[:30]}...", flush=True)
    except Exception as e:
        print(f"   ✗ Token failed: {e}", flush=True)
        return
    
    # Step 2: Connect to MCP servers (keep connections open)
    print("\n🔌 Step 2: Connecting to MCP servers...", flush=True)
    print(f"   Roaster URL: {ROASTER_SSE_URL}", flush=True)
    print(f"   Detection URL: {DETECTION_SSE_URL}", flush=True)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        async with sse_client(ROASTER_SSE_URL, headers=headers) as (roaster_read, roaster_write):
            async with ClientSession(roaster_read, roaster_write) as roaster_session:
                await roaster_session.initialize()
                roaster_tools = await roaster_session.list_tools()
                print(f"   ✓ Roaster Control connected", flush=True)
                print(f"   ✓ Available tools: {[t.name for t in roaster_tools.tools]}", flush=True)
                
                async with sse_client(DETECTION_SSE_URL, headers=headers) as (detection_read, detection_write):
                    async with ClientSession(detection_read, detection_write) as detection_session:
                        await detection_session.initialize()
                        detection_tools = await detection_session.list_tools()
                        print(f"   ✓ First Crack Detection connected", flush=True)
                        print(f"   ✓ Available tools: {[t.name for t in detection_tools.tools]}", flush=True)
                        
                        # Step 3: Initialize OpenAI
                        print("\n🧠 Step 3: Initializing AI Agent (GPT-4)...", flush=True)
                        if not os.getenv("OPENAI_API_KEY"):
                            print("   ✗ OPENAI_API_KEY not set", flush=True)
                            print("   Set it in Aspire user-secrets", flush=True)
                            return
                        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                        print("   ✓ GPT-4 ready", flush=True)
                        
                        # Step 4: Call roaster status
                        print("\n📊 Step 4: Reading roaster status...", flush=True)
                        result = await roaster_session.call_tool("read_roaster_status", {})
                        print(f"   ✓ Roaster status: {result.content[0].text[:100]}...", flush=True)
                        
                        # Step 5: Ask GPT to analyze and suggest
                        print("\n🤔 Step 5: Asking AI to analyze roast plan...", flush=True)
                        prompt = f"""
                        You are a coffee roasting expert. Analyze this roaster status and create a roasting plan 
                        for Ethiopian Yirgacheffe coffee (light roast, full city).
                        
                        Current roaster status:
                        {result.content[0].text}
                        
                        Provide:
                        1. Initial heat and fan settings
                        2. Target temperature for first crack (around 196°C)
                        3. Timeline expectations
                        4. Adjustments needed during the roast
                        """
                        
                        response = client.chat.completions.create(
                            model="gpt-4",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        
                        plan = response.choices[0].message.content
                        print(f"\n📋 AI Roasting Plan:\n{plan}", flush=True)
                        
                        # Step 6: Simulate roast control
                        print("\n🔥 Step 6: Demo - Start roaster and set initial parameters...", flush=True)
                        try:
                            # Start roaster
                            await roaster_session.call_tool("start_roaster", {})
                            print("   ✓ Roaster drum started", flush=True)
                            
                            # Set heat to 80%
                            await roaster_session.call_tool("set_heat", {"level": 80})
                            print("   ✓ Heat set to 80%", flush=True)
                            
                            # Set fan to 60%
                            await roaster_session.call_tool("set_fan", {"speed": 60})
                            print("   ✓ Fan set to 60%", flush=True)
                            
                            print("\n   🎯 Roaster is running in MOCK mode", flush=True)
                            print("   🎯 Ready to be controlled by AI agent!", flush=True)
                            
                        except Exception as e:
                            print(f"   ✗ Error: {e}", flush=True)
                        
                        print("\n" + "=" * 60, flush=True)
                        print("✅ Demo Complete!", flush=True)
                        print("\nWhat we demonstrated:", flush=True)
                        print("  ✓ Auth0 M2M authentication", flush=True)
                        print("  ✓ MCP SSE server connections", flush=True)
                        print("  ✓ Reading roaster status via MCP", flush=True)
                        print("  ✓ AI analysis and planning with GPT-4", flush=True)
                        print("  ✓ Controlling roaster via MCP tools", flush=True)
                        print("\n💡 Next: Build full autonomous agent loop!", flush=True)
    except Exception as e:
        print(f"\n✗ Demo failed: {e}", flush=True)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(demo_roast())
