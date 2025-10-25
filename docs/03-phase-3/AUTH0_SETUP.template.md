# Auth0 Setup - Template

**Date**: October 25, 2025  
**Status**: ✅ Partially Complete (Manual step required)

⚠️ **NOTE**: Copy this file to `AUTH0_SETUP.md` and fill in your credentials. The actual file is gitignored.

---

## Created Resources

### 1. Coffee Roasting API ✅

**Identifier**: `https://coffee-roasting-api`  
**ID**: `68fd4d50baba56916a9190b0`  
**Signing Algorithm**: RS256  
**Token Lifetime**: 86400 seconds (24 hours)

**Scopes**:
- `read:roaster` - Read roaster status and sensor data
- `write:roaster` - Control roaster (heat, fan, drum, drop)
- `read:detection` - Read first crack detection status
- `write:detection` - Start/stop first crack detection

### 2. n8n Roasting Agent (M2M Application) ✅

**Type**: Machine-to-Machine  
**Client ID**: `<YOUR_CLIENT_ID>`  
**Client Secret**: `<YOUR_CLIENT_SECRET>`

⚠️ **IMPORTANT**: Never commit these credentials to git!

---

## Manual Step Required ⚪

The n8n application needs to be authorized to call the Coffee Roasting API:

1. Go to [Auth0 Dashboard](https://manage.auth0.com/)
2. Navigate to **Applications** → **Applications**
3. Click **n8n Roasting Agent**
4. Go to the **APIs** tab
5. Find **Coffee Roasting API** and click **Authorize**
6. Select all 4 scopes:
   - ✅ `read:roaster`
   - ✅ `write:roaster`
   - ✅ `read:detection`
   - ✅ `write:detection`
7. Click **Update**

---

## Environment Variables

For MCP servers:

```bash
# .env
AUTH0_DOMAIN=genai-7175210165555426.uk.auth0.com
AUTH0_AUDIENCE=https://coffee-roasting-api
```

For n8n (credentials store):

```json
{
  "name": "Auth0 Coffee Roasting",
  "type": "httpHeaderAuth",
  "data": {
    "clientId": "<YOUR_CLIENT_ID>",
    "clientSecret": "<YOUR_CLIENT_SECRET>",
    "audience": "https://coffee-roasting-api",
    "tokenUrl": "https://genai-7175210165555426.uk.auth0.com/oauth/token"
  }
}
```

---

## Test Token Acquisition

```bash
curl -X POST https://genai-7175210165555426.uk.auth0.com/oauth/token \
  -H 'Content-Type: application/json' \
  -d '{
    "client_id": "<YOUR_CLIENT_ID>",
    "client_secret": "<YOUR_CLIENT_SECRET>",
    "audience": "https://coffee-roasting-api",
    "grant_type": "client_credentials"
  }'
```

Expected response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "scope": "read:roaster write:roaster read:detection write:detection"
}
```

---

## Next Steps

1. ⚪ Complete manual authorization step (see above)
2. ⚪ Add HTTP endpoints to MCP servers
3. ⚪ Implement JWT validation in both MCP servers
4. ⚪ Test authentication with curl
5. ⚪ Configure n8n with credentials
6. ⚪ Test end-to-end workflow

---

## Verification

Decode the access token at [jwt.io](https://jwt.io) and verify:
- `iss`: `https://genai-7175210165555426.uk.auth0.com/`
- `aud`: `https://coffee-roasting-api`
- `scope`: Contains all 4 scopes
- `exp`: Future timestamp

---

**Setup Status**: 2/3 complete (Manual step pending)
