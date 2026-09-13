# Optimized file-backed session storage

Establish a reusable realistic session-performance benchmark first, then use
its evidence to plan and verify optimized file-backed session storage in a
later approved phase.

## Requirements checklist

- [ ] **FSS-001** The canonical file-backed session representation separates
  lightweight session metadata from append-oriented message data.
- [ ] **FSS-002** The canonical representation uses compact serialization and
  does not retain formatting whitespace that nearly doubles sampled session
  sizes.
- [ ] **FSS-003** Normal message appends do not require parsing and rewriting
  all earlier core messages.
- [ ] **FSS-004** Last-N and indexed message-range reads perform work
  proportional to the requested range plus bounded index/tail work rather than
  the complete session history.
- [ ] **FSS-005** Retained provider-native history has a defined efficient
  representation that does not force the lightweight session record to
  contain the complete native history.
- [ ] **FSS-006** Readers never observe a mixed session assembled from
  metadata and message/native files belonging to different published states.
- [ ] **FSS-007** Delete, modify, slice, restore, and other structural history
  operations produce a coherent canonical state and reclaim or compact
  obsolete records according to documented behavior.
- [ ] **FSS-008** A crash or interrupted append cannot make all previously
  published session data unreadable; incomplete trailing data has defined
  detection and recovery behavior.
- [ ] **FSS-009** Existing monolithic JSON sessions remain importable through
  a defined migration or lazy-conversion path.
- [ ] **FSS-010** Sessions remain exportable as portable single-file JSON with
  equivalent supported session content.
- [ ] **FSS-011** Session-list fields and message counts are available from
  lightweight metadata without importing message or native-history payloads.
- [ ] **FSS-012** Inactive request status can inspect a bounded tail of message
  records rather than importing complete history.
- [ ] **FSS-013** Storage format/version compatibility, migration failure,
  rollback, and backup behavior are covered by automated tests.
- [ ] **FSS-014** The shared benchmark demonstrates improved large-session
  range-read and append behavior without unacceptable regression for small
  sessions.
- [ ] **FSS-015** The benchmark fixture pool contains one complete turn from
  each of three to five randomly selected recent sessions under the
  repository-local `.crystal/sessions` root.
- [ ] **FSS-016** A seeded generator randomly mixes the fixture turns until it
  reaches at least 50, 100, 200, 400, or 800 core messages, stopping only at a
  complete turn boundary.
- [ ] **FSS-017** Generated benchmark sessions preserve valid core/native
  relationships and are reproducible from the fixture version, target message
  count, and random seed.
- [ ] **FSS-018** The reusable baseline measures direct session work, local
  HTTP message access, and an SDK-initiated session load/reload through
  `ChatController`, `RestAgentBackend`, and `FetchTransport`.
- [ ] **FSS-019** The baseline separately measures isolated reads,
  same-session concurrent reads, different-session concurrent reads, and
  reads overlapping a same-session single-message write.
- [ ] **FSS-020** Write benchmarks append exactly one message before saving;
  they do not model one provider turn as one atomic append.
- [ ] **FSS-021** Benchmark reports identify the fixture hash, target and
  actual core-message counts, operation boundary, concurrency, payload and
  file sizes, latency distribution, makespan, throughput, and validation
  result.

## Scope

### Current planning scope

This Draft covers only the shared fixture generator and performance baseline
required by FSS-015 through FSS-021. It does not authorize file-format,
storage, migration, locking, API, frontend, or bridge optimizations.

In scope:

- Randomly selecting three to five recent real sessions and one complete turn
  from each.
- Keeping the selected turn payloads as received, without placeholder
  replacement or synthetic-provider generation.
- Generating approximately 50, 100, 200, 400, and 800 core-message sessions by
  seeded random turn mixing.
