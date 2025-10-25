#!/usr/bin/env python3
"""
Simple MCP client for testing the First Crack Detection server.

Usage:
    python manual_test_client.py
"""
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_server():
    """Test the MCP server by calling its tools."""
    
    # Server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp_servers.first_crack_detection.server"],
        env=None
    )
    
    print("🚀 Starting MCP server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            print("✅ Server initialized")
            
            # List tools
            tools = await session.list_tools()
            print(f"\n📋 Available tools ({len(tools.tools)}):")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # List resources
            resources = await session.list_resources()
            print(f"\n📦 Available resources ({len(resources.resources)}):")
            for resource in resources.resources:
                print(f"  - {resource.name} ({resource.uri})")
            
            # Read health resource
            print("\n🏥 Checking health...")
            health = await session.read_resource(uri="health://status")
            health_data = json.loads(health.contents[0].text)
            print(f"  Status: {health_data['status']}")
            print(f"  Model: {health_data['model_checkpoint']}")
            print(f"  Model exists: {health_data['model_exists']}")
            print(f"  Device: {health_data['device']}")
            
            # Test get_status (no session)
            print("\n📊 Getting status (no session)...")
            result = await session.call_tool("get_first_crack_status", arguments={})
            status_data = json.loads(result.content[0].text)
            print(f"  Session active: {status_data['result']['session_active']}")
            
            print("\n✅ All tests passed!")
            print("\nℹ️  To test with actual audio, modify this script to call:")
            print("  - start_first_crack_detection with audio_file_path or microphone")
            print("  - get_first_crack_status to poll during detection")
            print("  - stop_first_crack_detection to end session")


if __name__ == "__main__":
    try:
        asyncio.run(test_server())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
