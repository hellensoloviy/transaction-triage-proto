---
tags: [architecture, agent]
---

# Day Agent

**File:** `agents/day.py`

Processes the pending transaction queue in real time. Classifies each transaction as `clean`, `suspicious`, or `blocked`.

## Behaviour

1. Calls `list_transactions(status="pending")` to get the current queue
2. Iterates through results, calling `get_transaction` on each for full context
3. Calls `set_transaction_status` with a classification and mandatory `reasoning` note
4. Continues until the pending queue is empty or `MAX_ITERATIONS` is hit

## Classification outputs

| Status | Meaning |
|---|---|
| `clean` | No red flags, passes compliance checks |
| `suspicious` | Flagged for Night Agent review |
| `blocked` | Hard block — rejected immediately |

Suspicious transactions are queued for the [[night-agent]] to review overnight.

## Batching

Controlled by `DAY_AGENT_BATCH_SIZE` (default 50). Transactions are fetched in batches; `MAX_ITERATIONS` (default 80) acts as a safety ceiling across all batches.

The ceiling is high because each transaction is a separate tool call. See [[adr-001-sequential-processing]] for the tradeoff discussion.

## Prompt caching

The Day Agent sends its system prompt with `cache_control: ephemeral`. Cached tokens do not count toward the ITPM rate limit. See [[prompt-caching]].

## Related
- [[overview]]
- [[react-loop]]
- [[mcp-server]]
- [[environment]]
