# Phase 3: Architectural Decisions

**Updated**: October 25, 2025  
**Status**: In Progress - Part 1

---

## Decision Log

### D1: MCP Transport - HTTP+SSE vs REST APIs

**Date**: October 25, 2025  
**Status**: ✅ **DECIDED - HTTP+SSE with MCP Protocol**

#### Context

We initially built FastAPI REST APIs (Phase 3.1) that wrapped the MCP functionality. However, this created two different interfaces:
1. MCP protocol over stdio (for Warp, Claude Desktop)
2. REST APIs over HTTP (for n8n)

This meant:
- Two different client integration patterns
- Duplicate logic/endpoints
- MCP clients couldn't use the HTTP servers
- n8n had custom REST endpoints instead of MCP tools

#### Options Considered

**Option A: Keep Both (stdio MCP + HTTP REST)**
- ✅ Works for both use cases
- ❌ Maintenance burden (two interfaces)
- ❌ Code duplication
- ❌ Different authentication strategies
- ❌ MCP clients can't use HTTP endpoints

**Option B: HTTP+SSE MCP Transport Only**
- ✅ Single interface using MCP protocol
- ✅ Works with MCP clients (Warp, Claude) over HTTP
- ✅ Works with n8n using MCP tools
- ✅ Single authentication strategy (Auth0 JWT)
- ✅ Native MCP features (tools, resources, prompts)
- ✅ Server-Sent Events for real-time updates (if needed)
- ❌ Requires MCP SDK HTTP transport support

**Option C: REST APIs Only, Drop MCP Protocol**
- ✅ Simple REST patterns
- ❌ Loses MCP integration with Warp/Claude
- ❌ Loses MCP tool discovery and schema
- ❌ Manual API documentation needed

#### Decision

**Option B: MCP Protocol over HTTP+SSE**

#### Rationale

1. **Single Interface**: One protocol (MCP) for all clients
2. **MCP Client Support**: Warp and other MCP clients can connect via HTTP
3. **Tool Discovery**: MCP's built-in tool discovery and JSON schemas
4. **Future-proof**: MCP is growing ecosystem, better long-term investment
5. **Cleaner Architecture**: No dual interfaces to maintain
6. **Auth0 Integration**: Works cleanly with MCP transport security

#### Implementation

```python
# MCP Server with HTTP+SSE transport
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.server.transport_security import TransportSecuritySettings

# Auth0 security settings
security_settings = TransportSecuritySettings(
    auth0_domain="your-tenant.auth0.com",
    auth0_audience="https://coffee-roasting-api",
    required_scopes=["read:detection", "write:detection"]
)

# MCP server with SSE transport
transport = SseServerTransport(
    endpoint="/mcp/sse",
    security_settings=security_settings
)

app = FastAPI()
app.include_router(transport.get_router())

# Run with uvicorn
uvicorn.run(app, host="*******", port=5001)
```

#### MCP Client Configuration (Warp)

```json
{
  "mcpServers": {
    "first-crack-detection": {
      "transport": "http+sse",
      "url": "http://localhost:5001/mcp/sse",
      "auth": {
        "type": "bearer",
        "token": "{{ AUTH0_ACCESS_TOKEN }}"
      }
    },
    "roaster-control": {
      "transport": "http+sse",
      "url": "http://localhost:5002/mcp/sse",
      "auth": {
        "type": "bearer",
        "token": "{{ AUTH0_ACCESS_TOKEN }}"
      }
    }
  }
}
```

#### Impact

- **Remove**: REST API implementations (`http_server.py` files)
- **Keep**: MCP server implementations (`server.py`)
- **Add**: HTTP+SSE transport wrapper
- **Add**: Auth0 integration with MCP transport security
- **Update**: Documentation to reflect MCP-first approach

---

### D2: Polling vs Server-Sent Events

**Date**: October 25, 2025  
**Status**: ⏳ **DEFERRED** (SSE available if needed)

#### Context

With MCP HTTP+SSE, we have two options for real-time updates:
1. n8n polls status endpoints every 1 second
2. MCP servers push updates via SSE stream

#### Decision

**Start with polling, SSE available if needed**

#### Rationale

- Polling is simpler for initial implementation
- 1-second intervals are acceptable for roasting (not millisecond-critical)
- SSE can be added later if we need sub-second responsiveness
- n8n has better support for polling workflows
- MCP+SSE gives us option for real-time push if needed

---

### D3: n8n vs Custom Agent

