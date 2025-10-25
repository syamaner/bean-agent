# Phase 3: Agent

Building an LLM-powered coffee roasting agent with .NET Aspire orchestration.

**Status**: ⚪ PLANNED

## Overview

Phase 3 will create an intelligent agent that:
- Orchestrates the two MCP servers (first crack detection + roaster control)
- Makes roasting decisions based on sensor data and ML detections
- Implements roast profiles and control strategies
- Provides real-time monitoring and adjustments

## Planned Architecture

```
┌──────────────────────────────────────┐
│      .NET Aspire Agent               │
│                                      │
│  - LLM decision making               │
│  - Profile management                │
│  - Control strategy                  │
│  - Real-time monitoring              │
└────────┬─────────────────┬───────────┘
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌──────────────────┐
│ FC Detection    │  │ Roaster Control  │
│ MCP Server      │  │ MCP Server       │
└─────────────────┘  └──────────────────┘
```

## Prerequisites

- ✅ Phase 1: Model trained and validated
- 🟡 Phase 2: MCP servers operational
- ⚪ Auth0 integration
- ⚪ HTTP transport for MCP servers

## Planned Features

1. **Roast Profiles**: Light, medium, dark roast profiles
2. **Decision Engine**: LLM-powered control decisions
3. **Safety Limits**: Temperature and RoR constraints
4. **Logging**: Complete roast session recording
5. **UI**: Real-time monitoring dashboard (optional)

---

**Start Date**: TBD (after Phase 2 completion)  
**Prerequisites**: [Phase 2](../02-phase-2/) completion
