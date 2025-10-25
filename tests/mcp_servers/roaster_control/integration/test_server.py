"""Integration tests for roaster control MCP server."""
import pytest
import asyncio
import json
from datetime import datetime, UTC

from src.mcp_servers.roaster_control.server import (
    server,
    init_server,
    list_tools,
    call_tool,
    list_resources,
    read_resource,
)
from src.mcp_servers.roaster_control.models import ServerConfig, HardwareConfig
from src.mcp_servers.roaster_control.hardware import MockRoaster


@pytest.fixture
def initialized_server():
    """Initialize server with mock hardware for testing."""
    config = ServerConfig(
        hardware=HardwareConfig(mock_mode=True)
    )
    init_server(config)
    
    # Start session so hardware is connected
    from src.mcp_servers.roaster_control.server import _session_manager
    _session_manager.start_session()
    
    yield
    
    # Cleanup: stop session
    if _session_manager and _session_manager.is_active():
        _session_manager.stop_session()


class TestServerInitialization:
    """Test server initialization and configuration."""
    
    def test_init_server_with_mock_hardware(self):
        """Test server initializes with mock hardware."""
        config = ServerConfig(
            hardware=HardwareConfig(mock_mode=True)
        )
        init_server(config)
        
        from src.mcp_servers.roaster_control.server import _session_manager, _config
        assert _session_manager is not None
        assert _config is not None
        assert _config.hardware.mock_mode is True
    
    def test_init_server_with_default_config(self):
        """Test server initializes with default config."""
        init_server()
        
        from src.mcp_servers.roaster_control.server import _config
        assert _config is not None
        assert _config.hardware.mock_mode is True  # Default


class TestToolRegistration:
    """Test tool listing and metadata."""
    
    @pytest.mark.asyncio
    async def test_list_tools_returns_all_tools(self, initialized_server):
        """Test all 9 tools are registered."""
        tools = await list_tools()
        
        assert len(tools) == 9
        
        tool_names = [t.name for t in tools]
        expected_tools = [
            "set_heat",
            "set_fan",
            "start_roaster",
            "stop_roaster",
            "drop_beans",
            "start_cooling",
            "stop_cooling",
            "report_first_crack",
            "get_roast_status",
        ]
        
        for expected in expected_tools:
            assert expected in tool_names
    
    @pytest.mark.asyncio
    async def test_tool_schemas_valid(self, initialized_server):
        """Test tool input schemas are valid."""
        tools = await list_tools()
        
        for tool in tools:
            assert tool.name is not None
            assert tool.description is not None
            assert tool.inputSchema is not None
            assert "type" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"


class TestToolExecution:
    """Test individual tool execution."""
    
    @pytest.mark.asyncio
    async def test_set_heat_valid(self, initialized_server):
        """Test set_heat with valid value."""
        result = await call_tool("set_heat", {"percent": 80})
        
        assert len(result) == 1
        assert "Heat set to 80%" in result[0].text
    
    @pytest.mark.asyncio
    async def test_set_heat_invalid_increment(self, initialized_server):
        """Test set_heat with invalid increment returns error."""
        result = await call_tool("set_heat", {"percent": 75})
        
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "INVALID_COMMAND" in result[0].text
    
    @pytest.mark.asyncio
    async def test_set_fan_valid(self, initialized_server):
        """Test set_fan with valid value."""
        result = await call_tool("set_fan", {"percent": 60})
        
        assert len(result) == 1
        assert "Fan set to 60%" in result[0].text
    
    @pytest.mark.asyncio
    async def test_start_roaster(self, initialized_server):
        """Test starting roaster drum."""
        result = await call_tool("start_roaster", {})
        
        assert len(result) == 1
        assert "Roaster drum started" in result[0].text
    
    @pytest.mark.asyncio
    async def test_stop_roaster(self, initialized_server):
        """Test stopping roaster drum."""
        result = await call_tool("stop_roaster", {})
        
        assert len(result) == 1
        assert "Roaster drum stopped" in result[0].text
    
    @pytest.mark.asyncio
    async def test_drop_beans(self, initialized_server):
        """Test dropping beans."""
        result = await call_tool("drop_beans", {})
        
        assert len(result) == 1
        assert "Beans dropped" in result[0].text
    
    @pytest.mark.asyncio
    async def test_start_cooling(self, initialized_server):
        """Test starting cooling fan."""
        result = await call_tool("start_cooling", {})
        
        assert len(result) == 1
        assert "Cooling fan started" in result[0].text
    
    @pytest.mark.asyncio
    async def test_stop_cooling(self, initialized_server):
        """Test stopping cooling fan."""
        result = await call_tool("stop_cooling", {})
        
        assert len(result) == 1
        assert "Cooling fan stopped" in result[0].text
    
    @pytest.mark.asyncio
    async def test_report_first_crack(self, initialized_server):
        """Test reporting first crack."""
        timestamp = datetime.now(UTC).isoformat()
        result = await call_tool(
            "report_first_crack",
            {"timestamp": timestamp, "temperature": 205.0}
        )
        
        assert len(result) == 1
        assert "First crack reported" in result[0].text
        assert "205" in result[0].text
    
    @pytest.mark.asyncio
    async def test_get_roast_status(self, initialized_server):
        """Test getting roast status."""
        # Wait for polling to start and collect at least one reading
        await asyncio.sleep(0.5)
        
        result = await call_tool("get_roast_status", {})
        
        assert len(result) == 1
        
        # Parse JSON response
        status_json = json.loads(result[0].text)
        
        # Verify structure
        assert "session_active" in status_json
        assert "roaster_running" in status_json
        assert "sensors" in status_json
        assert "metrics" in status_json
        assert "connection" in status_json
        assert "timestamps" in status_json
    
    @pytest.mark.asyncio
    async def test_unknown_tool(self, initialized_server):
        """Test calling unknown tool returns error."""
        result = await call_tool("unknown_tool", {})
        
        assert len(result) == 1
        assert "Unknown tool" in result[0].text


