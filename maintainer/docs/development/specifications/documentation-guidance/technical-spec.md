# Documentation and specification guidance technical specification

## Maintained outputs

The reusable product consists of:

- `docs/development/documentation.md`, the complete project-independent guide;
- portable Documentation, Requirements, and Testing Markdown sections under
  `maintainer/guidance/current/sections/`;
- candidate overrides under `maintainer/guidance/candidates/` when approved
  work is under evaluation.

A consuming project owns its local documentation addendum, repository paths,
package map, publication behavior, and guidance target.

## Document model

The guide starts with an optional file tree, then defines file roles, writing
expectations, examples, specifications as targets, requirements as live state,
testing strategy, placement, discoverability, current documentation, generated
output, and incremental adoption.

Each substantive subject has one primary maintained source. Other pages link or
summarize only what their reader needs. Generated output is changed through its
maintained source or generator.

## Specification and requirements model

A specification may lead implementation. Requirements carry stable IDs when
independent implementation, verification, documentation, or human-confirmation
state benefits from tracking. Requirements state outcomes and constraints, not
work steps or evidence inventories.

Unapproved public, persisted, compatibility, security, privacy, or user-visible
choices remain questions or non-normative recommendations. A quality goal does
not authorize an internal mechanism.

## Testing model

Requirement verification maps each requirement or coherent group to the
smallest reliable evidence at a user-relevant boundary. Unit and component
checks cover local behavior. Integration or end-to-end checks are used when a
real boundary is material and lower layers cannot represent it faithfully.
Mocks that supply or bypass the claimed behavior are not decisive evidence.

A durable `testing-strategy.md` is optional and records significant risks,
selected boundaries, manual or hosted checks, and deliberate exclusions when
those choices need preservation.

## Portable repository guidance

Portable sections contain complete Markdown headings and concise rules. They do
not name repositories, packages, publication commands, or delivery roles. A
project-owned target decides where they appear in a compiled file. Delivery and
authority are documented separately from source compilation.

## Versioning and adoption

Simple guidance changes normally use Git history. A candidate directory is
used when comparison is useful. Promotion requires human approval, followed by
merging accepted source into the current bundle and recompiling each consuming
project independently.