- Direct Python store/application benchmarks.
- Local HTTP message-load and one-message-write benchmarks.
- SDK-initiated initial load and reload through the production frontend SDK.
- Same-session and different-session concurrent reads.
- Same-session reads overlapping one single-message write.
- A result format reusable by later storage, locking, message API, frontend,
  snapshot, diagnostics, and bridge tasks.

Out of the current planning scope:

- Selecting or implementing the optimized storage representation.
- Creating the persisted-storage specification.
- Migration, compaction, recovery, or rollback implementation.
- Locking changes.
- Frontend rendering or React Native component timing.
- Bridge transport timing or compression.
- Settings or UI-schema reload timing.
- Provider API calls or deterministic provider-plugin generation.

Parent Task:
`tasks/20260911-session-performance-and-storage-optimization/000-main.md`

Depends On:
`tasks/20260911-session-performance-and-storage-optimization/010-openai-usage-projection-and-response-mutation-probe.md`

## Requirement questions and decisions

- **Decision:** Do not replace selected session content with placeholders.
- **Decision:** Randomly select three to five recent sessions and one complete
  turn from each.
- **Decision:** Use a fixed reported seed for reproducibility even though
  selection and turn mixing are random.
- **Decision:** Generate by minimum core-message count, not serialized byte
  target.
- **Decision:** Standard targets are 50, 100, 200, 400, and 800 core messages.
- **Decision:** Stop after the complete turn that first reaches or exceeds the
  target; exact message counts are unnecessary.
- **Decision:** Benchmark writes append exactly one message.
- **Decision:** Include an SDK-driven reload baseline so later backend,
  transport, SDK, and frontend work can compare against the same scenario.
- **Decision:** Include both same-session and different-session concurrent
  reads so per-session locking can be distinguished from general CPU,
  allocation, filesystem, and HTTP contention.
- **Decision:** Current execution planning ends after baseline creation.
  Storage implementation will receive a separate Draft plan informed by the
  results.
- **Recommendation:** Use five selected sessions when five recent valid
  candidates exist; accept three or four only when complete-turn extraction
  rejects candidates.
- **Recommendation:** Use concurrency levels 1, 2, 4, and 8 for reads, with
  four as the default focused contention case.
- **Recommendation:** Measure both an ordinary write and a controlled
  250-millisecond write delay. The controlled case makes lock waiting visible
  and reproducible; it is not reported as ordinary persistence time.

## Research details

### Existing bottleneck boundaries

The current `FilesystemSessionStore` loads one complete pretty-printed JSON
file and imports the full `Session`. Saving writes the complete file, and the
application then reloads it.

The HTTP message route:

```text
GET /sessions/{session_id}/messages
```

acquires the process-local same-session lock, loads the complete session, and
only then applies the requested range. Therefore multiple same-session reads
currently serialize even though they do not mutate state.

An inactive request-status cache miss also loads the complete session.
Session-list cold resolution may load complete sessions when derived summaries
are not cached.

### SDK reload boundary

The production reload path is:

```text
ChatController.loadMessagesFromRangeText()
    -> ChatController.reloadMessages()
    -> RestAgentBackend.listMessages()
    -> FetchTransport.request()
    -> GET /sessions/{session_id}/messages
    -> JSON response decode
    -> ChatController state replacement
```

This measures more than session parsing. It includes server locking, file
read/import, message projection, response serialization, loopback HTTP
transfer, JavaScript JSON parsing, SDK normalization, and controller-state
replacement.

The benchmark should measure both:

- initial load into a new `ChatController`;
- repeated reload of the same range in the same controller.

Use last-50 as the primary reload scenario and retain full-history reload as a
separate diagnostic scenario. This allows later message-API and frontend work
to reduce transferred data without losing the original full-history baseline.

### Recent real-session diversity

A metadata-only inspection on September 12, 2026 found recent candidate
sessions with useful diversity:

