# Agent Platform Comparison: LangFlow vs Flowise

## Executive Summary

Both LangFlow and Flowise are viable alternatives to n8n for AI agent orchestration. Here's the verdict:

| Feature | LangFlow | Flowise | n8n |
|---------|----------|---------|-----|
| **Docker Support** | ✅ Official | ✅ Official | ✅ Official |
| **Free & Open Source** | ✅ Yes | ✅ Yes | ✅ Yes |
| **MCP Integration** | ✅ Native | ✅ Native | ⚠️ Limited |
| **Agent Loops** | ✅ Built-in | ✅ Built-in | ⚠️ Manual |
| **Dynamic Auth** | ✅ Variables + API | ✅ Variables + API | ❌ Static only |
| **Custom Tools** | ✅ Python/JS | ✅ JavaScript | ✅ Limited |
| **Auth0 Integration** | ✅ Via HTTP nodes | ✅ Via HTTP nodes | ✅ Via HTTP nodes |
| **Best For** | Python devs | JS/TS devs | Non-dev automation |

**Recommendation**: **LangFlow** (best match for your Python stack) or **Flowise** (if you prefer TypeScript)

---

## 1. LangFlow

### ✅ What Works

**Docker Deployment:**
- Official image: `langflowai/langflow:latest`
- One command: `docker run -p 7860:7860 langflowai/langflow:latest`
- Docker Compose with PostgreSQL included
- **Perfect for Aspire integration**

**MCP Support:**
```json
{
  "mcpServers": {
    "roaster-control": {
      "command": "npx",
      "args": ["-y", "mcp-proxy", "http://host.docker.internal:5002/sse"],
      "env": {
        "AUTH_TOKEN": "{{ $vars.auth_token }}"
      }
    }
  }
}
```

**Agent Loops:**
- Built-in Loop node with max iteration control
- Can loop back to specific nodes
- Automatic retry with improved queries

**Dynamic Authentication:**
- ✅ Global variables via `$vars`
- ✅ Flow state via `$flow.state`
- ✅ Session context via `$flow.sessionId`
- ✅ Environment variables accessible
- **Auth0 token can be fetched and stored in `$vars.auth_token`**

**Custom Tools:**
- Python custom components (matches your stack!)
- Can access `$vars`, `$flow`, and input parameters
- Tool mode for automatic agent integration

### ⚠️ Limitations

- UI can be slower than Flowise
- Python custom components require restart
- Less polished than Flowise (but more powerful)

### 📋 Implementation Plan for Your Use Case

```python
# LangFlow + .NET Aspire Setup

# 1. Add to Program.cs:
var langflow = builder.AddContainer("langflow", "langflowai/langflow", "latest")
    .WithHttpEndpoint(port: 7860, targetPort: 7860)
    .WithEnvironment("AUTH0_DOMAIN", auth0Domain)
    .WithEnvironment("AUTH0_CLIENT_ID", auth0ClientId)
    .WithEnvironment("AUTH0_CLIENT_SECRET", auth0ClientSecret)
    .WithEnvironment("AUTH0_AUDIENCE", auth0Audience)
    .WithBindMount(Path.Combine(projectRoot, ".langflow"), "/app/langflow")
    .WithReference(roasterControl)
    .WithReference(firstCrackDetection);
```

**Flow Structure:**
1. **HTTP Request node**: Get Auth0 token
2. **Set Variable node**: Store token in `$vars.auth_token`
3. **MCP Tools node**: Configure roaster control + first crack detection
   - Use `{{ $vars.auth_token }}` in headers
4. **Agent node**: Execute roasting loop
5. **Loop node**: Retry logic if needed

**Pros for your use case:**
- ✅ Python-based (matches your MCP servers)
- ✅ Native variable system handles Auth0 tokens
- ✅ MCP integration is first-class
- ✅ Agent loops are built-in
- ✅ Can deploy alongside Python services

**Cons:**
- Slightly steeper learning curve than Flowise
- UI can feel less responsive

---

## 2. Flowise

### ✅ What Works

**Docker Deployment:**
- Official image: `flowiseai/flowise`
- Simple: `docker pull flowiseai/flowise`
- Docker Compose examples included
- **Easy Aspire integration**

**MCP Support:**
```json
{
  "command": "npx",
  "args": ["-y", "mcp-proxy", "http://host.docker.internal:5002/sse"],
  "headers": {
    "Authorization": "Bearer {{ $vars.auth_token }}"
  }
}
```

**Agent Loops:**
- AgentFlow v2 supports loops
- Iteration node for array processing
- Condition Agent node for dynamic routing

**Dynamic Authentication:**
- ✅ Variables via `$vars`
- ✅ Flow context via `$flow`
- ✅ Override config via API
- ✅ Session management
- **Can pass Auth0 token through flow**

**Custom Tools:**
- JavaScript/TypeScript custom functions
- Access to `$flow.sessionId`, `$vars`, inputs
- Can call external APIs with dynamic auth

### ⚠️ Limitations

- JavaScript-only for custom tools (not Python)
- Less Python-friendly than LangFlow
- Some features require paid tier (enterprise features)

### 📋 Implementation Plan for Your Use Case

```csharp
// Flowise + .NET Aspire Setup

// Add to Program.cs:
var flowise = builder.AddContainer("flowise", "flowiseai/flowise")
    .WithHttpEndpoint(port: 3000, targetPort: 3000)
    .WithEnvironment("FLOWISE_USERNAME", "admin")
    .WithEnvironment("FLOWISE_PASSWORD", builder.AddParameter("flowise-password"))
    .WithEnvironment("AUTH0_DOMAIN", auth0Domain)
    .WithEnvironment("AUTH0_CLIENT_ID", auth0ClientId)
    .WithEnvironment("AUTH0_CLIENT_SECRET", auth0ClientSecret)
    .WithEnvironment("AUTH0_AUDIENCE", auth0Audience)
    .WithBindMount(Path.Combine(projectRoot, ".flowise"), "/root/.flowise")
    .WithReference(roasterControl)
    .WithReference(firstCrackDetection);
```

