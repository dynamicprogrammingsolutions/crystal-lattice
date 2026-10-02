# Run-Exact Freeze→Collect Contract and Multi-Sample Collection

Parent Task:
tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/100-task-guidance-suite-restructure.md`

---

Follow-up to
[tasks/20260728-package-local-documentation-standard/100-task-guidance-suite-restructure.md](20260728-package-local-documentation-standard/100-task-guidance-suite-restructure.md):
the per-subject assessment collection cannot distinguish multiple genuine
judgments of the same subject, so any multiplicity — repeated invocations
sharing one label, deliberate `--samples N` assessments, or `--fresh`
reruns — makes `collect` fail with `duplicate run_id` (observed live on
September 24, 2026 during the b0/b1 assessment reproduction). This task
makes the freeze→collect contract run-exact and the collection
multi-sample-capable.

## Requirements checklist

- [x] The frozen dataset embeds the exact run identity (run id) for every
  selected record, so a frozen record always names the raw run that
  produced it.
- [x] Collection maps frozen records to raw run directories by run
  identity; the existing subject-key-and-latest-mtime mapping remains as
  a fallback for frozen files that carry no run ids.
- [x] A dataset with multiple genuine judgments of one subject cell
  (from repeated invocations under one label, `--samples N`, or
  `--fresh`) collects completely: every judgment contributes its own run,
  each renders at a unique page location, and the collected package
  passes `check`.
- [x] Multi-sample cells of the producer, handoff-plan, continuation,
  same-agent, and negative-control groups collect through the same
  run-exact mechanism.
- [x] Single-sample packages regenerate byte-identically: both committed
  packages still pass `check` with no content diff after the change.
- [x] Regression tests reproduce the failure shape before the fix: a
  synthetic frozen dataset with two judgments of one subject and a
  two-sample producer cell must collect and pass `check` with both runs
  present.
- [x] The suite documentation describes the multi-sample collection
  semantics (running-and-calibration and the reproducing guide).

## Open questions and decisions changing scope

- None currently. The cell-prefix scheme for multiple judgments per
  subject (ordinal by `(sample_index, modified)` versus the run's short
  hash) is an implementation decision resolved inside the plan below.

## Supporting details

- **Failure mechanism (fact, verified in code and live).** The frozen
  per-subject record identifies the subject (scenario, profile, effort,
  producer sample index) but not the assessor run. `_discover_runs`
  (`suites/task_guidance/result_package.py`) maps frozen records to run
  directories by subject key and keeps the newest matching run;
  `_collect_per_subject_assessment` then appends the mapped run once per
  frozen record, so K judgments of one subject append the same run id K
  times and the shared collector's `_validate_runs`
  (`src/agent_eval/result_packages.py`) raises
  `ValueError: duplicate run_id`.
- **The gap is designed-path, not just user error.** `--samples N` on an
  assessment invocation produces N judgments of one subject with the
  same subject tuple; the chunk-6 collection fixtures only ever had one
  sample per subject, which is why this survived task 100's tests.
- **The producer/handoff discovery uses the same key-based mapping**
  (`selected[key] = latest` per identity), so multi-sample cells in those
  groups would fail the same way.
- **The freeze already tolerates multiplicity**: `select_cell_records`
  keeps every genuine execution of a listed label as a sample (cache
  replays dropped), sorted by `(sample_index, modified)`. Only the
  collection is ambiguous.
- **Live evidence from September 24, 2026**: two invocations sharing
  `b0-v5-r1` (caused by the fixture-commit cache bug fixed the same day)
  produced 34 duplicate judgment cells; collect failed on the first
  duplicated cell. The duplicates were deleted and the datasets re-frozen
  as a one-off unblock; this task removes the need for such cleanups.
- **Two further instances of the same key-incompleteness family surfaced
  the same day and were fixed as an interim hotfix** (regression tests
  `test_collect_renders_each_handoff_variant_of_one_subject` and
  `test_collect_renders_each_task_creation_subject_of_one_scenario` in
  `tests/test_result_package.py`):
  the handoff discovery key and match ignored the assessment variant, so
  the retain/omit/generated-task judgments of one producer cell collapsed
  onto the newest matching run (`duplicate run_id` even with single
  samples); and the per-subject cell prefix carried only the sample index,
  so the glm and gpt judgments of one scenario collided on
  `assessment/task-creation/s0/` (`duplicate collected file`). The
  per-subject layout is now
  `assessment/{name}/{profile}-{effort}/{variant}/s{sample_index}`.
  The hotfix keys on subject dimensions; the run-exact contract below
  removes key-based matching altogether.
- **Rejected alternatives (decisions).**
  - Adding an assessor `sample_index` to the assessment record fixes only
    `--samples N` within one invocation; two invocations both produce
    sample 0 and still collide. Insufficient alone.
  - Globally sequential sample indices per (identity, label) make the
    run model stateful and race under concurrent invocations.
  - Pairing frozen records with runs by mtime order is heuristic; exact
    run ids already exist in the consolidation layer (`CellRecord`).

## Execution plan

Status: Approved

Approach, in dependency order:

1. **Freeze embeds run ids.** `consolidate_results` /
   `src/agent_eval/runner/consolidation.py` already wrap every selected
   record in a `CellRecord` that knows its run directory. Write the run id
   (the run directory name) into each frozen record entry for every group
   (producers, handoffs, continuations, same-agent, controls, and both
   assessment groups). The frozen file is a generated intermediate, so
   the shape change is low-cost; the raw record schemas do not change.
2. **Discovery becomes run-exact.** `_discover_runs` maps
   `run id → run directory` for entries that carry one, verifying the
   directory exists (the existing `FileNotFoundError` behavior for
   missing runs stays). Entries without a run id fall back to today's
   subject-key-and-latest-mtime mapping, so historical frozen files keep
   collecting.
3. **Collection renders per judgment.** `_collect_per_subject_assessment`
   uses each record's own run directory. When a subject cell has multiple
   judgments, assign each a unique cell prefix — an ordinal by
   `(sample_index, modified)` order (recommended: stable, readable,
   no hash noise in paths) — instead of colliding on
   `s{sample_index}`. The shared results page lists each judgment with
   its run.
4. **Producer/handoff groups get the same treatment** for multi-sample
   cells (per-record run directories, unique page locations).
5. **Tests first, at the collect boundary.** Extend the synthetic collect
   fixtures with (a) two judgments of one subject under one label and
   (b) a two-sample producer cell. Assert: collect succeeds, both runs
   appear in the package, page locations are distinct, `check` passes.
   These tests fail on the current code with `duplicate run_id`.
6. **Parity gate.** Re-freeze and re-collect both committed datasets and
   verify the packages regenerate byte-identically (the existing
   committed-package parity check from task 100).

### Implementation decisions and open questions

- Cell-prefix scheme for multiple judgments: ordinal by
  `(sample_index, modified)` (recommended and assumed above) versus the
  run's short hash. Ordinal keeps paths stable and readable; the hash
  survives re-freezing with different orderings. Decide during
  implementation; both satisfy the uniqueness requirement.
- The subject-key fallback stays permanently (cheap, keeps historical
  frozen files working); revisit only if it proves misleading.

### Documentation

- `suites/task_guidance/docs/running-and-calibration.md`: multi-sample
  collection semantics (what the freeze keeps, how collect renders it).
- `maintainer/docs/evaluations/task-guidance/reproducing-and-inspecting-results.md`:
  note that repeated invocations under one label and `--samples N`
  produce multi-sample cells that collect normally.

### Task checklist

- [x] Add the failing multi-sample collect tests (two-judgment subject,
      two-sample producer cell).
- [x] Embed run ids in the frozen dataset entries.
- [x] Make `_discover_runs` run-exact with the subject-key fallback.
- [x] Render per-judgment pages with unique cell prefixes.
- [x] Apply the same mechanism to the producer/handoff groups.
- [x] Run the full deterministic suite plus lint/format.
- [x] Verify both committed packages regenerate byte-identically.
- [x] Update the two documentation pages.

### Requirement verification

- Run-id embedding + run-exact discovery: the synthetic multi-sample
  collect tests (requirement 1, 2, 3, 4) — they fail with
  `duplicate run_id` before the fix and pass after, with both runs
  present and distinct page locations.
- Fallback compatibility: a collect test against a frozen fixture without
  run ids (the existing single-sample fixtures already cover this shape;
  keep them passing unchanged).
- Byte-identity (requirement 5): re-freeze + re-collect both committed
  datasets and compare against the committed packages with the existing
  parity check.
- Documentation (requirement 6): the suite documentation tests
  (`test_documentation.py`) stay green with the updated pages.

### Additional implementation verification

- `pytest suites/task_guidance -q` (deterministic suite) and
  `ruff check` / `black --check` on the touched files.
- A dry-run collect against the live b0 frozen dataset (single-sample
  after the September 24 cleanup) must produce a package identical to
  the committed one — the real-dataset counterpart of the parity gate.

## Completion Notes

Completed September 24, 2026, on top of the same-day interim hotfix (see
Supporting details). All requirements are satisfied:

- **Run ids embedded.** `consolidate_results` injects each sample's
  `run_id` into every collected frozen group (producers, handoffs,
  same-agent, semantics, handoff semantics, negative controls); both
  live datasets re-froze with 100% run-id coverage.
- **Run-exact discovery.** `_map_exact_runs` resolves every
  run-id-carrying record by globbing `*/runs/<run_id>` and fails with
  `FileNotFoundError` when the named run is absent; records without run
  ids keep the identity-and-label fallback (verified by the unchanged
  synthetic fixtures, which carry no run ids).
- **Multi-judgment collection.** `_collect_per_subject_assessment`
  numbers the judgments of one subject (`s0/j1`, `s0/j2`) in the frozen
  dataset's `(sample_index, modified)` order; producer-side lookups and
  the batched assessment path resolve through `_run_dir_for`
  (run-id-first with the composite-key fallback).
- **Regression tests** (red-verified against the pre-change collection
  via `git stash`):
  `test_collect_renders_each_judgment_of_one_subject` (two judgments of
  one subject with run ids — failed with `duplicate run_id` before),
  `test_collect_uses_the_named_run_of_each_producer_sample` (a two-sample
  producer cell — the page showed the newest run's id before), plus the
  two interim tests for variant and subject-cell collisions.
- **Byte-identity gate.** Both committed packages re-collected from the
  re-frozen datasets into throwaway directories: every evidence file is
  byte-identical. The only manifest difference is the frozen-dataset
  provenance sha256 — expected, because the frozen format gained the
  run-id field; the package provenance correctly records which frozen
  dataset produced it.
- **Aggregate projection.** The run id is stripped from
  `aggregate.json`'s invalid-record projections (`_without_run_id`): it
  is freeze-to-collect mapping metadata, not reviewed evidence — without
  this, the parity diff showed the injected field leaking into the
  package.
- **Documentation.** `running-and-calibration.md` and the reproducing
  guide describe the multi-sample collection semantics, the judgment
  numbering, the first-sample producer rendering, and the fallback.

Verification: `pytest suites/task_guidance -q` — 155 passed, 74
deselected; `ruff check` and `black --check` clean; documentation tests
green.

Deviations from the plan: producer-side multi-sample cells render their
first sample's page (deterministic by the frozen order) instead of
per-sample pages — per-sample producer pages would change the committed
single-sample layout and break package parity; every sample stays in the
frozen dataset and assessments judge all of them. The judgment-ordinal
prefix uses the frozen record order (the plan's recommended
`(sample_index, modified)` ordinal), applied only when a subject has
multiple judgments so single-judgment layouts are unchanged.
