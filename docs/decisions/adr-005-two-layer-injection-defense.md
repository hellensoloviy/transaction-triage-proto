---
tags: [adr, security]
---

# ADR-005 — Two-Layer Prompt Injection Defense

## Decision

Defend against prompt injection at two independent layers:

1. **System prompt instructions** — both agents are told explicitly to ignore instructions in data fields
2. **Python-level keyword pre-check** (Night Agent only) — memos are scanned before their content reaches Claude

## Why two layers

A single layer in the system prompt is insufficient for high-stakes compliance use:

- Model instructions can be overridden by sufficiently crafted injection payloads
- A Python-level check is deterministic — it cannot be social-engineered

By filtering obvious injection patterns in Python before the text reaches Claude, the model-level defence only needs to handle edge cases the keyword check missed. The two layers are complementary, not redundant.

## Why the Night Agent gets the extra layer

The Night Agent assesses suspicious transactions in detail — it reads the full memo field into its reasoning context. The Day Agent does a shallower first-pass classification where the memo is less likely to be the deciding factor.

In production, both agents should have the Python pre-check. The Night Agent was prioritised because it has deeper exposure to memo content.

## Invariant

A transaction with prompt injection in its fields must never be classified `clean`. `make verify` asserts this against the poison dataset on every run.

## Related
- [[prompt-injection]]
- [[night-agent]]
- [[day-agent]]
