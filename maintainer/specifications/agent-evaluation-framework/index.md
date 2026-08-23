# Agent evaluation framework

This specification defines a small generic programmatic kernel for running
evaluation programs, reusing compatible state, observing results, and
preserving compact and raw artifacts.

One broad `RunEnvironment` contract supplies execution-specific context,
snapshot, compatibility, and observation behavior. Crystal Lattice is the
first complete environment and supplies optional lower-layer customization for
tool loops, configuration, snapshots, evidence, evaluation, and presentation.

The kernel is intentionally neutral about what an evaluation does. Prompts,
message roles, models, skills, plugins, request overrides, scoring, review, and
assertions remain environment configuration and ordinary Python test code.

The first consumers verify that supported agents can understand and apply the
documentation and specification standards defined by:

- [Documentation and specification standard](../documentation-and-specification-standard/index.md)
- [Its live requirements](../documentation-and-specification-standard/requirements.md)
- [Its agent-behavior verification scenarios](../documentation-and-specification-standard/agent-behavior-verification/index.md)

Specification documents:

- [Product specification](product-spec.md)
- [Technical specification](technical-spec.md)
- [Requirements and evidence](requirements.md)

Approval and execution are tracked by:

- [Agent evaluation framework task](../../../tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md)

The existing task-guidance evaluator is a validated prototype and later
consumer. Its relocation and adaptation remain owned by:

- [Task guidance and specification alignment](../../../tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md)

This specification is the intended target. Current implementation,
verification, documentation, and delivery state is recorded in
[requirements.md](requirements.md).