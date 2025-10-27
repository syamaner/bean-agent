# Observability Package

OpenTelemetry-based observability for the coffee roasting system. Provides logs, metrics, and distributed tracing that integrate seamlessly with .NET Aspire dashboard.

---

## Features

✅ **Structured Logging** via OpenTelemetry LogEmitter  
✅ **Metrics** for First Crack Detection, Roaster Control, and Agent  
✅ **Distributed Tracing** across all components  
✅ **Auto-instrumentation** for HTTP requests (Flask, FastAPI, requests)  
✅ **OTLP Export** to .NET Aspire dashboard  

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# OTLP endpoint (provided by .NET Aspire)
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"

# Optional: Log level
export LOG_LEVEL="INFO"
```

### 3. Initialize in Your Service

```python
from observability import setup_logging, setup_tracing, FirstCrackMetrics

# Setup logging
setup_logging(service_name="first-crack-mcp")

# Setup tracing
tracer = setup_tracing(service_name="first-crack-mcp")

# Setup metrics
metrics = FirstCrackMetrics(service_name="first-crack-mcp")
```

---

## Usage Examples

### Logging

```python
from observability import get_logger

logger = get_logger(__name__)

# Simple log
logger.info("First crack detection started")

# Structured log with extra fields
logger.info(
    "First crack detected",
    extra={
        "confidence": 0.87,
        "elapsed_time": "8:45",
        "audio_source": "usb_microphone"
    }
)

# Error logging
try:
    # ... some operation ...
    pass
except Exception as e:
    logger.error("Failed to load model", exc_info=True, extra={"model_path": path})
```

### Metrics

#### First Crack Detection

```python
from observability import FirstCrackMetrics
from datetime import datetime, timezone

metrics = FirstCrackMetrics()

# Record detection event
metrics.record_detection(
    utc_timestamp=datetime.now(timezone.utc),
    relative_timestamp_seconds=525.0,  # 8:45
    audio_source="usb_microphone",
    confidence=0.87
)

# Record inference performance
metrics.record_inference(duration_seconds=0.05, confidence=0.87)

# Record audio buffer size
metrics.record_audio_buffer(size=160000)

# Record session end
metrics.record_session_end(duration_seconds=600, detected=True)
```

#### Roaster Control

```python
from observability import RoasterMetrics
from datetime import datetime, timezone

metrics = RoasterMetrics()

# Record sensor readings
metrics.record_sensors(
    utc_timestamp=datetime.now(timezone.utc),
    bean_temp_c=185.5,
    chamber_temp_c=190.2,
    fan_speed_pct=45.0,
    heat_level_pct=75.0
)

# Record calculated metrics
metrics.record_calculated_metrics(
    utc_timestamp=datetime.now(timezone.utc),
    rate_of_rise_c_per_min=7.2,
    development_time_pct=18.5
)

# Record key events
metrics.record_first_crack_temp(datetime.now(timezone.utc), temp_c=196.5)
metrics.record_drop_temp(datetime.now(timezone.utc), temp_c=202.0)

# Record control actions
metrics.record_heat_adjustment(datetime.now(timezone.utc), new_level=60)
metrics.record_fan_adjustment(datetime.now(timezone.utc), new_speed=50)
```

#### Agent

```python
from observability import AgentMetrics

metrics = AgentMetrics()

# Record decision
metrics.record_decision(
    duration_seconds=0.5,
    action="reduce_heat",
    phase="development"
)

# Record safety violation
metrics.record_safety_violation(
    violation_type="max_temp_exceeded",
    value=206.0
)

# Record roast completion
metrics.record_roast_completed(
    profile="light",
    dev_time_pct=18.5,
    drop_temp=202.0
)

# Record LLM usage
metrics.record_llm_tokens(tokens=450, model="gpt-4")
```

### Tracing

```python
from observability import setup_tracing, trace_span, add_span_event, record_exception

tracer = setup_tracing("first-crack-mcp")

# Create a span
with trace_span(tracer, "inference_window", attributes={"window_index": 42}):
    # Do work
    audio_data = extract_audio()
    
    # Add event to span
    with trace_span(tracer, "model_forward_pass", attributes={"model": "ast"}):
        result = model(audio_data)
    
    # Record event
    if result > threshold:
        add_span_event(span, "pop_detected", {"confidence": float(result)})

# Error handling with tracing
with trace_span(tracer, "load_model") as span:
    try:
        model = load_model(path)
    except Exception as e:
        record_exception(span, e)
        raise
```

### HTTP Auto-Instrumentation

When you call `setup_tracing()`, HTTP libraries are automatically instrumented:

```python
# Flask routes are auto-traced
@app.route("/api/detect/status")
def get_status():
    # This request is automatically traced
    return jsonify(status)

# HTTP requests are auto-traced
import requests
response = requests.get("http://localhost:5002/api/roaster/status")
# ^ This request is automatically traced with parent context
```

---

## Integration with MCP Servers

### First Crack Detection MCP

Add to `src/mcp_servers/first_crack_detection/server.py`:

```python
from observability import setup_logging, setup_tracing, FirstCrackMetrics, get_logger

# Initialize at startup
setup_logging("first-crack-mcp")
tracer = setup_tracing("first-crack-mcp")
metrics = FirstCrackMetrics()
logger = get_logger(__name__)

