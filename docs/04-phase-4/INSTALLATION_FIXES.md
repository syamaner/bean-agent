# Agent Framework Installation & Fixes

## What Was Fixed

The Microsoft Agent Framework is in early development and not yet published to PyPI. We successfully installed it from GitHub and fixed all import issues.

## Installation Steps Completed

### 1. Installed git-lfs (Required)
```bash
brew install git-lfs
git lfs install
```

### 2. Installed Agent Framework from GitHub
```bash
pip install git+https://github.com/microsoft/agent-framework.git#subdirectory=python/packages/core
pip install git+https://github.com/microsoft/agent-framework.git#subdirectory=python/packages/devui
```

### 3. Fixed Import Statements

**Correct imports:**
```python
from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
from agent_framework_devui import serve
```

**NOT** (these don't exist):
```python
from agent_framework_core import ...  # ❌ Wrong
from agent_framework.devui import ... # ❌ Wrong
```

### 4. Fixed Agent Creation

**Correct API:**
```python
# Create chat client
chat_client = OpenAIChatClient(
    api_key=config.openai_api_key,
    model_id=config.openai_model,  # Note: model_id not model
)

# Create agent
agent = ChatAgent(
    chat_client=chat_client,
    name="CoffeeRoastingAgent",
    instructions=ROASTING_INSTRUCTIONS,
    tools=tools,
)

# Run agent
response = await agent.run("Check status")
print(response.text)  # Note: .text property
```

## Files Updated

1. **agents/roaster/agent.py** - Fixed imports and API calls
2. **agents/roaster/devui_server.py** - Fixed DevUI import
3. **agents/roaster/examples/devui_example.py** - Fixed DevUI import
4. **requirements.txt** - Updated to GitHub sources
5. **src/orchestration/aspire/Program.cs** - DevUI service already configured

## Testing

### Verify Installation
```bash
cd ~/git/coffee-roasting
source venv/bin/activate

# Test imports
python -c "from agent_framework import ChatAgent; print('✅ Core works')"
python -c "from agent_framework.openai import OpenAIChatClient; print('✅ OpenAI client works')"
python -c "from agent_framework_devui import serve; print('✅ DevUI works')"
python -c "from agents.roaster import create_roasting_agent; print('✅ Agent module works')"
```

All should print ✅ messages.

### Run Aspire
```bash
cd src/orchestration/aspire
dotnet run
```

Services should start:
- roaster-control (5002)
- first-crack-detection (5001)
- **devui (8080)** ← Should now work!
- n8n (5678)

Access DevUI at: http://localhost:8080

## Common Issues

### Issue: "ModuleNotFoundError: No module named 'agent_framework'"
**Fix:** Run the installation commands above

### Issue: "git-lfs: command not found"
**Fix:** 
```bash
brew install git-lfs
git lfs install
```

### Issue: "No module named 'agent_framework_core'"
**Fix:** Use `agent_framework` not `agent_framework_core`

### Issue: OpenAIChatClient requires 'model_id' not 'model'
**Fix:** Already fixed in our code - use `model_id` parameter

## Current Status

✅ **All packages installed**
✅ **All imports fixed**  
✅ **Aspire configuration updated**  
✅ **Ready for testing**

## Next Steps

1. Start Aspire: `cd src/orchestration/aspire && dotnet run`
2. Open DevUI: http://localhost:8080
3. Select "CoffeeRoastingAgent"
4. Test with: "Check the roaster status"

## References

- [Agent Framework GitHub](https://github.com/microsoft/agent-framework)
- [Agent Framework Python Docs](https://learn.microsoft.com/en-us/agent-framework/)
- [Testing Guide](./TESTING_GUIDE.md)
