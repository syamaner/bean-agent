# Agent Platforms for Coffee Roasting

## Overview

This directory contains setup guides, workflows, and documentation for three different agent orchestration platforms, all configured to work with the autonomous coffee roasting system.

## Quick Start

All three platforms are pre-configured in `.NET Aspire` and ready to use. Choose the one that fits your needs:

| Platform | Port | Best For | Status |
|----------|------|----------|--------|
| **LangFlow** | 7860 | Python devs, MCP-first | ⭐ **Recommended** |
| **Flowise** | 3000 | TypeScript devs, polished UI | ✅ Alternative |
| **n8n** | 5678 | Simple automation, manual auth | ⚠️ Limited |

## Platform Comparison

### 1. LangFlow (Recommended) ⭐

**Why Choose LangFlow:**
- ✅ **Native Python** - matches your MCP server stack
- ✅ **Dynamic Auth** - Auth0 tokens work seamlessly via `$vars`
- ✅ **Built-in agent loops** - no manual loop construction needed
- ✅ **First-class MCP support** - designed for Model Context Protocol
- ✅ **Free & open source** - deploy anywhere

**Best For:**
- Python developers
- MCP-first workflows
- Full control over authentication
- Agent-based workflows

**Directory:** `langflow/`

**Quick Start:**
```bash
cd src/orchestration/aspire
dotnet user-secrets set "Parameters:langflow-password" "your-password"
dotnet run
# Open http://localhost:7860
```

[→ Full LangFlow Setup Guide](langflow/docs/SETUP.md)

---

### 2. Flowise (Alternative) ✅

**Why Choose Flowise:**
- ✅ **Polished UI** - most user-friendly interface
- ✅ **Dynamic Auth** - tokens work via `$flow.state`
- ✅ **Good MCP support** - works well with MCP servers
- ✅ **Better documentation** - more examples available
- ⚠️ **JavaScript only** - doesn't match Python stack

**Best For:**
- TypeScript/JavaScript developers
- Teams wanting easy onboarding
- When UI polish matters more than language match

**Directory:** `flowise/`

**Quick Start:**
```bash
cd src/orchestration/aspire
dotnet user-secrets set "Parameters:flowise-password" "your-password"
dotnet run
# Open http://localhost:3000
```

[→ Full Flowise Setup Guide](flowise/docs/SETUP.md)

---

### 3. n8n (Limited) ⚠️

**Why Choose n8n:**
- ✅ **Simple** - easy for non-developers
- ✅ **Mature** - lots of integrations
- ❌ **Static auth** - can't dynamically pass tokens to MCP tools
- ⚠️ **Manual loops** - requires custom loop construction

**Best For:**
- Simple automation tasks
- When you're okay with manual token updates
- Non-agent workflows

**Directory:** `n8n/`

**Quick Start:**
```bash
cd src/orchestration/aspire
dotnet user-secrets set "Parameters:n8n-api-key" "your-api-key"
dotnet run
# Open http://localhost:5678
```

[→ Full n8n Setup Guide](n8n/docs/SETUP.md)

---

## Detailed Comparison

### Feature Matrix

| Feature | LangFlow | Flowise | n8n |
|---------|----------|---------|-----|
| **Free & Open Source** | ✅ | ✅ | ✅ |
| **Docker Support** | ✅ | ✅ | ✅ |
| **MCP Integration** | ✅ Native | ✅ Good | ⚠️ Limited |
| **Dynamic Auth (OAuth)** | ✅ `$vars` | ✅ `$flow.state` | ❌ Static only |
| **Agent Loops** | ✅ Built-in | ✅ Built-in | ⚠️ Manual |
| **Custom Tools** | ✅ Python | ✅ JavaScript | ⚠️ Limited |
| **Language** | Python | TypeScript | TypeScript |
| **Learning Curve** | Medium | Easy | Easy |
| **UI Polish** | Good | Excellent | Good |
| **Debugging** | Good | Excellent | Basic |

### Authentication Handling

**The Key Difference:**

All three can fetch Auth0 tokens, but only **LangFlow** and **Flowise** can pass them dynamically to MCP tools.

#### LangFlow ✅
```
[HTTP: Get Token] 
  → [Set $vars.auth_token] 
  → [MCP Tools use {$vars.auth_token}] 
  → Works!
```

#### Flowise ✅
```
[HTTP: Get Token] 
  → [Store in $flow.state.auth_token] 
  → [MCP Tools use {{$flow.state.auth_token}}] 
  → Works!
```

#### n8n ❌
```
[HTTP: Get Token] 
  → [Store in Set node] 
  → [MCP Tools CAN'T access it] 
  → Manual token update required
```

---

## Setup Instructions

### Prerequisites

All platforms require:
1. ✅ `.NET Aspire` configured (`Program.cs` already updated)
2. ✅ MCP servers running (Roaster Control + First Crack Detection)
3. ✅ Auth0 credentials in user secrets
4. ✅ OpenAI API key (for GPT-4o)

