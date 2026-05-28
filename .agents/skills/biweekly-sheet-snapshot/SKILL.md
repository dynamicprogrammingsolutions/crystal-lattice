---
name: biweekly-sheet-snapshot
description: Maintains the Crystal Lattice biweekly reporting spreadsheet from YouTrack and git history. Use when updating the Tasks and Summary tabs, pairing tasks with commits, calculating last commit datetime, proposing assignee corrections for approval, or refreshing the sprint summary formulas.
license: Apache-2.0
compatibility: Requires access to YouTrack CL issues, git history in this repository, and the target Google Sheet.
---

# Biweekly Sheet Snapshot

Use this skill when a user wants to update the Crystal Lattice biweekly reporting sheet.

The sheet has two tabs:

- `Tasks`: one normalized row per ticket included in a snapshot
- `Summary`: formula-driven aggregation rendered as three sprint blocks per reporting period

Target spreadsheet:

- Google Sheet ID: `1VxFdWZG0byHvokmaaELwBSsGawYIy8116wPi4rf6uYQ`
- Title: `Crystal Lattice progress summary`

This skill is designed around the current reporting rules:

- Treat all write operations as approval-gated.
- Do not use YouTrack `updatedAt` or `resolvedAt` as completion/activity indicators.
- Use tickets as the source of truth for snapshot inclusion.
- Pair tickets with commits as secondary validation and to help derive `Last Commit Datetime` when useful.
- Keep the raw YouTrack assignee in `Tasks`.
- If unassigned issues appear to need reassignment, propose the exact ticket list and wait for explicit user approval before updating YouTrack.
- The `Summary` tab should use formulas only. Do not manually type aggregate numbers.
- The `Summary` tab should be period-centric: one reporting period is rendered as three sprint blocks.

## When To Use

Activate this skill when the user asks to:

- update the reporting spreadsheet
- create or refresh a biweekly snapshot
- sync YouTrack tickets into the `Tasks` tab
- rebuild or repair the `Summary` tab formulas
- identify unassigned tasks that should probably be reassigned

If the user says `current snapshot`, derive it from `Tasks`:

1. Read `Tasks`
2. Find the latest populated `Snapshot Key`
3. Parse that key to recover snapshot date and period
4. Treat that snapshot key as canonical

## Workflow

1. Confirm the target spreadsheet and inspect its metadata, tabs, and existing structure.
2. Read the current reporting rules from [references/REFERENCE.md](references/REFERENCE.md).
3. Collect the reporting ticket set from YouTrack for the requested period and snapshot moment.
4. Pair each ticket to relevant commits on the current branch.
5. For each included ticket, derive `Last Commit Datetime` from the newest matched commit.
6. Detect unassigned tickets that look like they should be reassigned to `ferenci84`.
7. Prepare a short write plan summarizing:
   - snapshot being refreshed
   - tickets to add
   - tickets to update
   - tickets to remove
   - completion dates to seed or preserve
   - any assignee changes that would need approval
8. Stop and ask for explicit user approval before any write operation.
9. After approval, apply spreadsheet writes and any separately approved YouTrack changes.
10. Verify the formulas point at the expected `Tasks` columns and that each sprint block calculates from its own metadata row.

## Guardrails

- Never silently reassign issues in YouTrack.
- Never write to the spreadsheet or YouTrack without an explicit approval message in the current conversation.
- Never replace formula cells in `Summary` with hard-coded totals.
- Preserve raw task rows in `Tasks`; use `Summary` for aggregation.
- If the meaning of `Completed` versus `In Progress` is unclear for `Staging`, ask the user before changing classification rules.
- Keep the summary copy-friendly by using one metadata row per sprint block, then a header row, then three assignee rows.
- Avoid absolute row references in summary calculation formulas.

## Expected Outputs

- Updated `Tasks` rows for the requested snapshot
- Updated `Summary` sprint blocks for the requested reporting period
- If needed, a short approval request listing unassigned tickets proposed for reassignment

See [references/REFERENCE.md](references/REFERENCE.md) for the exact column layout, formula pattern, and approval workflow.