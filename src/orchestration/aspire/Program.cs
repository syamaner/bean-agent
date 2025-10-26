#pragma warning disable ASPIREHOSTINGPYTHON001 // Python hosting is experimental

var builder = DistributedApplication.CreateBuilder(args);

// Parameters (Aspire requires hyphens, not underscores)
var auth0Domain = builder.AddParameter("auth0-domain");
var auth0Audience = builder.AddParameter("auth0-audience");
var auth0ClientId = builder.AddParameter("auth0-client-id");
var auth0ClientSecret = builder.AddParameter("auth0-client-secret");
var openAiApiKey = builder.AddParameter("openai-api-key");

// Optional mock mode for testing without hardware
var useMockHardware = builder.AddParameter("use-mock-hardware", "false", secret: false);

// Optional audio file for FC detection testing
var testAudioFile = builder.AddParameter("test-audio-file", "", secret: false);

// Python MCP Servers (relative to git root)
// Note: Using shared venv at repo root, running servers as modules to support relative imports
// Working directory is project root so absolute imports like "from src.X" work
var projectRoot = Path.GetFullPath("../../..");
var sharedVenvPath = Path.GetFullPath("../../../venv");

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

/*
// AI Agent (Autonomous roasting agent)
var aiAgent = builder.AddPythonApp(
        "ai-agent",
        projectRoot,
        "src/orchestration/agents/autonomous_agent.py",
        sharedVenvPath)
    .WithEnvironment("OPENAI_API_KEY", openAiApiKey)
    .WithEnvironment("AUTH0_DOMAIN", auth0Domain)
    .WithEnvironment("AUTH0_CLIENT_ID", auth0ClientId)
    .WithEnvironment("AUTH0_CLIENT_SECRET", auth0ClientSecret)
    .WithEnvironment("AUTH0_AUDIENCE", auth0Audience)
    .WithEnvironment("TEST_AUDIO_FILE", testAudioFile)
    .WithReference(roasterControl)
    .WithReference(firstCrackDetection);
    */

// n8n Workflow Engine with MCP Client Support
// n8n can use the LangChain MCP Tool node to connect to MCP servers via SSE
var n8n = builder.AddContainer("n8n", "n8nio/n8n", "latest")
    .WithHttpEndpoint(port: 5678, targetPort: 5678, name: "http")
    .WithEnvironment("N8N_HOST", "0.0.0.0")
    .WithEnvironment("N8N_PORT", "5678")
    .WithEnvironment("N8N_PROTOCOL", "http")
    .WithEnvironment("WEBHOOK_URL", "http://localhost:5678")
    .WithEnvironment("GENERIC_TIMEZONE", "UTC")
    .WithEnvironment("N8N_SECURE_COOKIE", "false")  // Allow local development without HTTPS
    // Verbose logging for debugging
    .WithEnvironment("N8N_LOG_LEVEL", "debug")
    .WithEnvironment("N8N_LOG_OUTPUT", "console")
    .WithEnvironment("N8N_LOG_FILE_LOCATION", "/home/node/.n8n/logs/")
    .WithEnvironment("N8N_LOG_FILE_MAX_SIZE", "10")
    .WithEnvironment("N8N_LOG_FILE_MAX_COUNT", "3")
    // Pass MCP server SSE endpoints to n8n (accessible as env vars in workflows)
    // Note: n8n is in Docker, MCP servers are on host, so use host.docker.internal
    .WithEnvironment("ROASTER_CONTROL_SSE", "http://host.docker.internal:5002")
    .WithEnvironment("FIRST_CRACK_SSE", "http://host.docker.internal:5001")
    // Auth0 configuration for MCP authentication (Bearer tokens)
    .WithEnvironment("AUTH0_DOMAIN", auth0Domain)
    .WithEnvironment("AUTH0_AUDIENCE", auth0Audience)
    .WithEnvironment("AUTH0_CLIENT_ID", auth0ClientId)
    .WithEnvironment("AUTH0_CLIENT_SECRET", auth0ClientSecret)
    // Mount volume for n8n data persistence (workflows, credentials, settings)
    .WithBindMount(Path.Combine(projectRoot, ".n8n"), "/home/node/.n8n")
    .WithReference(roasterControl)
    .WithReference(firstCrackDetection);

builder.Build().Run();