| Candidate | Core/native messages | Structural value |
| --- | ---: | --- |
| `fbd34fa2…` | 190 / 348 | mixed text, custom tools, reasoning, and compaction |
| `7bbb9ff7…` | 53 / 84 | compact ordinary user/tool cadence |
| `dc533d63…` | 75 / 153 | one long tool-heavy turn with 58 calls/results |
| `b5c8008f…` | 341 / 672 | custom tools, web search, reasoning, and compaction |
| `be5e7d0a…` | 562 / 974 | broad mature-session mix with 312 tool results |

The implementation should perform a seeded random selection from the recent
eligible set instead of hard-coding these candidate IDs.

### Simple fixture composition

Each seed stores one complete user turn and its corresponding provider-native
records. A complete turn starts with a user message and continues through the
assistant, reasoning, tool-call, tool-result, phase, and final assistant
records before the next user message.

Generated sessions repeatedly choose one seed turn at random until the target
core-message count is met. Keep payloads unchanged. Apply only the minimum
structural adjustments required for a valid composed session:

- shift core `native_indices` by the generated native-history offset;
- include the system message once;
- recompute session-level message/native counts and native integrity.

Do not rewrite response IDs, call IDs, usage values, timestamps, prose, tool
results, or opaque provider values unless an actual import or integrity
failure proves a specific adjustment necessary.

### Benchmark layers

| Layer | Primary purpose |
| --- | --- |
| Store | Isolate JSON read/import and complete-file save/reload cost |
| Application | Include runtime/session resolution and derived service work |
| HTTP | Include locking, route handling, response serialization, and payload size |
| Frontend SDK | Include HTTP transfer, JavaScript parsing, normalization, and controller update |
| Concurrency | Distinguish serialized lock waiting from shared CPU/I/O contention |

The benchmark should preserve these separate measurements rather than expose
only one end-to-end number.

## Execution plan

Status: Draft

This plan covers the benchmark foundation only.

### 1. Select and store the seed turns

Add a small read-only extraction command under shared test infrastructure. It
will:

1. Enumerate recent canonical live sessions under a supplied session root.
2. Exclude malformed records, snapshots, conflict backups, and sessions
   without a complete user turn.
3. Use a supplied seed to randomly select five different sessions, accepting
   no fewer than three.
4. Use the same seeded generator to select one complete turn from each chosen
   session.
5. Store those turns as the compact fixture pool used by the benchmark.

Keep selected payloads unchanged. Perform only a simple inspection for obvious
credential patterns before committing the fixture files; do not introduce a
redaction or placeholder framework.

Record the selection seed, source file hashes, selected turn boundaries, core
and native record counts, and fixture-pool hash. Source-session naming or
hashing does not affect benchmark behavior.

### 2. Generate the five realistic session sizes

Create a deterministic fixture generator under `test/session_performance/`.
For each target in:

```text
50, 100, 200, 400, 800
```

start with one system message and repeatedly choose a seed turn using the
reported random seed. Append the complete turn and corresponding native slice.
Stop after the first complete turn that makes the core-message count at least
the target.

Rebase only native indices and session-level integrity/count fields. Validate
every generated session through `Session.from_dict`, portable
`AgentCore.import_session`/`export_session`, and the existing native-integrity
check.

Store generated sessions in a temporary or ignored benchmark workspace.
Generated full sessions are not committed. Save a small manifest containing
the fixture hash, target, actual core/native counts, generated file size, turn
sequence, and seed.

### 3. Add isolated Python and HTTP benchmarks

Use a fresh temporary session root for each measured run. Separate warmup from
recorded iterations.

Direct store/application scenarios:

1. full `FilesystemSessionStore.load`;
2. application `load_session_record`;
3. append one small user message and save;
4. append one representative large tool-result message and save;
5. last-50 load and slice through the current application behavior;
6. session-list cold and warm resolution;
7. inactive request-status cold and warm lookup;
8. portable session export.

Both write scenarios append one message only. Record file size before and
after, bytes added by the message, total bytes rewritten where measurable,
save time, application save-and-reload time, and returned payload size.

