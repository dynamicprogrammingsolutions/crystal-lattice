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

- [ ] Current, candidate, and target guidance sources have an inspectable
  maintainer-owned layout outside evaluation fixtures.
- [ ] A deterministic compiler assembles named sections into target bases and
  rejects missing, duplicate, unknown, and unused slots.
- [ ] Current source compiles the existing root `AGENTS.md` exactly before any
  guidance behavior changes.
- [ ] Canonical task guidance retains exact bundled-copy synchronization while
  moving to the shared source model where in scope.
- [ ] Combined-v2 is represented by a candidate directory containing only its
  changed sections and manifest.
- [ ] Evaluation defaults to current sources and can select a candidate
  directory and optional Git reference without hardcoded test revisions.
- [ ] Every run records an exact compilation lock and uses its hash for cache
  and dataset identity.
- [ ] Crystal Lattice, Eleventy, FastAPI, and Flask/Vue compile shared portable
  sections into project-appropriate bases.
- [ ] The old Crystal Lattice-context external-project matrix remains frozen
  and labeled legacy.
- [ ] Corrected current and combined-v2 tests are prepared from the new source
  model and started across the approved model/effort and delivery-mode matrix.
- [ ] Candidate promotion remains a separate manual, human-approved action.

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
- Tests default to current source and may explicitly select a candidate
  directory and optional Git reference.
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
- Approved: keep evaluation-only target bases with the documentation-standard
  suite.
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

- [ ] Implement section, bundle, target, compiler, and lock models.
- [ ] Add deterministic slot and source-selection tests.
- [ ] Extract the current root base and shared/local sections.
- [ ] Prove byte-identical current `AGENTS.md` compilation and drift checking.
- [ ] Migrate canonical task guidance where compatible with subtask 068.
- [ ] Move combined-v2 into an inspectable candidate overlay.
- [ ] Remove hardcoded root baseline/candidate selection from evaluator tests.
- [ ] Add generic runtime bundle, target, and optional-ref selection.
- [ ] Add Eleventy, FastAPI, and Flask/Vue project-specific bases.
- [ ] Include compilation locks in evaluation cache and records.
- [ ] Preserve and relabel the legacy matrix.
- [ ] Prepare corrected baseline and candidate full-matrix commands.
- [ ] Run deterministic verification.
- [ ] Commit migration and prepared test inputs.
- [ ] Start corrected tests in the background.

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