---
tags: [ops, config]
---

# Environment Variables

All configuration is in `.env`. Copy `.env.example` to get started.

```bash
cp .env.example .env
# Edit .env — at minimum set ANTHROPIC_API_KEY
```

## Required

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key — required, no default |
| `DATABASE_URL` | Postgres connection string |

## Agent behaviour

| Variable | Default | Description |
|---|---|---|
| `MODEL_NAME` | `claude-sonnet-4-6` | Claude model for all agents |
| `MAX_TOKENS` | `4096` | Global output token ceiling per API call |
| `DAY_AGENT_MAX_TOKENS` | `1024` | Day Agent override — responses are short, no need for 4k |
| `DAY_AGENT_BATCH_SIZE` | `50` | Transactions fetched per batch by Day Agent |
| `MAX_ITERATIONS` | `80` | Hard ceiling on [[react-loop]] iterations |
| `MAX_RETRIES` | `5` | API call retries before giving up |
| `NIGHT_AGENT_CUTOFF_HOURS` | `72` | How far back Night Agent looks for suspicious transactions |

## Seeder

| Variable | Default | Description |
|---|---|---|
| `SEED_RANDOM_SEED` | `17` | Random seed for deterministic transaction generation |
| `SEED_TOTAL_TRANSACTIONS` | `200` | Total transactions to seed |

## Infrastructure

| Variable | Default | Description |
|---|---|---|
| `MCP_HTTP_TIMEOUT` | `30.0` | Timeout for [[mcp-server]] → FastAPI HTTP calls (seconds) |

## Related
- [[runbook]]
- [[react-loop]]
