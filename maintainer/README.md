# Maintainer

This directory contains specifications, evaluation tooling, and other material
used to maintain repository guidance and agent workflows.

It is not the normal entry point for contributors or agents applying those
rules, and it is not part of the public documentation product. The material
is not necessarily confidential; `maintainer/` identifies its maintenance
purpose and publication boundary.

Because everything under this domain is development-only, specifications live
directly under `maintainer/specifications/`. Adding
`maintainer/docs/development/` would create parent indexes without clarifying
the audience or ownership.

Current specifications:

- [Documentation and specification standard](specifications/documentation-and-specification-standard/index.md)
- [Agent evaluation framework](specifications/agent-evaluation-framework/index.md)
- [Agent guidance source and compilation](specifications/agent-guidance-compilation/index.md)

Current maintainer tooling:

- [Agent evaluation kernel](agent-evaluation/README.md)

Current maintainer procedures:

- [Documentation guidance review bundle](documentation-standards-review-bundle.md)

The public documentation and specification guide and Crystal Lattice
conventions live under `docs/development/`. Those pages are for agents and
contributors applying the rules. They do not need to link back to the
maintainer specification.

The agent-evaluation specification defines the reusable generic kernel and its
first Crystal Lattice environment. The generic kernel and Crystal Lattice
environment are implemented; documentation-guidance consumers remain in
progress. Task-guidance evaluation and similar guidance-maintenance tooling
currently living elsewhere in the repository will move under `maintainer/`
through their own approved implementation work.