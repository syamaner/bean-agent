# C# Agent Framework - Future Roadmap

**Status:** Planned  
**Priority:** Medium  
**Prerequisite:** Python Agent Framework + DevUI working

---

## Overview

After successfully implementing the **Python Agent Framework** with DevUI, the next natural step is to create a **C# (.NET) version** of the coffee roasting agent using the Microsoft Agent Framework for .NET.

This would provide a fully native .NET experience that integrates seamlessly with your .NET Aspire orchestration.

---

## Why C# Agent Framework?

### Benefits

✅ **Native .NET Integration**
- Seamless Aspire orchestration
- Type-safe across the entire stack
- Better Visual Studio integration
- Native debugging with breakpoints

✅ **Performance**
- Compiled code (faster execution)
- Lower memory footprint
- Better async/await performance
- Optimal for production

✅ **Enterprise Features**
- Strong typing throughout
- LINQ for data manipulation
- Dependency injection built-in
- Better testability with xUnit

✅ **Unified Codebase**
- Match your .NET Aspire AppHost
- Consistent patterns across stack
- Easier for .NET developers
- Single language for orchestration + agents

### Comparison: Python vs. C# Agent

| Aspect | Python Agent | C# Agent |
|--------|-------------|----------|
| **Language** | Python 3.11 | C# 12 (.NET 8) |
| **Setup** | venv + pip | NuGet packages |
| **Type Safety** | Runtime (Pydantic) | Compile-time |
| **Performance** | Interpreted | Compiled |
| **Debugging** | Print/logging | Full debugger |
| **Integration** | Aspire Python app | Native Aspire |
| **Tools** | 11 Python functions | 11 C# methods |
| **DevUI** | Yes (Python) | Yes (.NET) |
| **Best For** | Rapid prototyping | Production deployment |

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│   Microsoft Agent Framework (.NET)                   │
│                                                        │
│   ┌────────────────────────────────────────────────┐ │
│   │  AgentsClient (Azure OpenAI)                   │ │
│   │                                                 │ │
│   │  Instructions: Roasting expertise              │ │
│   │  Tools: 11 MCP-backed functions                │ │
│   └────────────────────────────────────────────────┘ │
│                        │                               │
│                        ▼                               │
│   ┌────────────────────────────────────────────────┐ │
│   │  Tool Definitions (C#)                         │ │
│   │                                                 │ │
│   │  - FirstCrackTools                             │ │
│   │    └─ HttpClient → MCP Server (5001)          │ │
│   │                                                 │ │
│   │  - RoasterControlTools                         │ │
│   │    └─ HttpClient → MCP Server (5002)          │ │
│   └────────────────────────────────────────────────┘ │
│                        │                               │
└────────────────────────┼───────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │  MCP Servers (HTTP + Auth0)   │
         │  - First Crack (5001)         │
         │  - Roaster Control (5002)     │
         └───────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Basic Agent (1-2 days)

**Goal:** Create working C# agent that connects to MCP servers

**Tasks:**
1. Create new C# project: `CoffeeRoasting.Agent`
2. Add NuGet packages:
   ```xml
   <PackageReference Include="Microsoft.Extensions.AI" Version="9.0.0" />
   <PackageReference Include="Microsoft.Extensions.AI.OpenAI" Version="9.0.0" />
   <PackageReference Include="Microsoft.SemanticKernel" Version="1.x" />
   ```
3. Implement `IMcpClient` for HTTP calls
4. Create tool definitions for 11 MCP endpoints
5. Configure AgentsClient with OpenAI
6. Basic console app to test

**Files:**
```
src/agents/
├── CoffeeRoasting.Agent/
│   ├── CoffeeRoasting.Agent.csproj
│   ├── Program.cs
│   ├── Services/
│   │   ├── McpClientService.cs
│   │   └── Auth0TokenService.cs
│   ├── Tools/
│   │   ├── FirstCrackTools.cs
│   │   └── RoasterControlTools.cs
│   └── Configuration/
│       └── AgentConfig.cs
```

### Phase 2: Tool Integration (1-2 days)

**Goal:** All 11 MCP tools working from C#

**Tasks:**
1. Implement `FirstCrackTools`:
   - `StartDetection()`
   - `GetStatus()`
   - `StopDetection()`

2. Implement `RoasterControlTools`:
   - `GetStatus()`
   - `StartRoaster()`
   - `SetHeat()`
   - `SetFan()`
   - `DropBeans()`
   - `StopRoaster()`
   - `StartCooling()`
   - `StopCooling()`

3. Add Auth0 token management with caching
4. Add retry logic and error handling
5. Unit tests with NSubstitute

### Phase 3: Agent Instructions (1 day)

**Goal:** Embed roasting expertise in C# agent

**Tasks:**
1. Port Python instructions to C# constants
2. Add safety rules and limits
3. Implement decision-making prompts
4. Add structured logging

**Example:**
```csharp
public static class RoastingInstructions
{
    public const string SystemPrompt = """
        You are an expert autonomous coffee roasting agent.
        
        Your role is to monitor and control coffee roasting in real-time...
        """;
    
    public static class SafetyLimits
    {
        public const double MaxBeanTemp = 205.0;
        public const double MaxRoR = 10.0;
        public const double MinRoR = 3.0;
    }
}
```

### Phase 4: Aspire Integration (1 day)

**Goal:** Run C# agent in Aspire alongside Python version

**Tasks:**
1. Add agent to `Program.cs`:
   ```csharp
   var coffeeAgent = builder.AddProject<Projects.CoffeeRoasting_Agent>("coffee-agent")
       .WithEnvironment("OPENAI_API_KEY", openAiApiKey)
       .WithEnvironment("AUTH0_DOMAIN", auth0Domain)
       .WithReference(roasterControl)
       .WithReference(firstCrackDetection);
   ```

2. Configure as hosted service or console app
3. Add health checks
4. Integrate with Aspire Dashboard telemetry

### Phase 5: DevUI for .NET (Optional, 2-3 days)

**Goal:** .NET version of DevUI or integration with existing

**Options:**

**Option A:** Use Python DevUI API
- C# agent exposes HTTP API
- Python DevUI consumes it
- Simpler, reuses existing UI

**Option B:** Native .NET DevUI
- Blazor web UI
- SignalR for real-time updates
- Full .NET stack

---

## Code Examples

### Basic C# Agent Setup

```csharp
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;

public class CoffeeRoastingAgent
{
    private readonly IChatClient _chatClient;
    private readonly ILogger<CoffeeRoastingAgent> _logger;
    
    public CoffeeRoastingAgent(
        IChatClient chatClient,
        ILogger<CoffeeRoastingAgent> logger)
    {
        _chatClient = chatClient;
        _logger = logger;
    }
    
    public async Task<string> RunAsync(string userMessage)
    {
        var messages = new List<ChatMessage>
        {
            new(ChatRole.System, RoastingInstructions.SystemPrompt),
            new(ChatRole.User, userMessage)
        };
        
        var response = await _chatClient.CompleteAsync(
            messages,
            new ChatOptions
            {
                Tools = GetTools(),
                Temperature = 0.3f
            });
        
        return response.Message.Text;
    }
    
    private IList<AITool> GetTools()
    {
        return new List<AITool>
        {
            // First crack tools
            AIFunctionFactory.Create(FirstCrackTools.StartDetection),
            AIFunctionFactory.Create(FirstCrackTools.GetStatus),
            AIFunctionFactory.Create(FirstCrackTools.StopDetection),
            
            // Roaster control tools
            AIFunctionFactory.Create(RoasterControlTools.GetStatus),
            AIFunctionFactory.Create(RoasterControlTools.StartRoaster),
            // ... etc
        };
    }
}
```

### MCP Tool Example

```csharp
public static class FirstCrackTools
{
    [Description("Start first crack detection monitoring")]
    public static async Task<string> StartDetection(
        [Description("Audio source type")] string audioSource = "usb_microphone",
        [Description("Detection threshold (0-1)")] float threshold = 0.5f,
        [Description("Minimum pops to confirm")] int minPops = 3,
        IMcpClient mcpClient = null!)
    {
        var payload = new
        {
            audio_source_type = audioSource,
            detection_config = new
            {
                threshold,
                min_pops = minPops,
                confirmation_window = 30.0
            }
        };
        
        var response = await mcpClient.PostAsync(
            "/api/detection/start",
            JsonContent.Create(payload));
        
        return await response.Content.ReadAsStringAsync();
    }
}
```

### Auth0 Token Service

```csharp
public class Auth0TokenService
{
    private readonly HttpClient _httpClient;
    private readonly IOptions<Auth0Config> _config;
    private string? _cachedToken;
    private DateTime _tokenExpiry;
    
    public async Task<string> GetTokenAsync()
    {
        if (!string.IsNullOrEmpty(_cachedToken) && DateTime.UtcNow < _tokenExpiry)
        {
            return _cachedToken;
        }
        
        var request = new
        {
            client_id = _config.Value.ClientId,
            client_secret = _config.Value.ClientSecret,
            audience = _config.Value.Audience,
            grant_type = "client_credentials"
        };
        
        var response = await _httpClient.PostAsJsonAsync(
            $"https://{_config.Value.Domain}/oauth/token",
            request);
        
        response.EnsureSuccessStatusCode();
        
        var result = await response.Content.ReadFromJsonAsync<TokenResponse>();
        _cachedToken = result.AccessToken;
        _tokenExpiry = DateTime.UtcNow.AddSeconds(result.ExpiresIn - 300); // 5 min buffer
        
        return _cachedToken;
    }
}
```

---

## Testing Strategy

### Unit Tests (xUnit + NSubstitute)

```csharp
public class FirstCrackToolsTests
{
    [Fact]
    public async Task StartDetection_SendsCorrectPayload()
    {
        // Arrange
        var mockClient = Substitute.For<IMcpClient>();
        mockClient.PostAsync(Arg.Any<string>(), Arg.Any<JsonContent>())
            .Returns(Task.FromResult(new HttpResponseMessage
            {
                StatusCode = HttpStatusCode.OK,
                Content = new StringContent("{\"status\":\"started\"}")
            }));
        
        // Act
        var result = await FirstCrackTools.StartDetection(
            audioSource: "usb_microphone",
            mcpClient: mockClient);
        
        // Assert
        await mockClient.Received(1).PostAsync("/api/detection/start", Arg.Any<JsonContent>());
        Assert.Contains("started", result);
    }
}
```

### Integration Tests

```csharp
public class AgentIntegrationTests : IClassFixture<WebApplicationFactory<Program>>
{
    [Fact]
    public async Task Agent_CanCheckRoasterStatus()
    {
        // Arrange
        var agent = CreateAgent();
        
        // Act
        var response = await agent.RunAsync("Check the roaster status");
        
        // Assert
        Assert.Contains("roaster", response.ToLower());
        Assert.Contains("temperature", response.ToLower());
    }
}
```

---

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Phase 1** | 1-2 days | Basic C# agent with MCP connections |
| **Phase 2** | 1-2 days | All 11 tools working |
| **Phase 3** | 1 day | Roasting instructions embedded |
| **Phase 4** | 1 day | Aspire integration complete |
| **Phase 5** | 2-3 days | DevUI (optional) |
| **Total** | 6-9 days | Production-ready C# agent |

---

## Decision Points

### When to Build C# Version?

**Build Now If:**
- ✅ You prefer .NET for production
- ✅ Team is primarily C# developers
- ✅ Want better Aspire integration
- ✅ Need compiled performance
- ✅ Require strong typing everywhere

**Wait If:**
- ⚠️ Python agent works well
- ⚠️ No .NET expertise on team
- ⚠️ Rapid iteration still needed
- ⚠️ Python ecosystem preferred

### Python vs. C# - Which to Use?

**Use Python Agent:**
- Development and prototyping
- Data science workflows
- ML model integration
- Jupyter notebooks
- Quick experiments

**Use C# Agent:**
- Production deployment
- Enterprise integration
- High-performance requirements
- Full .NET stack preference
- Visual Studio development

**Use Both:**
- Python for dev/test
- C# for production
- Best of both worlds!

---

## Resources

### Microsoft Agent Framework (.NET)

- **GitHub:** https://github.com/microsoft/agent-framework/tree/main/dotnet
- **Samples:** https://github.com/microsoft/agent-framework/tree/main/dotnet/samples
- **NuGet:** `Microsoft.Extensions.AI`, `Microsoft.SemanticKernel`

### Related Documentation

- [Python Agent README](../../agents/roaster/README.md)
- [Phase 4 Overview](./README.md)
- [DevUI Guide](./DEVUI.md)
- [Aspire Documentation](https://learn.microsoft.com/dotnet/aspire/)

---

## Next Steps

1. ✅ Complete Python Agent Framework implementation
2. ✅ Test DevUI thoroughly with Python agent
3. ✅ Validate MCP server stability
4. ⏭️ **Decision:** Build C# version?
5. If yes → Follow Phase 1-5 plan above
6. If no → Continue with Python agent in production

---

**The C# agent path is ready when you are!** 🚀

Both Python and C# implementations can coexist, giving you flexibility to choose the best tool for each scenario.

---

**Built with ☕ and 🤖 - Ready for .NET!**
