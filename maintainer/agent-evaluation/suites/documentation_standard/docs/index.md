# Documentation-guidance suite

This suite is a consumer of `agent_eval`. It evaluates whether agents apply the
documentation, requirement, testing, routing, and task-guidance behavior
defined by the owning guidance specifications.

Every Crystal Lattice-backed model test uses the
[common runner contract](running-and-calibration.md#common-crystal-lattice-runner-contract):
a reduced projection of the normal default config, the standard model-family
system/developer message, workspace `AGENTS.md` loaded by the normal
system-message helpers, and canonical task guidance controlled by
`include_tasks`. This is shared test setup, not another behavioral scenario.

- [Running and calibration](running-and-calibration.md)
- [Development](development/index.md)
- [Scenarios](../scenarios/index.md)
- [Semantic targets](../targets/)
- [Frozen records](../fixtures/)
- [Human-readable results](../../../../docs/evaluations/documentation-guidance/index.md)

The suite records the maintained source and the effective delivery mechanism
separately. See
[Instruction delivery and authority](../../../../docs/instruction-delivery-and-authority.md).
