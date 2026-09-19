# Task-guidance evaluation suite

> **Not implemented:** These pages specify the approved target for a future
> package-owned suite. The existing evaluator remains under
> `test/task_guidance/` until the migration in task 090 is approved and
> executed.

The suite will evaluate whether task files are durable handoffs, whether plans
and task decomposition preserve approved outcomes, and whether a later agent
can continue with bounded rediscovery.

- [Running and calibration target](running-and-calibration.md)
- [Development specification](development/index.md)
- [Scenario contracts](../scenarios/index.md)
- [Execution task](../../../../../tasks/20260728-package-local-documentation-standard/090-task-guidance-handoff-baseline-and-placement.md)

The suite is a consumer of `agent_eval`. Generic kernel and Crystal Lattice
environment behavior remains owned by the package specifications under
`maintainer/agent-evaluation/docs/development/specifications/`.