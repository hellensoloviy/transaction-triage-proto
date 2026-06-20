---
tags: [adr, technical-debt]
---

# ADR-003 — MCP Response Parsing with `ast.literal_eval`

## Current state

The [[mcp-server]] returns Python `str()` representations of dicts when sending data back to agents, e.g.:

```
{'id': 'abc-123', 'amount': Decimal('100.00'), 'status': 'pending'}
```

Agents parse these with `ast.literal_eval()`, which is safe (evaluates Python literals only, not arbitrary code).

## Why not `json.loads()`

The server was built using Python's default `str()` on response dicts. `Decimal` and `UUID` types are not JSON-serialisable without a custom encoder, and the fix was caught late.

`ast.literal_eval()` was substituted for the original `eval()` as a safe intermediate step.

## Known fragility

- Breaks if any string field contains a single quote (e.g. `"counterparty": "O'Brien"`)
- Not cross-language compatible — a non-Python client cannot parse these responses

## Correct fix

Replace `str()` with `json.dumps(obj, default=str)` (or a custom encoder for `Decimal`/`UUID`) in the MCP server. Replace `ast.literal_eval()` with `json.loads()` in both agents. This is a ~30-minute change touching three files.

## Why not fixed yet

It was caught late and the working system was not changed close to a deadline. The fix is straightforward and low-risk but would need a full re-test cycle.

## Related
- [[mcp-server]]
- [[day-agent]]
- [[night-agent]]
