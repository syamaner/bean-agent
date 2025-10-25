"""
Integration tests for MCP server with file-based detection.

Tests the complete workflow:
1. Start server
2. Start detection with audio file
3. Poll status
4. Stop detection
5. Verify results
"""
import pytest
import asyncio
import json
import tempfile
import wave
import numpy as np
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.fixture
def test_audio_file():
    """Create a temporary test audio file."""
    # Create a simple 5-second mono audio file at 44.1kHz
    sample_rate = 44100
    duration = 5
    samples = np.random.rand(sample_rate * duration) * 0.1  # Low amplitude noise
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.wav', delete=False) as f:
        temp_path = f.name
    
    # Write WAV file
    with wave.open(temp_path, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes((samples * 32767).astype(np.int16).tobytes())
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
async def mcp_client():
    """Create MCP client connected to server."""
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp_servers.first_crack_detection"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


@pytest.mark.asyncio
async def test_server_initialization():
    """Test that server initializes correctly."""
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp_servers.first_crack_detection"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Server should initialize without errors
            assert session is not None


@pytest.mark.asyncio
async def test_list_tools():
    """Test listing available tools."""
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp_servers.first_crack_detection"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            tools = await session.list_tools()
            
            assert len(tools.tools) == 3
            tool_names = [t.name for t in tools.tools]
            assert "start_first_crack_detection" in tool_names
            assert "get_first_crack_status" in tool_names
            assert "stop_first_crack_detection" in tool_names


@pytest.mark.asyncio
async def test_health_resource():
    """Test health resource."""
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp_servers.first_crack_detection"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            health = await session.read_resource(uri="health://status")
            health_data = json.loads(health.contents[0].text)
            
            assert health_data["status"] == "healthy"
            assert "model_checkpoint" in health_data
            assert "device" in health_data
            assert "version" in health_data


@pytest.mark.asyncio
async def test_get_status_no_session():
    """Test getting status when no session is active."""
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp_servers.first_crack_detection"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool("get_first_crack_status", arguments={})
            data = json.loads(result.content[0].text)
            
            assert data["status"] == "success"
            assert data["result"]["session_active"] is False
            assert data["result"]["first_crack_detected"] is False


@pytest.mark.asyncio
@pytest.mark.skipif(not Path("experiments/final_model/model.pt").exists(), 
                    reason="Model checkpoint not found")
async def test_start_detection_missing_file():
    """Test starting detection with non-existent file."""
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp_servers.first_crack_detection"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "start_first_crack_detection",
                arguments={
                    "audio_source_type": "audio_file",
                    "audio_file_path": "/nonexistent/file.wav"
                }
            )
            data = json.loads(result.content[0].text)
            
            assert data["status"] == "error"
            # File validation happens after model validation
            assert data["error"]["code"] == "FILE_NOT_FOUND"


@pytest.mark.asyncio
async def test_stop_detection_no_session():
    """Test stopping detection when no session is active."""
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp_servers.first_crack_detection"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool("stop_first_crack_detection", arguments={})
            data = json.loads(result.content[0].text)
            
            assert data["status"] == "success"
            assert data["result"]["session_state"] == "no_active_session"


@pytest.mark.asyncio
@pytest.mark.skipif(not Path("experiments/final_model/model.pt").exists(), 
                    reason="Model checkpoint not found")
async def test_full_workflow_with_test_file(test_audio_file):
    """Test complete workflow with test audio file."""
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp_servers.first_crack_detection"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Start detection
            start_result = await session.call_tool(
                "start_first_crack_detection",
                arguments={
                    "audio_source_type": "audio_file",
                    "audio_file_path": test_audio_file
                }
            )
            start_data = json.loads(start_result.content[0].text)
            
            assert start_data["status"] == "success"
            assert start_data["result"]["session_state"] == "started"
            session_id = start_data["result"]["session_id"]
            assert session_id is not None
            
            # 2. Check status
            await asyncio.sleep(0.5)  # Brief delay
            
            status_result = await session.call_tool("get_first_crack_status", arguments={})
            status_data = json.loads(status_result.content[0].text)
            
            assert status_data["status"] == "success"
            assert status_data["result"]["session_active"] is True
            assert status_data["result"]["session_id"] == session_id
            assert "elapsed_time" in status_data["result"]
            
            # 3. Test idempotency - try to start again
            start_again = await session.call_tool(
                "start_first_crack_detection",
                arguments={
                    "audio_source_type": "audio_file",
                    "audio_file_path": test_audio_file
                }
            )
            start_again_data = json.loads(start_again.content[0].text)
            
            assert start_again_data["status"] == "success"
            assert start_again_data["result"]["session_state"] == "already_running"
            assert start_again_data["result"]["session_id"] == session_id
            
            # 4. Stop detection
            stop_result = await session.call_tool("stop_first_crack_detection", arguments={})
            stop_data = json.loads(stop_result.content[0].text)
            
            assert stop_data["status"] == "success"
            assert stop_data["result"]["session_state"] == "stopped"
            assert stop_data["result"]["session_id"] == session_id
            assert "session_summary" in stop_data["result"]
            
            # 5. Verify session is stopped
            final_status = await session.call_tool("get_first_crack_status", arguments={})
            final_data = json.loads(final_status.content[0].text)
            
            assert final_data["result"]["session_active"] is False


@pytest.mark.asyncio
@pytest.mark.skipif(not Path("data/raw").exists(), 
                    reason="Raw data directory not found")
async def test_with_real_audio_file():
    """Test with actual roast recording (if available)."""
    # Find a test audio file
    raw_dir = Path("data/raw")
    audio_files = list(raw_dir.glob("*.wav"))
    
    if not audio_files:
        pytest.skip("No audio files found in data/raw")
    
    test_file = str(audio_files[0])
    
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp_servers.first_crack_detection"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Start detection
            start_result = await session.call_tool(
                "start_first_crack_detection",
                arguments={
                    "audio_source_type": "audio_file",
                    "audio_file_path": test_file
                }
            )
            start_data = json.loads(start_result.content[0].text)
            
            print(f"\n🎵 Testing with: {Path(test_file).name}")
            print(f"Session ID: {start_data['result']['session_id']}")
            
            # Poll status for a bit
            for i in range(5):
                await asyncio.sleep(1)
                status_result = await session.call_tool("get_first_crack_status", arguments={})
                status_data = json.loads(status_result.content[0].text)
                
                print(f"  {status_data['result']['elapsed_time']} - "
                      f"First crack: {status_data['result']['first_crack_detected']}")
                
                if status_data["result"]["first_crack_detected"]:
                    print(f"  🎉 Detected at {status_data['result']['first_crack_time_relative']}")
                    break
            
            # Stop
            stop_result = await session.call_tool("stop_first_crack_detection", arguments={})
            stop_data = json.loads(stop_result.content[0].text)
            
            print(f"✅ Session summary: {stop_data['result']['session_summary']}")
            
            assert start_data["status"] == "success"
            assert stop_data["status"] == "success"
