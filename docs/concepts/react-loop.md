---
tags: [concept, implementation]
---

# ReAct Loop

**File:** `agents/loop.py`

Shared tool-use loop used by both the [[day-agent]] and [[night-agent]]. Written directly against the Anthropic SDK — no LangChain, no LlamaIndex, no agent frameworks.

## What it does

1. Sends a message to Claude
2. Receives a response — either text (done) or `tool_use` blocks (act)
3. Executes each requested tool via the [[mcp-server]]
4. Appends `tool_result` blocks to the message history
5. Loops back to step 1 until Claude stops calling tools or `MAX_ITERATIONS` is hit

## Structured logging

Every step is logged as a JSONL event. See [[log-format]] for the schema.

## Retry / rate limiting

Uses exponential backoff on API errors. On 429s, reads the `retry-after` header and waits exactly as long as the API instructs — no fixed sleep, no guessing.

## Tool-use / tool-result pairing — critical invariant

The Anthropic API requires every `tool_use` block to have a matching `tool_result` in the very next message. Two failure modes:

**Truncated response (`max_tokens` hit mid-call):** The loop detects `tool_use` blocks in the `max_tokens` branch and executes them before continuing — so no call goes unmatched.

**Exception mid-loop:** Any exception that would skip appending a result corrupts message history. The loop runs a sanity check after each turn and patches in a fallback error result for any `tool_use` ID that has no matching result.

## Prompt caching

System prompts are sent with `cache_control: ephemeral`. Cached tokens don't count toward ITPM. See [[prompt-caching]].

## Configuration

| Variable | Default | Effect |
|---|---|---|
| `MAX_ITERATIONS` | 80 | Hard ceiling on loop turns |
| `MAX_RETRIES` | 5 | API call retries before giving up |
| `MODEL_NAME` | `claude-sonnet-4-6` | Claude model |
| `MAX_TOKENS` | 4096 | Global output token ceiling |
| `DAY_AGENT_MAX_TOKENS` | 1024 | Day Agent override (responses are short) |

## Related
- [[day-agent]]
- [[night-agent]]
- [[log-format]]
- [[environment]]
