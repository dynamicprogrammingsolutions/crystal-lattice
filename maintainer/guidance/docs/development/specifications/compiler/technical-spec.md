# Agent guidance compiler technical specification

## Source model

A bundle directory contains `bundle.toml` and named Markdown sections. A
candidate may extend another bundle and override selected names. A target
directory contains `target.toml`, output templates, and optional local sections.

Example bundle:

```toml
format = 1
id = "current"

[sections]
shared-policy = "sections/shared-policy.md"
```

Example target slot:

```markdown
<!-- guidance-slot:shared-policy -->
```

Target manifests declare each slot's source and path or bundle section.

## Validation

The compiler:

- requires format version 1;
- permits relative or absolute bundle and target directories;
- rejects invalid output and source paths;
- requires every declared slot exactly once;
- rejects missing, duplicate, unknown, and unused mappings;
- supports no conditionals, interpolation, recursive includes, or arbitrary
  code;
- preserves ordinary UTF-8 Markdown content apart from defined newline
  normalization.

## Output and lock

Compilation returns output bytes and a lock containing:

- compiler and lock schema versions;
- bundle and target IDs and optional Git revision/dirty metadata;
- role-qualified relative input paths and SHA-256 hashes;
- output paths and hashes;
- one location-independent compilation hash.

Absolute diagnostic paths may appear in a local lock but do not participate in
the portable compilation hash.

## Commands

- `compile` writes a selected bundle/target result to a preview destination.
- `check` reports destination files that differ from compilation.
- `write` writes approved outputs explicitly.

A historical revision is selected by running the compiler from or pointing it
at a checkout/worktree for that revision. Tests do not permanently encode one
candidate or commit.

## Ownership and promotion

The compiler owns mechanics only. A consuming project owns its target and
compiled output. A guidance product owns section meaning and acceptance.
Promotion merges approved candidate source into the current bundle before
`write` is run against maintained destinations.
