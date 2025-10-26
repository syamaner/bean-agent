# Secrets Management - Phase 3

**Status**: Development  
**Updated**: October 25, 2025

---

## Overview

Phase 3 requires several secrets for Auth0, MCP servers, and n8n. This document describes how to manage them securely.

---

## Strategy

1. **Environment Variables**: All secrets stored in `.env` files
2. **Gitignore**: All `.env` files are excluded from git
3. **Templates**: `.env.example` files show required variables (no values)
4. **Documentation**: This file explains what each secret is for

---

## Environment Files

### Structure

```
coffee-roasting/
├── .env                           # Root secrets (gitignored)
├── .env.example                   # Root template (committed)
├── src/mcp_servers/
│   ├── first_crack_detection/
│   │   ├── .env                   # FC MCP secrets (gitignored)
│   │   └── .env.example           # FC MCP template (committed)
│   └── roaster_control/
│       ├── .env                   # Roaster MCP secrets (gitignored)
│       └── .env.example           # Roaster template (committed)
└── aspire/
    ├── .env                       # Aspire secrets (gitignored)
    └── .env.example               # Aspire template (committed)
```

---

## Required Secrets

### 1. Auth0 Configuration (All MCP Servers)

```bash
# .env (shared by both MCP servers)
AUTH0_DOMAIN=genai-7175210165555426.uk.auth0.com
AUTH0_AUDIENCE=https://coffee-roasting-api

# For testing only (do not use in production)
AUTH0_CLIENT_ID=Jk3aF2NfkiiOIXY0eHJQxfA6jkP0Pjf7
AUTH0_CLIENT_SECRET=YOUR_AUTH0_CLIENT_SECRET
```

### 2. Roaster Control MCP

```bash
# src/mcp_servers/roaster_control/.env
ROASTER_MOCK_MODE=0                    # 0=real hardware, 1=mock
ROASTER_PORT=/dev/tty.usbserial-DN016OJ3
HTTP_PORT=5002
```

### 3. First Crack Detection MCP

```bash
# src/mcp_servers/first_crack_detection/.env
HTTP_PORT=5001
MODEL_PATH=experiments/final_model/model.pt
```

### 4. n8n Configuration

```bash
# Managed by .NET Aspire / Docker Compose
N8N_ENCRYPTION_KEY=<random-32-char-key>  # Generate with: openssl rand -hex 16
N8N_PORT=5678
```

### 5. .NET Aspire

```bash
# aspire/.env
# No secrets needed - references other services
```

---

## Setup Instructions

### Initial Setup

1. **Copy templates**:
```bash
# Root
cp .env.example .env

# First Crack MCP
cp src/mcp_servers/first_crack_detection/.env.example \
   src/mcp_servers/first_crack_detection/.env

# Roaster Control MCP
cp src/mcp_servers/roaster_control/.env.example \
   src/mcp_servers/roaster_control/.env
```

2. **Fill in values**:
   - Edit each `.env` file
   - Use credentials from `AUTH0_SETUP.md`
   - Generate n8n encryption key if needed

3. **Verify gitignore**:
```bash
# Should return nothing (all .env files ignored)
git status | grep "\.env$"
```

---

## Loading Secrets

### Python (MCP Servers)

```python
# Use python-dotenv
from dotenv import load_dotenv
import os

# Load from .env file in same directory
load_dotenv()

AUTH0_DOMAIN = os.environ["AUTH0_DOMAIN"]
AUTH0_AUDIENCE = os.environ["AUTH0_AUDIENCE"]
```

### .NET Aspire

```csharp
// Loads from project .env automatically
var builder = DistributedApplication.CreateBuilder(args);

// Pass to Python projects
var firstCrack = builder.AddPythonProject("first-crack-mcp", ...)
    .WithEnvironment("AUTH0_DOMAIN", builder.Configuration["AUTH0_DOMAIN"])
    .WithEnvironment("AUTH0_AUDIENCE", builder.Configuration["AUTH0_AUDIENCE"]);
```

---

## Security Best Practices

### ✅ DO

- Use `.env` files for all secrets
- Keep `.env.example` updated when adding new variables
- Verify `.env` files are in `.gitignore`
- Use different credentials for dev/prod
- Rotate secrets if exposed
- Generate strong random keys (e.g., `openssl rand -hex 32`)

### ❌ DON'T

- Commit `.env` files to git
- Share secrets in chat/email
- Use production secrets in development
- Hardcode secrets in code
- Commit secrets to git history (if you do, rotate them!)

---

## Gitignore Entries

Ensure `.gitignore` contains:

```gitignore
# Environment variables and secrets
.env
.env.local
.env.*.local

# Auth0 setup with credentials
docs/03-phase-3/AUTH0_SETUP.md

# IDE/OS files that might contain secrets
.vscode/settings.json
.idea/
*.swp
*~
```

---

## Testing Without Real Secrets

For automated tests:

```python
# tests/conftest.py
import os
import pytest

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Inject fake secrets for testing."""
    monkeypatch.setenv("AUTH0_DOMAIN", "test.auth0.com")
    monkeypatch.setenv("AUTH0_AUDIENCE", "https://test-api")
    monkeypatch.setenv("ROASTER_MOCK_MODE", "1")
```

---

## Secret Rotation Procedure

If a secret is exposed:

1. **Immediately rotate** in Auth0/service
2. **Update local** `.env` files
3. **Update documentation** (`AUTH0_SETUP.md`)
4. **Notify team** if applicable
5. **Check git history** - if committed, rewrite history or rotate

---

## Secrets Inventory

| Secret | Location | Purpose | Rotation |
|--------|----------|---------|----------|
| AUTH0_DOMAIN | All MCPs | Auth0 tenant | N/A (public) |
| AUTH0_AUDIENCE | All MCPs | API identifier | N/A (public) |
| AUTH0_CLIENT_ID | n8n | M2M client | When exposed |
| AUTH0_CLIENT_SECRET | n8n | M2M client | When exposed |
| ROASTER_PORT | Roaster MCP | USB device | N/A |
| N8N_ENCRYPTION_KEY | n8n | Credential encryption | Annually |

---

## Troubleshooting

### "Environment variable not found"

```bash
# Verify .env file exists
ls -la src/mcp_servers/roaster_control/.env

# Check it's loaded
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.environ.get('AUTH0_DOMAIN'))"
```

### "401 Unauthorized" from MCP server

- Verify Auth0 credentials in `.env`
- Check token with `jwt.io`
- Ensure app is authorized in Auth0 dashboard

---

**Status**: Ready for Phase 3 development ✅
