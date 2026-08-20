# Technical specification

## Data model

The normalized CSV and Google Sheets column order is:

```csv
task,external_id,internal_id,title,purpose,priority,status,declared_dependencies,inferred_dependencies,notes
```

| Column | Authority and constraints |
|---|---|
| `task` | Authored identity. Required and unique case-insensitively after path normalization. |
| `external_id` | Optional authored identifier. May be shared by multiple tasks. |
| `internal_id` | Generated and persisted identifier. Required after normalization and unique case-insensitively. |
| `title` | Required authored display title. |
| `purpose` | Required authored roadmap-level outcome. |
| `priority` | `must have`, `should have`, or `good to have`. |
| `status` | `pending`, `in progress`, `review`, or `done`. |
| Dependency columns | Authored aliases on input; canonical internal IDs after normalization. |
| `notes` | Optional authored context. |

`task` replaces the current `key` as row identity. `external_id` replaces the
external-identifier part of `main_id`. `internal_id` replaces generated display
IDs and becomes the canonical dependency vocabulary.

## Task classification

Classification is ordered. The first matching form wins.

### Markdown path

A repository-relative value ending in `.md` is a Markdown task path.

Rules:

- resolve the path against the repository root;
- reject absolute paths;
- reject traversal outside the repository;
- require an existing regular Markdown file;
- preserve the normalized repository-relative path in the CSV;
- link the generated Markdown task title directly to the file.

A free name ending in `.md` is therefore interpreted as a path and must exist.

### Task-directory path

A repository-relative value under `tasks/` without a `.md` suffix is a task
directory.

Rules:

- accept an optional trailing slash and normalize it away;
- reject absolute paths and traversal outside the repository;
- require an existing directory;
- require an existing regular `000-main.md`;
- preserve the normalized directory path in the CSV;
- link the generated Markdown task title to `<task>/000-main.md`.

A free name beginning with `tasks/` is therefore interpreted as a task path and
must satisfy these rules.

### Free task name

Every other nonempty value is a free task name.

Rules:

- trim surrounding whitespace;
- require case-insensitive uniqueness;
- generate no repository link;
- permit spaces and punctuation useful for a human-readable placeholder;
- use the normalized complete value as the input to internal-ID generation and
  collision handling.

## Internal ID generation

Generation always ignores the entered `internal_id` as an authority. The
entered value is retained temporarily as an alias so existing references can
be migrated.

Canonical internal IDs:

- use uppercase ASCII letters, digits, and hyphens;
- contain no empty segments;
- are compared case-insensitively;
- must be unique after generation;
- are regenerated on ordinary generation and every synchronization operation.

### Dated task directories

For:

```text
tasks/YYYYMMDD-<slug>/<NNN>-<subtask>.md
```

the base is:

1. normalized `external_id`, when present; otherwise
2. `MMDD-XX`, where `XX` is formed from the first letters of the first two
   alphanumeric parent-slug words.

Append `NNN` unless the file is `000-main.md`.

Examples:

```text
20260804-open-source-public-release/040-...md -> 0804-OS-040
external_id CL-368                         -> CL-368-040
20260804-open-source-public-release/000-main.md -> 0804-OS
```

### Task-directory rows

Use the same parent base without a numeric suffix:

```text
tasks/20260804-open-source-public-release -> 0804-OS
external_id CL-368                       -> CL-368
```

### Dated standalone Markdown

For:

```text
tasks/YYYYMMDD-<slug>.md
```

use normalized `external_id` when present. Otherwise use `MMDD-XX` from the
first two slug words.

### Free names

Without an external ID, tokenize the free name into alphanumeric words and use
up to the first three uppercase characters of each of the first two words:

```text
website-ios-review  -> WEB-IOS
App Store screenshots -> APP-STO
```

With an external ID, use the normalized external ID as the first candidate.

### Collision disambiguation

First use an available numeric subtask prefix. If candidates still collide,
append the first four uppercase hexadecimal characters of the SHA-256 digest
of the normalized complete `task` value:

```text
WEB-IOS-7A3F
```

