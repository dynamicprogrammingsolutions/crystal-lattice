# Crystal Lattice Biweekly Sheet Reference

This reference defines how future agents should maintain the Crystal Lattice reporting sheet.

## Source Systems

- YouTrack project: `CL`
- Git repository branch history for secondary validation and activity hints
- Google Sheet ID: `1VxFdWZG0byHvokmaaELwBSsGawYIy8116wPi4rf6uYQ`
- Google Sheet title: `Crystal Lattice progress summary`
- Spreadsheet tabs:
  - `Tasks`
  - `Summary`

## Current Snapshot Derivation

When the user says `refresh the current snapshot`, derive the target snapshot from the sheet.

Canonical source:

- `Summary!B2` = `Snapshot Date`
- `Summary!B3` = `Period Start`
- `Summary!B4` = `Period End`

Those three control cells define the active snapshot to refresh.

Fallback only if those cells are blank:

- inspect `Tasks`
- find the latest populated `Snapshot Key`
- derive the snapshot from that key

Do not guess the current snapshot from today’s date when the sheet already contains explicit controls.

## Approval Workflow

All write operations are approval-gated.

This includes:

- writing `Tasks` rows
- changing `Summary` formulas or control cells
- inserting or deleting spreadsheet rows
- updating YouTrack assignees

Even if the user asked for the modification directly, do not write immediately.
First prepare a concise plan and request approval.

The approval summary should be easy to review and should include:

- snapshot key or period
- rows to add
- rows to update
- rows to remove
- completion dates that will be seeded from `Ticket Updated At`
- completion dates that will be preserved as manual
- unassigned tickets that would remain unassigned
- any proposed YouTrack assignee changes

Recommended approval prompt format:

```text
Planned snapshot refresh for 2026-05-20..2026-06-02 @ 2026-06-02

Add:
- CL-287 Sprint 3 Summary text
- CL-299 Release 2 Summary text

Update:
- CL-262 preserve manual Completion Date (blank)
- CL-150 preserve Completion Date 2026-05-27

Remove:
- CL-123 no longer matches current filters

Seed Completion Date from Ticket Updated At:
- CL-287 -> 2026-06-01

Unassigned tickets remaining unassigned:
- CL-304
- CL-332
- CL-333

Approve these writes?
```

Only after explicit approval should the agent perform the writes.

Primary reporting source of truth:

- ticket selection comes from YouTrack state, sprint, type, and grouping filters

Secondary validation:

- commits help validate whether a ticket belongs in a period and can provide `Last Commit Datetime`
- commits can also help discover missing tickets that should be created

## Core Rules

### Activity timing

Do not use YouTrack `updatedAt` or `resolvedAt` as the report activity signal.

Instead:

- pair each reported issue with one or more commits when useful
- use the newest matched commit timestamp as `Last Commit Datetime`

### Assignee handling

Keep the raw YouTrack assignee in the `Tasks` sheet.

If an issue is unassigned but appears to belong to `ferenci84`, do not auto-fix it.
Instead:

1. prepare a short approval list
2. show the exact issue IDs and summaries
3. wait for explicit user approval
4. only then update YouTrack
5. refresh the sheet after reassignment

Example approval prompt:

```text
The following unassigned issues appear to belong to ferenci84. Approve reassignment?
- CL-123 Summary text
- CL-456 Summary text
```

### Summary behavior

The `Summary` tab must be formula-driven.

Do not manually enter aggregate counts or story-point totals.

## Tasks Tab

Recommended columns:

1. `Snapshot Date`
2. `Period Start`
3. `Period End`
4. `Sprint`
5. `Issue ID`
6. `Summary`
7. `State`
8. `Assignee`
9. `Story Points`
10. `Bucket`
11. `Completion Date`
12. `Last Commit Datetime`
13. `Commit Count`
14. `Pairing Note`

Notes:

- `Bucket` is the normalized reporting classification, for example:
  - `Completed in Period`
  - `In Progress at Snapshot`
- `Completion Date` is a manually maintained field for completed tickets. Use it as the source of truth for completed aggregations.
- `Story Points` should be numeric when possible.
- `Pairing Note` is optional but useful when the match was inferred from a cluster instead of a one-to-one title match.

