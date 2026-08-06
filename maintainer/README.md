# Maintainer

This directory contains specifications, evaluation tooling, and other material
used to maintain repository standards and agent workflows.

It is not the normal entry point for contributors or agents applying those
standards, and it is not part of the public documentation product. The material
is not necessarily confidential; `maintainer/` identifies its maintenance
purpose and publication boundary.

Because everything under this domain is development-only, specifications live
directly under `maintainer/specifications/`. Adding
`maintainer/docs/development/` would create parent indexes without clarifying
the audience or ownership.

Current specifications:

- [Documentation and specification standard](specifications/documentation-and-specification-standard/index.md)
- [Agent evaluation framework](specifications/agent-evaluation-framework/index.md)

The target standard will produce reusable guidance and repository-specific
policy under `docs/development/`. Those output pages are artifacts for agents
and contributors using the rules. They do not need to link back to the
maintainer specification.

The agent-evaluation specification defines the reusable programmatic library
target. Task-guidance evaluation and similar standards-maintenance tooling
currently living elsewhere in the repository will move under `maintainer/`
through their own approved implementation work.