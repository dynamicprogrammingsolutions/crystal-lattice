# Lock-free reads and writer serialization

Minimize session synchronization so pure reads never queue behind other reads or a writer preparing the next state, while preserving coherent publication and conflict-safe writes.

## Requirements checklist

- [ ] **SLC-001** Pure reads do not acquire the exclusive in-process session writer lock.
- [ ] **SLC-002** Multiple same-session readers can import or query the same published state concurrently.
- [ ] **SLC-003** A reader that begins while a writer is preparing a replacement can continue reading the currently published complete state without waiting for the writer.
- [ ] **SLC-004** A reader observes either the complete previously published state or the complete newly published state, never a partial or mixed state.
- [ ] **SLC-005** In-process writers targeting the same session are serialized through a writer-specific mechanism with well-defined ordering.
- [ ] **SLC-006** Cross-process writers coordinate through a lock file or another justified inter-process mechanism and detect stale baselines before publication.
- [ ] **SLC-007** Immediate read-modify-write operations and long-running requests that checkpoint seconds later use synchronization appropriate to their differing conflict windows.
- [ ] **SLC-008** A successful save/checkpoint does not reread and reparse the canonical state merely to return the state that was just persisted.
- [ ] **SLC-009** Message data, selected-snapshot identity, publication identity, and event cursor returned by a read describe one coherent state.
- [ ] **SLC-010** Concurrent write, history-edit, restore, and external-file-change scenarios cannot silently lose a committed state.
- [ ] **SLC-011** Automated concurrency tests cover read/read, read/write, write/write, long-running stale baseline, and cross-process conflict behavior.
- [ ] **SLC-012** The shared benchmark shows that same-session readers no longer serialize and that readers remain responsive during writer preparation.

## Scope

In scope:

- Per-session in-process synchronization in the application and event/session services.
- Writer preparation, stale-baseline checks, atomic publication, checkpoint cursor coordination, and removal of the post-save reread.
- Pure reads, immediate mutating actions, long-running request checkpoints, history modification, restore, and cross-process writes.

Out of scope:

- General historical version retention or user-visible version APIs.
- SQLite-backed cache/write coordination.
- Debounced write-behind acknowledgement semantics.

Parent Task: `tasks/20260911-session-performance-and-storage-optimization/000-main.md`

Depends On: `tasks/20260911-session-performance-and-storage-optimization/020-file-backed-session-storage.md`

## Requirement questions

- What is the smallest publication identity needed to pair the files and event cursor without introducing general MVCC?
- Which operations require a write-intent API from their first read, and which should use optimistic baseline comparison only at publication?
- Should in-process writer ordering be a mutex, a per-session queue/actor, or another mechanism?
- What lock-file ownership, timeout, stale-lock, and crash cleanup semantics are required for cross-process writers?
- How should a reader capture the published files so an atomic replacement does not invalidate the data it is currently consuming?

## Research details and suggested direction

The minimal model is not expected to retain historical versions. It will probably still need a current publication token or generation so a writer can prove that its baseline is still current and a reader can pair the session files with the correct cursor.

One candidate shape is:

```text
reader:
    capture published state identity and readable file handles/paths
    read and decode without writer locking

writer:
    serialize with other writers
    compare expected published identity
    build the next state in an unpublished location
    atomically publish the next state
```

Long-running provider/tool work must not retain a writer lock. Its checkpoint should reconcile against the latest published identity and either merge under established rules or produce a conflict result/backup.

The current message route reads some snapshot response fields before taking its exclusive lock. The replacement design should improve both concurrency and state coherence rather than merely deleting the lock.

This task changes concurrency and persistence semantics and therefore requires a durable owning or cross-package specification before implementation.