## Summary Tab Structure

The `Summary` tab should represent one reporting period per section.

For the current workbook, use a single active section for the current period.

Recommended control cells near the top of the section:

- one cell for `Snapshot Date`
- one cell for `Period Start`
- one cell for `Period End`
- three cells for sprint names:
  - `Sprint 3`
  - `Release 1`
  - `Release 2`

Then create one data row per `(Sprint, Assignee)` pair.

Recommended assignee rows per sprint:

- `ferenci84`
- `Pujan`
- `Unassigned`

Recommended visible data columns:

1. `Snapshot Date`
2. `Period Start`
3. `Period End`
4. `Sprint`
5. `Assignee`
6. `Completed Tasks`
7. `Completed Story Points`
8. `In Progress Tasks`
9. `In Progress Story Points`

Important:

- repeat the period and sprint values visibly in every data row
- calculation formulas should read the filter values from the same row
- avoid absolute row references such as `$A$7` in aggregate formulas

## Formula Pattern

Assume:

- `Tasks` columns are arranged as recommended above
- the summary row columns are:
  - `A` `Snapshot Date`
  - `B` `Period Start`
  - `C` `Period End`
  - `D` `Sprint`
  - `E` `Assignee`
  - `F` `Completed Tasks`
  - `G` `Completed Story Points`
  - `H` `In Progress Tasks`
  - `I` `In Progress Story Points`

Example formulas for row `12`:

Completed task count:

```gs
=COUNTIFS(Tasks!$A:$A,$A12,Tasks!$B:$B,$B12,Tasks!$C:$C,$C12,Tasks!$D:$D,$D12,Tasks!$H:$H,$E12,Tasks!$K:$K,">="&$B12,Tasks!$K:$K,"<="&$C12)
```

Completed story points:

```gs
=SUMIFS(Tasks!$I:$I,Tasks!$A:$A,$A12,Tasks!$B:$B,$B12,Tasks!$C:$C,$C12,Tasks!$D:$D,$D12,Tasks!$H:$H,$E12,Tasks!$K:$K,">="&$B12,Tasks!$K:$K,"<="&$C12)
```

In-progress task count:

```gs
=COUNTIFS(Tasks!$A:$A,$A12,Tasks!$B:$B,$B12,Tasks!$C:$C,$C12,Tasks!$D:$D,$D12,Tasks!$H:$H,$E12,Tasks!$J:$J,"In Progress at Snapshot")
```

In-progress story points:

```gs
=SUMIFS(Tasks!$I:$I,Tasks!$A:$A,$A12,Tasks!$B:$B,$B12,Tasks!$C:$C,$C12,Tasks!$D:$D,$D12,Tasks!$H:$H,$E12,Tasks!$J:$J,"In Progress at Snapshot")
```

For the `Unassigned` row, use `Unassigned` consistently in `Tasks!H:H` if the issue has no assignee at snapshot time.

## Ticket Selection Workflow

For each report run:

1. Determine the reporting period start and end.
2. Determine the snapshot moment for in-progress tasks.
3. Query YouTrack for relevant issues in `Sprint 3`, `Release 1`, and `Release 2`.
4. Identify:
   - completed tickets in the requested period
   - in-progress tickets at snapshot time
5. Pair those issues with commits on the current branch.
6. Populate the `Tasks` sheet.
7. Refresh formulas in `Summary` only if the layout needs repair or initial setup.
8. Prefer formulas without absolute row references so a whole period section can be copied safely.

## Commit Pairing Guidance

Use the strongest available evidence:

- issue ID in commit message
- explicit task/ticket description match
- tightly related commit cluster around the relevant timeframe
- file-level correspondence to known task scope

When pairing is uncertain:

- prefer a short `Pairing Note`
- avoid inventing precision that is not actually supported by the history

## Suggested User-Facing Reporting Language

When you find unassigned tickets:

```text
I found unassigned tickets in the reporting set that likely belong to ferenci84.
I have not changed YouTrack. Approve reassignment for:
- CL-123 Summary
- CL-456 Summary
```

When the sheet update is complete:

```text
Updated the Tasks snapshot rows and refreshed the Summary formulas.
Last activity dates come from the newest paired commit per ticket, not YouTrack timestamps.
```