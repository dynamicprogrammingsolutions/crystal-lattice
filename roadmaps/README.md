# Roadmaps

Roadmaps are repository work-tracking documents that place selected tasks in a
useful priority order while preserving the dependencies needed to interpret
that order.

Each roadmap has two files:

- `<name>.csv` is the authored source of truth and may be edited by people or
  agents.
- `<name>.md` is generated from the CSV and must not be edited directly.

`config.json` assigns short names to roadmap CSV files and optional Google
Sheets destinations.

| Key | Authored CSV | Purpose |
|---|---|---|
| `release` | `open-source-and-ios-release.csv` | Public/open-source and application-release readiness |
| `product` | `product-development-roadmap.csv` | Cross-package product development and UX work |

Roadmap documentation starts at [`docs/index.md`](docs/index.md). It separates
the focused CSV-editing workflow from Google Sheets synchronization and
development internals.

## Quick start

Create the ignored local environment file:

```bash
cp roadmaps/.env.example roadmaps/.env
```

Install the standalone Python dependencies:

```bash
python -m pip install -r roadmaps/requirements.txt
```

Set these values in `roadmaps/.env`:

```dotenv
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
ROADMAP_RELEASE_SPREADSHEET_ID=your-google-spreadsheet-id
```

The configured spreadsheet stores the release roadmap in `Sheet1` and the
product roadmap in `Sheet4`.

Then regenerate the `release` Markdown roadmap and update its configured Google
Sheet:

```bash
npm run roadmap:release:update
```

The scoped npm command runs:

```bash
python roadmaps/generate.py release
python roadmaps/sync.py push release --write
```

Root npm scripts for this specific roadmap are:

| Script | Operation |
|---|---|
| `roadmap:release:generate` | Normalize the release CSV and regenerate Markdown. |
| `roadmap:release:check` | Check local CSV normalization and generated Markdown without writing. |
| `roadmap:release:test` | Run the generic roadmap unit tests. |
| `roadmap:release:status` | Compare normalized local data with the configured sheet. |
| `roadmap:release:push` | Preview a local-to-sheet update. |
| `roadmap:release:push:write` | Apply and verify a local-to-sheet update. |
| `roadmap:release:pull` | Preview a sheet-to-local update. |
| `roadmap:release:pull:write` | Apply and verify a sheet-to-local update. |
| `roadmap:release:update` | Generate locally and push the release roadmap. |
| `roadmap:release:verify` | Run local checks/tests plus status and pull dry runs. |

The `release` segment is intentional: these scripts are integration shortcuts
for `open-source-and-ios-release.csv`, not generic commands for every configured
roadmap.

Equivalent `roadmap:product:*` scripts operate on
`product-development-roadmap.csv` and its configured sheet:

```bash
npm run roadmap:product:generate
npm run roadmap:product:check
npm run roadmap:product:status
npm run roadmap:product:update
npm run roadmap:product:verify
```

For a read-only setup check:

```bash
python roadmaps/generate.py --check release
python roadmaps/sync.py status release
python roadmaps/generate.py --check product
python roadmaps/sync.py status product
```

Roadmaps are deliberately selective. They may retain a few recently completed
tasks as context without reproducing every historical prerequisite. When an
older dependency is already complete and omitted from the CSV, record that fact
in an arbitrary context field such as `notes`. Every dependency retained after
normalization must refer to an earlier row.

## CSV format

Every CSV must contain these semantic fields, in any column order:

```text
task
external_id
internal_id
priority
status
declared_dependencies
inferred_dependencies
```

Every other nonempty, case-insensitively unique header is an arbitrary user
field. Arbitrary fields retain their order and values through normalization,
generated Markdown, push, and pull. `readiness` and
`blocking_dependencies` are reserved for generated sheet presentation.

| Column | Meaning |
|---|---|
| `task` | Required unique identity: a repository Markdown path, a task-directory path, or a free task name. |
| `external_id` | Optional user-managed ID such as `CL-368`. It may be shared by multiple rows. |
| `internal_id` | Generated unique short ID used by dependency references and Markdown links. |
| `priority` | `must have`, `should have`, or `good to have`. |
| `status` | `pending`, `in progress`, `review`, or `done`. |
| `declared_dependencies` | Semicolon-separated dependency aliases declared by task files; normalized to internal IDs. |
| `inferred_dependencies` | Semicolon-separated dependency aliases established by roadmap analysis; normalized to internal IDs. |

For example, the current release roadmap uses arbitrary `main_task`,
`completed_at`, `title`, `purpose`, and `notes` fields. `completed_at` is a
manually maintained ISO date for completed rows. Those names have no special
meaning to the scripts.

Dependencies are always tasks. Approval, timing, feedback, credentials, and
other conditions belong in `notes` unless a task exists to represent them.

## Task forms

`task` is classified in this order:

1. A repository-relative value ending in `.md` links directly to that existing
   Markdown file.
2. Any existing repository-relative directory links to its configured task
   entry file, which defaults to `000-main.md`.
3. Every other value is a free unique name and generates no repository link.

Absolute paths, repository traversal, missing Markdown files, and task
directories without the configured entry file are rejected. Free names support
roadmap placeholders without creating task files.

## IDs

`external_id` is optional and may repeat. It provides the preferred base for
generated internal IDs:

