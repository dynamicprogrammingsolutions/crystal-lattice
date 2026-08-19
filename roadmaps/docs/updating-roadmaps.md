# Updating a roadmap

Generated roadmap Markdown files must not be edited directly. Update the
roadmap through its CSV or synchronized Google Sheet, then regenerate.

## First-time setup

From the repository root:

```bash
python -m pip install -r roadmaps/requirements.txt
cp roadmaps/.env.example roadmaps/.env
```

Fill `roadmaps/.env` with:

```dotenv
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
ROADMAP_RELEASE_SPREADSHEET_ID=your-google-spreadsheet-id
```

The real `.env` is ignored and must not be committed.

## Choose the source of an edit

Before changing anything, inspect synchronization state:

```bash
python roadmaps/sync.py status release
```

If the Google Sheet contains the intended edits, preview and apply a pull:

```bash
python roadmaps/sync.py pull release
python roadmaps/sync.py pull release --write
```

If the local CSV is the intended source, edit
`roadmaps/open-source-and-ios-release.csv`, then normalize and regenerate:

```bash
python roadmaps/generate.py release
```

Preview and apply the sheet update:

```bash
python roadmaps/sync.py push release
python roadmaps/sync.py push release --write
```

The root convenience command regenerates and pushes in one step:

```bash
npm run roadmap:update
```

## Editing rules

- `task` is the unique row identity. It may be:
  - a task Markdown path;
  - a task directory containing `000-main.md`;
  - a free unique name for work without a task file.
- `external_id` is optional and may be shared by multiple rows.
- `internal_id` is generated. Do not choose it manually as an enduring
  identifier.
- Dependencies use internal IDs after normalization.
- Dependency input may temporarily use an old internal ID, exact task value, or
  unique external ID; generation rewrites it to the canonical internal ID.
- A shared external ID is ambiguous as a dependency and must be replaced by one
  matching internal ID.
- All `done` rows stay at the top.
- Every represented dependency must appear above its dependent row.
- Priority is `must have`, `should have`, or `good to have`.
- Status is `pending`, `in progress`, `review`, or `done`.

Ordinary generation may rewrite the CSV to normalize task values, IDs, and
dependency references. Check mode is read-only:

```bash
python roadmaps/generate.py --check release
```

## Final verification

After an update:

```bash
python roadmaps/generate.py --check release
python roadmaps/sync.py status release
python -m unittest discover -s roadmaps/tests -p 'test_*.py'
```

The expected final state is:

```text
Local CSV and Google Sheet are synchronized.
```