---
tags: [concept, performance]
---

# Prompt Caching

Only the [[day-agent]] sends its system prompt with `cache_control: ephemeral`. The [[night-agent]] makes direct `client.messages.create()` calls without `cache_control`.

## Why it matters

Cached tokens do **not** count toward the ITPM (input tokens per minute) rate limit. On Tier 1, this is the primary mechanism that makes the 200-transaction Day Agent run feasible — without caching, the repeated system prompt tokens across 200 classification calls would exhaust the rate limit far faster.

The Night Agent processes far fewer transactions per run (only the suspicious subset), so the rate limit impact is lower and caching was not added to its direct API calls.

## How it works

The system prompt is marked once with `cache_control: ephemeral`. On the first call the prompt is cached; subsequent calls within the 5-minute TTL reuse the cache. The Anthropic API reports cache hits in the usage block (`cache_read_input_tokens`).

## TTL consideration

The cache TTL is 5 minutes. If the agent is paused (e.g. waiting on a rate-limit `retry-after`) for longer than 5 minutes, the next call will miss the cache and re-prime it. This is expected behaviour and handled automatically.

## Scope

Caching is applied in [[react-loop]] (`agents/loop.py`) inside `run_agent_loop`, which is used exclusively by the Day Agent. The Night Agent's per-transaction assessment calls and sub-agent call do not set `cache_control`.

## Related
- [[react-loop]]
- [[environment]]
