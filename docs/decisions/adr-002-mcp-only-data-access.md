---
tags: [adr, architecture]
---

# ADR-002 — Agents Access Data Through MCP Only

## Decision

Agents never call FastAPI directly and never query Postgres directly. All data access goes through the [[mcp-server]] via stdio. The MCP server is the only thing that calls FastAPI. FastAPI is the only thing that touches Postgres.

## Why

**Auditability.** Every data access by an agent is a named MCP tool call. The tool name, arguments, and result appear in the structured log. You can reconstruct exactly what an agent saw and did by reading `logs/agent_run.jsonl`.

**Validation boundary.** FastAPI owns all schema validation. Agents cannot bypass it by constructing raw SQL or HTTP calls.

**Testability.** The MCP server can be tested independently (`tests/test_mcp_server.py`). Agent tests can mock the MCP layer without touching the database.

**Separation of concerns.** Agents reason about transactions; the MCP server and FastAPI handle persistence. Mixing these would make the agent code harder to reason about.

## Cost

Adds a network hop per tool call (agent → MCP subprocess → FastAPI → Postgres). At this scale the latency is dominated by Claude API calls, so the extra hop is not measurable.

## Related
- [[overview]]
- [[mcp-server]]
- [[react-loop]]
