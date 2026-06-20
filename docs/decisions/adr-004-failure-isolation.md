---
tags: [adr, reliability]
---

# ADR-004 — Night Agent Failure Isolation Investment

## Decision

The [[night-agent]] wraps every transaction in a `try/except` block. On any exception: log it, attempt to set `needs-human-review`, continue to the next transaction. The report is always written, even if every transaction failed.

## Why it was prioritised

Failure isolation was treated as the most critical dimension of the Night Agent. The reasoning:

1. **A compliance team depends on the morning report.** A crash with no output is worse than a partial report — it gives the team nothing to act on.

2. **Agent failures should be visible, not hidden.** Structured `tool_call_failure` and `skip_item` log events give compliance teams an auditable record of what was skipped and why.

3. **One bad transaction should not block the rest.** In production, data quality issues are expected. An agent that halts on the first bad input is not production-ready.

## The zero-amount rule

Zero-amount transactions raise an explicit error and require human review. This is defensible business logic — a zero-amount financial transaction is not valid — and it also guarantees that `make verify` always finds a real `tool_call_failure` event, testing the actual failure-isolation path on every run.

## Alternatives considered

- **Fail fast:** halt on the first exception. Rejected — leaves most transactions unprocessed.
- **Retry the failed transaction:** could cause infinite loops on deterministic failures. Rejected.
- **Silent skip:** continue without logging. Rejected — breaks auditability.

## Related
- [[failure-isolation]]
- [[night-agent]]
- [[log-format]]
