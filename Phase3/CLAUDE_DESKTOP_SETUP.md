# Claude Desktop Setup for Coffee Roasting MCP Servers

## Prerequisites

1. Install [Claude Desktop](https://claude.ai/download)
2. Ensure Aspire is running with both MCP servers healthy
3. Get an Auth0 token (expires in 24 hours)

## Step 1: Get Auth0 Token

Run this command to get a token:

```bash
curl -s -X POST https://genai-7175210165555426.uk.auth0.com/oauth/token \
  -H 'Content-Type: application/json' \
  -d '{
    "client_id": "Jk3aF2NfkiiOIXY0eHJQxfA6jkP0Pjf7",
    "client_secret": "05agLnSUZceYK2Yl9bYGGnV_zuy7EAJ9ZWnMuOpCHEIOx2v8xZ7XNAmsQW020m2k",
    "audience": "https://coffee-roasting-api",
    "grant_type": "client_credentials"
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])"
```

Copy the token output.

## Step 2: Configure Claude Desktop

### Location of Config File

```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Configuration

Edit the config file and add your MCP servers:

```json
{
  "mcpServers": {
    "roaster-control": {
      "command": "node",
      "args": [
        "-e",
        "const http = require('http'); const req = http.get('http://localhost:5002/sse', {headers: {'Authorization': 'Bearer YOUR_TOKEN_HERE', 'Accept': 'text/event-stream'}}, res => { res.pipe(process.stdout); }); req.on('error', e => console.error(e));"
      ]
    },
    "first-crack-detection": {
      "command": "node",
      "args": [
        "-e",
        "const http = require('http'); const req = http.get('http://localhost:5001/sse', {headers: {'Authorization': 'Bearer YOUR_TOKEN_HERE', 'Accept': 'text/event-stream'}}, res => { res.pipe(process.stdout); }); req.on('error', e => console.error(e));"
      ]
    }
  }
}
```

**Important:** Replace `YOUR_TOKEN_HERE` with your Auth0 token from Step 1.

## Step 3: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Relaunch Claude Desktop
3. Look for the 🔨 hammer icon in the chat - this shows MCP tools are loaded

## Step 4: Test the Integration

Try these prompts in Claude:

### Check Status
```
What's the current status of the coffee roaster?
```

### Start a Roast
```
Start the roaster drum and set heat to 80% and fan to 60%
```

### Get AI Guidance
```
I'm roasting Ethiopian Yirgacheffe. Based on the current roaster status, 
what heat and fan settings would you recommend?
```

### Monitor for First Crack
```
Check if first crack detection is running. If not, can you describe how 
we would start it when we're ready?
```

## Troubleshooting

### Token Expired
Tokens expire after 24 hours. If you get authentication errors:
1. Get a new token (Step 1)
2. Update the config file
3. Restart Claude Desktop

### Servers Not Available
If Claude can't find the tools:
1. Verify Aspire is running: Check Aspire dashboard at http://localhost:15055
2. Test health endpoints:
   ```bash
   curl http://localhost:5002/health
   curl http://localhost:5001/health
   ```
3. Check logs in Aspire dashboard

### Alternative: Python Wrapper

If the Node.js approach doesn't work, you can create Python wrapper scripts:

**roaster_control_wrapper.py:**
```python
#!/usr/bin/env python3
import sys
import httpx

async def main():
    headers = {
        "Authorization": "Bearer YOUR_TOKEN_HERE",
        "Accept": "text/event-stream"
    }
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", "http://localhost:5002/sse", headers=headers) as response:
            async for line in response.aiter_lines():
                print(line, flush=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

Then configure Claude with:
```json
{
  "mcpServers": {
    "roaster-control": {
      "command": "python3",
      "args": ["/path/to/roaster_control_wrapper.py"]
    }
  }
}
```

## What You Can Do

Once configured, Claude can:
- ✅ Read roaster status (temperature, heat, fan, timing)
- ✅ Start/stop the roaster drum
- ✅ Adjust heat levels (0-100%)
- ✅ Adjust fan speed (0-100%)
- ✅ Drop beans and start cooling
- ✅ Monitor first crack detection
- ✅ Provide expert roasting guidance based on real-time data

## Security Notes

⚠️ The Auth0 token in the config file provides full access to roaster control
⚠️ Keep your config file secure
⚠️ Tokens expire after 24 hours (good security practice)
⚠️ For production, implement automatic token refresh

## Next Steps

- Build automated roast profiles
- Create first crack response workflows
- Log all roasts with AI analysis
- Compare roast outcomes and optimize
