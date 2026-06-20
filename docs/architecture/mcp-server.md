---
tags: [architecture, mcp]
---

# MCP Server

**File:** `mcp_server/server.py`

Custom MCP server that acts as the only bridge between agents and the FastAPI data plane. Both the [[day-agent]] and [[night-agent]] communicate exclusively through this server via stdio.

## The 5 tools

| Tool | Purpose |
|---|---|
| `list_transactions` | List transactions by status and optional time window |
| `get_transaction` | Fetch one transaction by UUID, including prior agent notes |
| `set_transaction_status` | Update status with a required `reasoning` note |
| `get_risk_metrics` | Aggregate counts, amounts, and top counterparties over a window |
| `write_report` | Save a markdown report to Postgres and `reports/` directory |

## `list_transactions` — valid statuses

`pending` · `clean` · `suspicious` · `blocked` · `needs-human-review`

The Day Agent uses `pending`; the Night Agent uses `suspicious`.

## `set_transaction_status` — required fields

```json
{
  "transaction_id": "<uuid>",
  "status": "clean | suspicious | blocked | needs-human-review",
  "reasoning": "<required explanation>",
  "agent": "day-agent | night-agent"
}
```

The `reasoning` field is required — the server rejects calls without it.

## Response format (known limitation)

The server currently returns Python `str()` representations of dicts (e.g. `"{'id': '...', 'amount': Decimal('100.00')}"`) rather than JSON. Agents parse these with `ast.literal_eval()`. See [[adr-003-ast-literal-eval]] for the full tradeoff.

## Subprocess model

The MCP server is spawned as a subprocess on every agent run (stdio transport). There is no persistent process or connection pool — startup cost is paid each run.

## Related
- [[overview]]
- [[adr-002-mcp-only-data-access]]
- [[adr-003-ast-literal-eval]]
