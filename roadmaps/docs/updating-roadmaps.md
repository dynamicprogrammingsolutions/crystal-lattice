# Updating a roadmap through CSV

This guide is for agents updating an authored roadmap CSV and regenerating its
Markdown. Do not edit generated roadmap Markdown directly.

Google Sheets synchronization details are documented in
[Synchronizing Google Sheets](synchronizing-google-sheets.md).

## Invocation from a main task

Main task files may point to this guide and the generated roadmap while
instructing agents not to read either during ordinary execution. Follow those
links only when the user explicitly requests a roadmap status update.

A direct request such as “update the task status in the roadmap as per the
instructions in the main task” authorizes:

- reading the linked roadmap and this guide;
- updating the relevant CSV row and generated Markdown;
- synchronizing the configured Google Sheet when synchronization is already
  set up and reachable.

That request does not authorize unrelated row, ordering, dependency, priority,
or note changes. A generic request to complete a task does not authorize a
roadmap update. If the user explicitly requests a local-only update, do not
mutate Google Sheets.

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

## Complete configured synchronization

When the roadmap target and Google credentials are already configured, a
user-requested roadmap status update is incomplete until the Google Sheet has
been synchronized and verified.

First inspect the proposed push:

```bash
python roadmaps/sync.py status release
python roadmaps/sync.py push release
```

If the dry-run difference contains only the intended roadmap update and
normalization, apply it:

```bash
npm run roadmap:update
```

Then verify:

```bash
python roadmaps/sync.py status release
python roadmaps/sync.py pull release
```

If the dry run reveals unrelated remote edits, stop and ask the user how to
resolve them instead of overwriting them. If synchronization is not configured,
credentials are unavailable, or the sheet cannot be reached, complete the safe
local update, report synchronization as blocked, and do not claim that the
roadmap update is fully synchronized.