HTTP scenarios:

1. full message history;
2. last 50 messages;
3. one-message append;
4. session-list cold and warm request;
5. inactive request-status cold and warm request.

Use a real local FastAPI server. Record total request time, status, response
body bytes, returned message count, and server-side operation timing where it
can be collected by benchmark-only instrumentation without changing
production response contracts.

### 4. Add the SDK initial-load and reload baseline

Reuse the frontend SDK integration server harness and production:

- `FetchTransport`;
- `RestAgentBackend`;
- `ChatController`.

For every generated size, measure:

1. a new controller loading last 50 messages;
2. the same controller reloading last 50 messages;
3. a new controller loading full history;
4. the same controller reloading full history.

Record total duration, response bytes from a benchmark transport wrapper,
returned messages, controller messages after update, and JavaScript heap
change where the Node runtime provides a stable value.

Keep transport wrapping observational: it may time and count bytes, but it
must not replace parsing, normalization, or controller behavior.

### 5. Add concurrent read and write/read baselines

For read concurrency, run levels 1, 2, 4, and 8 against:

- the same session and same last-50 SDK reload path;
- different generated sessions of the same approximate size as a control.

Start requests behind one benchmark barrier. Record each request latency,
overall makespan, throughput, fastest/slowest completion, and the ratio between
same-session and different-session makespan.

For overlapping write/read behavior:

1. start one HTTP append of exactly one message;
2. begin four same-session last-50 SDK reloads while that write is active;
3. record write latency, each read latency, makespan, completion order, and
   errors;
4. repeat with a different-session read control.

Run this once with ordinary persistence and once with a benchmark-controlled
250-millisecond save delay. The controlled case must verify that the delay is
active before releasing the read barrier so the result reliably captures
lock waiting. Report controlled-delay results separately from ordinary
performance.

The benchmark is observational. It must not weaken or bypass the production
locking path to make the scenario pass.

### 6. Define and record the reusable baseline

Use one result schema for Python, HTTP, SDK, and concurrency scenarios. Each
record includes:

- benchmark and schema version;
- source fixture and generated-session hashes;
- random seed;
- target and actual core/native message counts;
- operation, layer, history range, and concurrency;
- warmup and measured iteration counts;
- median, minimum, maximum, and percentile latency;
- makespan and throughput where concurrent;
- request/response and on-disk bytes;
- success/error counts and validation result;
- runtime, OS, Python, Node, and relevant package versions.

Run all five target sizes for the baseline. Use enough repeated iterations for
stable medians without turning the benchmark into a long soak test. Commit a
small content-free baseline report so later tasks can compare against the same
fixture hashes and scenario keys.

Do not introduce pass/fail latency thresholds in this phase. The baseline
records current behavior. Later optimization tasks define acceptance ratios
against the applicable scenarios while retaining correctness assertions.

### 7. Add minimal benchmark verification

Add:

- one generator test proving deterministic random mixing, minimum target
  counts, complete-turn boundaries, and valid native indices;
- one small Python-runner smoke test using the 50-message fixture;
- one local integration test proving the SDK scenario reaches the real FastAPI
  route through `ChatController`, `RestAgentBackend`, and `FetchTransport`;
- one controlled concurrency test proving all reads are launched while the
  delayed write is active and that all results are reported.

Run existing focused session-store, message-route, SDK chat-controller, and
frontend SDK integration tests. The benchmark does not need provider API
coverage.

### Implementation decisions and open questions

- **Decision:** Use real recent session turns without placeholder replacement.
- **Decision:** Seeded random selection and mixing provide reproducibility
  without trying to model exact production distributions.
- **Decision:** Core-message counts, not bytes, define fixture sizes.
- **Decision:** Overshooting a target at a turn boundary is expected.
- **Decision:** Generated full sessions remain outside Git; the compact seed
  turns and content-free baseline report are committed.
- **Decision:** Adjust only native indices and session-level integrity/counts
  unless validation proves another adjustment necessary.
