# Phase 2: MCP Servers

Building two Model Context Protocol (MCP) servers for coffee roasting.

## Overview

[Phase 2 Requirements](overview.md)

## Objectives

### Objective 1: First Crack Detection MCP ✅ COMPLETE

**Purpose**: Detect first crack from audio using trained ML model

[Full Documentation →](objective-1-first-crack/README.md)

**Status**: Complete (86 tests passing)  
**Completion**: 2025-01-25

### Objective 2: Roaster Control MCP ✅ COMPLETE

**Purpose**: Control Hottop roaster hardware and track roast metrics

[Full Documentation →](objective-2-roaster-control/README.md)

**Status**: Complete (122 tests passing)  
**Completion**: October 2025

---

## Architecture

```
┌─────────────────────┐         ┌──────────────────────┐
│ First Crack         │         │ Roaster Control      │
│ Detection MCP       │         │ MCP Server           │
│                     │         │                      │
│ - Audio input       │         │ - Hardware control   │
│ - ML inference      │         │ - Sensor reading     │
│ - Detection alerts  │         │ - Roast tracking     │
└──────────┬──────────┘         └──────────┬───────────┘
           │                               │
           │         ┌────────────────────┐│
           └─────────►  .NET Aspire       ││
                     │  Agent (Phase 3)   ││
                     └────────────────────┘│
                            │
                    Orchestrates roasting
```

---

**Phase 2 Started**: January 2025  
**Phase 2 Completed**: October 2025 ✅  
**Deliverables**: 2 MCP servers, 208+ tests, HTTP + SSE APIs, Auth0 authentication