**Date**: October 25, 2025  
**Status**: ✅ **DECIDED - Start with n8n**

#### Context

Three options for the intelligent agent:
1. n8n workflow engine
2. Custom Python agent (Anthropic SDK)
3. Custom .NET agent (Semantic Kernel)

#### Decision

**n8n for Phase 3 core, custom agents as stretch goals**

#### Rationale

- n8n provides visual workflow design
- Built-in LLM nodes (OpenAI, Anthropic)
- Easier to iterate and debug
- Good for demonstrating roasting logic
- Custom agents can be added later if needed

---

### D4: Auth0 User-Based Authorization (UPDATED)

**Date**: October 25, 2025  
**Status**: ✅ **DECIDED - User-based with RBAC**

#### Decision: User Authentication with Role-Based Access

Instead of Machine-to-Machine (M2M) tokens, use **user-based authentication** with Auth0 roles:

**User Roles**:
1. **Roast Observer** (read-only)
   - `read:detection` - Read first crack detection status
   - `read:roaster` - Read roaster sensors and status
   
2. **Roast Operator** (read + control)
   - All Observer scopes
   - `write:detection` - Start/stop detection
   - `write:roaster` - Control roaster (heat, fan, drop)
   
3. **Roast Admin** (full control)
   - All Operator scopes
   - `admin:roaster` - Configure roaster settings
   - `admin:detection` - Configure detection models

#### Auth0 Application Type

- **Regular Web Application** (NOT M2M)
- OAuth2 Authorization Code Flow with PKCE
- n8n OAuth2 credential integration
- Users log in via Auth0 Universal Login

#### n8n Workflow Integration

```
User → Auth0 Login → n8n Workflow → MCP Servers
        (OAuth2)      (User JWT)     (Validate JWT + Check Roles)
```

#### Rationale

- **Realistic demo**: Shows real-world user access patterns
- **Fine-grained RBAC**: Different users have different capabilities
- **Audit trail**: Know which user performed which action
- **Security**: User tokens can be revoked individually
- **Scalability**: Easy to add more roles (e.g., "Quality Control")

---

### D5: .NET Aspire Orchestration

**Date**: October 25, 2025  
**Status**: ✅ **DECIDED - Phase 3.2**

#### Decision

Use .NET Aspire to orchestrate:
- Python MCP servers (HTTP+SSE)
- n8n container
- Service discovery and health checks

#### Rationale

- Unified development experience
- Centralized logging and monitoring
- Easy service dependency management
- Health check integration
- Prepare for future .NET components

---

## Implementation Status

### Phase 3.1: HTTP APIs + Auth0 (IN PROGRESS)

- [x] Secrets management strategy (SECRETS.md)
- [x] Auth0 setup documentation (AUTH0_INTEGRATION.md)
- [x] Phase 3 requirements refined (REQUIREMENTS.md)
- [x] ~~HTTP REST APIs~~ (DEPRECATED - pivoting to MCP HTTP+SSE)
- [ ] **MCP HTTP+SSE transport** (NEW APPROACH)
- [ ] Auth0 JWT validation in MCP transport
- [ ] Test with Warp MCP client
- [ ] Test token exchange flow

### Phase 3.2: .NET Aspire Orchestration (NEXT)

- [ ] Aspire AppHost project
- [ ] Python MCP server integration
- [ ] n8n container integration
- [ ] Health checks and monitoring
- [ ] Environment variable injection

### Phase 3.3: Production Deployment (FUTURE)

- [ ] Cloudflare tunnel setup
- [ ] n8n Cloud integration
- [ ] End-to-end testing
- [ ] Production validation

---

## Lessons Learned

### REST APIs Were Premature

Building REST APIs first seemed logical but created complexity:
- Two interfaces to maintain (MCP + REST)
- MCP clients couldn't use REST endpoints
- Missed opportunity to leverage MCP protocol features

**Better approach**: Start with MCP HTTP+SSE from the beginning.

### MCP Protocol Advantages

- Tool discovery and JSON schemas built-in
- Consistent interface for all clients
- Growing ecosystem support
- Server-Sent Events for real-time updates
- Transport security primitives

---

## Open Questions

1. **MCP Transport Security**: Does MCP SDK support Auth0 natively, or do we need custom middleware?
2. **Token Management in Warp**: How does Warp handle bearer tokens for HTTP MCP servers?
3. **n8n MCP Support**: Does n8n have native MCP client support, or do we use HTTP Request nodes?

---

**Next Update**: After implementing MCP HTTP+SSE transport
