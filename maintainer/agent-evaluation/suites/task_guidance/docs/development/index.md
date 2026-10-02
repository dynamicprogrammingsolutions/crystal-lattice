# Task-guidance suite development

The legacy evaluator migration and staged handoff/decomposition evaluator are
implemented.
[Stage B0 — Current-guidance baseline](../../../../../docs/evaluations/task-guidance/test-plan.md#stage-b0--current-guidance-baseline)
is frozen with all planned task-creation and handoff cells. One GPT same-agent
chain is preserved as invalid upstream behavior.
[Stage B1 — Task-mechanics candidate](../../../../../docs/evaluations/task-guidance/test-plan.md#stage-b1--task-mechanics-candidate)
v1 is frozen and not promoted verbatim. Its decomposition gains are retained
for a practical-baseline revision with focused plan/handoff confirmation.
[Stage B2 — Guidance-placement confirmation](../../../../../docs/evaluations/task-guidance/test-plan.md#stage-b2--guidance-placement-confirmation)
remains pending task 090.

- [Suite specification](specification.md)
- [Suite requirements](requirements.md)
- [Testing strategy](testing-strategy.md)
- [Running and calibration target](../running-and-calibration.md)
- [Scenario contracts](../../scenarios/index.md)
- [Shared evaluation result package target](../../../../docs/development/specifications/result-packages/index.md)
- [Result-package execution task](../../../../../../tasks/20260728-package-local-documentation-standard/095-evaluation-result-review-packages.md)

The suite specification owns evaluator behavior. Actual task-guidance content,
delivery, synchronization, and placement are owned by the
[Crystal Lattice guidance integration specification](../../../../../docs/development/specifications/crystal-lattice-guidance-integration/index.md).
The shared result-package specification owns generic collection and rendering;
the Crystal Lattice environment owns runtime-specific review projection.