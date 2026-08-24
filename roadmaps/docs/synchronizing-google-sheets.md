# Synchronizing Google Sheets

This guide covers synchronization between a roadmap CSV and its configured
Google Sheet.

## Agent approval boundary

Reading synchronization state and producing dry-run diffs are non-mutating:

```bash
python roadmaps/sync.py status release
python roadmaps/sync.py push release
python roadmaps/sync.py pull release
```

Before an agent runs any command with `--write`, it must:

1. explain which direction will be synchronized;
2. summarize the expected local and remote changes;
3. offer to apply the synchronization;
4. obtain explicit user approval.

A direct request to update a task status according to the roadmap instructions
in a linked main task is that explicit approval for the relevant local update
and configured Google Sheet push. It does not authorize unrelated roadmap
changes. A generic request to complete a task is not approval to read or update
the roadmap, and an explicit local-only limitation forbids the sheet write.

This applies to:

```bash
python roadmaps/sync.py push release --write
python roadmaps/sync.py pull release --write
npm run roadmap:release:update
```

`npm run roadmap:release:update` regenerates local Markdown and writes the
release CSV to Google Sheets, so it also requires explicit approval.

When such an explicitly requested roadmap update is made and synchronization
is already configured and reachable, the agent must perform and verify the
sheet synchronization. It must not report the roadmap update as fully complete
after changing only the CSV and generated Markdown.

## First-time setup

Install the standalone dependencies:

```bash
python -m pip install -r roadmaps/requirements.txt
```

Create the ignored environment file:

```bash
cp roadmaps/.env.example roadmaps/.env
```

Fill:

```dotenv
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
ROADMAP_RELEASE_SPREADSHEET_ID=your-google-spreadsheet-id
```

The real `.env` is ignored and must not be committed.

## Synchronization direction

Use `push` when the local CSV is authoritative:

```bash
python roadmaps/sync.py push release
python roadmaps/sync.py push release --write
```

Use `pull` when the Google Sheet is authoritative:

```bash
python roadmaps/sync.py pull release
python roadmaps/sync.py pull release --write
```

Push and pull are dry runs without `--write`. Pull validates and normalizes
remote task identities, internal IDs, dependencies, and arbitrary source
columns before changing local files.

Before an approved task-status push, inspect the dry-run difference. If it
contains unrelated sheet edits, stop for user direction rather than
overwriting them.

## Managed sheet presentation

The synchronized source starts at column A and has the same dynamic headers and
order as the CSV. The next two columns are generated presentation data:

```text
<first column after the source> readiness
<next column>                   blocking_dependencies
```

Readiness is derived as follows:

| Status | Dependency state | Readiness |
|---|---|---|
| `done` | Any | `done` |
| `in progress` or `review` | Any | `active` |
| `pending` | Every dependency is `done` | `ready` |
| `pending` | Every unfinished dependency is `ready` or `active` | `queued` |
| `pending` | At least one unfinished dependency is `queued` or `blocked` | `blocked` |

The synchronization command also manages whole-row conditional formatting from
column A through the generated presentation columns:

- `done`: light green;
- `ready`: light blue;
- `queued`: light purple;
- `in progress` or `review`: light orange;
- `blocked` and every other value: no roadmap-managed background rule.

Status and readiness formula columns are calculated from header positions, so
adding, removing, or reordering arbitrary fields moves the presentation and
formatting safely. Unrelated conditional-formatting rules are preserved.
Roadmap-owned rules are recognized by their formula shape and full-row range
before replacement.

## Final verification

After an approved write:

```bash
python roadmaps/generate.py --check release
python roadmaps/sync.py status release
python roadmaps/sync.py pull release
```

The expected final state is:

```text
Local CSV and Google Sheet are synchronized.
Local files already match Google Sheets.
```