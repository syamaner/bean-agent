# Auth0 User-Based Authentication Setup

Complete guide for setting up Auth0 with **user-based authentication** and role-based access control (RBAC) for the coffee roasting system.

**Updated**: October 25, 2025  
**Auth Type**: User Authentication (NOT Machine-to-Machine)

---

## Overview

Instead of M2M authentication, we use **user authentication** where:
- Users log in via Auth0 Universal Login
- Each user is assigned roles (Observer, Operator, Admin)
- n8n workflows use the logged-in user's JWT token
- MCP servers validate user tokens and check roles
- Actions are auditable (know which user did what)

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    User Browser                           │
│  1. User clicks "Login" in n8n                           │
│  2. Redirected to Auth0 Universal Login                  │
│  3. User authenticates (email/password, Google, etc.)    │
│  4. Auth0 returns to n8n with authorization code         │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│                    n8n Workflow                           │
│  5. Exchanges code for access token (OAuth2)             │
│  6. Stores user's access token                           │
│  7. Uses token to call MCP servers                       │
└────────────────────┬─────────────────────────────────────┘
                     │ User JWT Token
                     │ (includes user_id, roles, scopes)
                     ▼
┌──────────────────────────────────────────────────────────┐
│            MCP HTTP+SSE Servers                           │
│  8. Validate JWT signature                               │
│  9. Check user has required role/scope                   │
│  10. Execute action if authorized                        │
│  11. Log action with user_id for audit                   │
└──────────────────────────────────────────────────────────┘
```

---

## Auth0 Configuration

### Step 1: Create Auth0 API

1. Go to **Applications > APIs** in Auth0 Dashboard
2. Click **Create API**

```
Name: Coffee Roasting API
Identifier: https://coffee-roasting-api
Signing Algorithm: RS256
Allow Offline Access: Yes (for refresh tokens)
Token Expiration: 86400 seconds (24 hours)
```

### Step 2: Define API Scopes

In the API Permissions tab, add these scopes:

#### Read Scopes
```
read:detection      Read first crack detection status
read:roaster        Read roaster sensors and status
```

#### Write Scopes
```
write:detection     Start/stop first crack detection
write:roaster       Control roaster (heat, fan, drop beans)
```

#### Admin Scopes
```
admin:detection     Configure detection models and settings
admin:roaster       Configure roaster settings and profiles
```

### Step 3: Create Roles

Go to **User Management > Roles**, create these roles:

#### 1. Roast Observer (Read-Only)

```json
{
  "name": "Roast Observer",
  "description": "Read-only access to view roasting status and metrics",
  "permissions": [
    {
      "api": "https://coffee-roasting-api",
      "scopes": ["read:detection", "read:roaster"]
    }
  ]
}
```

**Use case**: Quality control team, students, observers

#### 2. Roast Operator (Control Access)

```json
{
  "name": "Roast Operator",
  "description": "Can control roaster and view all data",
  "permissions": [
    {
      "api": "https://coffee-roasting-api",
      "scopes": [
        "read:detection",
        "read:roaster",
        "write:detection",
        "write:roaster"
      ]
    }
  ]
}
```

**Use case**: Roast operators, production staff

#### 3. Roast Admin (Full Access)

```json
{
  "name": "Roast Admin",
  "description": "Full administrative access to all features",
  "permissions": [
    {
      "api": "https://coffee-roasting-api",
      "scopes": [
        "read:detection",
        "read:roaster",
        "write:detection",
        "write:roaster",
        "admin:detection",
        "admin:roaster"
      ]
    }
  ]
}
```

**Use case**: Head roasters, system administrators

### Step 4: Create Regular Web Application

1. Go to **Applications > Applications**
2. Click **Create Application**

```
Name: n8n Coffee Roasting
Type: Regular Web Application
```

3. Configure Application Settings:

```
Application URIs:
  Allowed Callback URLs: 
    - http://localhost:5678/rest/oauth2-credential/callback
    - https://your-n8n-instance.com/rest/oauth2-credential/callback
  
  Allowed Logout URLs:
    - http://localhost:5678
    - https://your-n8n-instance.com
  
  Allowed Web Origins:
    - http://localhost:5678
    - https://your-n8n-instance.com

Grant Types:
  ☑ Authorization Code
  ☑ Refresh Token
  ☐ Implicit (not needed)
  ☐ Client Credentials (not needed)

Token Endpoint Authentication Method:
  ○ None (public client)
