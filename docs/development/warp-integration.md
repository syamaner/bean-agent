# Warp Integration - Quick Reference

**Status**: ✅ Ready for Integration  
**Last Updated**: 2025-01-25

---

## 🚀 Quick Start

### 1. Add to Warp MCP Configuration

Add this to your Warp MCP settings:

```json
{
  "mcpServers": {
    "first-crack-detection": {
      "command": "<PROJECT_ROOT>/venv/bin/python",
      "args": ["-m", "src.mcp_servers.first_crack_detection"],
      "cwd": "<PROJECT_ROOT>",
      "env": {
        "PYTHONPATH": "<PROJECT_ROOT>",
        "FIRST_CRACK_MODEL_CHECKPOINT": "<PROJECT_ROOT>/experiments/runs/10s_70overlap_v1/checkpoints/best_model.pt"
      }
    }
  }
}
```

**Note**: Replace `<PROJECT_ROOT>` with your actual project path (e.g., `/Users/yourname/git/coffee-roasting`)

### 2. Verify Installation

In Warp, the agent should now have access to these tools:
- `start_first_crack_detection`
- `get_first_crack_status`
- `stop_first_crack_detection`

---

## 📋 Available Tools

### Tool 1: `start_first_crack_detection`

**Purpose**: Start monitoring for first crack

**Parameters**:
- `audio_source_type` (required): `"audio_file"` | `"usb_microphone"` | `"builtin_microphone"`
- `audio_file_path` (conditional): Required if `audio_source_type` is `"audio_file"`
- `detection_config` (optional): Override detection parameters

**Example Prompts**:
- "Start monitoring for first crack using the audio file at data/raw/roast.wav"
- "Begin first crack detection with USB microphone"
- "Monitor for first crack with built-in mic"

**Returns**:
```json
{
  "status": "success",
  "result": {
    "session_state": "started",
    "session_id": "uuid",
    "started_at_utc": "2025-01-25T16:00:00Z",
    "started_at_local": "2025-01-25T08:00:00-08:00",
    "audio_source": "audio_file",
    "audio_source_details": "file: data/raw/roast.wav"
  }
}
```

---

### Tool 2: `get_first_crack_status`

**Purpose**: Check current detection status

**Parameters**: None

**Example Prompts**:
- "Has first crack been detected?"
- "What's the current status?"
- "Check first crack detection"

**Returns** (no detection):
```json
{
  "status": "success",
  "result": {
    "session_active": true,
    "session_id": "uuid",
    "elapsed_time": "05:30",
    "first_crack_detected": false
  }
}
```

**Returns** (detection confirmed):
```json
{
  "status": "success",
  "result": {
    "session_active": true,
    "first_crack_detected": true,
    "first_crack_time_relative": "08:06",
    "first_crack_time_utc": "2025-01-25T16:08:06Z",
    "first_crack_time_local": "2025-01-25T08:08:06-08:00",
    "elapsed_time": "08:30"
  }
}
```

---

### Tool 3: `stop_first_crack_detection`

**Purpose**: Stop monitoring and get summary

**Parameters**: None

**Example Prompts**:
- "Stop first crack detection"
- "End monitoring"
- "Get the final summary"

**Returns**:
```json
{
  "status": "success",
  "result": {
    "session_state": "stopped",
    "session_id": "uuid",
    "session_summary": {
      "duration": "10:30",
      "first_crack_detected": true,
      "first_crack_time": "08:06",
      "audio_source": "audio_file"
    }
  }
}
```

---

## 💡 Example Workflows

### Workflow 1: Monitor Audio File

```
You: "Start monitoring for first crack using data/raw/brazil-roast.wav"
Agent: [Calls start_first_crack_detection]
       ✅ Started session abc-123

You: "Check the status"
Agent: [Calls get_first_crack_status]
       No first crack detected yet (elapsed: 05:30)

[Wait 3 minutes]

You: "Check again"
Agent: [Calls get_first_crack_status]
       🎉 First crack detected at 08:06!

You: "Stop monitoring"
Agent: [Calls stop_first_crack_detection]
       Summary: Duration 10:30, first crack at 08:06
```

