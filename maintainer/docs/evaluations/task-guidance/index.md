# Task-guidance evaluation

This area explains how task-guidance changes are evaluated, what each test case
contains, and what the latest runs found. It is the human-review entry point;
evaluator implementation and complete machine records remain with the owning
suite.

Read these pages in order:

1. [Test plan](test-plan.md) — defines the three evaluation stages, evidence,
   model matrix, and acceptance gates.
2. [Test cases](test-cases.md) — describes the six repository tasks and the
   behavior each one tests.
3. [Current-guidance baseline results](20260919-current-guidance-baseline-results.md)
   — records the latest completed evidence and limitations.
4. [Task-mechanics candidate results](20260919-task-mechanics-b1-results.md)
   — compares the first candidate with the baseline and records the revised
   practical-baseline direction.
5. [Task-mechanics candidate v2 results](20260925-task-mechanics-b1v2-results.md)
   — the decisive-check and design-visibility calibration on the per-subject
   assessor.
6. [Task-mechanics candidate v3 results](20260926-task-mechanics-b1v3-results.md)
   — the structure-choice rewording; strongest task-creation results so far.
7. [Task-quality coverage results](20260926-task-quality-coverage-results.md)
   — the quality-assessment and generated-file planning stages on the v3
   outputs; two fabricated plans found, fresh-agent planning confirmed.
8. [Task-kind baseline results](20260926-task-kind-baseline-results.md)
   — the four task-kind scenarios' first run on v3; conditional-plan
   guidance gaps caught in 1-of-3 samples each.
9. [Reproducing and inspecting results](reproducing-and-inspecting-results.md)
   — provides the commands, identities, raw-record paths, report-generation
   flow, and result-package navigation.

## Current status

[Stage B0 — Current-guidance baseline](test-plan.md#stage-b0--current-guidance-baseline)
is complete: all task-creation and fresh-agent cells ran, five of six
same-agent chains are valid, and the invalid GPT selected-filter chain is
preserved as current behavior.

[Stage B1 — Task-mechanics candidate](test-plan.md#stage-b1--task-mechanics-candidate)
was compiled and evaluated. Candidate v1 is not promoted verbatim, but its
strong decomposition gains are the foundation of a practical baseline with
focused plan-preservation, design-visibility, dependency, and connected-test
clarifications.

Candidates
[v2](20260925-task-mechanics-b1v2-results.md) and
[v3](20260926-task-mechanics-b1v3-results.md) ran on the restructured
per-subject suite. V3 removes the ask-and-stop structure-choice failure and
records the strongest task-creation results; its matrix is complete after
a transient provider outage was rerun.

The practical task-mechanics baseline (v3) was **promoted on September 26,
2026** after the focused confirmation evidence (see the
[quality coverage](20260926-task-quality-coverage-results.md) and
[kind baseline](20260926-task-kind-baseline-results.md) reports) and
explicit approval: the candidate's tasks-v7 section replaced
`maintainer/guidance/current/sections/tasks-v7.md` and the compiled
outputs were regenerated (commit `4fb5f6a6`). The six remaining
task-file quality gaps are recorded as the next candidate cycle's
calibration targets in
`tasks/20260728-package-local-documentation-standard/120-task-file-quality-coverage.md`.

[Stage B2 — Guidance-placement confirmation](test-plan.md#stage-b2--guidance-placement-confirmation)
has not started and remains blocked on approval; it now builds on the
promoted v3 baseline.

## Machine evidence

Each completed evaluation is preserved as a self-contained result package
under `results/`:

- [Current-guidance baseline package](results/20260919-current-guidance-b0/index.md)
- [Task-mechanics candidate package](results/20260919-task-mechanics-b1/index.md)

A package holds the committed machine records (per-run `run.json`, session
transcripts, generated task files, semantic assessments, aggregate matrix
source, usage and cost inventory) plus regenerated human views
([matrix](results/20260919-task-mechanics-b1/matrix.md),
[costs](results/20260919-task-mechanics-b1/costs.md)). Start from its
`index.md`; every judgment links the exact run or stage directory it is about.

The [scenario input definitions](scenarios/index.md) export holds what the
evaluations fed the models: reviewed targets, exact prompts, prompt
templates, sanitized effective configs, compiled system messages, and every
file added to the workspaces beyond the repository checkout, with one
`input.md` per stage and assessment. Git tracks its evolution between
evaluations; each result package freezes its own copies.

The evaluator's detailed contracts remain under
`maintainer/agent-evaluation/suites/task_guidance/scenarios/`. The
[test-case catalog](test-cases.md) is the review-oriented description and
links those contracts only when deeper detail is useful.