# Documentation and specification standard

This specification defines the target documentation structure, specification
workflow, Crystal Lattice conventions, agent routing, publication behavior,
migration, audience/reference boundaries, blocked-workflow behavior,
proportional routed reading, placement communication, explicit safe layout
overrides, and validation rules.

It governs two public guidance documents:

- a project-independent documentation and specification guide at
  `docs/development/documentation.md`;
- a Crystal Lattice addendum at
  `docs/development/crystal-lattice-documentation.md`.

`docs/development/index.md` provides a short route to those documents and to
cross-package specifications. The guide documents a menu of useful file roles,
not a required directory schema: a task may use one existing page, one new
page, a small specification, or a larger documentation tree according to its
actual needs.

It also governs related operational files such as root `AGENTS.md`,
`CONTRIBUTING.md`, task guidance, documentation-site assembly, and standards
validation.

The specification is a target and is not evidence that these outputs currently
exist or behave as described. Current implementation, verification, and
documentation state is recorded in
[requirements.md](requirements.md).

Specification documents:

- [Product specification](product-spec.md)
- [Technical specification](technical-spec.md)
- [Requirements and evidence](requirements.md)
- [Agent-behavior verification](agent-behavior-verification/index.md)

Approval and execution are tracked by:

- [Package-local documentation standard task](../../../tasks/20260728-package-local-documentation-standard/000-main.md)

Related maintainer specification:

- [Agent evaluation framework](../agent-evaluation-framework/index.md), whose
  first consumers provide behavioral evidence for the project-independent and
  Crystal Lattice instructions governed here.
- [Agent guidance source and compilation](../agent-guidance-compilation/index.md),
  which maintains inspectable shared sections, project-specific bases,
  candidate variations, and pinned compiled evaluation inputs.

The project-independent and Crystal Lattice rules share one meta-specification
because they have one approval path, owner, delivery, and validation system. If
the project-independent guide later gains independent owners, releases, or
multiple repository consumers, it may be split into a separately versioned
specification.
