# Roadmaps

Roadmaps are repository work-tracking documents that place selected tasks in a
useful priority order while preserving the dependencies needed to interpret
that order.

Each roadmap has two files:

- `<name>.csv` is the authored source of truth and may be edited by people or
  agents.
- `<name>.md` is generated from the CSV and must not be edited directly.

`config.json` assigns short names to roadmap CSV files and optional Google
Sheets destinations. The initial roadmap is named `release`.

Maintainer documentation and specifications start at
[`docs/development/index.md`](docs/development/index.md).

## Quick start

Create the ignored local environment file:

```bash
cp roadmaps/.env.example roadmaps/.env
```

Set these values in `roadmaps/.env`:

```dotenv
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
GOOGLE_PROJECT_ID=your-google-project-id
ROADMAP_RELEASE_SPREADSHEET_ID=your-google-spreadsheet-id
```

Then regenerate the `release` Markdown roadmap and update its configured Google
Sheet:

```bash
npm run roadmap:update
```

The npm command runs:

```bash
python roadmaps/generate.py release
python roadmaps/sync.py push release --write
```

For a read-only setup check:

```bash
python roadmaps/generate.py --check release
python roadmaps/sync.py status release
```

Roadmaps are deliberately selective. They may retain a few recently completed
tasks as context without reproducing every historical prerequisite. When an
older dependency is already complete and omitted from the CSV, record that fact
in `notes`. Every dependency that is represented in the CSV must refer to an
earlier row.

## CSV format

The required header is:

```csv
task,external_id,internal_id,title,purpose,priority,status,declared_dependencies,inferred_dependencies,notes
```

| Column | Meaning |
|---|---|
| `task` | Required unique identity: a repository Markdown path, a task-directory path, or a free task name. |
| `external_id` | Optional user-managed ID such as `CL-368`. It may be shared by multiple rows. |
| `internal_id` | Generated unique short ID used by dependency references and Markdown links. |
| `title` | Required human-readable task title. |
| `purpose` | Required concise roadmap-level outcome. |
| `priority` | `must have`, `should have`, or `good to have`. |
| `status` | `pending`, `in progress`, `review`, or `done`. |
| `declared_dependencies` | Semicolon-separated dependency aliases declared by task files; normalized to internal IDs. |
| `inferred_dependencies` | Semicolon-separated dependency aliases established by roadmap analysis; normalized to internal IDs. |
| `notes` | Optional concise context, including omitted completed prerequisites. |

Dependencies are always tasks. Approval, timing, feedback, credentials, and
other conditions belong in `notes` unless a task exists to represent them.

## Task forms

`task` is classified in this order:

1. A repository-relative value ending in `.md` links directly to that existing
   Markdown file.
2. A repository-relative directory under `tasks/` links to its existing
   `000-main.md`.
3. Every other value is a free unique name and generates no repository link.

Absolute paths, repository traversal, missing Markdown files, and task
directories without `000-main.md` are rejected. Free names support roadmap
placeholders without creating task files.

## IDs

`external_id` is optional and may repeat. It provides the preferred base for
generated internal IDs:

```text
external_id CL-368 + subtask 040 -> CL-368-040
```

When no external ID exists, the generator derives a deterministic ID from a
dated task path:

```text
tasks/20260804-open-source-public-release/040-...md -> 0804-OS-040
tasks/20260802-windows-installer/010-...md          -> 0802-WI-010
tasks/20260729-staged-application-config-...md      -> 0729-SA
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
- All `done` rows must be at the top of the CSV.
- Every represented dependency must exist and appear above its dependent row.
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

Ordering, schema, path, ID, or dependency errors stop generation with a
non-zero exit status. Check mode does not write and fails when CSV
normalization or generated Markdown is stale.

## Google Sheets synchronization

Named roadmaps may define a spreadsheet ID, expected spreadsheet title, and
sheet name. [`config.json`](config.json) is self-contained: it defines the
`mcp-gsheets` command, pinned npm package, environment mapping, named CSV, and
sheet destination. It does not depend on the Crystal application config.

Secret and deployment-specific values come from the ignored `roadmaps/.env`.
The committed [`.env.example`](.env.example) documents every required
variable. The config uses `${env:NAME}` placeholders and fails before starting
MCP when a required value is absent.

The real `.env` must not be committed. It contains:

- `GOOGLE_APPLICATION_CREDENTIALS`: absolute path to the Google service-account
  JSON file;
- `GOOGLE_PROJECT_ID`: project identifier passed to `mcp-gsheets`;
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
paths, and other text are not interpreted as formulas. Pull uses unformatted
values, treats remote IDs and dependencies as aliases, and updates the local
CSV, generated Markdown, and normalized sheet only after validation. An empty
or incorrectly headed sheet cannot overwrite local files.

`status`, `push`, and `pull` verify the spreadsheet ID, expected title, and
sheet name before comparing data. Push and pull are dry runs unless `--write`
is supplied. The tool warns when the configured MCP npm package uses an
unpinned version such as `@latest`.

Configuration paths can be overridden without editing the repository:

```text
ROADMAP_CONFIG=/path/to/config.json
ROADMAP_ENV=/path/to/roadmap.env
```

Run the focused tests with:

```bash
python -m unittest discover -s roadmaps/tests -p 'test_*.py'
```