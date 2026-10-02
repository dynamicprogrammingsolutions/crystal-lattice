# Maintainer documentation ownership migration inventory

Date: September 18, 2026

## Added

- `maintainer/docs/index.md` as the cross-cutting maintainer entry point.
- Instruction-delivery, guidance-workflow, evaluation-status, ownership, and
  evaluation-result indexes under `maintainer/docs/`.
- Separate reusable documentation-guidance and Crystal Lattice integration
  specifications.
- Package-owned framework, Crystal Lattice environment, and compiler
  specification routes.
- Suite-owned documentation, requirements, scenario index, compiled-matrix
  freezer, and frozen September 18 records.

## Moved

- Human-readable dated evaluation reports moved from the old combined
  specification into `maintainer/docs/evaluations/documentation-guidance/`.
- Documentation-guidance seeds, scenarios, and semantic targets moved to
  `maintainer/agent-evaluation/suites/documentation_standard/`.
- The agent-evaluation framework specification moved beside the package and
  was separated from Crystal Lattice environment and suite requirements.
- The guidance compiler specification moved beside the compiler and was
  narrowed to generic compilation mechanics.
- The former combined documentation specification moved under
  `maintainer/docs/development/specifications/` and split into reusable
  guidance and Crystal Lattice integration.
- The one-off Kindle review-bundle instructions moved to `archive/reviews/`
  because they are not current operating guidance.

## Edited

- Root `AGENTS.md` and its maintained target now route maintainers to the new
  specification locations.
- The Crystal Lattice documentation addendum explains cross-cutting versus
  package-owned maintainer specifications.
- Agent-evaluation and guidance README, AGENTS, and development indexes route
  to package-owned specifications and suite docs.
- Scenario traceability links point to current requirement/specification
  owners and current two-page guidance.
- Evaluation records now distinguish instruction source from structured
  delivery role and strategy.
- Task-output capture recovers retained untracked files after isolated
  workspaces are cleaned.

## Kept in place

- `docs/development/documentation.md` remains the reusable guidance read by
  ordinary contributors and agents.
- `docs/development/crystal-lattice-documentation.md` remains the current
  repository-specific addendum.
- `maintainer/guidance/current/`, `candidates/`, and `targets/` remain source
  inputs rather than documentation.
- Generic `agent_eval` user documentation remains under
  `maintainer/agent-evaluation/docs/`.
- Frozen JSON remains under the documentation suite because it is
  machine-readable suite evidence.
- Historical root-guidance snapshots remain byte-for-byte unchanged because
  they represent the exact text tested by older comparisons.
- Task files retain execution history; current links and active terminology
  were updated without rewriting historical findings.

## Removed

- The central `maintainer/specifications/` directory.
- The mixed specification/result/scenario index under
  `agent-behavior-verification/`.
- Documentation-suite requirements from the generic evaluation-framework
  ledger.
- Documentation-specific matrix and portable-section requirements from the
  generic compiler ledger.

## Deferred

- A promotion decision for combined-v2, pending the focused completeness
  correction described by the corrected default-runner report.
- Committing the already compiled IOCharts migration in the IOCharts Frontend
  repository.
