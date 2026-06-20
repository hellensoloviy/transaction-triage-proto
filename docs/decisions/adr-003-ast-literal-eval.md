---
tags: [adr, technical-debt]
---

# ADR-003 — MCP Response Parsing

## Current state (resolved)

The MCP server returns `json.dumps(result)` for all tool responses. Both agents parse responses with `json.loads()`. This is the correct, cross-language-compatible approach.

## History

The original implementation used Python's default `str()` on response dicts, producing strings like `{'id': '...', 'amount': Decimal('100.00')}`. Agents initially parsed these with `eval()`, then `ast.literal_eval()` as a safer intermediate step.

The `ast.literal_eval()` approach was fragile in two ways:
- It would break on any string field containing a single quote (e.g. `"counterparty": "O'Brien"`)
- It was not cross-language compatible

## Resolution

The MCP server was updated to use `json.dumps(result, default=str)` which serialises `Decimal` and `UUID` types via their `str()` representation. Agents now use `json.loads()`. CLAUDE.md describes the old `ast.literal_eval()` state — the code has since been updated.

## Related
- [[mcp-server]]
- [[day-agent]]
- [[night-agent]]
