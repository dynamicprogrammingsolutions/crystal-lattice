# Deterministic Progress Snapshot Updater

Create a simple deterministic script for refreshing the Crystal Lattice progress snapshot sheet from YouTrack. The script should be easy to run repeatedly, preserve prior snapshots, and support a dry-run review mode before writing.

## Requirements checklist

- [x] Add a config-file driven snapshot updater script.
- [x] Verify API connectivity before implementation.
- [x] Support `show` and `write` modes.
- [x] Read the YouTrack token from `./.env`.
- [x] Use the provided config file for watched sprints, sheet ID, project/filter settings, and the current snapshot period.
- [x] Derive snapshot date from system time when the script runs.
- [x] Preserve previous snapshot data when the snapshot key/date changes.
- [x] Update the `Tasks` sheet based on the configured period start/end.
- [x] Apply the agreed filtered YouTrack source set:
  - project/prefix `CL`
  - watched sprints from config
  - relevant states such as `In Progress`, `Staging`, and `Done`
  - exclude `Type: Group`
  - exclude `Grouping: Level 2`
- [x] Determine completion date from either a manually entered sheet field or the first time the ticket was set to `Staging` / `Done`.
- [x] Warn when snapshot date is outside the snapshot period, but allow it because snapshot closing can happen after the period ends.
- [x] Apply stable deterministic row ordering.
- [x] Keep the script easy to run with little typing.
- [x] Use test spreadsheet `1ZRdxbvT5VknFErYW2z_JYBCa8Wv7o3FHXqcJ9VpSmbs` for testing.

## Execution plan

Added during completion after user approval.

1. Create a dedicated git worktree and branch for the script implementation.
2. Move this task file into the new worktree.
3. Copy `.env` into the new worktree and add the Google Sheets credential variables provided by the user.
4. Verify direct YouTrack REST access using the token from `.env`.
5. Verify direct Google Sheets read access using the provided service account JSON.
6. Add a config-file driven updater script with short commands:
   - `python scripts/update_progress_snapshot.py show`
   - `python scripts/update_progress_snapshot.py write`
7. Initially test against the provided test sheet, then point the committed default config at the original progress sheet.
8. Implement deterministic diffing and stable ordering.
9. Implement `show` mode first and test it without writing to the sheet.
10. Implement `write` mode, but do not run it without explicit approval because it mutates the workbook.
11. Add focused local tests for deterministic helper behavior.

## Agreed Design Notes

The script should not infer snapshot membership from commits. YouTrack tickets are the source of truth. Commits can remain available as manual/validation fields, but the only manual field that affects aggregation should be the manual completion date.

The script should support two modes:

- `show`: compute and display the planned changes only.
- `write`: apply the planned changes to the sheet.

The sheet update should be deterministic for a configured period:

1. Read config.
2. Use system date as `Snapshot Date`.
3. Build the snapshot key from `Period Start`, `Period End`, and `Snapshot Date`.
4. Query YouTrack for the configured ticket set.
5. Build expected `Tasks` rows in stable sorted order.
6. Compare existing rows for the same snapshot key or period against expected rows.
7. In `show` mode, print new tickets, edited tickets, and removed tickets with review-relevant fields.
8. In `write` mode, rewrite/apply only the target snapshot data.
9. Leave rows for previous snapshot keys untouched.

If the snapshot key/date changes, the old snapshot rows must remain in place. This allows older report sections to stay above newer report sections in `Summary`.

## Proposed Simplified Tasks Columns

The current sheet can be simplified during implementation. Recommended columns:

1. `Snapshot Key`
2. `Snapshot Date`
3. `Period Start`
4. `Period End`
5. `Issue ID`
6. `Sprint`
7. `State`
8. `Summary`
9. `Assignee`
10. `Story Points`
11. `Manual Completion Date`
12. `Derived Completion Date`
13. `Effective Completion Date`
14. `Ticket Updated At`
15. `Last Commit Datetime`
16. `Commit Count`
17. `Pairing Note`

`Summary` is technically redundant but should be kept for human review. Commit-related fields can remain for manual validation. `Bucket` / `Completed in Period` should be removed because completion can be derived from state and completion dates.

## Completion Date Rules

For each ticket:

1. If an existing row has `Manual Completion Date`, preserve and use it.
2. Otherwise derive the date from YouTrack history.
3. The derived date is the first time the ticket was set to `Staging` or `Done`.
4. `Effective Completion Date` is the manual date if present, otherwise the derived date.
5. Completed aggregations should use `Effective Completion Date` between period start and period end.
6. In-progress aggregations should use current ticket state, normally `In Progress`.

## Show Mode Output

`show` mode should print a concise diff grouped into:

- `Add`
- `Update`
- `Remove`

Each item should include:

- `Issue ID`
- `Sprint`
- `State`
- `Summary`
- `Assignee`
- `Story Points`
- `Manual Completion Date`
- `Derived Completion Date`
- `Effective Completion Date`
- `Ticket Updated At`

Updates should show field-level changes so the user can review what would be written.

## Config File Shape

The exact format can be finalized during implementation, but it should include:

```yaml
sheet_id: "1ZRdxbvT5VknFErYW2z_JYBCa8Wv7o3FHXqcJ9VpSmbs"
project: "CL"
period_start: "2026-05-20"
period_end: "2026-06-02"
watched_sprints:
  - "Sprint 3"
  - "Release 1"
  - "Release 2"
states:
  - "In Progress"
  - "Staging"
  - "Done"
exclude:
  type:
    - "Group"
  grouping:
    - "Level 2"
assignee_order:
  - "ferenci84"
  - "Pujan"
  - "Unassigned"
```

## API Notes

Relevant YouTrack REST documentation:

- `GET /api/issues` supports a `query` parameter and explicit `fields`.
- Custom fields should be requested explicitly with nested `customFields(name,value(...))`.
- State history can be read from `GET /api/issues/{issueID}/activities`.
- Activity history requires a category such as `CustomFieldCategory`.
- Useful activity fields for state transitions are `timestamp`, `added(name)`, and `removed(name)`.

Implementation should verify the exact local YouTrack base URL from existing environment/config before coding.

## Connection Check Findings

Added during planning.

YouTrack:

- `.env` contains `YOUTRACK_TOKEN`.
- A known issue URL shows the base URL is `https://dynamicprogrammingsolutions.myjetbrains.com/youtrack`.
- Direct REST with `Authorization: Bearer $YOUTRACK_TOKEN` works for:
  - `GET /api/issues/CL-287?fields=idReadable,summary,updated,customFields(name,value(name,login,presentation))`
  - `GET /api/issues/CL-287/activities?categories=CustomFieldCategory&fields=timestamp,field(name),added(name,presentation),removed(name,presentation)`
  - `GET /api/issues?query=...&fields=...`
- The activity endpoint returns state transition data needed to derive first `Staging` / `Done` dates.

Google Sheets:

- Test spreadsheet `1ZRdxbvT5VknFErYW2z_JYBCa8Wv7o3FHXqcJ9VpSmbs` is reachable through the current Sheets integration.
- The workbook title is `Copy of Crystal Lattice progress summary TEST`.
- It has `Tasks` and `Summary` tabs.
- Local Python currently has `google-auth` and `google.oauth2.service_account`, but does not have `googleapiclient.discovery` or `gspread`.
- Local Application Default Credentials are not configured.
- Implementation must therefore include a small dependency/auth decision for direct script writes to Google Sheets.

Documentation references:

- YouTrack issue list endpoint: `https://www.jetbrains.com/help/youtrack/devportal/resource-api-issues.html`
- YouTrack activity categories: `https://www.jetbrains.com/help/youtrack/devportal/api-entity-ActivityCategory.html`
- YouTrack specific issue endpoint: `https://www.jetbrains.com/help/youtrack/devportal/operations-api-issues.html`

## Completion Notes

Added during completion.

Implementation created on branch `feature/deterministic-progress-snapshot-updater` in worktree `ai-agent-platform-worktrees/deterministic-progress-snapshot-updater`.

Added files:

- `scripts/update_progress_snapshot.py`
- `scripts/progress_snapshot.json`
- `scripts/test_update_progress_snapshot.py`
- `tasks/20260601-deterministic-progress-snapshot-updater.md`

The script uses raw REST calls with `requests`:

- YouTrack REST is authenticated with `YOUTRACK_TOKEN` from `.env`.
- Google Sheets REST is authenticated with `GOOGLE_APPLICATION_CREDENTIALS` from `.env`.
- No additional Python package installation was needed because `requests` and `google-auth` were already available locally.

Verified:

- Direct YouTrack issue fetch, issue search, and state-history activity fetch.
- Direct Google Sheets read access to the provided test spreadsheet.
- `python scripts/update_progress_snapshot.py show`
- `python -m py_compile scripts/update_progress_snapshot.py`
- `PYTHONPATH=scripts pytest scripts/test_update_progress_snapshot.py -q`

`write` mode is implemented. It mutates the workbook and should be run only after reviewing `show` output and approving the write.

Final run adjustment:

- The committed default config is `scripts/progress_snapshot.json`.
- It points to original sheet `1VxFdWZG0byHvokmaaELwBSsGawYIy8116wPi4rf6uYQ`.
- The earlier test sheet `1ZRdxbvT5VknFErYW2z_JYBCa8Wv7o3FHXqcJ9VpSmbs` was used for implementation validation only.
- After approval, `python scripts/update_progress_snapshot.py write --replace-same-period` was run against the original sheet.
- The original sheet now contains snapshot `2026-05-20..2026-05-31@2026-06-01`.
- A follow-up `show --replace-same-period` returned no add/update/remove/protected changes.

Observed edge case:

- Some tickets currently in `Staging` have no detectable activity transition into `Staging` / `Done`, so their derived completion date remains blank. This follows the agreed rule to derive completion from the first `Staging` / `Done` state transition rather than guessing from `updatedAt`.

Follow-up adjustment:

- If a completed ticket has no detectable transition into `Staging` / `Done`, the script now falls back to the issue creation date.
- Manual rows are treated as an additional source of overrides, not only current-snapshot rows.
- Manual fields are read from all `Tasks` rows for the same issue.
- Manual rows are protected from deletion in `write` mode when the computed snapshot would otherwise remove them.
- If a protected target-snapshot row is still included by the computed snapshot, the script rewrites the computed row instead of duplicating it.