### Workflow 2: Live Microphone Monitoring

```
You: "Start monitoring with USB microphone"
Agent: [Calls start_first_crack_detection with usb_microphone]
       ✅ Started monitoring with USB mic

You: "What's the status?"
Agent: [Polls get_first_crack_status]
       Listening... (05:00 elapsed, no detection yet)

[Roasting continues...]

Agent: [Auto-polls status]
       🎉 First crack detected at 08:30!

You: "Stop"
Agent: [Calls stop_first_crack_detection]
       Roast complete. First crack confirmed at 08:30
```

---

## 🔧 Configuration

### Model
- **Checkpoint**: `experiments/runs/10s_70overlap_v1/checkpoints/best_model.pt`
- **Threshold**: 0.5
- **Min pops**: 3
- **Confirmation window**: 30 seconds

### Environment Variables (Optional)
Override defaults via environment:

```bash
export FIRST_CRACK_MODEL_CHECKPOINT=/custom/path/model.pt
export FIRST_CRACK_LOG_LEVEL=DEBUG
```

---

## ⚠️ Important Notes

### Behavior
- **Single session**: Only one detection can run at a time
- **Idempotent**: Safe to call start/stop multiple times
- **Thread-safe**: All operations are thread-safe
- **No persistence**: Session data in-memory only

### Timing
- **Model load**: ~2 seconds on first start
- **Detection**: Real-time (processes faster than playback for files)
- **Status query**: <50ms response time

### Audio Files
- **Format**: WAV files recommended
- **Location**: Use absolute paths or relative to project root
- **Example**: `data/raw/your-roast.wav`

---

## 🐛 Troubleshooting

### Server won't start
```bash
# Test server manually
cd <PROJECT_ROOT>
PYTHONPATH=. python -m src.mcp_servers.first_crack_detection
```

### Model not found
```bash
# Check model exists
ls -lh experiments/runs/10s_70overlap_v1/checkpoints/best_model.pt

# Update config if needed
export FIRST_CRACK_MODEL_CHECKPOINT=/path/to/model.pt
```

### USB Microphone not detected
```bash
# List available audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Check system permissions (macOS)
# System Settings > Privacy & Security > Microphone
```

### Check logs
```bash
# Enable debug logging
export FIRST_CRACK_LOG_LEVEL=DEBUG

# Server logs will show in Warp console
```

---

## 📊 Test Results

### Verified Working
✅ Model loads (987MB checkpoint)  
✅ Audio file detection  
✅ First crack detected at 08:06 in test file  
✅ Session management (start/stop/status)  
✅ Timestamps (UTC + local)  
✅ Idempotency  
✅ Error handling  

### Test Audio
- **File**: `data/raw/25-10-19_1315-brazil4.alog.wav`
- **First crack**: 08:06
- **Confidence**: 3 pops in 30s window
- **Detection time**: 31 seconds elapsed

---

## 🎯 Success Indicators

When working correctly, you should see:
1. ✅ Server starts without errors
2. ✅ Tools appear in Warp's available tools
3. ✅ Start returns session ID
4. ✅ Status queries return current state
5. ✅ First crack detected and reported
6. ✅ Stop returns summary

---

## 📞 Support

### Documentation
- [Complete README](first_crack_detection/README.md)
- [Phase 2 Completion Summary](PHASE2_OBJ1_COMPLETE.md)
- [Testing Guide](TESTING.md)

### Test Scripts
```bash
# Quick functionality test
PYTHONPATH=. ./venv/bin/python tests/mcp_servers/first_crack_detection/quick_test.py

# Full detection test (with real audio)
PYTHONPATH=. ./venv/bin/python tests/mcp_servers/first_crack_detection/test_first_crack_detection.py
```

---

## 🚀 You're Ready!

The MCP server is production-ready and successfully tested with real audio.

**First crack detection verified**: 08:06 detection with 3 pops confidence! ☕

Go ahead and test it in Warp! 🎉