**Flow Structure:**
1. **HTTP Node**: Fetch Auth0 token
2. **Custom Function node**: Store in `$flow.state.auth_token`
3. **MCP Custom Tool nodes**: 
   - Roaster Control MCP
   - First Crack Detection MCP
   - Use `{{ $flow.state.auth_token }}` in Authorization header
4. **Agent node**: Roasting orchestration
5. **Loop/Condition nodes**: Handle retries and state

**Pros for your use case:**
- ✅ More polished UI than LangFlow
- ✅ Better documentation and examples
- ✅ Easier for team members to learn
- ✅ Good MCP support
- ✅ Native loop mechanisms

**Cons:**
- ❌ JavaScript-only (doesn't match Python stack)
- Custom tools require node-fetch/JS knowledge
- Less "native" feeling with Python MCP servers

---

## 3. Detailed Feature Comparison

### MCP Integration

| Feature | LangFlow | Flowise | n8n |
|---------|----------|---------|-----|
| **SSE Transport** | ✅ Native | ✅ Native | ✅ Native |
| **Stdio Transport** | ✅ Yes | ✅ Yes | ❌ No |
| **Auth Headers** | ✅ Dynamic | ✅ Dynamic | ❌ Static |
| **Environment Variables** | ✅ Pass-through | ✅ Pass-through | ⚠️ Limited |
| **Multiple Servers** | ✅ Easy | ✅ Easy | ⚠️ Manual |

### Authentication & Token Management

| Feature | LangFlow | Flowise | n8n |
|---------|----------|---------|-----|
| **Fetch OAuth Token** | ✅ HTTP Request | ✅ HTTP Node | ✅ HTTP Request |
| **Store Token** | ✅ `$vars` | ✅ `$flow.state` | ⚠️ Set node only |
| **Pass to Tools** | ✅ `{{ $vars.X }}` | ✅ `{{ $flow.state.X }}` | ❌ Can't access |
| **Refresh Logic** | ✅ Custom nodes | ✅ Custom function | ⚠️ Manual |
| **Session Scope** | ✅ Yes | ✅ Yes | ❌ No |

### Agent Capabilities

| Feature | LangFlow | Flowise | n8n |
|---------|----------|---------|-----|
| **Loop Mechanism** | ✅ Loop node | ✅ Iteration node | ⚠️ Manual |
| **Max Iterations** | ✅ Configurable | ✅ Configurable | ❌ No limit |
| **Conditional Routing** | ✅ Built-in | ✅ Condition Agent | ⚠️ If node |
| **State Management** | ✅ `$flow.state` | ✅ `$flow.state` | ⚠️ Loop only |
| **Tool Selection** | ✅ LLM-driven | ✅ LLM-driven | ✅ LLM-driven |

### Developer Experience

| Feature | LangFlow | Flowise | n8n |
|---------|----------|---------|-----|
| **Language** | Python | TypeScript/JS | TypeScript |
| **Custom Components** | ✅ Python classes | ✅ JS functions | ⚠️ Limited |
| **Debugging** | ✅ Good | ✅ Excellent | ⚠️ Basic |
| **Version Control** | ✅ JSON export | ✅ JSON export | ✅ JSON export |
| **API Access** | ✅ REST API | ✅ REST API | ✅ REST API |

---

## 4. Recommendation for Coffee Roasting Use Case

### 🥇 Winner: **LangFlow**

**Why:**
1. ✅ **Native Python** - matches your MCP server stack
2. ✅ **Better variable system** - Auth0 tokens work seamlessly  
3. ✅ **First-class MCP support** - designed for it
4. ✅ **Built-in loops** - agent iteration is native
5. ✅ **Free & open source** - deploy anywhere
6. ✅ **Docker-native** - perfect for Aspire

**Your workflow would be:**
```
[Get Auth0 Token] → [Store in $vars] → [MCP Tools with dynamic auth] → [Agent Loop] → [Monitor roast]
```

### 🥈 Runner-up: **Flowise**

**Choose Flowise if:**
- Your team prefers TypeScript/JavaScript
- You want the most polished UI
- You don't need Python integration

### 🥉 n8n

**n8n is best for:**
- Simple automation (not agents)
- Non-technical users
- When you don't need dynamic auth

---

## 5. Next Steps

### Option A: Try LangFlow (Recommended)
```bash
# Quick start
docker run -p 7860:7860 langflowai/langflow:latest

# Or with Aspire (see implementation plan above)
```

### Option B: Try Flowise
```bash
# Quick start
docker run -p 3000:3000 flowiseai/flowise

# Or with Aspire (see implementation plan above)
```

### Option C: Stick with n8n
- Accept manual token updates
- Keep current workflow
- Simple but limited

---

## Summary Table

| Criteria | LangFlow | Flowise | n8n |
|----------|----------|---------|-----|
| **Docker** | ✅ | ✅ | ✅ |
| **Free** | ✅ | ✅ | ✅ |
| **MCP with Auth** | ✅ | ✅ | ❌ |
| **Agent Loops** | ✅ | ✅ | ⚠️ |
| **Python Stack** | ✅ | ❌ | ❌ |
| **Easy Setup** | ⚠️ | ✅ | ✅ |
| **Best For You** | **⭐⭐⭐** | **⭐⭐** | **⭐** |

**Final Verdict**: **Go with LangFlow** - it solves all the Auth0 token issues we hit with n8n and fits your Python stack perfectly.
