Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md`
- `tasks/20260728-package-local-documentation-standard/069-task-guidance-scope-and-decomposition.md`
- `tasks/20260728-package-local-documentation-standard/071-guidance-source-compilation-migration.md`

# Maintainer documentation ownership migration

Separate durable maintainer concepts and evaluation results from target
specifications, move reusable product specifications to their owning packages,
separate reusable guidance from Crystal Lattice integration, and correct the
instruction-delivery model without weakening historical evidence.

## Requirements checklist

- [x] Maintainers have a short documentation entry point for cross-cutting
  concepts, workflows, current guidance status, and human-readable evaluation
  results.
- [x] Durable guidance distinguishes instruction source, delivery channel,
  authority, availability or discovery, and observed use; maintained guidance
  no longer uses “always loaded” as a substitute for those distinctions.
- [x] Human-readable evaluation summaries are outside specification
  directories, while frozen machine-readable records remain owned by their
  evaluation suite.
- [x] The generic `agent_eval` framework documentation and specification are
  package-owned and do not contain documentation-guidance consumer
  requirements.
- [x] The Crystal Lattice evaluation environment and documentation-guidance
  suite have separate, explicit ownership from the reusable evaluation
  kernel.
- [x] The guidance compiler documentation and specification are package-owned
  and describe a generic compiler rather than requiring documentation-specific
  section names or model matrices.
- [x] Reusable documentation and specification guidance is specified
  separately from the narrow Crystal Lattice repository integration.
- [x] Documentation-guidance scenarios, targets, suite procedures, and frozen
  evidence remain discoverable from the owning evaluation suite.
- [x] Existing maintained links, test paths, requirement evidence, and
  generated guidance references are updated to the new ownership paths.
- [x] Historical reports retain their tested facts and dates; interpretation
  notes clarify obsolete delivery terminology without rewriting past results.
- [x] The portable root-guidance matrix is frozen and summarized in
  a durable human-readable report with exact source and delivery provenance.
- [x] A final ownership inventory explains what was added, edited, moved,
  retained, archived, or deliberately left in place and why.

## Scope and supporting facts

- `maintainer/` is a publication and audience boundary, not a document role.
  It now contains reusable tools, tool users, tool developers, specifications,
  suite-specific scenarios, raw evidence, and interpreted results.
- The generic documentation structure applies inside `maintainer/`: package
  users are maintainers operating a tool, while package developers modify the
  tool itself.
- Direct system/developer instruction delivery has different authority from
  repository text discovered or read as a file. Evaluation must record both
  the maintained source and the effective delivery channel.
- The September 18 portable matrix completed 84 producers, 12 semantic
  batches, and 42 pairwise reviews without timeouts. Its local records must be
  frozen before suite paths change.
- Existing legacy and focused reports remain historical evidence and are not
  overwritten by the new matrix.

## Execution plan

Status: Approved

### Approach

Establish the new maintainer documentation entry points first, freeze the
completed matrix, then move content according to ownership. Keep reusable
product documentation and specifications local to `agent-evaluation/` and
`guidance/`; keep cross-cutting concepts, interpreted results, and
documentation-guidance specifications under `maintainer/docs/`. Move
documentation-suite scenarios and procedures into the suite without changing
their tested meaning. Update links and code mechanically, then perform
content-scope and behavior verification.

### Implementation decisions and open questions

- Approved: use `maintainer/docs/` for cross-cutting maintainer concepts,
  workflows, current status, and interpreted evaluation results.
- Approved: use `maintainer/docs/development/` for cross-cutting maintainer
  architecture and specifications.
- Approved: move the generic evaluation-kernel specification under
  `maintainer/agent-evaluation/docs/development/specifications/`.
- Approved: separate the reusable kernel from the Crystal Lattice environment
  and move documentation-suite-specific requirements out of both.
- Approved: move the compiler specification under
  `maintainer/guidance/docs/development/specifications/` and keep section
  semantics outside the generic compiler contract.
- Approved: split reusable documentation guidance from Crystal Lattice
  integration under `maintainer/docs/development/specifications/`.
- Approved: put dated human-readable results under
  `maintainer/docs/evaluations/`; preserve frozen JSON with the suite.
- Approved: put scenario definitions and suite operation documentation under
  `maintainer/agent-evaluation/suites/documentation_standard/`.
- Approved: preserve historical wording when it records what was actually
  tested, adding a clarification rather than silently rewriting history.
- Approved: archive or remove one-off review material rather than presenting
  it as current maintainer guidance.
- Local implementation choice: use the smallest directory depth that keeps
  ownership clear; omit empty indexes and compatibility pointers when all
  internal references can be updated atomically.

### Documentation

- Add a maintainer documentation index.
- Add the canonical instruction-delivery and authority concept page.
- Add a concise guidance-maintenance workflow and current-guidance status.
- Move and index human-readable evaluation reports.
- Add package-local indexes and development/specification routes for
  `agent-evaluation` and `guidance`.
- Add a suite-local documentation index for the documentation-guidance suite.
- Add cross-cutting specification indexes for reusable guidance and Crystal
  Lattice integration.

### Task checklist

- [x] Freeze the completed September 18 compiled-guidance matrix without
  overwriting legacy results.
- [x] Add maintainer documentation and development entry points.
- [x] Add instruction delivery/authority terminology and update maintained
  uses of “always loaded.”
- [x] Move human-readable result reports and update their index.
- [x] Move scenario and seed pages to the documentation suite.
- [x] Move suite-specific operational documentation to the suite.
- [x] Move and separate the evaluation framework specifications.
- [x] Move and narrow the guidance compiler specification.
- [x] Split reusable guidance and Crystal Lattice integration specifications.
- [x] Update requirement ownership and evidence links without losing live
  state.
- [x] Update code, tests, README files, AGENTS routing, and task references.
- [x] Classify the one-off review bundle and other retained maintainer files.
- [x] Run focused and broad verification.
- [x] Record completion notes and the final ownership inventory.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Instruction model | Durable concept page and maintained guides distinguish source, delivery, authority, availability, and observed reads; terminology search finds no ambiguous current use of “always loaded.” |
| Result ownership | Dated Markdown summaries resolve under `maintainer/docs/evaluations/`; frozen JSON and run-record tooling remain suite-owned. |
| Framework ownership | Generic framework tests and docs contain no documentation-guidance requirement IDs or mandatory documentation-suite models/scenarios. |
| Compiler ownership | Compiler specification and tests use generic section/target terminology; documentation-specific section requirements are owned elsewhere. |
| Guidance separation | Reusable guidance and Crystal Lattice integration have distinct specifications and requirements with explicit relationship links. |
| Suite ownership | Scenario pages, targets, commands, semantic review, and freezing procedures are reachable from the suite-local index. |
| Link and path migration | Repository link validation, targeted path searches, Python collection/imports, and affected tests pass with no stale maintained references. |
| Current matrix | Frozen records contain 84 producers and recovered task files, 42 valid root-only semantic assessments, and 21 valid root-only pairwise reviews with exact compiled guidance and delivery provenance. The report explicitly records unavailable task-mode interpretation rather than counting failed stages as evidence. |

### Additional implementation verification

- Run `pytest maintainer/agent-evaluation/tests -q`.
- Run focused documentation-standard deterministic tests.
- Run compiler checks and canonical/bundled task-guidance synchronization.
- Run Ruff and Python compilation over moved evaluation and guidance code.
- Validate relative Markdown links under `maintainer/`.
- Inspect every remaining file under the old specification path before
  deleting that path.
- Compare Git move similarity and review the final added/moved/edited/retained
  inventory.

## Implementation Notes

- September 18, 2026: Moved cross-cutting maintainer concepts and interpreted
  results under `maintainer/docs/`; moved package specifications beside
  `agent-evaluation` and `guidance`; moved scenarios, targets, and suite
  procedures to the documentation-guidance suite.
- September 18, 2026: Split reusable documentation guidance from Crystal
  Lattice integration. Split the generic evaluation kernel from the Crystal
  Lattice environment and documentation suite. Narrowed the compiler
  specification to generic section/target mechanics.
- September 18, 2026: Added the instruction-delivery concept and corrected
  current contributor, suite, guidance, task, and root routing language.
  Historical reports remain unchanged except for moved links and a current
  interpretation note.
- September 18, 2026: Found that all 42 task-mode agents created task files,
  but the recorder read the cleaned live workspace and stored empty
  `generated_files`. Added recovery from retained raw workspace evidence and a
  deterministic regression test.
- September 18, 2026: Found that task mode concatenated root `AGENTS.md` and
  `TASKS-v7` into one system/endpoint-instructions delivery. The resulting
  task files are retained, but task-mode semantic and pairwise conclusions are
  unavailable for the intended repository-file/developer-message comparison.
- September 18, 2026: Retried the two invalid root-only pairwise JSON
  responses successfully. The frozen result now has 84 producers, 42
  root-only semantic assessments, and 21 root-only pairwise reviews.

## Completion Notes

The migration established clear document roles without changing the reusable
guidance content under test. Human-readable results are now maintainer
documentation, scenario definitions and frozen JSON are suite-owned, and
specifications contain intended contracts rather than result narratives.

Verification completed:

- 110 maintainer agent-evaluation tests;
- 2 canonical/bundled task-guidance synchronization tests;
- 15 documentation-site assembly tests;
- Ruff and Python compilation;
- exact current guidance compilation and task-guidance synchronization;
- deterministic compiled-matrix regeneration;
- maintained Markdown links;
- stale-path and requirement-ID uniqueness checks.

The current root-only candidate evidence is complete and favors combined-v2
overall, but promotion remains blocked by two partial high-assurance
requirement sets and unavailable task-mode integration evidence. The next
calibration should correct delivery layering and rerun task mode only.
