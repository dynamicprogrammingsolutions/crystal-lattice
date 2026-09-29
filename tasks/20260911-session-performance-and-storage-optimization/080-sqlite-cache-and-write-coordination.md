# SQLite cache and coordinated write pipeline

Evaluate and, if justified, add a rebuildable SQLite acceleration layer for parsed session reads and in-process write coordination while retaining the JSON/JSONL session bundle as the recoverable canonical representation.

## Requirements checklist

- [ ] **SCACHE-001** The task records a benchmark-backed go/no-go decision after optimized file storage and minimal locking are measured.
- [ ] **SCACHE-002** If SQLite is introduced, its read cache can be deleted and rebuilt from canonical JSON/JSONL data without losing published session state.
- [ ] **SCACHE-003** Cached data is accepted only when its canonical publication identity and source fingerprint still match.
- [ ] **SCACHE-004** Concurrent cache misses for one unchanged session are single-flighted so canonical data is imported once.
- [ ] **SCACHE-005** Cached range, tail, metadata, and request-status reads avoid canonical JSON/JSONL parsing when the cache is valid.
- [ ] **SCACHE-006** Cache memory/disk growth, eviction, compaction, and startup rebuild behavior are bounded and observable.
- [ ] **SCACHE-007** In-process writes use one ordered per-session coordination path while readers continue using the last committed cache state.
- [ ] **SCACHE-008** Cross-process writers still use the canonical publication lock and compare expected versus observed publication identity before publishing.
- [ ] **SCACHE-009** External canonical-file changes invalidate or rebuild affected cache entries without trusting mtime alone.
- [ ] **SCACHE-010** The durability boundary for debounced/write-behind work is explicitly selected and tested: either acknowledgement waits for canonical publication, or SQLite is a durable replayable pending-write journal until publication.
- [ ] **SCACHE-011** A crash between cache commit and canonical publication has defined recovery behavior with no silent loss of acknowledged writes.
- [ ] **SCACHE-012** Debouncing/coalescing does not omit semantically required checkpoints, user messages, final responses, or externally observed committed state.
- [ ] **SCACHE-013** SQLite corruption or schema incompatibility degrades to safe cache rebuild or an explicit recoverable error without damaging canonical files.
- [ ] **SCACHE-014** The shared benchmark demonstrates material additional benefit beyond optimized JSONL and lock-free reads before SQLite becomes a required runtime dependency.

## Scope

In scope:

- Benchmark-backed decision on adding SQLite.
- SQLite schema, source fingerprints, publication identity, single-flight import, cache invalidation, range/tail reads, bounded storage, and per-session in-process writer coordination.
- Optional checkpoint coalescing and durable pending-write replay if explicitly selected.
- Cross-process interaction with canonical lock files and external file changes.

Out of scope:

- Replacing the JSON/JSONL bundle as the portable and recoverable canonical representation.
- General historical session browsing or user-facing version APIs.
- Unbounded write-behind that can lose acknowledged work.

Parent Task: `tasks/20260911-session-performance-and-storage-optimization/000-main.md`

Depends On:

- `tasks/20260911-session-performance-and-storage-optimization/020-file-backed-session-storage.md`
- `tasks/20260911-session-performance-and-storage-optimization/030-lock-free-reads-and-writer-serialization.md`

## Requirement questions

- Must SQLite remain strictly disposable, requiring canonical publication before acknowledgement?
- If acknowledgement may precede file publication, is SQLite approved as a durable pending-write journal and temporary recovery authority?
- Which publication revision, inode, size, nanosecond mtime, and optional hashes make up the source fingerprint?
- Is one global database, one database per session, or a sharded database the correct operational boundary?
- Which checkpoints are safe to coalesce, and which are externally meaningful commits?
- How is cache schema migration handled across application versions?
- What cache rebuild work is allowed in the foreground versus a bounded background worker?

## Research details and suggested direction

Two operating modes are credible:

1. **Cache-only:** acknowledgement waits for canonical publication. SQLite accelerates reads and preparation but is always disposable.
2. **Durable write-behind:** a committed SQLite row is a replayable pending write until JSON/JSONL publication. This improves perceived write latency but makes SQLite temporarily authoritative for acknowledged state.

The task must not describe durable write-behind as a mere cache. If the source-of-truth constraint is strict, start with cache-only mode and limit coalescing to intermediate checkpoints that are not acknowledged as durable public state.

File attributes can supplement but should not replace an explicit canonical publication identity. Rapid replacement, restoration, and multi-file bundles can defeat mtime-only assumptions.

A per-session in-process writer queue may update committed cache state quickly while one worker serializes canonical publication. Readers should use the latest state whose durability classification is clear.

This is a material persistence and durability design. It intentionally has no execution plan until the earlier benchmark evidence exists and the durability requirement question is answered.