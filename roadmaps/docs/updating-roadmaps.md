# Updating a roadmap through CSV

This guide is for agents updating an authored roadmap CSV and regenerating its
Markdown. Do not edit generated roadmap Markdown directly.

Google Sheets synchronization is a separate workflow. See
[Synchronizing Google Sheets](synchronizing-google-sheets.md). An agent must
offer the user the sheet update and obtain explicit approval before running a
command that mutates the sheet.

## Edit the source CSV

For the release roadmap, edit:

```text
roadmaps/open-source-and-ios-release.csv
```

Important rules:

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

## Normalize and regenerate

Run:

```bash
python roadmaps/generate.py release
```

Ordinary generation may rewrite the CSV to normalize task values, internal
IDs, and dependency references. It also regenerates:

```text
roadmaps/open-source-and-ios-release.md
```

Review both files after generation.

Blocking dependencies are shown as red links in generated Markdown. A
dependency is blocking whenever its referenced task does not have status
`done`.

## Verify the local update

Run:

```bash
python roadmaps/generate.py --check release
python -m unittest discover -s roadmaps/tests -p 'test_*.py'
```

Check mode is read-only and fails if either the CSV requires normalization or
the generated Markdown is stale.

Do not run `npm run roadmap:update` as part of an ordinary CSV edit unless the
user has explicitly approved updating Google Sheets. That npm command performs
a remote write.