```

4. **IMPORTANT**: Note these values:
   - `Domain`: `your-tenant.auth0.com`
   - `Client ID`: `abc123...`
   - `Client Secret`: Not needed for public OAuth2 clients

### Step 5: Enable RBAC

1. Go to your API settings
2. Under **RBAC Settings**:

```
☑ Enable RBAC
☑ Add Permissions in the Access Token
```

This ensures user permissions (scopes) are included in the JWT.

### Step 6: Create Test Users

Go to **User Management > Users**, create test accounts:

#### Observer User
```
Email: observer@coffee.local
Password: Test1234!
Role: Roast Observer
```

#### Operator User
```
Email: operator@coffee.local
Password: Test1234!
Role: Roast Operator
```

#### Admin User
```
Email: admin@coffee.local  
Password: Test1234!
Role: Roast Admin
```

**Assign roles**:
1. Click on each user
2. Go to **Roles** tab
3. Click **Assign Roles**
4. Select appropriate role

---

## n8n Configuration

### OAuth2 Credential Setup

1. In n8n, go to **Credentials**
2. Create new **OAuth2 API** credential

```yaml
Name: Auth0 Coffee Roasting

Grant Type: Authorization Code
Authorization URL: https://your-tenant.auth0.com/authorize
Access Token URL: https://your-tenant.auth0.com/oauth/token
Client ID: YOUR_CLIENT_ID
Client Secret: (leave empty for public client)
Scope: read:detection write:detection read:roaster write:roaster offline_access
Auth URI Query Parameters:
  audience: https://coffee-roasting-api

Authentication: Header Auth
```

### n8n Workflow: User Login Node

```json
{
  "nodes": [
    {
      "name": "User Authentication",
      "type": "n8n-nodes-base.httpRequest",
      "credentials": {
        "oAuth2Api": {
          "id": "1",
          "name": "Auth0 Coffee Roasting"
        }
      },
      "parameters": {
        "method": "GET",
        "url": "http://localhost:5001/health",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "oAuth2Api"
      }
    }
  ]
}
```

When workflow runs:
1. User is prompted to log in (if not already)
2. Auth0 login page appears
3. User authenticates
4. n8n receives user's access token
5. Token is used for all subsequent MCP requests

---

## JWT Token Structure

### Example User Token

```json
{
  "iss": "https://your-tenant.auth0.com/",
  "sub": "auth0|507f1f77bcf86cd799439011",
  "aud": "https://coffee-roasting-api",
  "iat": 1730000000,
  "exp": 1730086400,
  "scope": "read:detection read:roaster write:detection write:roaster",
  "permissions": [
    "read:detection",
    "read:roaster",
    "write:detection",
    "write:roaster"
  ],
  "email": "operator@coffee.local",
  "name": "Jane Operator",
  "nickname": "jane",
  "picture": "https://s.gravatar.com/avatar/..."
}
```

### Token Claims Explanation

- `sub`: Unique user ID (use for audit logs)
- `scope`: Space-separated scopes
- `permissions`: Array of permissions (if RBAC enabled)
- `email`, `name`: User profile info
- `exp`: Token expiration (Unix timestamp)

---

## MCP Server JWT Validation

### Python Implementation

```python
from jose import jwt, JWTError
import requests
from functools import lru_cache

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")

@lru_cache(maxsize=1)
def get_jwks():
    """Fetch and cache Auth0 public keys."""
    url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

async def validate_user_token(token: str) -> dict:
    """
    Validate user JWT and return payload.
    
    Returns:
        dict: Token payload with user_id, scopes, email, etc.
    
    Raises:
        JWTError: If token is invalid
    """
    jwks = get_jwks()
    
    # Get signing key
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = None
    
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
            break
    
    if not rsa_key:
        raise JWTError("Unable to find appropriate signing key")
    
    # Verify and decode
    payload = jwt.decode(
        token,
        rsa_key,
        algorithms=["RS256"],
        audience=AUTH0_AUDIENCE,
        issuer=f"https://{AUTH0_DOMAIN}/"
    )
    
    return payload

def check_user_has_scope(payload: dict, required_scope: str) -> bool:
    """Check if user token has required scope."""
    scopes = payload.get("scope", "").split()
    permissions = payload.get("permissions", [])
    
    # Check both scope and permissions (RBAC)
    return required_scope in scopes or required_scope in permissions

def get_user_id(payload: dict) -> str:
    """Extract user ID from token for audit logging."""
    return payload.get("sub")
```

### Usage in MCP Endpoint

```python
@app.post("/api/roaster/start")
async def start_roaster(request: Request):
    # Middleware already validated token
    token_payload = request.state.auth
    
    # Check write permission
    if not check_user_has_scope(token_payload, "write:roaster"):
        raise HTTPException(403, "Insufficient permissions")
    
    # Get user for audit log
    user_id = get_user_id(token_payload)
    user_email = token_payload.get("email", "unknown")
    
    # Execute action
    session_manager.start_roaster()
    
    # Audit log
    logger.info(f"Roaster started by user {user_email} ({user_id})")
    
    return {"status": "success", "user": user_email}
