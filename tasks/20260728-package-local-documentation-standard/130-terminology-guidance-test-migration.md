# Migrate terminology/vocabulary guidance tests to the guidance-testing architecture

Follow-up to the guidance-rewrite line (task 067 context). The source
worktrees were removed September 29; their branches are kept and pushed
as reference material — they must NOT be merged.

## Source branches (reference only, never merged)

- `task/20260914-destination-vocabulary-guidance` — vocabulary guidance
  work, evaluation results, fixtures, test plan (tip `207102f2`).
- `task/20260919-destination-terminology-guidance` — terminology
  guidance work incl. promotion/evaluation (5 commits).

For each migrated test, use whichever branch carries the more relevant
version (the terminology branch is the later, evolved line; the
vocabulary branch carries the recorded results and review documents).

## Requirements checklist

- [ ] The relevant tests from the source branches (documentation
  behavior/terminology suites and agent-behavior-verification seeds)
  are re-created on the current guidance-testing architecture: stage
  catalog, harness with stage-declared config+overrides, shared
  execution recipes, parallel runner, records/freeze — not as a copy of
  the source suites' bespoke plumbing.
- [ ] Neither source branch is merged; migrated content is authored in
  the current tree with the branches as read-only reference.
- [ ] A concise, minimal guidance change (candidate section(s) in the
  guidance bundle pipeline) is constructed that makes the migrated
  tests pass — wording deltas only where a test demands them.
- [ ] The migrated tests and the minimal guidance change both pass the
  suite's deterministic gates, and live verification runs through the
  one-command runner.
- [ ] The outcome records which source tests were migrated, dropped as
  obsolete, or redesigned, and why.

## Execution plan

Status: Draft

1. Inventory both branches' test surfaces (seeds, revised-consumer
   tests, review/test-plan documents) and classify each item: migrate
   as-is, redesign for the stage/harness architecture, or drop as
   superseded by the task-guidance suite's coverage.
2. Pick the minimal set that still exercises the terminology/vocabulary
   guidance claims (the source evaluation results identify which seeds
   discriminated).
3. Author the stage(s)/cases on the current architecture, reusing the
   planning/producer patterns from subtask 125.
4. Run migrated tests against the current promoted guidance; record
   failures; write the minimal candidate wording that closes them;
   verify via the candidate pipeline (compile/check/write flow).
5. Verify deterministically, then one live runner slice; update the
   suite docs pages.

### Implementation decisions and open questions

- Which guidance section owns the terminology wording (documentation
  section vs a new section) is open until the failures are seen —
  decide from the actual failing claims, not in advance.

### Documentation

- Suite test-plan/test-cases pages gain the migrated stage(s);
  README of the owning guidance section documents the new wording.

### Task checklist

- [ ] Branch inventory + classification
- [ ] Stage/case authoring on the new architecture
- [ ] Minimal candidate guidance change
- [ ] Deterministic + live verification
- [ ] Migration record + docs

### Requirement verification

- No merge commits from either source branch in the current tree
  (branch ancestry check).
- Migrated tests pass with the minimal candidate promoted; the same
  tests fail without it (or the wording is recorded as already-covered).
- One live runner slice through the new stages completes with records
  and freeze output.

### Additional implementation verification

- The classification record maps every source seed/test to its
  disposition; nothing silently disappears.
