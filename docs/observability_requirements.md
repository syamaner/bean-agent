# Observability requirements

We will be using Open Telemetry for traces as well as custom metrics.

## Metrics

- First Crack Detector
 
  - Emits a metrics when first crack is detected
    - Tags:
      - UTC Time Stamp
      - relative timestamp from start
      - What microphone was used

- Roaster control
  - Sensor data as individual metrics:
    - Bean Temperature
      - Tags: UTC time
    - Environment (chamber) temperature
      - Tags: UTC time
    - FAN Speed (anytime it is changed)
      - Tags: UTC time
    - Heat Level: (anytime it is adjusted)
      - Tags: UTC time
    - Rate of rise
      - Tags: UTC time
    - Development time
      - Tags: UTC time
    - Development time Percentage
      - Tags: UTC time
    - Charge Temperature
      - Tags: UTC time
    - FC Temperature
      - Tags: UTC time
    - Drop Temperature
      - Tags: UTC time
    - Roast Duration
      - Tags: UTC time

# Traces

- All components (python agent, n8n as well as mcp servers internal components) should participate in end to end tracing

# Logs

Our components should also use structured logging. The components should produce logs for all lifecycle events, detection, control and so on.

