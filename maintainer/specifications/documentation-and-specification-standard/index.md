# Documentation and specification standard

This specification defines the target documentation structure, specification
workflow, repository policy, agent routing, publication behavior, migration,
and validation rules.

It governs two user-facing output layers:

- reusable, package-neutral standards under `docs/development/standards/`;
- Crystal Lattice repository policy under `docs/development/repository/`.

It also governs related operational artifacts such as root `AGENTS.md`,
`CONTRIBUTING.md`, task guidance, documentation-site assembly, and standards
validation.

The specification is a target and is not evidence that these outputs currently
exist or behave as described. Current implementation, verification, and
documentation state is recorded in
[requirements.md](requirements.md).

Artifacts:

- [Product specification](product-spec.md)
- [Technical specification](technical-spec.md)
- [Requirements and evidence](requirements.md)
- [Agent-behavior verification](agent-behavior-verification/index.md)

Approval and execution are tracked by:

- [Package-local documentation standard task](../../../tasks/20260728-package-local-documentation-standard/000-main.md)

Related maintainer specification:

- [Agent evaluation framework](../agent-evaluation-framework/index.md), whose
  first consumers provide behavioral evidence for the generic and
  repository-specific instructions governed here.

The generic and repository-specific rules share one meta-specification because
they have one approval path, owner, delivery, and validation system. If the
generic standard later gains independent owners, releases, or multiple
repository consumers, it may be split into a separately versioned
specification.