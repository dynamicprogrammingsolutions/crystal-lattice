# Requirements

Feature prefix: `RMAP`

These requirements track the implemented task-identity and synchronization
contract.

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| RMAP-001 | Every roadmap row has a required case-insensitively unique `task` identity and the source contains every required semantic header in any column order. | Implemented | Automated | Documented | `generate.py`, `test_generate.py` |
| RMAP-002 | A task is classified as an existing repository Markdown path, an existing task directory linked through the configured entry file, or a unique free task name without a link. | Implemented | Automated | Documented | `classify_task`, path/link tests |
| RMAP-003 | `external_id` is optional, user-managed, visible in generated Markdown, and may be shared by multiple tasks. | Implemented | Automated | Documented | shared and unique external-ID tests |
| RMAP-004 | `internal_id` is regenerated deterministically, persisted for editing, short, case-insensitively unique, and canonical for dependency references. | Implemented | Automated | Documented | ID normalization and collision tests |
| RMAP-005 | Dated paths under arbitrary repository directories, numeric subtasks, task directories, standalone tasks, free names, shared external IDs, and collisions follow deterministic generation rules. | Implemented | Automated | Documented | portable path, standalone, directory, free-name, and collision tests |
| RMAP-006 | Dependency input accepts canonical internal IDs, previous internal IDs, exact task values, and unique external IDs, then rewrites every reference to the canonical internal ID. | Implemented | Automated | Documented | alias normalization tests |
| RMAP-007 | Ambiguous shared external IDs, duplicate aliases, self-dependencies, duplicate dependencies, and dependencies at or below the current row are rejected before mutation. | Implemented | Automated | Documented | ambiguity and ordering tests |
| RMAP-008 | When regeneration changes an internal ID, dependencies using the previous ID are updated automatically on the CSV and synchronized sheet. | Implemented | Automated | Documented | stale-ID generator and pull normalization tests |
| RMAP-009 | Ordinary generation atomically normalizes CSV IDs and dependencies before Markdown generation, while check mode reports stale normalization without writing. | Implemented | Automated | Documented | generation/check tests |
| RMAP-010 | Generated Markdown colors primary IDs by derived readiness, renders arbitrary fields in source order, links task paths and directories, leaves free-task IDs unlinked, colors only blocking dependencies red, places External ID/Priority/Status after Dependencies, and points readers to the focused CSV update guide. | Implemented | Automated | Documented | Markdown generation tests, update guide, and generated release roadmap |
| RMAP-011 | Status normalizes both sides without mutation and distinguishes synchronization, normalization-only differences, substantive differences, and invalid aliases. | Implemented | Automated | Documented | `sync.py`, live synchronized status |
| RMAP-012 | Push normalizes local CSV and Markdown, writes dynamic normalized `RAW` source values only with `--write`, clears obsolete sheet values, verifies read-back equality, and refreshes presentation after the source width. | Implemented | Automated | Documented | dynamic push tests and live schema migration read-back |
| RMAP-013 | Pull normalizes remote aliases and arbitrary columns, updates local CSV and Markdown only with `--write`, writes canonical source data back to the sheet, verifies read-back equality, and refreshes managed presentation. | Implemented | Automated | Documented | dynamic pull and normalization tests |
| RMAP-014 | Invalid or empty remote tables cannot overwrite local files, and validation precedes every local or remote mutation. | Implemented | Automated | Documented | empty pull and header validation tests |
| RMAP-015 | The existing release CSV, generated Markdown, and Google Sheet migrate together from `key`/`main_id` to the normalized schema without losing task order, placeholders, IDs, dependencies, priorities, statuses, or arbitrary fields. | Implemented | Automated | Documented | migrated release files, live sheet read-back, synchronized status |
| RMAP-016 | Synchronization uses a self-contained named config, ignored roadmap dotenv file, and direct Google Sheets API client without depending on Crystal application or plugin source code, committing credentials or spreadsheet IDs, or exposing secret values and paths. | Implemented | Automated | Documented | `config.json`, `.env.example`, `requirements.txt`, `roadmap_config.py`, config tests, live Sheets API synchronization |
| RMAP-017 | Synchronization derives readiness and blocking dependency IDs immediately after the dynamic source width, colors done rows green, ready rows blue, queued rows purple, active rows orange, leaves blocked rows unformatted, preserves unrelated rules, and requires explicit user approval before an agent mutates the sheet. | Implemented | Automated | Documented | readiness tests, dynamic conditional-format tests, synchronization guide |
| RMAP-019 | Non-semantic CSV headers are arbitrary ordered fields preserved through normalization, Markdown, push, pull, and sheet read-back; generated presentation headers are reserved. | Implemented | Automated | Documented | arbitrary-field generator and synchronization tests |
| RMAP-020 | Dependency aliases that no longer match a row are removed with warnings while ambiguous, self, duplicate, overlapping, and incorrectly ordered dependencies remain errors. | Implemented | Automated | Documented | dependency cleanup and safety tests |
| RMAP-021 | Generator and synchronization source code derive repository roots, task entry files, path IDs, sheet widths, ranges, and formulas without depending on the configured roadmap name or Crystal Lattice task directory layout. | Implemented | Automated | Documented | portable path, config, column-letter, and temporary-project tests |

## Verification

- Focused roadmap unit tests cover task forms, path safety, deterministic IDs,
  external-ID sharing, collision suffixes, aliases, stale-ID rewriting,
  ambiguity, ordering, generation, check mode, and synchronization.
- The `release` CSV, generated Markdown, and Google Sheet were migrated
  together and verified through exact read-back.
- `generate --check release`, synchronized status, and pull dry run pass after
  migration.