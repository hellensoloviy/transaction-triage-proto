---
tags: [ops, observability]
---

# Log Format

**File:** `logs/agent_run.jsonl`

One JSON object per line (JSONL). Every entry has a `timestamp` (UTC ISO 8601) and an `event` field. `make verify` reads this file to assert correctness — the field names are load-bearing.

---

## Event types

### `agent_start`
```json
{
  "timestamp": "...",
  "event": "agent_start",
  "run_id": "<uuid>",
  "agent_name": "night-agent"
}
```

### `agent_complete`
```json
{
  "timestamp": "...",
  "event": "agent_complete",
  "run_id": "<uuid>",
  "agent_name": "night-agent",
  "summary": "Processed 12 suspicious transactions..."
}
```

### `tool_call`
```json
{
  "timestamp": "...",
  "event": "tool_call",
  "run_id": "<uuid>",
  "tool_name": "get_transaction",
  "arguments": { "transaction_id": "..." }
}
```

### `tool_result`
```json
{
  "timestamp": "...",
  "event": "tool_result",
  "run_id": "<uuid>",
  "tool_name": "get_transaction",
  "result": "..."
}
```

### `tool_call_failure` — asserted by `make verify`
```json
{
  "timestamp": "...",
  "event": "tool_call_failure",
  "run_id": "<uuid>",
  "tool_name": "get_transaction",
  "error": "Zero-amount transaction requires human review",
  "transaction_id": "..."
}
```

### `skip_item` — asserted by `make verify`
```json
{
  "timestamp": "...",
  "event": "skip_item",
  "run_id": "<uuid>",
  "transaction_id": "...",
  "reason": "..."
}
```

### `api_rate_limit`
```json
{
  "timestamp": "...",
  "event": "api_rate_limit",
  "run_id": "<uuid>",
  "attempt": 2,
  "wait_seconds": 45
}
```

### `api_error`
```json
{
  "timestamp": "...",
  "event": "api_error",
  "run_id": "<uuid>",
  "attempt": 1,
  "error": "...",
  "wait_seconds": 5
}
```

### `sub_agent_spawn`
```json
{
  "timestamp": "...",
  "event": "sub_agent_spawn",
  "run_id": "<uuid>",
  "parent_agent": "night-agent",
  "purpose": "write morning report"
}
```

---

## Log clearing behaviour

`logs/agent_run.jsonl` is **truncated** at the start of every Day Agent or Night Agent run. Sub-agents use `agent_name: "report-writer"` and **append** rather than clearing — this ensures the Night Agent's log is intact when the sub-agent writes its events.

---

## Related
- [[failure-isolation]]
- [[night-agent]]
- [[react-loop]]
