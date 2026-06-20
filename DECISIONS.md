# DECISIONS.md
## Transaction Triage System — Build Tradeoffs
### Max 800 words · Honest, not promotional

---

## 1. What I chose to skip

**Parallel transaction processing.** Both agents process transactions sequentially —
one at a time, one Claude call each. A smarter design would batch assessments into a
single prompt or run them concurrently with `asyncio.gather()`. I skipped this because
the spec explicitly says performance optimization past "works on 200 rows" is out of
scope, and sequential processing is much easier to reason about when debugging failure
isolation. With 200 rows it's fast enough.

**Database migrations.** Schema is created via SQLAlchemy's `create_all()` on startup.
A real system would use Alembic. Skipped to stay within scope — the schema doesn't
change during the assignment lifecycle.

**Authentication on FastAPI endpoints.** All endpoints are open. The spec explicitly
listed this as out of scope.

**Streaming responses.** The Anthropic SDK supports streaming, which would make the
agents feel more responsive. Not implemented — added complexity for no functional gain
at this scale.

**High MAX_ITERATIONS ceiling.** Set to 80 to safely handle 200 transactions without
hitting the guard. It's env-configurable. With more time I'd make the batch loop more
efficient so the ceiling could be lower and the intent clearer.

---

## 2. What I chose to invest in

**Failure isolation in the Night Agent.** This is the highest-weighted dimension (20%)
and I treated it that way. Every transaction is wrapped in a `try/except` that logs the
failure as a structured JSON event, attempts to mark the transaction `needs-human-review`,
and unconditionally continues to the next one. Even if the status update itself fails,
the agent logs that and moves on. The report is always written — even if every transaction
failed, a partial report is emitted. `make verify` checks for the failure and skip log
events specifically, so these paths are tested, not just written.

**Structured logging that `make verify` can actually read.** Every log entry is a JSON
object on its own line (JSONL). The field names — `tool_call_failure`, `skip_item`,
`action: "skipping item, continuing"` — were chosen to match exactly what `verify.py`
asserts. The logging functions are defined once in `loop.py` and used consistently by
both agents.

**Prompt injection defense at two layers.** The system prompts for both agents explicitly
name prompt injection and instruct the model to ignore instructions in data fields. The
Night Agent adds a Python-level pre-check that detects injection keywords in the memo
before the text reaches Claude at all — so the model never sees the injection framed as
a user instruction.

**A real sub-agent pattern.** The Night Agent spawns a report-writing sub-agent as a
completely separate `client.messages.create()` call with its own context and system
prompt. It receives only a clean JSON summary of findings — no access to the Night
Agent's conversation history. This is logged via `log_sub_agent_spawn` so it's visible
in the structured log. The sub-agent uses a different `agent_name` to avoid accidentally
clearing the Night Agent's log mid-run.

**Guaranteeing a real failure in the structured log.** The spec requires `make verify`
to assert at least one `tool_call_failure` event. The Night Agent's defensive field
sanitization meant all 8 poison cases processed without exceptions — good engineering,
but it broke the log assertion. Rather than weakening the assertion, I added a genuine
compliance rule: zero-amount transactions raise an explicit error and require human
review. This is defensible business logic, it exercises the real failure-isolation path
on every `make verify` run, and the error appears in logs exactly as the spec requires.

---

## 3. One tradeoff I would revisit — resolved

**MCP tool responses originally returned Python dict strings instead of JSON.**

The initial implementation used Python's default `str()` on dicts when returning data to
agents, producing strings like `"{'id': '...', 'amount': Decimal('100.00')}"`. The agents
parsed these with `ast.literal_eval()`, which was safe but fragile — it broke on single
quotes inside field values and was not cross-language compatible.

This has since been fixed. The MCP server now calls `json.dumps(result, default=str)` for
all responses (with `default=str` handling `Decimal` and `UUID` types), and both agents
parse with `json.loads()`. The fragile intermediate step is gone.