```

---

## Testing

### 1. Obtain User Token (Manual)

```bash
# Get authorization code (opens browser)
open "https://your-tenant.auth0.com/authorize?
  response_type=code&
  client_id=YOUR_CLIENT_ID&
  redirect_uri=http://localhost:3000/callback&
  scope=read:detection write:detection read:roaster write:roaster&
  audience=https://coffee-roasting-api"

# Exchange code for token
curl -X POST https://your-tenant.auth0.com/oauth/token \
  -H 'Content-Type: application/json' \
  -d '{
    "grant_type": "authorization_code",
    "client_id": "YOUR_CLIENT_ID",
    "code": "AUTHORIZATION_CODE_FROM_CALLBACK",
    "redirect_uri": "http://localhost:3000/callback"
  }'
```

### 2. Test with User Token

```bash
# Store token
export USER_TOKEN="eyJ0eXAi..."

# Test as Observer (should work)
curl -X GET http://localhost:5002/api/roaster/status \
  -H "Authorization: Bearer $USER_TOKEN"

# Test start roaster as Observer (should fail - 403)
curl -X POST http://localhost:5002/api/roaster/start \
  -H "Authorization: Bearer $USER_TOKEN"

# Login as Operator, then test again (should work)
```

### 3. Verify Token Claims

```bash
# Decode JWT at jwt.io
echo $USER_TOKEN | pbcopy
# Paste into https://jwt.io

# Check:
# - aud: https://coffee-roasting-api
# - scope or permissions: includes required scopes
# - sub: user ID
# - exp: not expired
```

---

## Security Best Practices

1. **Short-lived tokens**: 24 hours max, use refresh tokens
2. **HTTPS only**: Never send tokens over plain HTTP in production
3. **Scope principle**: Grant minimum scopes needed
4. **Audit logging**: Log all actions with user ID
5. **Token rotation**: Encourage users to re-login periodically
6. **Revocation**: Can revoke user's refresh tokens in Auth0 dashboard

---

## Audit Logging

### Log Format

```json
{
  "timestamp": "2025-10-25T22:50:00Z",
  "action": "roaster.start",
  "user_id": "auth0|507f1f77bcf86cd799439011",
  "user_email": "operator@coffee.local",
  "ip_address": "192.168.1.100",
  "success": true,
  "details": {
    "initial_temp": 180.5,
    "target_profile": "medium_roast"
  }
}
```

### Query Logs

```python
# Who started roasts today?
logs = query_audit_logs(action="roaster.start", date=today)
for log in logs:
    print(f"{log['user_email']} at {log['timestamp']}")

# What did user X do?
user_actions = query_audit_logs(user_id="auth0|507f...")
```

---

## Troubleshooting

### 401 Unauthorized

**Problem**: Token rejected

**Solutions**:
- Check token not expired (`exp` claim)
- Verify `aud` matches API identifier
- Verify `iss` matches your Auth0 domain
- Check token signature with JWKS keys

### 403 Forbidden

**Problem**: Valid token but insufficient permissions

**Solutions**:
- Check user has correct role assigned in Auth0
- Verify RBAC is enabled in API settings
- Confirm "Add Permissions in the Access Token" is checked
- Check `scope` or `permissions` claim in JWT

### n8n OAuth Flow Fails

**Problem**: Redirect error or "invalid callback"

**Solutions**:
- Verify callback URL in Auth0 matches n8n's URL
- Check `audience` parameter in Auth URI Query Parameters
- Ensure application is Regular Web Application (not SPA)
- Check Auth0 application logs for specific error

---

## Next Steps

1. [ ] Create Auth0 tenant and API
2. [ ] Define scopes and roles
3. [ ] Create test users (observer, operator, admin)
4. [ ] Configure n8n OAuth2 credential
5. [ ] Update MCP servers to validate user tokens
6. [ ] Add audit logging
7. [ ] Test with different user roles
8. [ ] Document user workflows

---

**Auth0 References**:
- [Authorization Code Flow](https://auth0.com/docs/get-started/authentication-and-authorization-flow/authorization-code-flow)
- [Role-Based Access Control](https://auth0.com/docs/manage-users/access-control/rbac)
- [Add Permissions to Access Tokens](https://auth0.com/docs/secure/tokens/access-tokens/get-access-tokens#control-the-contents-of-access-tokens)
