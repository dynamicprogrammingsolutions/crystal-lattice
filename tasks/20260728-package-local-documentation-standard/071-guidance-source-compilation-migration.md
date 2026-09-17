Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md`
- `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`
- `tasks/20260728-package-local-documentation-standard/069-task-guidance-scope-and-decomposition.md`

Specification:

- `maintainer/specifications/agent-guidance-compilation/index.md`

Requirement IDs:

- `GCOMP-001`–`GCOMP-013`

# Guidance source and compilation migration

Migrate root and evaluation guidance from hardcoded files and Python
replacement strings to deterministic section bundles, project-specific base
files, candidate overlays, compilation locks, and runtime-selected evaluation
sources. Preserve the old-context matrix as legacy evidence, then start the
corrected current/candidate comparison.

## Requirements checklist

- [x] Current, candidate, and target guidance sources have an inspectable
  maintainer-owned layout outside evaluation fixtures.
- [x] A deterministic compiler assembles named sections into target bases and
  rejects missing, duplicate, unknown, and unused slots.
- [x] Current source compiles the existing root `AGENTS.md` exactly before any
  guidance behavior changes.
- [x] Canonical task guidance retains exact bundled-copy synchronization while
  moving to the shared source model where in scope.
- [x] Combined-v2 is represented by a candidate directory containing only its
  changed sections and manifest.
- [x] Evaluation defaults to current portable sources and can select a
  candidate bundle plus consuming-repository target directory without
  hardcoded test revisions.
- [x] Every run records an exact compilation lock and uses its hash for cache
  and dataset identity.
- [x] The compiler reads portable sections from Crystal Lattice and
  project-specific templates/sections from an independently owned consuming
  repository path.
- [x] The old Crystal Lattice-context external-project matrix remains frozen
  and labeled legacy.
- [ ] A consuming repository validates current and candidate portable guidance
  with its own target and representative model/effort coverage.
- [x] Candidate promotion remains a separate manual, human-approved action.

## Supporting details

### Facts

- The September 17 legacy matrix has 84 producer records and 84 valid semantic
  assessments.
- Combined-v2 improves aggregate scope restraint and testing but regresses GPT
  high/xhigh/max requirement completeness.
- The legacy fixtures inject full Crystal Lattice root guidance into unrelated
  repositories, so their results are comparison evidence rather than the
  corrected portable baseline.
- The current evaluator pins root baseline commit `4a0c078c` and synthesizes
  candidate sections in
  `maintainer/agent-evaluation/suites/documentation_standard/requirement_quality.py`.
- Raw run records preserve effective messages, but the candidate is not owned
  as ordinary maintained guidance source.

### Approved decisions

- Candidate guidance is a maintained source variation, not a fixture.
- Current and candidate bundles compile through target-specific base files.
- Base files use simple named slots and no general template language.
- Tests default to current portable source and may explicitly select a
  candidate bundle and consuming-repository target directory.
- No test remains permanently tied to a candidate or commit.
- Current repository files use the same compiler and are regenerated manually
  only after successful testing and human approval.
- External project tests use their own bases with the same portable sections.
- The old matrix is called legacy or old comparison evidence, not the future
  transfer/stress mode.
- The current baseline and latest candidate are rerun after migration.

## Execution plan

Status: Approved

### Approach

Establish the generic source and compilation layer first, prove exact current
output, migrate the candidate and evaluator selection, add corrected project
bases, then start the paired corrected matrix. Do not change the accepted root
guidance while migrating its source representation.

### Implementation decisions and open questions

- Approved: use `maintainer/guidance/` for generic compiler, current bundle,
  candidates, and production targets.
- Revised and approved September 17, 2026: do not keep consuming-project target
  bases in Crystal Lattice. Each consuming repository owns its templates and
  local sections.
- Revised and approved September 17, 2026: evaluation sample projects are
  repository-owned fixtures, not consuming repositories. Store each fixture's
  target template and factual local sections beside that fixture. This does
  not authorize storing a real consuming repository's templates or local
  guidance.
- Approved: target selection uses an explicit consuming-project override when
  supplied, otherwise the requirement-quality scenarios use their fixture-owned
  targets.
- Approved: fixture project context contains repository facts only and does not
  teach the requirement or testing behavior being evaluated.
- Approved: use complete Markdown sections inserted by
  `<!-- guidance-slot:<name> -->` placeholders.
- Approved: use TOML manifests for bundles, candidates, and targets.
- Approved: keep provenance out of compiled model instructions and in lock
  files and evaluation records.
- Approved: preserve current task-guidance synchronization; do not silently
  replace the bundled-copy workflow.
- Local implementation choice: command/module names and internal Python types
  may be selected for the smallest maintainable implementation.
- Open only if encountered: a current-file byte-identity boundary that cannot
  be expressed without adding template logic must be reported before expanding
  the slot language.

### Documentation

- Add a concise maintainer guide under `maintainer/guidance/`.
- Update the agent-evaluation development guide with current/candidate/ref
  commands and corrected-target terminology.
- Keep ordinary root guidance free of compiler-maintenance explanation.
- Update the specification requirements and this task with exact evidence.

### Task checklist

- [x] Implement section, bundle, target, compiler, and lock models.
- [x] Add deterministic slot and source-selection tests.
- [x] Extract the current root base and shared/local sections.
- [x] Prove byte-identical current `AGENTS.md` compilation and drift checking.
- [x] Migrate canonical task guidance where compatible with subtask 068.
- [x] Move combined-v2 into an inspectable candidate overlay.
- [x] Remove hardcoded root baseline/candidate selection from evaluator tests.
- [x] Add generic runtime bundle and independently located target selection.
- [x] Support target templates and local sections outside the Crystal Lattice
  repository.
- [x] Restore fixture-owned targets under each requirement-quality fixture and
  reinstate scenario defaults without weakening the external target override.
- [x] Include compilation locks in evaluation cache and records.
- [x] Preserve and relabel the legacy matrix.
- [x] Document a machine-local absolute-path compilation command.
- [x] Run deterministic verification.
- [x] Commit migration and prepared test inputs.
- [ ] Run consumer-owned current/candidate behavioral comparison when a
  consuming repository supplies its target and tasks.

## Implementation Notes

- September 17, 2026: Added `maintainer/guidance/` with TOML bundles and
  targets, named Markdown slots, deterministic compilation/check/write
  commands, Git-ref selection, input/output locks, and manual promotion.
- September 17, 2026: Extracted current root and TASKS source without changing
  either compiled file. Current root SHA remains `a56c068e…`; task guidance
  remains `191fc888…`; Crystal Lattice combined-v2 remains `cf943bb…`.
- September 17, 2026: The exact current Crystal Lattice root keeps a full
  `root-testing` compatibility section because splitting its interleaved
  generic and package-specific rules would change current instructions before
  guidance acceptance; `GCOMP-003` remains partially implemented for that
  production source boundary.
- September 17, 2026: Active producer, semantic, and pairwise suites select a
  bundle and consuming-repository target directory at runtime. The old
  hardcoded variant functions remain only for reproducing frozen legacy
  evidence.
- September 17, 2026: A corrected in-repository matrix was started using
  project targets stored under Crystal Lattice, then invalidated when the user
  clarified that consuming repositories exclusively own their templates and
  local sections. Its semantic run was stopped and its local scratch results
  are not evidence. The compiler and tests were revised to use independent
  paths instead.
- September 17, 2026: Clarified that the prior correction was too broad.
  Sample projects are maintained test fixtures and may own fixture-only target
  templates in this repository. The clean boundary is now: portable sections
  and compiler under `maintainer/guidance/`; Crystal Lattice's own target under
  `maintainer/guidance/targets/`; fixture targets beside their evaluation
  fixtures; real consuming-project targets only in those projects. The
  corrected producer and semantic runs must restart from the resulting
  compiler locks.
- September 17, 2026: Restored test-only targets beside the three
  requirement-quality fixtures, marked them `kind = "fixture"`, and reinstated
  scenario defaults. `AGENT_EVAL_GUIDANCE_TARGET` remains the explicit
  consuming-project override; task guidance remains separately delivered by
  Crystal Lattice runtime configuration.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Source and compiler | Deterministic tests compile valid slots and reject every invalid mapping class. |
| Current-file preservation | Compiler output and root `AGENTS.md` are byte-identical; check mode detects a deliberate temporary drift. |
| Candidate inspection | Combined-v2 candidate manifest and changed Markdown sections reproduce the committed legacy candidate hash. |
| Runtime selection | The same test runs current checkout, explicit candidate, and optional historical ref without code edits. |
| Project isolation | External compiled guidance contains its own project context and shared section hashes, without Crystal Lattice repository instructions. |
| Provenance | Run records and cache identity contain the same compilation hash and input/output lock. |
| Corrected comparison | Current and combined-v2 background matrices start from the corrected target bases across approved profiles and modes. |

### Additional implementation verification

- Run compiler and evaluator unit tests.
- Run canonical/bundled TASKS parity when canonical source is touched.
- Regenerate and compare frozen compiler snapshots deterministically.
- Confirm no compiler or candidate source is placed under a fixture directory.