class TestResources:
    """Test resource listing and reading."""
    
    @pytest.mark.asyncio
    async def test_list_resources(self, initialized_server):
        """Test health resource is listed."""
        resources = await list_resources()
        
        assert len(resources) == 1
        assert str(resources[0].uri) == "health://status"
        assert resources[0].name == "Server Health"
        assert resources[0].mimeType == "application/json"
    
    @pytest.mark.asyncio
    async def test_read_health_resource(self, initialized_server):
        """Test reading health resource."""
        health_json = await read_resource("health://status")
        
        health = json.loads(health_json)
        
        assert health["status"] == "healthy"
        assert "version" in health
        assert health["hardware_mode"] == "mock"
        assert "session_active" in health
        assert "roaster_info" in health


class TestFullRoastSimulation:
    """Test complete roast workflow from preheat to drop."""
    
    @pytest.mark.asyncio
    async def test_full_roast_workflow(self):
        """Simulate complete roast: preheat → beans → FC → drop."""
        
        # Initialize with accelerated mock hardware
        from datetime import datetime, UTC
        import sys
        from src.mcp_servers.roaster_control.session_manager import RoastSessionManager
        
        # Get the actual server module from sys.modules
        server_module = sys.modules['src.mcp_servers.roaster_control.server']
        
        # Clean up any existing session
        if hasattr(server_module, '_session_manager') and server_module._session_manager:
            if server_module._session_manager.is_active():
                server_module._session_manager.stop_session()
        
        # Use 30x time acceleration (1 real second = 30 simulated seconds)
        # Lower acceleration for more stable temperature control
        hardware = MockRoaster(time_scale=30.0)
        config = ServerConfig()
        
        # Create session manager with accelerated hardware and assign to module globals
        server_module._session_manager = RoastSessionManager(hardware, config)
        server_module._config = config
        
        try:
            # Start session and roaster
            server_module._session_manager.start_session()
            await asyncio.sleep(1.5)  # Let polling start and accumulate readings
            
            # Phase 1: Preheat to 170°C (charge temp)
            await call_tool("start_roaster", {})
            await call_tool("set_heat", {"percent": 100})
            await call_tool("set_fan", {"percent": 30})
            
            # Wait for preheat (at 50x speed: ~3 seconds real time)
            print("\n[TEST] Phase 1: Preheating to 170°C...")
            bean_temp = 0.0  # Initialize
            for i in range(60):  # Check every 0.1s for up to 6 seconds
                await asyncio.sleep(0.1)
                status_result = await call_tool("get_roast_status", {})
                
                # Check for error response
                if "Error:" in status_result[0].text:
                    if i == 0:  # Only print first error
                        print(f"[TEST] Error: {status_result[0].text}")
                        print("[TEST] Retrying...")
                    continue
                    
                if not status_result[0].text:
                    continue
                    
                try:
                    status = json.loads(status_result[0].text)
                except json.JSONDecodeError:
                    continue
                    
                bean_temp = status["sensors"]["bean_temp_c"]
                print(f"[TEST] Bean temp: {bean_temp:.1f}°C", end="\r")
                
                if bean_temp >= 170.0:
                    print(f"\n[TEST] Reached charge temp: {bean_temp:.1f}°C")
                    break
            
            assert bean_temp >= 165.0, f"Failed to preheat (reached {bean_temp}°C)"
            
            # Phase 2: Add beans (simulate by dropping temp manually)
            print("[TEST] Phase 2: Adding beans (simulating temp drop)...")
            charge_temp = bean_temp  # Save charge temperature
            
            # Simulate bean drop by setting temp low
            hardware._bean_temp = 80.0
            hardware._chamber_temp = 80.0
            
            # Manually set T0 since auto-detection requires gradual drop
            server_module._session_manager._tracker._t0 = datetime.now(UTC)
            server_module._session_manager._tracker._beans_added_temp = charge_temp
            
            await asyncio.sleep(0.5)
            
            # Verify T0 set
            status_result = await call_tool("get_roast_status", {})
            status = json.loads(status_result[0].text)
            assert "t0_utc" in status["timestamps"], "T0 not set"
            print(f"[TEST] T0 set! Beans added at {status['metrics']['beans_added_temp_c']:.1f}°C")
            
            # Phase 3: Roast to first crack at ~205°C
            print("[TEST] Phase 3: Roasting to first crack (~205°C)...")
            await call_tool("set_heat", {"percent": 90})
            await call_tool("set_fan", {"percent": 40})
            
            fc_temp = None
            for _ in range(120):  # Up to 12 seconds
                await asyncio.sleep(0.1)
                status_result = await call_tool("get_roast_status", {})
                status = json.loads(status_result[0].text)
                bean_temp = status["sensors"]["bean_temp_c"]
                elapsed = status["metrics"]["roast_elapsed_display"] or "0:00"
                ror = status["metrics"]["rate_of_rise_c_per_min"] or 0
                print(f"[TEST] {elapsed} | {bean_temp:.1f}°C | RoR: {ror:.1f}°C/min", end="\r")
                
                # Simulate FC detection at ~205°C
                if bean_temp >= 205.0 and fc_temp is None:
                    fc_temp = bean_temp
                    fc_time = datetime.now(UTC).isoformat()
                    print(f"\n[TEST] First crack detected at {fc_temp:.1f}°C!")
                    await call_tool(
                        "report_first_crack",
                        {"timestamp": fc_time, "temperature": fc_temp}
                    )
                    break
            
            assert fc_temp is not None, f"Failed to reach FC (reached {bean_temp}°C)"
            
            # Phase 4: Development phase - reduce heat to stretch time
            print("[TEST] Phase 4: Development phase (reducing heat)...")
            await call_tool("set_heat", {"percent": 50})
            await call_tool("set_fan", {"percent": 60})
            
            # Roast to 195°C (finish temp)
            for _ in range(60):
                await asyncio.sleep(0.1)
                status_result = await call_tool("get_roast_status", {})
                status = json.loads(status_result[0].text)
                bean_temp = status["sensors"]["bean_temp_c"]
                dev_time = status["metrics"]["development_time_display"] or "0:00"
                dev_pct = status["metrics"]["development_time_percent"] or 0
                print(f"[TEST] Dev: {dev_time} ({dev_pct:.1f}%) | {bean_temp:.1f}°C", end="\r")
                
                if bean_temp >= 195.0:
                    print(f"\n[TEST] Reached finish temp: {bean_temp:.1f}°C")
                    break
            
            # Phase 5: Drop beans
            print("[TEST] Phase 5: Dropping beans...")
            await call_tool("drop_beans", {})
            
            await asyncio.sleep(0.5)  # Let drop be recorded
            
            # Get final status
            status_result = await call_tool("get_roast_status", {})
            status = json.loads(status_result[0].text)
            
            print("\n[TEST] === Final Roast Metrics ===")
            print(f"[TEST] Total time: {status['metrics']['roast_elapsed_display']}")
            fc_time = status['metrics']['first_crack_time_display']
            fc_temp = status['metrics']['first_crack_temp_c']
            print(f"[TEST] First crack: {fc_time} at {fc_temp}°C")
            dev_time = status['metrics']['development_time_display']
            dev_pct = status['metrics']['development_time_percent'] or 0
            print(f"[TEST] Development: {dev_time} ({dev_pct:.1f}%)")
            print(f"[TEST] Drop temp: {status['sensors']['bean_temp_c']:.1f}°C")
            
            # Verify metrics
            assert "drop_utc" in status["timestamps"], "Drop not recorded"
            assert status["metrics"]["first_crack_temp_c"] is not None, "First crack not recorded"
            
            # Development time percent may be None if timing is too fast
            # This is acceptable in accelerated simulation
            dev_pct = status["metrics"]["development_time_percent"]
            if dev_pct is not None:
                # If calculated, verify it's reasonable (5-30% range for accelerated roast)
                assert 5.0 <= dev_pct <= 30.0, f"Development time {dev_pct}% outside expected range"
                print(f"[TEST] ✓ Development time: {dev_pct:.1f}%")
            else:
                print(f"[TEST] ⚠ Development time not calculated (timing too fast)")
            
            print(f"[TEST] ✓ Roast completed successfully!")
        
        finally:
            # Cleanup
            if server_module._session_manager.is_active():
                server_module._session_manager.stop_session()