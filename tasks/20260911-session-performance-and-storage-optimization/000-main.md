# Session performance and storage optimization

Improve session growth, persistence, concurrent access, reload behavior, snapshot handling, and bridge transfer efficiency without sacrificing session durability, conflict safety, or portable JSON import/export.

## Requirements checklist

- [ ] **SPSO-001** Session persistence avoids known superlinear metadata growth and supports efficient append, tail, and range access.
- [ ] **SPSO-002** Pure session reads can proceed concurrently and are not blocked while a writer prepares a replacement state.
- [ ] **SPSO-003** Session writes remain durable and conflict-aware across both in-process and cross-process concurrency.
- [ ] **SPSO-004** Initial frontend loads and later reloads avoid retransferring or recomputing unchanged messages, settings, and UI schemas.
- [ ] **SPSO-005** Snapshot listing, snapshot selection checks, session listing, and request-status lookup do not require importing unrelated large message payloads.
- [ ] **SPSO-006** Large bridge responses use an efficient body-transfer path and negotiated compression while retaining an explicit compatibility path.
- [ ] **SPSO-007** Conflict backups and repeated diagnostics do not pollute ordinary session discovery or create avoidable synchronous I/O.
- [ ] **SPSO-008** Every optimization has reproducible functional and performance evidence at its public or persistence boundary; realistic large-session fixtures are added within the first later optimization that needs them rather than as standalone benchmark work.
- [ ] **SPSO-009** Existing single-file JSON sessions remain importable, and sessions remain exportable as portable single-file JSON.

## Scope

This task coordinates work across the session store, application request/checkpoint lifecycle, HTTP API, frontend SDK and applications, snapshots, bridge transports, provider usage persistence, and diagnostics.

The intended canonical file-backed direction is a lightweight JSON session record plus JSONL/NDJSON message data. A later subtask may add SQLite as a secondary acceleration layer, but the file-backed representation remains the recoverable source of truth unless a separately approved requirement changes that boundary.

This task set does not itself authorize implementation. Each subtask must be reassessed and, where it contains an execution plan, approved before execution under the task workflow.

## Cross-cutting decisions and requirement questions

- **Decision:** The first subtask introduces a generalized persisted-session
  data policy, adopts it for OpenAI Responses, and sanitizes existing live
  sessions and snapshots. Realistic large-session fixture generation is
  deferred until a later optimization needs it and remains part of that
  optimization rather than a standalone benchmark task.
- **Decision:** Compact serialization alone is insufficient; the canonical storage task includes a lightweight JSON plus JSONL/NDJSON layout.
- **Decision:** The first concurrency task keeps reads lock-free and writers serialized with the smallest correctness mechanism practical. Historical version storage or general MVCC is not assumed.
- **Decision:** The previous parsed-session cache and advanced versioning work are combined into one later SQLite/cache task.
- **Question:** If SQLite-backed writes are acknowledged before the canonical files are published, is SQLite allowed to act as a durable pending-write journal, or must acknowledgements wait for file publication so SQLite remains strictly disposable?
- **Question:** Should hybrid bridge transport become the default after verification, or remain opt-in?
- **Question:** Which application UI schema inputs are static enough for revision caching, and which require a separate dynamic state response?

## Baseline findings

- Last-message latency across sampled sessions was approximately linear with file size: about 20.4 milliseconds per MB in a warm direct-HTTP run, with an observed coefficient of determination near 0.99.
- Mature last-50 responses were approximately 4.0-4.8 MB. One 4.81 MB response compressed to about 658 KB with gzip.
- Current message range handling imports the complete session before applying the requested range.
- Same-session message reads currently serialize behind an exclusive per-session lock, while different-session imports still contend for Python CPU, allocation, and filesystem resources.
- A successful checkpoint currently rewrites the complete JSON and then rereads the file while the writer lock remains held.
- Frontend chat activation can request the same session UI and application UI schemas more than once and can eagerly load additional settings endpoints.
- Snapshot listing currently imports complete snapshot files for metadata, and selected-snapshot checks can repeatedly import the selected snapshot.
- Conflict backups are safety-preserving, but storing them among live session JSON files creates avoidable discovery and diagnostic work.

## Subtasks

- [ ] `tasks/20260911-session-performance-and-storage-optimization/010-persisted-session-data-policy-and-sanitization.md`
- [ ] `tasks/20260911-session-performance-and-storage-optimization/020-file-backed-session-storage.md`
- [ ] `tasks/20260911-session-performance-and-storage-optimization/030-lock-free-reads-and-writer-serialization.md`
- [ ] `tasks/20260911-session-performance-and-storage-optimization/040-message-api-and-incremental-history.md`
- [ ] `tasks/20260911-session-performance-and-storage-optimization/050-settings-and-ui-schema-synchronization.md`
- [ ] `tasks/20260911-session-performance-and-storage-optimization/060-snapshot-manifests-and-selection.md`
- [ ] `tasks/20260911-session-performance-and-storage-optimization/070-conflict-backup-isolation.md`
- [ ] `tasks/20260911-session-performance-and-storage-optimization/080-sqlite-cache-and-write-coordination.md`
- [ ] `tasks/20260911-session-performance-and-storage-optimization/090-bridge-response-compression.md`
- [ ] `tasks/20260911-session-performance-and-storage-optimization/100-bridge-transport-policy.md`
- [ ] `tasks/20260911-session-performance-and-storage-optimization/110-warning-and-diagnostic-de-noising.md`

## Documentation and specification boundary

These task files record scope, approval, research, execution, and evidence. Persisted-data, concurrency, API, or bridge contracts that require a durable target must be added to the owning package or cross-package specification before implementation. Current user and implementation documentation must describe only delivered behavior and must not expose task identifiers or progress language.