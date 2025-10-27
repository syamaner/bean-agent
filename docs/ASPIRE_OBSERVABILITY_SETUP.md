# Aspire Observability Setup

## How Aspire Works with OpenTelemetry

When you run `.NET Aspire`, it automatically:

1. **Starts the Aspire Dashboard** with an OTLP collector
2. **Sets environment variables** for each project:
   - `OTEL_EXPORTER_OTLP_ENDPOINT` = `http://localhost:4317` (gRPC) or `http://localhost:4318` (HTTP)
   - `OTEL_SERVICE_NAME` = your service name
   - `OTEL_RESOURCE_ATTRIBUTES` = service.instance.id=...

3. **Projects automatically export** telemetry to the dashboard

## For Python MCP Servers

Since your Python MCP servers aren't managed by Aspire's AppHost yet, you need to **manually set the environment variable**:

### Option 1: Set in Shell (Temporary)

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
```

Then run your MCP servers.

### Option 2: Set in .env File

Create `.env` file:
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=first-crack-mcp
```

### Option 3: Add to Aspire AppHost (Recommended)

If you have an Aspire AppHost, add your Python projects:

```csharp
var builder = DistributedApplication.CreateBuilder(args);

// Add Python MCP servers
var firstCrack = builder.AddExecutable(
    "first-crack-mcp",
    "python",
    "/Users/sertanyamaner/git/coffee-roasting",
    "-m", "src.mcp_servers.first_crack_detection"
).WithOtlpExporter(); // This adds OTEL_EXPORTER_OTLP_ENDPOINT automatically

var roasterControl = builder.AddExecutable(
    "roaster-control-mcp",
    "python",
    "/Users/sertanyamaner/git/coffee-roasting",
    "-m", "src.mcp_servers.roaster_control"
).WithOtlpExporter();

builder.Build().Run();
```

## Quick Test

1. **Start Aspire Dashboard**:
   ```bash
   dotnet run --project path/to/YourAspireApp.AppHost
   ```

2. **In another terminal, set the environment variable**:
   ```bash
   export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
   ```

3. **Run your MCP server**:
   ```bash
   python -m src.mcp_servers.first_crack_detection
   ```

4. **Check Aspire Dashboard** at `http://localhost:18888`:
   - Go to **Structured Logs** → Should see "first-crack-mcp" logs
   - Go to **Metrics** → Should see metrics being recorded
   - Go to **Traces** → Should see trace spans

## Troubleshooting

### "Observability package not available"
```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc
```

### "Connection refused" or no data in dashboard
- Check Aspire is running: `curl http://localhost:4317`
- Verify environment variable: `echo $OTEL_EXPORTER_OTLP_ENDPOINT`
- Look for "OpenTelemetry logging configured" in MCP server output

### Logs appear but no metrics
- Metrics are batched every 5 seconds - wait a bit
- Check the Metrics tab filters for your service name

---

**Key Point**: Aspire automatically provides the OTLP endpoint (`http://localhost:4317`), you just need to make sure your Python services can access that environment variable!
