# Requirements

Feature prefix: `RMAP`

These requirements track the implemented task-identity and synchronization
contract.

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| RMAP-001 | Every roadmap row has a required case-insensitively unique `task` identity, and the normalized schema begins with `task`, `external_id`, and `internal_id`. | Implemented | Automated | Documented | `generate.py`, `test_generate.py` |
| RMAP-002 | A task is classified as an existing repository Markdown path, an existing task directory linked through `000-main.md`, or a unique free task name without a link. | Implemented | Automated | Documented | `classify_task`, path/link tests |
| RMAP-003 | `external_id` is optional, user-managed, visible in generated Markdown, and may be shared by multiple tasks. | Implemented | Automated | Documented | shared and unique external-ID tests |
| RMAP-004 | `internal_id` is regenerated deterministically, persisted for editing, short, case-insensitively unique, and canonical for dependency references. | Implemented | Automated | Documented | ID normalization and collision tests |
| RMAP-005 | Dated paths, numeric subtasks, task directories, standalone tasks, free names, shared external IDs, and collisions follow the specified deterministic generation rules. | Implemented | Automated | Documented | dated, standalone, directory, free-name, and collision tests |
| RMAP-006 | Dependency input accepts canonical internal IDs, previous internal IDs, exact task values, and unique external IDs, then rewrites every reference to the canonical internal ID. | Implemented | Automated | Documented | alias normalization tests |
| RMAP-007 | Ambiguous shared external IDs, duplicate aliases, unknown aliases, self-dependencies, duplicate dependencies, and dependencies at or below the current row are rejected before mutation. | Implemented | Automated | Documented | ambiguity and ordering tests |
| RMAP-008 | When regeneration changes an internal ID, dependencies using the previous ID are updated automatically on the CSV and synchronized sheet. | Implemented | Automated | Documented | stale-ID generator and pull normalization tests |
| RMAP-009 | Ordinary generation atomically normalizes CSV IDs and dependencies before Markdown generation, while check mode reports stale normalization without writing. | Implemented | Automated | Documented | generation/check tests |
| RMAP-010 | Generated Markdown links from the unwrapped internal-ID caption, renders the task title separately, links task directories to `000-main.md`, leaves free-task IDs unlinked, colors only blocking dependencies red, orders External ID/Priority/Status after Dependencies, and points readers to the focused CSV update guide. | Implemented | Automated | Documented | Markdown generation tests, update guide, and generated release roadmap |
| RMAP-011 | Status normalizes both sides without mutation and distinguishes synchronization, normalization-only differences, substantive differences, and invalid aliases. | Implemented | Automated | Documented | `sync.py`, live synchronized status |
| RMAP-012 | Push normalizes local CSV and Markdown, writes normalized `RAW` sheet values only with `--write`, clears only obsolete trailing rows, verifies read-back equality, and refreshes managed sheet presentation. | Implemented | Automated | Documented | push tests and live schema migration read-back |
| RMAP-013 | Pull normalizes remote aliases, updates local CSV and Markdown only with `--write`, writes canonical IDs and dependencies back to the sheet, verifies read-back equality, and refreshes managed sheet presentation. | Implemented | Automated | Documented | pull normalization tests and live pull dry run |
| RMAP-014 | Invalid or empty remote tables cannot overwrite local files, and validation precedes every local or remote mutation. | Implemented | Automated | Documented | empty pull and header validation tests |
| RMAP-015 | The existing release CSV, generated Markdown, and Google Sheet migrate together from `key`/`main_id` to the normalized schema without losing task order, placeholders, IDs, dependencies, priorities, statuses, or notes. | Implemented | Automated | Documented | migrated release files, live sheet read-back, synchronized status |
| RMAP-016 | Synchronization uses a self-contained named config, ignored roadmap dotenv file, and direct Google Sheets API client without depending on Crystal application or plugin source code, committing credentials or spreadsheet IDs, or exposing secret values and paths. | Implemented | Automated | Documented | `config.json`, `.env.example`, `requirements.txt`, `roadmap_config.py`, config tests, live Sheets API synchronization |
| RMAP-017 | Synchronization derives readiness and blocking dependency IDs in sheet columns K–L, colors done rows green, ready rows blue, queued rows purple, active rows orange, leaves blocked rows unformatted, preserves unrelated rules, and requires explicit user approval before an agent mutates the sheet. | Implemented | Automated | Documented | readiness tests, conditional-format tests, synchronization guide, live presentation read-back |

## Verification

- Focused roadmap unit tests cover task forms, path safety, deterministic IDs,
  external-ID sharing, collision suffixes, aliases, stale-ID rewriting,
  ambiguity, ordering, generation, check mode, and synchronization.
- The `release` CSV, generated Markdown, and Google Sheet were migrated
  together and verified through exact read-back.
- `generate --check release`, synchronized status, and pull dry run pass after
  migration.