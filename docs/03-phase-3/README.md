# Phase 3: Intelligent Roasting Agent

Building an LLM-powered coffee roasting agent with .NET Aspire orchestration and n8n workflow automation.

**Status**: 📋 READY TO START  
**Prerequisites**: Phase 1 ✅ + Phase 2 ✅

---

## Overview

Phase 3 creates an intelligent agent that orchestrates coffee roasting using the two MCP servers from Phase 2. The agent makes real-time decisions based on sensor data and first crack detection to execute roasting profiles.

**Two-Part Approach**:
1. **Part 1**: Local development with .NET Aspire + n8n workflow
2. **Part 2**: Production deployment with Cloudflare tunnel + n8n Cloud

---

## Architecture Summary

### Part 1: Local Development
```
.NET Aspire Host
  ├─ n8n Workflow (Container)
  │   └─ HTTP polling (1s) + LLM decisions
  ├─ First Crack MCP (Python)
  │   └─ HTTP API + Auth0
  └─ Roaster Control MCP (Python)
      └─ HTTP API + Auth0 + Hottop USB
```

### Part 2: Production
```
n8n Cloud → Cloudflare Tunnel → Home Network
                                  ├─ First Crack MCP
                                  └─ Roaster Control MCP → Hottop
```

---

## Key Decisions

✅ **Polling over SSE**: Agent polls HTTP endpoints every 1 second (simpler, works well for n8n)  
✅ **n8n Workflow**: Primary agent implementation (LLM decision nodes)  
✅ **Auth0**: JWT authentication with `roast:admin` and `roast:observer` roles  
✅ **.NET Aspire**: Orchestrates Python MCP servers + n8n container  
✅ **Cloudflare Tunnel**: Secure remote access to home roaster  

**Stretch Goals**: Custom Python agent (Anthropic SDK) + .NET agent (Semantic Kernel)

---

## Documents

- **[REQUIREMENTS.md](./REQUIREMENTS.md)** - Detailed requirements and architecture
- **Design docs** - Coming soon
- **Implementation plan** - Coming soon

---

## Prerequisites

✅ **Phase 1**: Model trained and validated (93% accuracy)  
✅ **Phase 2**: MCP servers operational (stdio + Warp integration)  
⚪ **Auth0 setup**: Configure tenant, roles, and API  
⚪ **HTTP APIs**: Upgrade MCP servers from stdio to HTTP  
⚪ **.NET Aspire**: Install workload and create AppHost  
⚪ **n8n**: Container or cloud instance  
⚪ **Cloudflare**: Account + tunnel setup (Part 2)  

---

## Timeline

**Part 1** (2-3 weeks):
- Week 1: HTTP APIs + Auth0 integration
- Week 2: Aspire orchestration + n8n workflow
- Week 3: Testing + refinement

**Part 2** (1 week):
- Cloudflare tunnel + n8n Cloud
- Production validation

**Stretch Goals** (as time permits):
- Python agent: 1 week
- .NET agent: 1 week

---

## Success Metrics

### Part 1
✅ MCP servers expose HTTP APIs with Auth0  
✅ .NET Aspire orchestrates all services  
✅ n8n workflow executes full roast cycle  
✅ Agent makes autonomous decisions via LLM  
✅ Roast completes successfully with real hardware  

### Part 2
✅ MCP servers accessible via Cloudflare tunnel  
✅ n8n Cloud can control home roaster remotely  
✅ Auth0 authentication working end-to-end  
✅ Acceptable latency (<2s round-trip)  

---

**Start Date**: After Phase 2 completion ✅  
**Current Status**: Phase 2 complete, ready to begin Phase 3
