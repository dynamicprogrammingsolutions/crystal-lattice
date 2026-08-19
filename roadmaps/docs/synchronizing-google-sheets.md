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

This applies to:

```bash
python roadmaps/sync.py push release --write
python roadmaps/sync.py pull release --write
npm run roadmap:update
```

`npm run roadmap:update` regenerates local Markdown and writes the local CSV to
Google Sheets, so it also requires explicit approval.

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
remote task identities, internal IDs, and dependencies before changing local
files.

## Managed sheet presentation

Columns A–J contain the synchronized roadmap source. Columns K–L are generated
presentation data:

```text
K readiness
L blocking_dependencies
```

Readiness is derived as follows:

| Status | Dependency state | Readiness |
|---|---|---|
| `done` | Any | `done` |
| `in progress` or `review` | Any | `active` |
| `pending` | Every dependency is `done` | `ready` |
| `pending` | Every unfinished dependency is `ready` or `active` | `queued` |
| `pending` | At least one unfinished dependency is `queued` or `blocked` | `blocked` |

The synchronization command also manages whole-row conditional formatting over
columns A–L:

- `done`: light green;
- `ready`: light blue;
- `queued`: light purple;
- `in progress` or `review`: light orange;
- `blocked` and every other value: no roadmap-managed background rule.

Unrelated conditional-formatting rules are preserved. Roadmap-owned rules are
recognized by their exact formula and A–L range before replacement.

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