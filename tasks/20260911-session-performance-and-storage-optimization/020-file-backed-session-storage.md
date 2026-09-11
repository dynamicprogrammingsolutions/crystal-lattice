# Optimized file-backed session storage

Replace the monolithic pretty-printed runtime session document with an efficient file-backed session bundle while retaining portable single-file JSON import and export.

## Requirements checklist

- [ ] **FSS-001** The canonical file-backed session representation separates lightweight session metadata from append-oriented message data.
- [ ] **FSS-002** The canonical representation uses compact serialization and does not retain formatting whitespace that nearly doubles sampled session sizes.
- [ ] **FSS-003** Normal message appends do not require parsing and rewriting all earlier core messages.
- [ ] **FSS-004** Last-N and indexed message-range reads perform work proportional to the requested range plus bounded index/tail work rather than the complete session history.
- [ ] **FSS-005** Retained provider-native history has a defined efficient representation that does not force the lightweight session record to contain the complete native history.
- [ ] **FSS-006** Readers never observe a mixed session assembled from metadata and message/native files belonging to different published states.
- [ ] **FSS-007** Delete, modify, slice, restore, and other structural history operations produce a coherent canonical state and reclaim or compact obsolete records according to documented behavior.
- [ ] **FSS-008** A crash or interrupted append cannot make all previously published session data unreadable; incomplete trailing data has defined detection and recovery behavior.
- [ ] **FSS-009** Existing monolithic JSON sessions remain importable through a defined migration or lazy-conversion path.
- [ ] **FSS-010** Sessions remain exportable as portable single-file JSON with equivalent supported session content.
- [ ] **FSS-011** Session-list fields and message counts are available from lightweight metadata without importing message or native-history payloads.
- [ ] **FSS-012** Inactive request status can inspect a bounded tail of message records rather than importing complete history.
- [ ] **FSS-013** Storage format/version compatibility, migration failure, rollback, and backup behavior are covered by automated tests.
- [ ] **FSS-014** The shared benchmark demonstrates improved large-session range-read and append behavior without unacceptable regression for small sessions.

## Scope

In scope:

- The canonical filesystem representation owned by the application session store.
- A lightweight JSON record plus JSONL/NDJSON or another justified record-oriented JSON-compatible message representation.
- Core messages, retained native history/provider state, session metadata, publication identity, compaction, migration, recovery, and portable export.
- Session list and request-status access paths that can use the lightweight record or bounded JSONL tail.

Out of scope:

- SQLite as a read cache or write coordinator.
- Frontend message DTOs and schema revision protocols.
- The detailed read/write locking implementation, except for defining the storage publication contract that the locking task consumes.

Parent Task: `tasks/20260911-session-performance-and-storage-optimization/000-main.md`

Depends On: `tasks/20260911-session-performance-and-storage-optimization/010-session-growth-and-benchmark-foundation.md`

## Requirement questions

- What exact data belongs in `session.json`, core message JSONL, native-history JSONL, and any provider-state file?
- Is publication represented by a manifest, a generation directory plus atomic current pointer, or another minimal mechanism?
- Does migration occur eagerly, lazily on first write, or through an explicit command?
- How are edited/deleted JSONL records compacted, and what threshold triggers compaction?
- Can retained native records be independently appended, or do provider integrity rules require grouped publication with core messages?
- Which lightweight presentation fields are authoritative in `session.json`, and which are derived during publication?

## Research details and suggested direction

A candidate bundle is:

```text
sessions/<session-id>/
    session.json
    messages.jsonl
    native_messages.jsonl
```

`session.json` can contain identifiers, agent/config/overrides, title/presentation fields, counts, small session-level metadata, and a current publication identity. Each complete JSONL record can represent one immutable message or provider-native entry.

Normal turns favor append. Structural history operations may write a compacted replacement log and publish it atomically. A generation/manifest design may provide cleaner multi-file publication than mutating several current files in place, but the task must compare its write amplification and cleanup costs against simpler append rules.

The portable single-file JSON format should remain an interchange representation. It does not need to remain the runtime layout.

JSONL tail reading can locate the latest relevant conversational state by scanning backward through complete records. A separate summary/tail database should not be introduced unless the shared benchmark shows this bounded approach is insufficient.

Because this changes persisted data, implementation should be preceded by an owning or cross-package persistence specification once ownership and overlap with existing session contracts are established and approved.