---
tags: [home, nav]
---

# Transaction Triage System — Knowledge Base

A fintech compliance triage system built with two cooperating Claude agents, a custom MCP server, FastAPI, and Postgres.

---

## System at a glance

| Layer | Component | File |
|---|---|---|
| Agents | Day Agent, Night Agent | `agents/day.py`, `agents/night.py` |
| Shared loop | ReAct tool-use loop | `agents/loop.py` |
| Data bridge | MCP server | `mcp_server/server.py` |
| Data plane | FastAPI + Postgres | `app/main.py`, `app/database.py` |

---

## Navigation

### Architecture
- [[overview]] — data flow, component topology
- [[day-agent]] — real-time classification
- [[night-agent]] — overnight review and reporting
- [[mcp-server]] — 5 tools, HTTP bridge to FastAPI

### Concepts
- [[react-loop]] — shared ReAct loop (no frameworks)
- [[failure-isolation]] — Night Agent never-crash policy
- [[prompt-injection]] — two-layer defense strategy
- [[prompt-caching]] — ITPM rate-limit relief

### Operations
- [[runbook]] — make targets, startup, gotchas
- [[environment]] — all environment variables
- [[log-format]] — JSONL schema, event types

### Decisions
- [[adr-001-sequential-processing]] — why agents run one transaction at a time
- [[adr-002-mcp-only-data-access]] — architecture boundary rule
- [[adr-003-ast-literal-eval]] — MCP response parsing tradeoff
- [[adr-004-failure-isolation]] — investment in Night Agent resilience
- [[adr-005-two-layer-injection-defense]] — prompt injection defense design