```text
external_id CL-368 + subtask 040 -> CL-368-040
```

When no external ID exists, the generator derives a deterministic ID from a
dated task path:

```text
work/20260804-open-source-public-release/040-...md -> 0804-OS-040
planning/20260802-windows-installer/010-...md      -> 0802-WI-010
items/20260729-staged-application-config-...md     -> 0729-SA
```

Task-directory rows omit the numeric suffix. Free names use up to the first
three characters of their first two words:

```text
website-ios-review -> WEB-IOS
```

Collisions receive a deterministic four-character SHA-256 suffix.

`internal_id` is persisted for editing but regenerated on every generation or
synchronization operation. An entered old or manually changed internal ID is a
temporary alias, not authority.

Dependency input accepts:

- a canonical internal ID;
- the row's previous internal ID;
- an exact task value;
- a unique external ID.

Dependencies are rewritten to canonical internal IDs. A shared external ID is
ambiguous as a dependency and must be replaced with one matching internal ID.
Changing an external ID or manually changing an internal ID therefore updates
all resolvable references automatically.

## Ordering rules

- Rows are emitted exactly in CSV order. The generator never sorts them.
- Every resolved dependency must appear above its dependent row.
- A dependency whose row was removed is deleted during normalization with a
  warning. This supports intentionally deleting completed historical rows.
- A row cannot depend on itself.
- Tasks and generated internal IDs must be unique case-insensitively.
- Inferred dependencies have the same ordering force as declared dependencies
  and are labeled in generated Markdown.
- Fully completed historical dependencies may be omitted to keep a roadmap
  focused. Do not omit active or unresolved dependencies.

Position is a priority recommendation, not a claim that every task must execute
serially. Tasks without a dependency relationship may proceed in parallel.

## Generate and check

From the repository root:

```bash
python roadmaps/generate.py release
```

Ordinary generation normalizes task values, external IDs, internal IDs, and
dependency references before atomically rewriting the CSV and generated
Markdown.

To verify that committed Markdown is current without writing it:

```bash
python roadmaps/generate.py --check release
```

Passing the CSV path remains supported:

```bash
python roadmaps/generate.py roadmaps/open-source-and-ios-release.csv
```

Direct CSV generation does not require Google Sheets configuration. It uses
`ROADMAP_REPOSITORY_ROOT` when set, otherwise discovers the Git root from the
CSV location and falls back to the current working directory. The task entry
filename can be overridden with `ROADMAP_TASK_DIRECTORY_ENTRY`.

Ordering, schema, path, ID, ambiguous dependency, or unsafe dependency errors
stop generation with a non-zero exit status. Unknown dependency references are
removed with warnings. Check mode does not write and fails when CSV
normalization, dependency cleanup, or generated Markdown refresh is required.

## Google Sheets synchronization

Named roadmaps may define a spreadsheet ID, expected spreadsheet title, and
sheet name. [`config.json`](config.json) is self-contained: it defines the
repository root, task-directory entry filename, Google Sheets credential
mapping, request timeout, named CSV, and sheet destination. It does not depend
on Crystal application or plugin source code.

Secret and deployment-specific values come from the ignored `roadmaps/.env`.
The committed [`.env.example`](.env.example) documents every required
variable. The config uses `${env:NAME}` placeholders and fails before making a
Google API request when a required value is absent.

The real `.env` must not be committed. It contains:

- `GOOGLE_APPLICATION_CREDENTIALS`: absolute path to the Google service-account
  JSON file;
- `ROADMAP_RELEASE_SPREADSHEET_ID`: destination spreadsheet for the `release`
  named roadmap.

Already-exported environment variables override values from `roadmaps/.env`.

Inspect local/remote differences without changing either side:

```bash
python roadmaps/sync.py status release
```

Preview a CSV-to-Sheets update:

```bash
python roadmaps/sync.py push release
```

Apply it and verify the written values by reading them back:

```bash
python roadmaps/sync.py push release --write
```

Preview or apply a Sheets-to-CSV update:

```bash
python roadmaps/sync.py pull release
python roadmaps/sync.py pull release --write
```

Push normalizes local CSV and Markdown before using `RAW` values so task IDs,
paths, arbitrary fields, and other text are not interpreted as formulas. Pull
uses unformatted values, treats remote IDs and dependencies as aliases,
preserves arbitrary columns, and updates the local CSV, generated Markdown, and
normalized sheet only after validation. An empty or incorrectly headed sheet
cannot overwrite local files.

The source table width is dynamic. Generated `readiness` and
`blocking_dependencies` columns are placed immediately after the final source
column, and formatting formulas are calculated from header positions rather
than fixed spreadsheet letters.

`status`, `push`, and `pull` verify the spreadsheet ID, expected title, and
sheet name before comparing data. Push and pull are dry runs unless `--write`
is supplied.

Configuration paths can be overridden without editing the repository:

```text
ROADMAP_CONFIG=/path/to/config.json
ROADMAP_ENV=/path/to/roadmap.env
ROADMAP_REPOSITORY_ROOT=/path/to/project
ROADMAP_TASK_DIRECTORY_ENTRY=000-main.md
```

Run the focused tests with:

```bash
python -m unittest discover -s roadmaps/tests -p 'test_*.py'
```