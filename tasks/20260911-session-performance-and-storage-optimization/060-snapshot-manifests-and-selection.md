# Snapshot manifests and selected-snapshot efficiency

Make snapshot metadata and selection checks lightweight while preserving exact snapshot restore semantics.

## Requirements checklist

- [ ] **SNAP-001** Snapshot listing reads lightweight snapshot metadata and does not import complete snapshot message/native payloads.
- [ ] **SNAP-002** Snapshot-list latency is independent of total snapshot payload bytes within bounded filesystem enumeration costs.
- [ ] **SNAP-003** Validating the selected snapshot does not import the selected snapshot payload.
- [ ] **SNAP-004** A message-history request imports a selected snapshot at most once.
- [ ] **SNAP-005** Event polling performs no selected-snapshot payload import.
- [ ] **SNAP-006** Snapshot metadata includes enough identity and integrity information to detect missing, mismatched, or incomplete snapshot data.
- [ ] **SNAP-007** Snapshot restore publishes a complete coherent canonical session state and never exposes a mixed metadata/message/native state.
- [ ] **SNAP-008** Existing snapshots remain usable through compatibility handling or a documented migration.
- [ ] **SNAP-009** Snapshot creation and retention behavior remains explicit; any hard-link, copy-on-write, or generation reuse does not allow later session mutation to alter a snapshot.
- [ ] **SNAP-010** Tests cover listing, selection, event polling, restore, invalid selection recovery, legacy snapshots, and concurrent session publication.
- [ ] **SNAP-011** The shared benchmark demonstrates bounded metadata operations for large and numerous snapshots.

## Scope

In scope:

- Snapshot metadata manifests/indexes.
- Snapshot creation, listing, selected-snapshot validation, event-response fields, loading, restore, compatibility, and integrity checks.
- Alignment with the canonical JSON/JSONL session bundle and its publication identity.

Out of scope:

- General session read caching.
- Snapshot UI redesign.
- Unrelated session asset storage.

Parent Task: `tasks/20260911-session-performance-and-storage-optimization/000-main.md`

Depends On: `tasks/20260911-session-performance-and-storage-optimization/020-file-backed-session-storage.md`

## Requirement questions

- Is snapshot metadata one manifest per snapshot, a per-session index, or both?
- Can immutable canonical generations be referenced safely by snapshots, or must snapshot payloads always be copied?
- What integrity check is sufficient without hashing multi-hundred-megabyte content during ordinary listing?
- How are legacy monolithic snapshot files represented after migration?
- Should an invalid selected-snapshot read clear selection automatically, or report a recoverable state without mutating during a GET?

## Research details and suggested direction

The investigation found 225 snapshot files totaling about 3.77 GB. Listing one 94 MB snapshot took about 0.81 seconds, and listing two snapshots totaling about 234 MB took about 1.65 seconds despite sub-kilobyte responses. The current selected-snapshot flow can validate by full import multiple times and can repeat validation from event polling.

A lightweight manifest should hold snapshot ID, session ID, creation time, reason, source publication identity, storage-format version, and payload location/integrity metadata. Ordinary list and selection operations should use only this manifest.

Snapshot representation depends on the canonical file-backed storage decision, so this task intentionally omits an execution plan until Task 2 establishes that contract.