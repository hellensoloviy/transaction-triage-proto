---
tags: [concept, performance]
---

# Prompt Caching

Both agents send their system prompts with `cache_control: ephemeral` on every API call.

## Why it matters

Cached tokens do **not** count toward the ITPM (input tokens per minute) rate limit. On Tier 1, this is the primary mechanism that makes the 200-transaction Day Agent run feasible — without caching, the repeated system prompt tokens would exhaust the rate limit far faster.

## How it works

The system prompt is marked once with `cache_control: ephemeral`. On the first call the prompt is cached; subsequent calls within the 5-minute TTL reuse the cache. The Anthropic API reports cache hits in the usage block (`cache_read_input_tokens`).

## TTL consideration

The cache TTL is 5 minutes. If the agent is paused (e.g. waiting on a rate-limit `retry-after`) for longer than 5 minutes, the next call will miss the cache and re-prime it. This is expected behaviour and handled automatically.

## Scope

Both [[day-agent]] and [[night-agent]] use caching. The caching logic lives in [[react-loop]] (`agents/loop.py`) and is applied to the system prompt on every `client.messages.create()` call.

## Related
- [[react-loop]]
- [[environment]]
