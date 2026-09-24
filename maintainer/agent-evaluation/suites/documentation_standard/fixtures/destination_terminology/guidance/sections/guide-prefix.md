# Documentation and specification guide

Help a reader complete a task, understand current behavior, or make a durable
development decision. Start with the smallest structure that does that clearly.

## Start with the smallest useful structure

A repository, package, application, or component may use any subset of this
layout:

```text
README.md
AGENTS.md
docs/
├── index.md
├── quickstart.md
├── <user-topic>.md
├── development/
│   ├── index.md
│   ├── <developer-topic>.md
│   └── specifications/
│       └── <capability>/
│           ├── index.md
│           ├── product-spec.md
│           ├── technical-spec.md
│           ├── requirements.md
│           ├── testing-strategy.md
│           └── decisions/
└── reference/
```

Every entry is optional. This guide does not require empty directories or
placeholder pages.

- One existing README may be enough for a small package.
- One standalone page may be clearer than a new directory and index.
- An index and one focused page may be enough for a growing subject.
- A specification may be one file, or one file plus requirements.
- Separate product, technical, requirements, testing, and decision files help
  only when their separation makes substantial work easier to understand.

For a single-package repository, the repository root is the package location.

## Choose files by their role

Define each subject in one primary maintained place. Other pages may link to it
or summarize only what their readers need.

| File or page | Reader and purpose |
|---|---|
| `README.md` | Gives a first-time visitor the purpose, installation or setup, first successful use or build, and links to more detail. Keep it easy to scan. |
| `AGENTS.md` | Gives developers and automated contributors local instructions, important entry points, constraints, and verification commands. It is operational guidance, not a product manual or progress ledger. |
| `docs/index.md` | Maps a multi-page user-documentation area. Keep it short and link to focused pages instead of reproducing them. |
| `docs/quickstart.md` | Leads a new user through one complete successful path, including a concrete result when the behavior is observable. |
| User documentation | Explains available installation, configuration, concepts, workflows, recipes, and troubleshooting for someone using the package or product. |
| `docs/development/index.md` | Maps a multi-page developer area, including architecture, testing, specifications, and maintenance. |
| Developer documentation | Explains current internals, code entry points, architecture, debugging, testing, operations, and maintenance. |
| Specification | Describes intended behavior, constraints, and important design decisions. It may lead implementation. |
| `requirements.md` | Lists necessary outcomes and records their implementation, verification, and documentation state. |
| `testing-strategy.md` | Records important risks, selected test boundaries, manual or hosted checks, and deliberate exclusions when those choices need durable explanation. |
| Reference | Gives exact API, type, schema, command, or protocol details. It may be maintained by hand or generated from source declarations. |
| Decision record | Preserves one material choice among credible alternatives and the reason for it. |

Someone importing an SDK or implementing a supported extension is a package
user for that public interface, even if they are also a developer.

### README and quickstart

A README should answer, in order:

1. What is this?
2. Who should use it?
3. How do I install, run, import, or build it?
4. What is the shortest successful example?
5. Where do I go next?

Move detail into focused pages when the README becomes difficult to scan.

A quickstart is useful when first use needs more explanation than the README
can comfortably hold. Show the input, command, configuration, or code and the
result the user should observe. A later verification section does not replace a
clear result beside the first-use example.

### Index pages

Create an index when readers need a map across several pages. An index should
name the available subjects and help readers choose. It should not become a
second copy of those pages. If one page is already easy to find, an extra index
may add no value.

### User and developer documentation

User documentation teaches supported use without requiring readers to
understand implementation plans or repository maintenance. Developer
documentation can assume the reader is changing or operating the implementation
and may link to specifications, requirements, code, and tests.

Keep both aligned with available behavior. A specification can describe a
target that does not exist yet; ordinary user and developer documentation
should not present that target as available.