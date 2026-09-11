# Session growth reduction and benchmark foundation

Establish the reusable session-performance benchmark while removing repeated cumulative provider usage data that causes disproportionate session growth.

## Requirements checklist

- [ ] **SGF-001** A reusable benchmark fixture generator and runner is established within this task rather than as a separate task.
- [ ] **SGF-002** Benchmark fixtures cover representative small, medium, large, and very large sessions, including tool-heavy messages, retained native history, usage metadata, and ordinary conversations.
- [ ] **SGF-003** The benchmark reports cold and warm import latency, last-message and last-50 latency, save/checkpoint latency, response payload size, and concurrency behavior; CPU and peak memory are reported where the environment supports reliable collection.
- [ ] **SGF-004** Subsequent subtasks can reuse the same fixtures, commands, and result format without copying benchmark logic.
- [ ] **SGF-005** Persisted provider usage retains the compact token, cost, and attribution summary required by supported UI and accounting behavior.
- [ ] **SGF-006** Cumulative raw usage attribution is not duplicated into every later core message and retained native-history entry.
- [ ] **SGF-007** Repeated comparable turns produce approximately linear persisted-session growth rather than growth driven by repeated copies of prior attribution data.
- [ ] **SGF-008** Existing supported usage and cost presentation remains functionally equivalent after compaction.
- [ ] **SGF-009** Regression tests cover both newly produced sessions and import/use of existing sessions containing the older expanded usage representation.
- [ ] **SGF-010** Benchmark results record the before/after effect of the usage-persistence change and provide evidence for the parent requirements they support.

## Scope

In scope:

- OpenAI Responses provider usage capture and its usage extension.
- Core and native-history metadata written by those components.
- Consumers that display or calculate supported token, cost, and attribution summaries.
- Reusable local benchmark fixtures and runners for the complete task directory.
- Focused regression tests and owning package documentation affected by the delivered behavior.

Out of scope:

- The canonical JSON/JSONL storage layout.
- General message wire projection.
- SQLite caching.
- Lock redesign beyond any narrow adjustment strictly necessary to benchmark existing behavior.

Parent Task: `tasks/20260911-session-performance-and-storage-optimization/000-main.md`

## Supporting details

The investigation found large cumulative `usage.attribution.items` structures persisted repeatedly in assistant-message metadata, phase messages, and retained provider-native history. The benchmark should distinguish file-byte growth from message count and should include a deterministic fixture capable of reproducing this pattern without hosted-provider credentials.

In the sampled `be5e...` session, 419 persisted `usage` objects contained attribution data. The largest attribution list had 973 entries, and one serialized `usage` object was about 177 KB. The attribution list grew with later responses and was copied into both public/core and retained native metadata.

Current repository consumers use bounded token, cost, auth-mode, service-tier, reasoning-mode, and turn-cumulative fields. Consumer tracing found no runtime use of `usage.attribution` or `usage.attribution.items`. Existing unit tests assert the raw `usage` mapping for bounded token fixtures but do not establish unbounded attribution history as a supported contract.

The usage extension already receives raw response usage long enough to calculate cost, ChatGPT cached-token estimates, and cumulative fields. A bounded persisted projection can therefore be produced after those calculations without removing request-local information prematurely.

The benchmark is production test infrastructure. It should use public session-store and HTTP/application boundaries where those are the behavior under measurement, and it should avoid test-only shortcuts that bypass import, persistence, or response serialization.

## Execution plan

Status: Draft

Create a reusable deterministic benchmark under `test/session_performance/`, capture a reproducible baseline for expanded usage persistence, then replace persisted raw usage with a bounded projection while preserving the supported normalized token/cost behavior.

Do not register this as an `evaluations/` benchmark: that package owns model/task evaluation through `AgentApplication`, while this work is deterministic cross-package performance test infrastructure. Do not put the shared runner in the existing OpenAI Responses model benchmark directory either; later storage, locking, HTTP, frontend, and bridge subtasks must reuse it without depending on a provider-specific benchmark package.

The benchmark should generate sessions into a temporary/output directory from semantic profiles rather than commit large session files. Initial profiles should include:

- ordinary text history;
- tool-heavy core and native history;
- bounded usage metadata;
- pathological cumulative attribution growth.

The full benchmark should support approximate 1, 10, 50, 100, and 250 MB targets. Automated tests should use a small smoke profile; the large matrix is an explicit benchmark command rather than a default unit-test burden.

Measure wall time with a monotonic high-resolution clock, process CPU separately, serialized byte sizes directly, and peak memory through a supported process metric. Define “cold” as a fresh benchmark subprocess and “warm” as repeated operations in one process; do not claim the kernel filesystem cache was dropped unless the runner actually controls it.

Exercise the public persistence and application/HTTP boundaries relevant to each metric. The runner should emit machine-readable JSON or JSONL records containing environment, profile, actual file size, operation, iteration, wall/CPU time, payload bytes, and memory observations, plus a concise human-readable summary.

In the OpenAI Responses usage extension, introduce one bounded persisted-usage projection used for both native `_metadata` and public/core message metadata. The projection should retain the scalar token totals and recognized bounded detail counters needed for:

