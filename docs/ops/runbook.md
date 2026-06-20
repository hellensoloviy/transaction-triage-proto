---
tags: [ops]
---

# Runbook

## First-time setup

```bash
cp .env.example .env
# Set ANTHROPIC_API_KEY in .env

make up       # Starts Postgres via Docker Compose, installs deps, starts FastAPI on :8000
make seed     # Seeds 200 deterministic transactions (seed=17), including 8 poison cases
```

## Normal workflow

```bash
make day-run   # Day Agent classifies all pending transactions → clean/suspicious/blocked
make night-run # Night Agent reviews suspicious items, writes reports/morning-report.md
make test      # pytest (61 tests, ~2 seconds)
make verify    # End-to-end verification — must exit 0
```

## All make targets

| Target | What it does |
|---|---|
| `make up` | Starts Postgres (Docker), installs Python deps, starts FastAPI on port 8000 |
| `make down` | Stops Docker containers and kills the FastAPI process |
| `make seed` | Seeds 200 deterministic transactions including 8 poison cases |
| `make day-run` | Runs the Day Agent |
| `make night-run` | Runs the Night Agent, writes morning report |
| `make test` | Runs pytest (61 tests) |
| `make verify` | Seeds 8 poison cases, runs Night Agent, asserts all required behaviours |
| `make clean` | Stops everything, removes Docker volumes, clears reports and caches |

## Expected run times

| Command | Tier 1 | Tier 2 | Tier 3+ |
|---|---|---|---|
| `make day-run` (200 tx) | ~10–15 min | ~5–8 min | ~2–4 min |
| `make night-run` | ~5–8 min | ~2–3 min | ~1–2 min |
| `make verify` | ~3–5 min | ~2–3 min | ~1 min |

Rate limit pauses are expected — the agents read the `retry-after` header and wait exactly as instructed. Let them run.

---

## Gotchas

### Port 5432 conflict on `make up`

If Postgres is already running locally (Homebrew or Postgres.app), Docker will fail to bind port 5432.

```bash
lsof -i :5432          # identify what's holding the port

# Homebrew
brew services stop postgresql@16   # adjust version as needed

# Postgres.app — quit from the menu bar
```

### `make seed` prompts before clearing

If the database already has transactions, the seeder asks `"Clear and re-seed? (y/n)"` before wiping. This is intentional. For non-interactive use:

```bash
echo y | make seed
```

### `make verify` wipes the database

The verify script clears all transactions and seeds its own 8 poison cases before running the Night Agent. Do not run it mid-workflow if you want to keep day-run data.

### Logs are cleared on each primary agent run

`logs/agent_run.jsonl` is truncated at the start of every Day Agent or Night Agent run. Sub-agents append to the log rather than clearing it (they use a different `agent_name`).

### `make clean` removes all reports

`make clean` deletes everything in `reports/`. Copy any reports you want to keep before running it.

---

## Related
- [[environment]]
- [[log-format]]
- [[failure-isolation]]
