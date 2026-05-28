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
- `Summary`: formula-driven aggregation for one reporting period section at a time

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
- The `Summary` tab should be period-centric: one section represents one reporting period and includes rows for all active sprints and assignees.

## When To Use

Activate this skill when the user asks to:

- update the reporting spreadsheet
- create or refresh a biweekly snapshot
- sync YouTrack tickets into the `Tasks` tab
- rebuild or repair the `Summary` tab formulas
- identify unassigned tasks that should probably be reassigned

If the user says `current snapshot`, derive it from the spreadsheet itself:

1. Read `Summary!B2:B4`
2. Interpret them as:
   - `B2` `Snapshot Date`
   - `B3` `Period Start`
   - `B4` `Period End`
3. Treat those values as the canonical active snapshot controls

Fallback only if the summary controls are empty:

1. Read `Tasks`
2. Find the latest populated `Snapshot Key`
3. Parse that key to recover snapshot date and period

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
10. Verify the formulas point at the expected `Tasks` columns and that each data row calculates from the visible fields in that same row.

## Guardrails

- Never silently reassign issues in YouTrack.
- Never write to the spreadsheet or YouTrack without an explicit approval message in the current conversation.
- Never replace formula cells in `Summary` with hard-coded totals.
- Preserve raw task rows in `Tasks`; use `Summary` for aggregation.
- If the meaning of `Completed` versus `In Progress` is unclear for `Staging`, ask the user before changing classification rules.
- Keep the summary section copy-friendly by using visible per-row `Snapshot Date`, `Period Start`, `Period End`, `Sprint`, and `Assignee` fields.
- Avoid absolute row references in summary calculation formulas.

## Expected Outputs

- Updated `Tasks` rows for the requested snapshot
- Updated `Summary` formula section for the requested reporting period
- If needed, a short approval request listing unassigned tickets proposed for reassignment

See [references/REFERENCE.md](references/REFERENCE.md) for the exact column layout, formula pattern, and approval workflow.