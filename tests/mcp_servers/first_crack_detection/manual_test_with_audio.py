#!/usr/bin/env python3
"""
Manual test of MCP server with real audio file.

This script will:
1. Find an audio file in data/raw
2. Start detection
3. Poll status every second
4. Report first crack if detected
5. Stop after 10 seconds or on detection
"""
import asyncio
import json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_with_audio():
    """Test MCP server with real audio file."""
    
    # Find audio file
    raw_dir = Path("data/raw")
    if not raw_dir.exists():
        print("❌ data/raw directory not found")
        return
    
    audio_files = list(raw_dir.glob("*.wav"))
    if not audio_files:
        print("❌ No .wav files found in data/raw")
        return
    
    audio_file = str(audio_files[0])
    print(f"🎵 Testing with: {Path(audio_file).name}\n")
    
    # Server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp_servers.first_crack_detection"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Server initialized\n")
            
            # Start detection
            print(f"▶️  Starting detection...")
            start_result = await session.call_tool(
                "start_first_crack_detection",
                arguments={
                    "audio_source_type": "audio_file",
                    "audio_file_path": audio_file
                }
            )
            start_data = json.loads(start_result.content[0].text)
            
            if start_data["status"] != "success":
                print(f"❌ Start failed: {start_data}")
                return
            
            session_id = start_data["result"]["session_id"]
            print(f"✅ Session started: {session_id}")
            print(f"   Audio source: {start_data['result']['audio_source_details']}")
            print(f"   Started at: {start_data['result']['started_at_local']}\n")
            
            # Poll status
            print("📊 Polling status (10 seconds max)...\n")
            for i in range(10):
                await asyncio.sleep(1)
                
                status_result = await session.call_tool("get_first_crack_status", arguments={})
                status_data = json.loads(status_result.content[0].text)
                
                if status_data["status"] != "success":
                    print(f"❌ Status query failed: {status_data}")
                    break
                
                result = status_data["result"]
                elapsed = result["elapsed_time"]
                detected = result["first_crack_detected"]
                
                if detected:
                    fc_time = result.get("first_crack_time_relative", "unknown")
                    fc_utc = result.get("first_crack_time_utc", "unknown")
                    print(f"   [{elapsed}] 🎉 FIRST CRACK DETECTED at {fc_time}")
                    print(f"           UTC: {fc_utc}")
                    print(f"           Local: {result.get('first_crack_time_local', 'unknown')}")
                    break
                else:
                    print(f"   [{elapsed}] Listening... (no first crack yet)")
            
            # Stop detection
            print(f"\n⏹️  Stopping detection...")
            stop_result = await session.call_tool("stop_first_crack_detection", arguments={})
            stop_data = json.loads(stop_result.content[0].text)
            
            if stop_data["status"] == "success":
                summary = stop_data["result"]["session_summary"]
                print(f"✅ Session stopped")
                print(f"\n📋 Summary:")
                print(f"   Duration: {summary['duration']}")
                print(f"   First crack detected: {summary['first_crack_detected']}")
                if summary['first_crack_detected']:
                    print(f"   First crack time: {summary.get('first_crack_time', 'N/A')}")
                print(f"   Audio source: {summary['audio_source']}")
            else:
                print(f"❌ Stop failed: {stop_data}")


if __name__ == "__main__":
    try:
        asyncio.run(test_with_audio())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
