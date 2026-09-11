# Conflict-backup isolation and diagnostics

Preserve conflicting session work without allowing backup files to participate in normal session discovery, summary resolution, or repeated diagnostic failure.

## Requirements checklist

- [ ] **CONFLICT-001** New conflict backups are stored outside the live-session discovery namespace.
- [ ] **CONFLICT-002** Known legacy conflict-backup filename patterns are ignored by normal session discovery without parsing their complete payloads.
- [ ] **CONFLICT-003** A conflict backup records enough metadata to identify the session, request/operation, expected publication state, observed publication state, creation time, and reason.
- [ ] **CONFLICT-004** A genuine incompatible concurrent write preserves the non-published candidate state without overwriting the currently published session.
- [ ] **CONFLICT-005** Read-only requests cannot create conflict backups.
- [ ] **CONFLICT-006** Backup creation and conflict comparison work with both legacy monolithic sessions and the canonical file-backed session bundle during migration.
- [ ] **CONFLICT-007** Repeated session listing does not retry failed summary/import work for conflict backups or emit repeated session-ID mismatch diagnostics.
- [ ] **CONFLICT-008** Conflict diagnostics do not log complete large session payloads or secrets.
- [ ] **CONFLICT-009** Backup retention and cleanup are explicit and do not silently delete unresolved work.
- [ ] **CONFLICT-010** Tests cover in-process stale writes, cross-process/external changes, backup creation failure, legacy backup discovery, and ordinary reads.
- [ ] **CONFLICT-011** Shared benchmark/listing measurements show no live-session discovery cost attributable to isolated backups.

## Scope

In scope:

- Conflict detection output, backup paths, backup metadata, normal session discovery filters, diagnostics, migration compatibility, and retention boundaries.
- Both the current monolithic JSON path and the planned file-backed session bundle.

Out of scope:

- Automatic semantic merge beyond existing supported reconciliation.
- General session-history version browsing.
- A destructive cleanup policy for unresolved backups without separate approval.

Parent Task: `tasks/20260911-session-performance-and-storage-optimization/000-main.md`

Depends On: `tasks/20260911-session-performance-and-storage-optimization/010-session-growth-and-benchmark-foundation.md`

## Supporting details

Previous observation found four conflict backups totaling about 11.7 MB in the live session directory. Broad JSON discovery treated them as sessions, parsed them, rejected their embedded IDs, and emitted diagnostics. No conflict backups were present in the later observation, so the behavior is episodic but remains a structural risk.

Conflict backup creation is legitimate safety preservation. Placement among live sessions and repeated parsing are avoidable costs.

## Execution plan

Status: Draft

Introduce a dedicated conflict-backup namespace and a small metadata envelope. Update discovery so it enumerates only canonical live session records and cheaply excludes recognized legacy conflict filenames. Keep conflict creation on the incompatible-write path only.

Compatibility handling should leave existing backups intact. A non-destructive optional migration can be considered, but moving user files is not required merely to stop discovery from parsing them.

### Implementation decisions and open questions

- Select the owning backup directory and metadata naming convention without placing backups back into live discovery.
- Decide whether a backup contains a portable single-file export, a copied session bundle, or both during migration.
- Define retention visibility and user recovery entry points before adding any automated cleanup.
- Coordinate multi-file backup capture with the canonical publication contract from the storage task.

### Documentation

- Document conflict backup location, recovery, and retention in the owning application user or troubleshooting documentation when the behavior is delivered.
- Document discovery exclusions and diagnostic metadata in owning development documentation.
- Do not expose task identifiers or internal progress in user documentation.

### Task checklist

- [ ] Add regression fixtures for legacy conflict filenames in the live directory.
- [ ] Add a dedicated conflict-backup path and metadata envelope.
- [ ] Update live-session discovery to avoid parsing backup files.
- [ ] Preserve incompatible candidate state on genuine conflicts.
- [ ] Ensure ordinary reads cannot enter backup creation.
- [ ] Cover legacy and file-bundle backup representations.
- [ ] Add bounded, non-sensitive diagnostics.
- [ ] Define retention/recovery behavior without destructive cleanup.
- [ ] Run session listing, conflict, and shared benchmark verification.
- [ ] Update applicable documentation and evidence.

### Requirement verification

- **CONFLICT-001 through CONFLICT-003:** Inspect created backup paths and metadata after a deterministic conflict.
- **CONFLICT-004 through CONFLICT-006:** Exercise stale in-process and external/cross-process writes against both supported storage generations.
- **CONFLICT-005:** Run concurrent and repeated read-only requests and verify no backup creation.
- **CONFLICT-007 and CONFLICT-011:** Place legacy backups in the fixture directory, run repeated session listing, and verify zero backup imports and stable latency.
- **CONFLICT-008:** Inspect captured logs for bounded metadata only.
- **CONFLICT-009:** Verify documented recovery/retention behavior and absence of unapproved deletion.
- **CONFLICT-010:** Run the owning automated conflict/discovery suites.

### Additional implementation verification

- Simulate backup-write failure and confirm the published session remains intact.
- Verify session-list cache invalidation does not enqueue isolated backups.
- Verify application startup with legacy backups does not generate a repeated diagnostic storm.