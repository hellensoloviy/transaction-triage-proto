---
tags: [architecture]
---

# System Overview

## Data flow

```
CLI / Make targets
        │
        ├── Day Agent (agents/day.py)
        │       │  MCP stdio
        │       ▼
        │   MCP Server (mcp_server/server.py)
        │       │  HTTP
        │       ▼
        │   FastAPI (app/main.py) ── Postgres
        │
        └── Night Agent (agents/night.py)
                │  MCP stdio
                ▼
            MCP Server ── FastAPI ── Postgres
                │
                └── Report Sub-Agent (separate Claude call)
```

## Hard boundaries

1. Agents call **MCP tools only** — never raw HTTP, never direct DB
2. MCP server calls **FastAPI** — the only thing that touches Postgres
3. FastAPI **owns the schema** — `create_all()` on startup, all validation here
4. All config from **environment variables** — no hardcoded values in code

These boundaries are not conventions — they are load-bearing. Violating them bypasses the failure isolation and audit trail the system is built around.

## Transaction lifecycle

```
seed → pending
           │
    Day Agent classifies
           │
     ┌─────┴──────────┐
  clean            suspicious / blocked
                       │
               Night Agent reviews
                       │
          ┌────────────┴────────────┐
       confirmed              needs-human-review
```

## Related
- [[day-agent]]
- [[night-agent]]
- [[mcp-server]]
- [[react-loop]]