- prompt, cached-read, cache-write, completion, reasoning, and total tokens;
- cost estimation and cumulative cost;
- ChatGPT cached-token estimation;
- existing OpenRouter-compatible usage presentation.

Raw provider usage remains available only during processing. Unbounded provider attribution payloads, including `attribution.items` and `attribution.request_fields`, should not be copied into persisted usage metadata unless a traced supported consumer proves that a bounded field is required. Do not add a new public attribution schema merely to preserve unused raw data.

Existing expanded sessions remain readable. This subtask should stop new cumulative duplication but should not introduce a bulk migration or rewrite old history; canonical storage migration and compaction belong to the later storage task. When an old usage mapping participates in a new request, calculations continue to read its recognized token/detail fields while new persisted usage uses the bounded representation.

Verify native compaction compatibility because its cached-token and cost behavior reads retained native usage metadata. The native-compaction protocol and canonical native-history requirements remain unchanged; only unbounded response-only usage attribution is removed.

### Implementation decisions and open questions

- **Recommendation:** Place the reusable runner and generated-fixture helpers under `test/session_performance/`; keep provider-specific regression tests under `plugins/openai_responses/tests`.
- **Recommendation:** Persist a bounded token/detail `usage` mapping and the existing derived metadata fields; omit unbounded attribution data after current-response calculations.
- **Recommendation:** Preserve compatibility reads for old expanded mappings but defer bulk/lazy historical compaction to the canonical storage task.
- Confirm whether any external consumer outside this repository relies on raw `metadata.usage.attribution`; no in-repository consumer was found.
- Decide whether unknown future scalar/detail usage fields are retained through a bounded generic rule or require an explicit allowlist. The rule must reject unbounded nested lists/maps.
- Decide the exact optional HTTP benchmark mode: an isolated production FastAPI app on a temporary port or an ASGI test client plus a separately labeled live-HTTP mode. Results must state the boundary actually measured.

### Documentation

- Update the OpenAI Responses cost-estimation development page to state that persisted usage retains bounded accounting fields and does not retain unbounded provider attribution history.
- Add a concise benchmark README under the selected `test/session_performance/` owner with commands, metric definitions, fixture profiles, and the cold/warm distinction.
- Update current provider/plugin user documentation only if supported usage fields or presentation change; no user-facing change is expected from removing unused raw attribution.
- Keep benchmark results and task evidence in development/test records rather than public user guides.

### Task checklist

- [ ] Record the completed in-repository usage consumer trace and confirm the bounded persisted field set.
- [ ] Add deterministic fixture profiles and benchmark tests under `test/session_performance/`.
- [ ] Add the reusable benchmark command and machine-readable result schema.
- [ ] Capture a before-change baseline for growth, import, last-message, last-50, save/checkpoint, payload, concurrency, CPU, and memory metrics supported by the runner.
- [ ] Add a provider regression fixture whose cumulative attribution list grows on each response.
- [ ] Add assertions covering public/core metadata, retained native metadata, phase/checkpoint persistence, and serialized session growth.
- [ ] Implement one bounded persisted-usage projection after raw-usage calculations.
- [ ] Preserve cost, token, ChatGPT cache estimation, turn accounting, and native compaction behavior.
- [ ] Preserve compatibility when loading and continuing an existing expanded session.
- [ ] Run focused OpenAI Responses unit and non-API integration suites.
- [ ] Run relevant core/application persistence tests and one real frontend usage-presentation consumer test.
- [ ] Run the benchmark again and record directly comparable results.
- [ ] Update applicable development documentation and requirement evidence.

### Requirement verification

- **SGF-001 through SGF-004:** Run the benchmark smoke tests and the documented full command from a clean checkout; inspect generated JSON/JSONL records for every required metric and profile.
- **SGF-005 and SGF-008:** Verify bounded `metadata.usage`, formatted fields, cumulative totals, ChatGPT estimates, and cost presentation through provider/application tests and at least one production frontend presentation consumer.
- **SGF-006:** Inspect persisted core messages, phase/checkpoint data, and native history after the pathological fixture; no new entry may contain cumulative attribution history.
- **SGF-007:** Compare repeated-turn serialized-byte growth and report per-turn increments or a fitted trend demonstrating removal of attribution-driven superlinear growth.
- **SGF-009:** Load an existing-format expanded fixture, calculate the next turn correctly, persist the next turn in bounded form, and retain old history without failure.
- **SGF-010:** Attach before/after benchmark summaries and machine-readable result locations to completion evidence.

### Additional implementation verification

- Run `pytest plugins/openai_responses/tests -q`.
- Run focused core/application persistence and HTTP tests selected by the implementation boundary.
- Run the frontend SDK presentation test that resolves usage metadata paths.
- Run hosted provider verification only if local deterministic coverage cannot establish the provider response shape; a skipped API test is not evidence.
- Confirm native compaction unit/integration coverage still passes because it consumes retained native usage fields.
- Confirm benchmark commands collect the intended cases rather than silently skipping gated scenarios.