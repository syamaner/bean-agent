# Phase 3: Intelligent Roasting Agent

Building an LLM-powered coffee roasting agent with .NET Aspire orchestration and n8n workflow automation.

**Status**: ✅ COMPLETE  
**Prerequisites**: Phase 1 ✅ + Phase 2 ✅  
**Implementation**: Custom Python autonomous agent with GPT-4

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
✅ **Phase 2**: MCP servers operational (HTTP + SSE)  
✅ **Auth0 setup**: Configured tenant, roles, and API  
✅ **HTTP APIs**: MCP servers upgraded from stdio to HTTP + SSE  
✅ **.NET Aspire**: Installed workload and created AppHost  
🔴 **n8n**: Skipped - Used custom Python agent instead  
⚪ **Cloudflare**: Account + tunnel setup (Part 2 - optional)

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

### Part 1 - Local Development ✅ COMPLETE
✅ MCP servers expose HTTP + SSE APIs with Auth0  
✅ .NET Aspire orchestrates all services  
✅ Custom Python agent executes autonomous roast cycle  
✅ Agent makes intelligent decisions via GPT-4  
✅ Full roast simulation validated with mock hardware  
✅ Auth0 JWT authentication working end-to-end  

### Part 2 - Production Deployment ⚪ PENDING
⚪ MCP servers accessible via Cloudflare tunnel  
⚪ Agent can control home roaster remotely  
⚪ Stable 24/7 operation  
⚪ Acceptable latency (<2s round-trip)  

---

**Start Date**: October 2025  
**Completion Date**: October 2025  
**Current Status**: Phase 3 Part 1 complete ✅ - Autonomous agent operational with .NET Aspire orchestration
