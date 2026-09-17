# Agent guidance source and compilation

This specification defines how maintained agent-guidance sections,
project-specific base files, candidate variations, compiled repository files,
and evaluation snapshots relate.

It establishes a deterministic compiler so:

- current guidance is maintained as inspectable source sections and target
  bases;
- candidate guidance is a source variation rather than a test fixture;
- different projects can compile the same shared sections into
  project-appropriate `AGENTS.md` files;
- tests use the current checked-out sources by default and may explicitly
  select a candidate directory and optional Git reference;
- every evaluated compilation is pinned by its inputs and output hashes;
- accepted guidance is promoted manually before repository files are
  regenerated.

Specification documents:

- [Product specification](product-spec.md)
- [Technical specification](technical-spec.md)
- [Requirements and evidence](requirements.md)
- [Testing strategy](testing-strategy.md)

Approval and execution are tracked by:

- [Guidance source and compilation migration](../../../tasks/20260728-package-local-documentation-standard/071-guidance-source-compilation-migration.md)

Related specifications:

- [Documentation and specification standard](../documentation-and-specification-standard/index.md)
- [Agent evaluation framework](../agent-evaluation-framework/index.md)

The September 17, 2026 full matrix that injected Crystal Lattice guidance into
unrelated repositories remains available as
[legacy comparison evidence](../documentation-and-specification-standard/agent-behavior-verification/20260917-legacy-root-guidance-full-matrix.md).
It is not the corrected baseline for this specification.

This specification describes the target. Current implementation,
verification, documentation, and evaluation state is recorded in
[requirements.md](requirements.md).