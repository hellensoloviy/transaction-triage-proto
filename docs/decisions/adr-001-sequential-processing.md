---
tags: [adr, performance]
---

# ADR-001 — Sequential Transaction Processing

## Decision

Both agents process transactions one at a time — one `get_transaction` call, one Claude assessment, one `set_transaction_status` call per transaction. No parallelism with `asyncio.gather()` or batch prompting.

## Alternatives considered

- **Batch assessment:** send multiple transactions in a single Claude prompt
- **Concurrent processing:** `asyncio.gather()` across transactions
- **Hybrid:** batch fetch, sequential classify

## Why sequential

1. **Failure isolation is simpler.** When each transaction is its own loop iteration, a failure on one has no effect on others. Batching means a single exception can corrupt the state of multiple transactions.

2. **Debugging is easier.** Sequential logs map 1:1 to transactions. Concurrent logs interleave in ways that are harder to trace.

3. **Sufficient at this scale.** 200 transactions run sequentially in 10–15 minutes on Tier 1. Performance optimisation was explicitly out of scope.

## Known cost

`MAX_ITERATIONS` is set high (80) to safely handle 200 transactions. With a more efficient batch design the ceiling could be lower and the intent clearer.

## If revisited

Smarter Day Agent batching (pre-classifying multiple transactions per Claude call) would reduce total API round-trips and let `MAX_ITERATIONS` be lowered. The Night Agent would need more care — its failure isolation policy assumes per-transaction granularity.

## Related
- [[day-agent]]
- [[night-agent]]
- [[failure-isolation]]
- [[environment]]