Hash suffixes are added only when needed. A remaining collision after the hash
suffix is an error rather than a reason to lengthen IDs unpredictably.

Shared external IDs are valid. Their internal IDs remain unique through numeric
subtask prefixes or deterministic task-derived collision suffixes.

## Alias and dependency resolution

Before regeneration, retain each nonempty entered `internal_id` as that row's
previous internal-ID alias.

After generating canonical IDs, build these maps:

| Alias | Resolution |
|---|---|
| Canonical internal ID | Exact row |
| Previous internal ID | That row's new canonical internal ID |
| Exact normalized task | That row's canonical internal ID |
| Unique external ID | The only matching row's canonical internal ID |

Alias comparison is case-insensitive for IDs and exact after task
normalization for task values.

Resolve each semicolon-separated dependency token in this order:

1. canonical internal ID;
2. previous internal ID;
3. exact task value;
4. unique external ID.

Then rewrite the dependency cell as semicolon-separated canonical internal
IDs, preserving the authored dependency order and removing no intentional
dependency.

Reject:

- unknown aliases;
- self-dependencies;
- duplicate dependencies;
- a token present in both declared and inferred dependencies;
- an external ID matching multiple rows;
- a previous internal ID matching multiple rows;
- dependencies on rows at the same or a later position;
- cycles implied by invalid ordering.

An ambiguous external-ID error lists the matching canonical internal IDs so the
editor can choose one explicitly.

## CSV normalization

Ordinary generation is a normalizing operation:

```bash
python roadmaps/generate.py release
```

It:

1. parses and classifies tasks;
2. normalizes task values;
3. generates canonical internal IDs;
4. resolves dependency aliases;
5. rewrites dependency cells to canonical internal IDs;
6. validates schema, uniqueness, statuses, priorities, and ordering;
7. rewrites the CSV only when its normalized representation differs;
8. generates Markdown from the normalized rows.

The CSV rewrite uses a temporary file and same-directory atomic replacement.

Check mode is non-mutating:

```bash
python roadmaps/generate.py --check release
```

It fails when:

- task values are not normalized;
- internal IDs are stale;
- dependencies are not canonical;
- the normalized CSV differs;
- generated Markdown differs.

## Generated Markdown

Every generated roadmap contains a prominent pointer to
`roadmaps/docs/updating-roadmaps.md`, allowing an agent that receives only the
generated Markdown to find the focused update workflow.

The `ID` cell uses the canonical internal ID as the link caption:

```text
Caption: CL-368-040
Target: tasks/20260804-open-source-public-release/040-minimum-ci-and-automation-hardening.md
```

The task title is rendered in a separate `Task` column. A task-directory ID
links to `000-main.md`. A free-name ID renders without a link.

The generated column order is:

```text
Order, ID, Task, Purpose, Dependencies, External ID, Priority, Status, Notes
```

Repeated external IDs are shown as entered and do not affect link uniqueness.

Dependencies render canonical internal IDs and retain the current inferred
dependency marker. Normal dependency links use ordinary Markdown without code
formatting. A dependency whose referenced task status is not `done` is
rendered as a red HTML link; a blocking free task is rendered as red inline
HTML without a link.

## Google Sheets synchronization

The named roadmap config selects the CSV, spreadsheet, expected spreadsheet
title, sheet, Google service-account credential, and request timeout. It is
independent of Crystal application and plugin source code.

Deployment-specific values are resolved from the ignored `roadmaps/.env`.
The committed `.env.example` documents required names without containing
credentials or spreadsheet IDs. Exported process values override dotenv values.

### Approval boundary

Read-only status and dry-run push/pull commands do not require mutation
authority. Before an agent runs `push --write`, `pull --write`, or
`npm run roadmap:update`, it must summarize the direction and expected changes,
offer the update, and obtain explicit user approval.

A main task may link the roadmap and focused update guide while forbidding
routine roadmap reads. A direct user request to update task status according to
those main-task instructions authorizes reading the linked files, changing only
the relevant roadmap data, and pushing to an already configured Google Sheet.
A generic task-completion request does not.

