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
5. [Reproducing and inspecting results](reproducing-and-inspecting-results.md)
   — provides the commands, identities, raw-record paths, report-generation
   flow, and cell-level inspection examples.

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

[Stage B2 — Guidance-placement confirmation](test-plan.md#stage-b2--guidance-placement-confirmation)
has not started and remains blocked on approval and focused confirmation of
the practical task-mechanics baseline.

## Machine evidence

Frozen JSON, prompts, generated task files, plan responses, tool telemetry,
and semantic assessments remain under
`maintainer/agent-evaluation/suites/task_guidance/fixtures/results/`.

The evaluator's detailed contracts remain under
`maintainer/agent-evaluation/suites/task_guidance/scenarios/`. The
[test-case catalog](test-cases.md) is the review-oriented description and
links those contracts only when deeper detail is useful.