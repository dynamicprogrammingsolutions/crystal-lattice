# Progress Snapshot Updater

Internal project management tool that refreshes the Crystal Lattice progress
snapshot Google Sheet from YouTrack. This is not part of the product; it is a
maintainer utility for tracking sprint progress deterministically.

## What it does

- Reads a config file (`progress_snapshot.json` by default) for sheet ID,
  YouTrack base URL, project prefix, watched sprints, states, snapshot
  period, and stable row ordering.
- Reads the YouTrack token from `./.env` (`YOUTRACK_TOKEN`).
- Queries YouTrack for the configured ticket set (project prefix `CL`,
  watched sprints, relevant states, with type/grouping exclusions).
- Derives completion date from either a manually entered sheet field or the
  first time the ticket was set to a completed state.
- Computes a deterministic diff against existing sheet rows and applies it in
  `write` mode, preserving prior snapshot data and manual fields.
- Warns when the snapshot date is outside the snapshot period (allowed because
  snapshot closing can happen after the period ends).

## Usage

```bash
# Show the planned changes without writing
python tools/progress-snapshot/update_progress_snapshot.py show

# Apply the planned changes to the sheet
python tools/progress-snapshot/update_progress_snapshot.py write
```

Both modes accept:

- `--config <path>` — config file path (defaults to `progress_snapshot.json`
  next to the script)
- `--sheet-id <id>` — override the sheet ID from config
- `--snapshot-date <YYYY-MM-DD>` — override the system-derived snapshot date

## Config

`progress_snapshot.json` (next to the script) defines:

- `sheet_id` — Google Sheets document ID
- `youtrack_base_url` — YouTrack instance URL
- `project` — YouTrack project prefix (e.g. `CL`)
- `snapshot.period_start`, `snapshot.period_end`, `snapshot.snapshot_date`
- `watched_sprints` — sprint names to include
- `states` — states to include in the snapshot
- `completed_states` — states that count as completed for derived dates
- `exclude.type`, `exclude.grouping` — YouTrack exclusions
- `ordering.sprint`, `ordering.state`, `ordering.assignee` — stable row order
- `summary_assignees` — assignees included in the summary sheet
- `timezone` — timezone for date derivation

## Credentials

The script reads `YOUTRACK_TOKEN` from `./.env` and uses a Google service
account JSON (configured via standard `GOOGLE_APPLICATION_CREDENTIALS` or
the application default credentials path) for Sheets API access.

## Tests

```bash
pytest tools/progress-snapshot/test_update_progress_snapshot.py -q
```

The tests cover deterministic helper behavior: snapshot key ordering, legacy
column normalization, manual completion date overrides, row inclusion
filtering, and warning conditions. They do not hit YouTrack or Google Sheets.