# LangFlow Import Guide

## Quick Import Steps

### 1. Start LangFlow

```bash
# From coffee-roasting root
cd src/orchestration/aspire
dotnet run
```

Then open: **http://localhost:7860**

Login with:
- Username: `admin`
- Password: (the one you set in user secrets)

---

### 2. Import the Flow

1. Click **"New Project"** or **"+"** button
2. Click **"Import"** from the menu
3. Select the file: `docs/agent-platforms/langflow/workflows/coffee-roasting-agent.json`
4. Click **"Import"**

---

### 3. Configure the Flow

#### Set OpenAI API Key

1. Click on the **"OpenAI"** node (blue node on the left)
2. Find the **"OpenAI API Key"** field
3. Enter your OpenAI API key
4. Click **"Save"**

Alternative: Set environment variable in Aspire:

```csharp
.WithEnvironment("OPENAI_API_KEY", builder.Configuration["OpenAI:ApiKey"])
```

#### Set MCP Server URL

The tools are pre-configured to use `http://localhost:3001` by default.

To change this:
1. Click on each **Tool** node (green nodes)
2. Edit the `mcp_url` in the Python function
3. Or set environment variable: `MCP_SERVER_URL=http://your-mcp-server:3001`

---

### 4. Test the Flow

#### Start Your MCP Server First

```bash
# Terminal 1: Start MCP server
cd src/mcp
node dist/index.js
```

#### Run the Flow

1. Click the **"Play"** button (▶️) in LangFlow
2. Type in the chat: `"Start monitoring for first crack using a USB microphone"`
3. The agent will:
   - Call `start_first_crack_detection` tool
   - Monitor status periodically
   - Alert you when first crack is detected

---

## What's Included in the Template

### Nodes

1. **Chat Input** - Receives user messages
2. **MCP Tools** (3 custom tools):
   - `start_first_crack_detection` - Begin monitoring
   - `get_first_crack_status` - Check current status
   - `stop_first_crack_detection` - Stop and get summary
3. **Agent** - ReAct agent with tool-calling capability
4. **OpenAI LLM** - GPT-4 Turbo for reasoning
5. **Chat Output** - Displays responses

### Pre-configured Features

✅ **System prompt** tailored for coffee roasting assistance  
✅ **Tool descriptions** optimized for agent understanding  
✅ **MCP integration** via HTTP calls  
✅ **Error handling** in all tool functions  
✅ **Configurable parameters** (threshold, min_pops, etc.)

---

## Customization Options

### Change LLM Provider

Replace the **OpenAI** node with:
- **Anthropic** (Claude)
- **Ollama** (local models)
- **Azure OpenAI**
- **Google Vertex AI**

### Add More Tools

1. Click **"+ Add Node"**
2. Select **"Tool"**
3. Add your custom Python function
4. Connect to the **Agent** node's "tools" input

### Modify System Prompt

Click the **Agent** node and edit the `system_message` field to:
- Add roasting profiles
- Include temperature guidance
- Add safety warnings
- Customize personality

### Add Memory

1. Add a **"Memory"** node (e.g., `ConversationBufferMemory`)
2. Connect to the **Agent** node
3. Now the agent remembers conversation context

---

## Environment Variables

Set these in your Aspire `Program.cs`:

```csharp
var langflow = builder.AddContainer("langflow", "langflowai/langflow")
    .WithHttpEndpoint(port: 7860, targetPort: 7860)
    .WithEnvironment("OPENAI_API_KEY", builder.Configuration["OpenAI:ApiKey"])
    .WithEnvironment("MCP_SERVER_URL", "http://mcp-server:3001")
    .WithEnvironment("LANGFLOW_AUTO_LOGIN", "true")
    .WithEnvironment("LANGFLOW_SUPERUSER", "admin")
    .WithEnvironment("LANGFLOW_SUPERUSER_PASSWORD", langflowPassword.Resource.Value);
```

---

## Troubleshooting

### Import fails with "Invalid JSON"

- Verify the JSON file isn't corrupted
- Try creating a new project and importing again

### Tools not working

1. Check MCP server is running: `curl http://localhost:3001/health`
2. Verify `MCP_SERVER_URL` environment variable
3. Check LangFlow logs in Aspire dashboard

### Agent doesn't call tools

- Ensure LLM supports function calling (GPT-4, GPT-3.5-turbo)
- Check tool descriptions are clear
- Verify tools are connected to Agent node

### Authentication errors

- Verify OpenAI API key is set correctly
- Check API key has sufficient credits
- Try a different model if rate limited

---

## Next Steps

1. ✅ Import the template
2. ✅ Configure API keys
3. ✅ Test basic functionality
4. 🔧 Customize system prompt for your needs
5. 🔧 Add additional roasting tools
6. 🔧 Connect to your roaster hardware
7. 🚀 Deploy to production

---

## Advanced: Custom MCP Tool Template

If you want to add more MCP tools, use this template:

```python
import requests
import json
import os

def your_tool_name(param1: str, param2: int = 10) -> str:
    """Your tool description here.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        JSON string with results
    """
    mcp_url = os.getenv('MCP_SERVER_URL', 'http://localhost:3001')
    
    payload = {
        "param1": param1,
        "param2": param2
    }
    
    try:
        response = requests.post(
            f"{mcp_url}/tools/your_mcp_endpoint",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})
```

---

## Resources

- [LangFlow Documentation](https://docs.langflow.org/)
- [LangChain Agent Documentation](https://python.langchain.com/docs/modules/agents/)
- [Coffee Roasting Agent Setup](./SETUP.md)
- [MCP Server Documentation](../../../mcp/README.md)