### Aspire Configuration

All three platforms are already configured in `/src/orchestration/aspire/Program.cs`:

```csharp
// LangFlow (port 7860)
var langflow = builder.AddContainer("langflow", "langflowai/langflow", "latest")
    .WithHttpEndpoint(port: 7860, targetPort: 7860)
    .WithEnvironment("AUTH0_DOMAIN", auth0Domain)
    // ... (full config in Program.cs)

// Flowise (port 3000)  
var flowise = builder.AddContainer("flowise", "flowiseai/flowise", "latest")
    .WithHttpEndpoint(port: 3000, targetPort: 3000)
    .WithEnvironment("AUTH0_DOMAIN", auth0Domain)
    // ... (full config in Program.cs)

// n8n (port 5678)
var n8n = builder.AddContainer("n8n", "n8nio/n8n", "latest")
    .WithHttpEndpoint(port: 5678, targetPort: 5678)
    .WithEnvironment("N8N_API_KEY", n8nApiKey)
    // ... (full config in Program.cs)
```

### Set Passwords/Keys

```bash
cd src/orchestration/aspire

# LangFlow
dotnet user-secrets set "Parameters:langflow-password" "your-secure-password"

# Flowise
dotnet user-secrets set "Parameters:flowise-password" "your-secure-password"

# n8n
dotnet user-secrets set "Parameters:n8n-api-key" "$(openssl rand -base64 32)"
```

### Start Everything

```bash
cd src/orchestration/aspire
dotnet run
```

**Aspire Dashboard:** http://localhost:15000

**Access platforms:**
- LangFlow: http://localhost:7860
- Flowise: http://localhost:3000
- n8n: http://localhost:5678

---

## Directory Structure

```
docs/agent-platforms/
├── README.md                          # This file
├── langflow/                          # LangFlow (Recommended)
│   ├── docs/
│   │   ├── SETUP.md                  # Step-by-step setup
│   │   ├── WORKFLOW.md               # Flow design details
│   │   └── TROUBLESHOOTING.md        # Common issues
│   ├── workflows/
│   │   └── autonomous-roast.json     # Importable flow (create after setup)
│   └── config/
│       └── mcp-config.json           # MCP server configurations
├── flowise/                          # Flowise (Alternative)
│   ├── docs/
│   │   ├── SETUP.md
│   │   ├── WORKFLOW.md
│   │   └── TROUBLESHOOTING.md
│   ├── workflows/
│   │   └── autonomous-roast.json
│   └── config/
│       └── mcp-config.json
└── n8n/                              # n8n (Limited)
    ├── docs/
    │   ├── SETUP.md
    │   └── TROUBLESHOOTING.md
    ├── workflows/
    │   └── Autonomous Coffee Roast.json  # Already created
    └── config/
        └── bearer-auth-credential.json

```

---

## Workflow Overview

All three platforms implement the same autonomous roasting logic:

### Core Flow

```
1. Get Auth0 Token
   ↓
2. Store Token (in $vars, $flow.state, or Set node)
   ↓
3. Configure MCP Tools with Token
   - Roaster Control MCP
   - First Crack Detection MCP
   ↓
4. Agent Loop (every 10 seconds, max 30 min)
   - Call get_roast_status
   - Start roaster if needed
   - Start first crack detection (~8-10 min)
   - Adjust heat/fan after first crack
   - Drop beans when ready (dev time 15-20%, temp 192-195°C)
   ↓
5. Complete
```

### Key Difference

- **LangFlow/Flowise**: Steps 2-3 work automatically with dynamic tokens
- **n8n**: Step 2-3 requires manual token update in credentials

---

## Recommendations by Use Case

### For Production Use
→ **LangFlow** - Most robust, matches your stack

### For Team Collaboration
→ **Flowise** - Easiest UI for onboarding

### For Simple Automation
→ **n8n** - If you don't need dynamic auth

### For Learning/Experimentation
→ **Try all three!** They're all running simultaneously

---

## Next Steps

1. **Choose a platform** (LangFlow recommended)
2. **Follow the setup guide** in that platform's `/docs/SETUP.md`
3. **Import or create the workflow**
4. **Test with a roast!**

## Support

- LangFlow issues: Check `langflow/docs/TROUBLESHOOTING.md`
- Flowise issues: Check `flowise/docs/TROUBLESHOOTING.md`
- n8n issues: Check `n8n/docs/TROUBLESHOOTING.md`
- Aspire issues: Check main project `/docs/DEVELOPMENT.md`

## Contributing

Found a better way? Improvements welcome:
1. Test your workflow
2. Export to `/workflows/`
3. Update relevant `/docs/`
4. Submit PR

---

**Built with ❤️ for the Coffee Roasting project**
