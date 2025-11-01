# n8n Workflow Setup - Dynamic Bearer Auth

This workflow automatically fetches an Auth0 token and updates the Bearer Auth credential used by MCP tools.

## Prerequisites

### 1. Set n8n API Key in .NET Aspire User Secrets

**Generated API Key:** `U1B5ut26pz4Do+dqy7lXGmp255G/Kk71IfzvekUatqI=`

Add this to your user secrets:
```bash
cd src/orchestration/aspire
dotnet user-secrets set "Parameters:n8n-api-key" "U1B5ut26pz4Do+dqy7lXGmp255G/Kk71IfzvekUatqI="
```

Restart Aspire after setting this.

### 2. Create HTTP Header Auth Credential
1. In n8n, go to **Credentials** → **Add New** → **HTTP Header Auth**
2. Configure:
   - **Name**: `n8n API Key`
   - **Header Name**: `X-N8N-API-KEY`
   - **Header Value**: `your-secret-api-key-here` (same as above)
3. Save

### 3. Bearer Auth Credential (already exists)
The credential `Bearer Auth account` (ID: `yQFT5yL0T4LlCk8s`) should already exist in your n8n instance.

The workflow will automatically update this credential's token on each run.

## How It Works

**Workflow Flow:**
1. **Start Roast** → triggers workflow
2. **Get Auth0 Token** → fetches fresh JWT from Auth0
3. **Update Bearer Auth Credential** → calls n8n API to update the Bearer Auth credential with the new token
4. **Initialize State** → continues with workflow
5. **MCP tools** (Roaster Control MCP, First Crack Detection MCP) → use the updated Bearer Auth credential automatically

## Import Workflow

Simply import `Autonomous Coffee Roast.json` into n8n. The workflow is pre-configured to:
- Update credential ID `yQFT5yL0T4LlCk8s`
- Use the n8n API on `http://localhost:5678`

**Note:** If your n8n is running on a different port or host, update the URL in the "Update Bearer Auth Credential" node.

## Verify Setup

1. Import the workflow
2. Open the "Update Bearer Auth Credential" node
3. Make sure the "n8n API Key" credential is selected
4. Test the workflow by executing it manually
5. Check that the Bearer Auth credential in n8n Credentials shows a fresh token

## Troubleshooting

**401 Unauthorized on credential update:**
- Verify `N8N_API_KEY` environment variable is set
- Ensure the HTTP Header Auth credential has the correct API key

**Credential not found:**
- Verify the Bearer Auth credential ID (`yQFT5yL0T4LlCk8s`) matches your actual credential
- Check in n8n → Credentials → Bearer Auth account → Settings → ID

**MCP tools still failing:**
- Ensure the credential was actually updated (check the timestamp in n8n Credentials)
- Verify both MCP servers are running and accessible
