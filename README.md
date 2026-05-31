# Transaction Triage System

A fintech compliance triage system built with two cooperating Claude agents, a custom MCP server, FastAPI, and Postgres. The Day Agent classifies incoming transactions in real time; the Night Agent reviews flagged items overnight and produces a morning report.

Built for the XBO AI Engineer take-home assignment.

---

## Quick start

```bash
git clone https://github.com/hellensoloviy/transaction-triage-proto
cd transaction-triage-proto

cp .env.example .env
# open .env and set ANTHROPIC_API_KEY

make up       # starts Postgres + FastAPI, installs dependencies
make seed     # seeds 200 deterministic transactions (seed=17)
make day-run  # Day Agent classifies all pending transactions
make night-run # Night Agent reviews suspicious items, writes morning report
make test     # runs pytest (61 tests)
make verify   # end-to-end verification suite — must exit 0
```

---

## ⚠️ Expected run times

The agents call the Anthropic API directly. Run times depend on your API tier.

| Command | Tier 1 | Tier 2 | Tier 3+ |
|---|---|---|---|
| `make day-run` (200 tx) | ~10–15 min | ~5–8 min | ~2–4 min |
| `make night-run` | ~5–8 min | ~2–3 min | ~1–2 min |
| `make verify` | ~3–5 min | ~2–3 min | ~1 min |

**This is expected behavior, not a bug.** The agents read the `retry-after` header on every 429 and wait exactly as long as the API instructs. You will see the agent pause and resume automatically — just let it run.

If you want to speed things up, increase `DAY_AGENT_BATCH_SIZE` or upgrade `MODEL_NAME` in `.env`.

---

## Architecture

```
CLI / Make targets
        │
        ├── Day Agent (agents/day.py)
        │       │  MCP stdio
        │       ▼
        │   MCP Server (mcp_server/server.py)
        │       │  HTTP
        │       ▼
        │   FastAPI (app/main.py) ── Postgres
        │
        └── Night Agent (agents/night.py)
                │  MCP stdio
                ▼
            MCP Server ── FastAPI ── Postgres
                │
                └── Report Sub-Agent (separate Claude call)
```

Agents never call FastAPI or Postgres directly. All data access goes through the MCP server. The MCP server is the only thing that calls FastAPI. FastAPI is the only thing that touches Postgres.

---

## Make targets

| Target | What it does |
|---|---|
| `make up` | Starts Postgres via Docker Compose, installs Python dependencies, starts FastAPI on port 8000 |
| `make down` | Stops Docker containers and kills the FastAPI process |
| `make seed` | Seeds 200 deterministic transactions including 8 poison cases (random seed=17) |
| `make day-run` | Runs the Day Agent — classifies all pending transactions as clean/suspicious/blocked |
| `make night-run` | Runs the Night Agent — reviews suspicious items, spawns report sub-agent, writes `reports/morning-report.md` |
| `make test` | Runs pytest (61 tests, ~2 seconds) |
| `make verify` | Seeds 8 poison cases, runs Night Agent, asserts all required behaviors — exits 0 on pass |
| `make clean` | Stops everything, removes Docker volumes, clears reports and caches |

---

## Project layout

```
app/
    main.py          — FastAPI service (data plane)
    database.py      — SQLAlchemy models and session setup
mcp_server/
    server.py        — Custom MCP server, 5 tools
agents/
    loop.py          — Shared ReAct tool-use loop (Anthropic SDK directly, no frameworks)
    day.py           — Day Agent
    night.py         — Night Agent + report sub-agent
seed/
    seeder.py        — Deterministic seeder (200 transactions, seed=17)
    poison_ids.txt   — Written by make seed, read by make verify
tests/
    test_agent_loop.py     — Loop imports, logging, configuration
    test_mcp_server.py     — MCP tool registration and integration
    test_night_agent.py    — Failure isolation, injection detection, status parsing
    verify.py              — End-to-end verification suite
reports/
    morning-report.md      — Written by Night Agent after each run
logs/
    agent_run.jsonl        — Structured JSONL log, one event per line
```

---

## Environment variables

All configuration is in `.env`. Copy `.env.example` to get started.

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | **Required.** Your Anthropic API key |
| `DATABASE_URL` | `postgresql://triage:triage_pass@localhost:5432/transaction_triage` | Postgres connection string |
| `MODEL_NAME` | `claude-sonnet-4-6` | Claude model to use |
| `MAX_TOKENS` | `4096` | Global max output tokens per API call |
| `DAY_AGENT_MAX_TOKENS` | `1024` | Day Agent output ceiling (responses are short) |
| `DAY_AGENT_BATCH_SIZE` | `50` | Transactions per batch for Day Agent |
| `MAX_ITERATIONS` | `80` | Safety ceiling on agent loop iterations |
| `MAX_RETRIES` | `5` | API call retries before giving up |
| `NIGHT_AGENT_CUTOFF_HOURS` | `72` | How far back Night Agent looks for suspicious transactions |
| `SEED_RANDOM_SEED` | `17` | Random seed for deterministic seeding |
| `SEED_TOTAL_TRANSACTIONS` | `200` | Total transactions to seed |
| `MCP_HTTP_TIMEOUT` | `30.0` | Timeout for MCP → FastAPI HTTP calls |

---

## MCP tools

The MCP server exposes 5 tools callable by both agents:

| Tool | Description |
|---|---|
| `list_transactions` | List transactions filtered by status and time window |
| `get_transaction` | Fetch one transaction by ID, including prior agent notes |
| `set_transaction_status` | Update status with a required reasoning note |
| `get_risk_metrics` | Aggregate counts, amounts, and top counterparties over a window |
| `write_report` | Save a markdown report to Postgres and `reports/` directory |

---

## Night Agent failure policy

The Night Agent never halts on a single bad transaction. For each item:

1. Try to fetch and assess the transaction
2. If any exception occurs — log the failure as a structured JSON event, call `set_transaction_status` with `needs-human-review`, continue to the next item
3. If even the status update fails — log that too and move on
4. Always produce a report at the end — even if every transaction failed, a partial report is emitted

This behavior is verified by `make verify`, which asserts that at least one `tool_call_failure` and one `skip_item` event appear in `logs/agent_run.jsonl` after the Night Agent runs.

---

## Known issues and gotchas

**Port 5432 conflict on `make up`**
If you have Postgres running locally (Homebrew or Postgres.app), Docker will fail to bind port 5432. Check with `lsof -i :5432` and stop the local instance before running `make up`.

```bash
# Homebrew
brew services stop postgresql@16

# Postgres.app — quit from the menu bar
```

**`make seed` asks before clearing**
If the database already has transactions, the seeder prompts before clearing. This is intentional — running `make seed` twice without answering `y` will leave the existing data intact.

**`make verify` clears the database**
The verify script wipes all transactions and seeds its own 8 poison cases before running. Don't run it mid-workflow if you want to keep your day-run data.

**Logs are cleared on each agent run**
`logs/agent_run.jsonl` is cleared at the start of every Day Agent or Night Agent run so `make verify` reads only the current run's events. Sub-agent logs are appended, not cleared.