# Use in session manager
class DetectionSessionManager:
    def start_session(self, audio_config):
        logger.info("Starting detection session", extra={"audio_source": audio_config.audio_source_type})
        
        with trace_span(tracer, "start_detection_session"):
            # ... existing code ...
            metrics.record_session_start()
            
    def _on_first_crack_detected(self, timestamp, confidence):
        logger.info("First crack detected", extra={"timestamp": timestamp, "confidence": confidence})
        metrics.record_detection(
            utc_timestamp=datetime.now(timezone.utc),
            relative_timestamp_seconds=timestamp,
            audio_source=self.audio_source_type,
            confidence=confidence
        )
```

### Roaster Control MCP

Add to `src/mcp_servers/roaster_control/server.py`:

```python
from observability import setup_logging, setup_tracing, RoasterMetrics, get_logger

setup_logging("roaster-control-mcp")
tracer = setup_tracing("roaster-control-mcp")
metrics = RoasterMetrics()
logger = get_logger(__name__)

class RoasterSessionManager:
    def read_sensors(self):
        with trace_span(tracer, "read_sensors") as span:
            temps = self.roaster.read_temperatures()
            
            metrics.record_sensors(
                utc_timestamp=datetime.now(timezone.utc),
                bean_temp_c=temps.bean,
                chamber_temp_c=temps.chamber,
                fan_speed_pct=self.roaster.fan_speed,
                heat_level_pct=self.roaster.heat_level
            )
            
            return temps
```

---

## .NET Aspire Integration

### 1. Start Aspire Dashboard

The .NET Aspire AppHost automatically starts the dashboard and OTLP collector:

```bash
dotnet run --project src/aspire/CoffeeRoasting.AppHost
```

The dashboard will be available at `http://localhost:18888` (or shown in console output).

### 2. Python Services Auto-Connect

Python MCP servers will automatically export telemetry to `http://localhost:4317` (OTLP gRPC endpoint provided by Aspire).

### 3. View in Dashboard

Open the Aspire dashboard and navigate to:

- **Logs**: See structured logs from all services
- **Metrics**: View real-time metrics charts
- **Traces**: Explore distributed traces across services

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP gRPC endpoint |
| `OTEL_SERVICE_NAME` | (from code) | Override service name |
| `LOG_LEVEL` | `INFO` | Python log level |
| `OTEL_TRACES_EXPORTER` | `otlp` | Traces exporter type |
| `OTEL_METRICS_EXPORTER` | `otlp` | Metrics exporter type |
| `OTEL_LOGS_EXPORTER` | `otlp` | Logs exporter type |

---

## Metrics Reference

### First Crack Detection

| Metric | Type | Description |
|--------|------|-------------|
| `fc.detections.total` | Counter | Total first crack detections |
| `fc.inference.duration` | Histogram | Model inference latency |
| `fc.confidence` | Gauge | Current detection confidence |
| `fc.audio_buffer.size` | Gauge | Audio buffer size (samples) |
| `fc.session.duration` | Histogram | Session duration |
| `fc.audio.errors.total` | Counter | Audio stream errors |
| `fc.model.load_duration` | Histogram | Model load time |

### Roaster Control

| Metric | Type | Description |
|--------|------|-------------|
| `roaster.bean_temp.celsius` | Gauge | Bean temperature |
| `roaster.chamber_temp.celsius` | Gauge | Chamber temperature |
| `roaster.fan_speed.percent` | Gauge | Fan speed |
| `roaster.heat_level.percent` | Gauge | Heat level |
| `roaster.rate_of_rise.c_per_min` | Gauge | Rate of rise |
| `roaster.development_time.percent` | Gauge | Development time % |
| `roaster.charge_temp.celsius` | Histogram | Charge temperature |
| `roaster.first_crack_temp.celsius` | Histogram | First crack temperature |
| `roaster.drop_temp.celsius` | Histogram | Drop temperature |
| `roaster.roast_duration.seconds` | Histogram | Roast duration |
| `roaster.heat_adjustments.total` | Counter | Heat adjustments |
| `roaster.fan_adjustments.total` | Counter | Fan adjustments |
| `roaster.bean_drops.total` | Counter | Bean drops |
| `roaster.sensor_errors.total` | Counter | Sensor errors |
| `roaster.command_errors.total` | Counter | Command errors |
| `roaster.connection.status` | Gauge | Connection status (0/1) |

### Agent

| Metric | Type | Description |
|--------|------|-------------|
| `agent.decision.duration` | Histogram | Decision latency |
| `agent.decisions.total` | Counter | Total decisions |
| `agent.safety_violations.total` | Counter | Safety violations |
| `agent.roasts_completed.total` | Counter | Completed roasts |
| `agent.roasts_aborted.total` | Counter | Aborted roasts |
| `agent.target_achievement.ratio` | Histogram | Target achievement % |
| `agent.llm_tokens.total` | Counter | LLM tokens consumed |
| `agent.llm_errors.total` | Counter | LLM errors |

---

## Troubleshooting

### Logs not appearing in Aspire?

1. Check OTLP endpoint: `echo $OTEL_EXPORTER_OTLP_ENDPOINT`
2. Ensure Aspire dashboard is running
3. Verify network connectivity: `curl http://localhost:4317`

### Metrics not updating?

Metrics are exported every 5 seconds by default. Wait a few seconds after recording.

### Traces missing spans?

Ensure `setup_tracing()` is called before creating any spans. Check that HTTP auto-instrumentation succeeded (no warnings in console).

---

## Next Steps

1. ✅ Install OpenTelemetry dependencies
2. ✅ Integrate logging/metrics/tracing into MCP servers
3. ⚪ Configure .NET Aspire AppHost to run Python services
4. ⚪ Create custom dashboard views in Aspire
5. ⚪ Add alerting rules for safety violations

---

**Status**: Implementation complete, ready for integration testing with .NET Aspire.
