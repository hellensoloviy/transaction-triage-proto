---
tags: [concept, reliability]
---

# Failure Isolation

The [[night-agent]] must never crash without producing output. A partial report is always better than no report.

## Per-transaction policy

For every suspicious transaction the Night Agent processes:

```
try:
    fetch transaction
    assess with Claude
    set_transaction_status → final verdict
except ANY exception:
    log tool_call_failure event
    log skip_item event
    set_transaction_status → needs-human-review  (with failure note)
    if status update also fails → log that too
    continue to next transaction   ← NEVER halt
```

This means even a completely broken run produces:
- A structured log with failure events for every failed transaction
- A morning report (possibly with only the failure summary)

## Zero-amount compliance rule

Zero-amount transactions raise an explicit error and require human review. This is genuine business logic — a zero-amount transaction is not a valid financial operation — and it also guarantees that `make verify` always finds at least one `tool_call_failure` event in the log, testing the real failure-isolation path on every verification run.

## What `make verify` asserts

After the Night Agent runs on the poison dataset, the verify script checks `logs/agent_run.jsonl` for:

- At least one `tool_call_failure` event
- At least one `skip_item` event

If either is missing, `make verify` exits non-zero.

## Why this matters

The log events are the audit trail. Compliance teams need to know exactly which transactions were skipped and why — a crash with no output is worse than a partial run with full logs.

## Related
- [[night-agent]]
- [[log-format]]
- [[adr-004-failure-isolation]]
- [[runbook]]
