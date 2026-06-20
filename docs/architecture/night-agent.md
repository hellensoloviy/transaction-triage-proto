---
tags: [architecture, agent]
---

# Night Agent

**File:** `agents/night.py`

Runs once overnight. Reviews every `suspicious` transaction from the past `NIGHT_AGENT_CUTOFF_HOURS` hours, produces a morning report, and spawns a separate report-writing sub-agent.

## Behaviour

1. Calls `get_risk_metrics` to get an aggregate overview before processing
2. Calls `list_transactions(status="suspicious", since=<cutoff>)` to get the review queue
3. For each transaction:
   - Fetches full details with `get_transaction`
   - Raises immediately on zero-amount (exercises [[failure-isolation]] path)
   - Runs a Python-level [[prompt-injection]] keyword check on the memo field
   - If injection detected: marks `suspicious`, skips Claude assessment, continues
   - Otherwise: sends to Claude for assessment, calls `set_transaction_status`
4. Spawns a report sub-agent (`report-sub-agent`) with a clean JSON summary of findings
5. Saves the report via `write_report`

## Never-crash policy

The Night Agent must never halt without producing output. See [[failure-isolation]] for the full policy.

Short version:
- Every transaction is wrapped in `try/except`
- On failure: log `tool_call_failure`, set `needs-human-review`, continue
- Always produce a report — even if every transaction failed

## Sub-agent pattern

The report writer is a **completely separate** `client.messages.create()` call with its own system prompt and context. It receives only a clean JSON summary — no access to the Night Agent's conversation history.

The sub-agent logs events under `"agent": "report-sub-agent"` and does not clear the log — only the main Night Agent entry point truncates `logs/agent_run.jsonl` at startup.

## Output statuses

After Night Agent review, a suspicious transaction becomes one of:

| Status | Meaning |
|---|---|
| `clean` | Re-assessed as safe after deeper review |
| `blocked` | Confirmed bad, hard block |
| `needs-human-review` | Ambiguous, or processing failed |

## Related
- [[overview]]
- [[failure-isolation]]
- [[prompt-injection]]
- [[log-format]]
- [[react-loop]]
- [[adr-004-failure-isolation]]