- **Decision:** Writes append exactly one message.
- **Decision:** The SDK reload is a first-class baseline, not an inference
  from Python or HTTP timing.
- **Decision:** Concurrent same-session reads and read/write overlap are part
  of the first baseline.
- **Decision:** Different-session concurrency is the control for identifying
  per-session serialization.
- **Decision:** No storage implementation or specification is part of this
  execution plan.
- **Recommendation:** Five source sessions, concurrency levels 1/2/4/8, and a
  separate 250-millisecond controlled-delay case are the default benchmark
  settings.
- **Open:** Choose the exact fixed selection/mixing seed during implementation
  and record it in the fixture manifest and report.

### Documentation

- Add a concise benchmark README beside `test/session_performance` with the
  fixture-generation and baseline commands, result fields, and guidance for
  reusing an existing generated workspace.
- Document that fixture turns contain real session content and must not be
  regenerated from a session root that contains sensitive data.
- Document ordinary and controlled-delay results separately.
- Update later performance subtasks to reference benchmark scenario keys
  rather than duplicating fixture or timing instructions.
- Do not create storage, locking, API, frontend, or bridge documentation in
  this benchmark-only phase.

### Task checklist

- [ ] Add recent-session candidate enumeration and seeded random selection.
- [ ] Select three to five source sessions and one complete turn from each.
- [ ] Inspect selected turns for obvious credential content.
- [ ] Add the compact real-turn fixture pool and fixture manifest.
- [ ] Add deterministic random turn mixing for 50/100/200/400/800 targets.
- [ ] Rebase native indices and recompute session integrity/counts.
- [ ] Validate every generated session through import/export and integrity
  checks.
- [ ] Add isolated store and application scenarios.
- [ ] Add HTTP full, last-50, one-message-write, list, and status scenarios.
- [ ] Add SDK initial-load and reload scenarios.
- [ ] Add same-session and different-session concurrent-read scenarios.
- [ ] Add ordinary and controlled write/read overlap scenarios.
- [ ] Add the shared result schema and content-free baseline report.
- [ ] Add the four minimal benchmark tests.
- [ ] Run focused Python and frontend SDK verification.
- [ ] Record baseline findings in implementation notes.
- [ ] Return with a separate storage implementation Draft informed by the
  baseline.

### Requirement verification

- **FSS-001 through FSS-013:** Not part of this benchmark-only execution plan;
  they remain incomplete for the later storage implementation plan.
- **FSS-014:** This phase establishes the baseline half of the before/after
  evidence. The requirement remains incomplete until storage optimization is
  implemented and remeasured.
- **FSS-015:** Fixture manifest records three to five different randomly
  selected recent source sessions and one complete turn boundary from each.
- **FSS-016 and FSS-017:** Generator tests and output manifests prove seeded
  mixing, minimum target counts, turn-boundary stopping, reproducibility, and
  valid core/native relationships.
- **FSS-018:** SDK integration verification and benchmark records prove the
  production SDK-to-HTTP reload path was exercised.
- **FSS-019:** Concurrency reports contain isolated, same-session,
  different-session, and write-overlap scenarios with synchronized starts.
- **FSS-020:** Write scenario inspection and fixture deltas prove exactly one
  message was appended per measured save.
- **FSS-021:** Result-schema validation proves every required identity,
  workload, timing, size, concurrency, and correctness field is present.

### Additional implementation verification

- Run focused `core/python` session-store, session-list, and request-status
  tests.
- Run focused `application/python` message-route and concurrency tests.
- Run `npm --workspace @crystal-lattice/frontend-sdk test`.
- Run the explicitly enabled local backend integration scenario rather than
  accepting a skipped integration test.
- Run Ruff, Black, Pyright, and TypeScript/Vitest checks over changed
  benchmark infrastructure.
- Inspect one generated 800-message session and one baseline report without
  printing or copying session content into task notes.