#pragma warning disable ASPIREHOSTINGPYTHON001 // Python hosting is experimental

var builder = DistributedApplication.CreateBuilder(args);

// Parameters (Aspire requires hyphens, not underscores)
var auth0Domain = builder.AddParameter("auth0-domain");
var auth0Audience = builder.AddParameter("auth0-audience");

// Optional mock mode for testing without hardware
var useMockHardware = builder.AddParameter("use-mock-hardware", "false", secret: false);

// Python MCP Servers (relative to git root)
// Note: Using shared venv at repo root, running servers as modules to support relative imports
// Working directory is project root so absolute imports like "from src.X" work
var projectRoot = Path.GetFullPath("../..");
var sharedVenvPath = Path.GetFullPath("../../venv");

var roasterControl = builder.AddPythonApp(
        "roaster-control",
        projectRoot,
        "-m",
        sharedVenvPath)
    .WithArgs("src.mcp_servers.roaster_control.sse_server")
    .WithHttpEndpoint(port: 5002, env: "ROASTER_CONTROL_PORT")
    .WithEnvironment("AUTH0_DOMAIN", auth0Domain)
    .WithEnvironment("AUTH0_AUDIENCE", auth0Audience)
    .WithEnvironment("USE_MOCK_HARDWARE", useMockHardware);

var firstCrackDetection = builder.AddPythonApp(
        "first-crack-detection",
        projectRoot,
        "-m",
        sharedVenvPath)
    .WithArgs("src.mcp_servers.first_crack_detection.sse_server")
    .WithHttpEndpoint(port: 5001, env: "FIRST_CRACK_DETECTION_PORT")
    .WithEnvironment("AUTH0_DOMAIN", auth0Domain)
    .WithEnvironment("AUTH0_AUDIENCE", auth0Audience);

#pragma warning restore ASPIREHOSTINGPYTHON001

// AI Agent (Autonomous roasting agent)
var aiAgent = builder.AddPythonApp(
        "ai-agent",
        projectRoot,
        "Phase3/autonomous_agent.py",
        sharedVenvPath)
    .WithEnvironment("OPENAI_API_KEY", builder.AddParameter("openai-api-key"))
    .WithEnvironment("AUTH0_DOMAIN", auth0Domain)
    .WithEnvironment("AUTH0_CLIENT_ID", builder.AddParameter("auth0-client-id"))
    .WithEnvironment("AUTH0_CLIENT_SECRET", builder.AddParameter("auth0-client-secret"))
    .WithEnvironment("AUTH0_AUDIENCE", auth0Audience)
    .WithReference(roasterControl)
    .WithReference(firstCrackDetection);

// n8n removed - using Python AI agent instead

builder.Build().Run();
