# First Crack Detection MCP Server

MCP (Model Context Protocol) server that exposes first crack detection functionality for coffee roasting.

**Version**: 1.0.0 | **Transport**: stdio | **Status**: ✅ Ready

---

## Quick Start

```bash
# Run server
python -m src.mcp_servers.first_crack_detection

# Test server
python tests/mcp_servers/first_crack_detection/manual_test_client.py
```

---

## MCP Tools

### `start_first_crack_detection`
Start monitoring for first crack with audio file, USB microphone, or built-in microphone.

### `get_first_crack_status`  
Query current detection status and first crack timing.

### `stop_first_crack_detection`
Stop detection and get session summary.

---

## MCP Resources

### `health://status`
Server health, model status, and device information.

---

## Documentation

See full documentation in this directory:
- **USAGE.md** - Detailed usage examples
- **API.md** - Complete API reference
- **DEPLOYMENT.md** - Deployment guide

---

## Features

✅ Three audio sources (file/USB/built-in)  
✅ Real-time detection  
✅ UTC + local timestamps  
✅ Thread-safe  
✅ Idempotent operations  
✅ Comprehensive error handling

---

**For detailed documentation, see the full README content above or individual doc files.**