For an explicitly requested status update, configured and reachable sheet
synchronization is required for completion. The agent inspects the push dry
run, stops on unrelated remote differences, applies the intended push, and
verifies synchronized status plus a pull dry run. A local-only user constraint
forbids the remote write; unavailable configuration or credentials must be
reported as a synchronization blocker.

The focused CSV workflow and synchronization workflow are documented
separately under `roadmaps/docs/`.

### Derived presentation

Columns A–J remain the synchronized authored roadmap table. Synchronization
owns:

```text
K readiness
L blocking_dependencies
```

Readiness uses:

- `done` for a done task;
- `active` for `in progress` or `review`;
- `ready` for a pending task whose dependencies are all done;
- `queued` for a pending task whose unfinished dependencies are all `ready` or
  `active`;
- `blocked` for a pending task with at least one unfinished dependency that is
  `queued` or `blocked`.

The blocking-dependencies cell lists canonical internal IDs separated by
semicolons.

Synchronization manages whole-row conditional-formatting rules over A–L:

- `=$G2="done"`: light green;
- `=$K2="ready"`: light blue;
- `=$K2="queued"`: light purple;
- `=OR($G2="in progress",$G2="review")`: light orange.

No roadmap rule formats `blocked` or other values. Existing roadmap-owned rules
are recognized by exact formula and A–L range before replacement; unrelated
rules are preserved.

### Status

`status` is read-only. It normalizes both local and remote tables in memory and
reports:

- synchronized normalized data;
- local normalization required;
- remote normalization required;
- substantive row differences;
- invalid or ambiguous aliases.

It does not write either side.

### Push

Push normalizes local data before comparison.

Dry run reports:

- CSV normalization;
- generated Markdown changes;
- Google Sheets changes.

With `--write`:

1. validate and normalize in memory;
2. atomically update local CSV and Markdown when needed;
3. write the normalized table to Google Sheets with `RAW`;
4. clear only obsolete trailing rows after the table write;
5. read back with `UNFORMATTED_VALUE`;
6. require exact normalized matrix equality;
7. refresh readiness, blockers, and conditional formatting.

### Pull

Pull treats remote `internal_id` values and dependency entries as aliases, not
as authority.

Dry run:

1. reads and validates the exact target spreadsheet and sheet;
2. normalizes the remote table in memory;
3. shows local CSV and Markdown changes;
4. shows remote canonicalization required after the pull.

With `--write`:

1. atomically update local CSV;
2. atomically regenerate Markdown;
3. write the normalized table back to Google Sheets when remote IDs or
   dependencies were noncanonical;
4. read back and require exact normalized matrix equality;
5. refresh readiness, blockers, and conditional formatting.

An empty or incorrectly headed sheet cannot overwrite local files.

## Failure and recovery

- No command silently chooses synchronization direction.
- `push` and `pull` remain dry runs without `--write`.
- Validation occurs before local or remote mutation.
- A failed remote write leaves validated local normalization available for a
  retry and reports that remote convergence is incomplete.
- A failed local pull validation changes neither local file.
- A failed normalized sheet write-back after pull is reported as incomplete;
  local normalized files remain valid and a later push can converge the sheet.
- Credential values and credential paths are never included in logs or diffs.
- Google API and credential failures are reported without exposing credential
  paths, spreadsheet IDs, tokens, or response bodies.

## Migration

Migration from the legacy schema was performed as one coordinated operation.

1. Preserve a validated in-memory copy of the legacy CSV.
2. Move each nonempty legacy `task` path into the new first column.
3. For the website placeholder row, use its stable key as the free task
   name.
4. Convert only genuine user-managed identifiers to `external_id`; do not
   treat every generated `main_id` as external.
5. Seed previous `internal_id` aliases from legacy generated display IDs.
6. Convert `key` dependency references through the old-key-to-new-internal-ID
   map.
7. Normalize and validate the target CSV.
8. Generate target Markdown.
9. Dry-run the Google Sheets header and row migration.
10. Write local CSV, Markdown, and Google Sheet as one controlled migration.
11. Read back and run generation check, sync status, and pull dry run.

The migration is complete. The normalized header is now authoritative for the
local CSV and synchronized Google Sheet.