# Crystal Lattice guidance integration product specification

## Purpose

Make the reusable documentation guidance easy to apply in the Crystal Lattice
repository while preserving package ownership, generated-site behavior,
maintainer boundaries, task workflow, and instruction-delivery provenance.

## Target experience

Contributors start from root or package guidance and reach one
project-independent guide plus a concise Crystal Lattice addendum. Package docs
remain authoritative, root docs cover cross-package concerns, shared plugin
rules remain discoverable, and generated site output is never edited as source.

Root repository guidance contains concise portable sections plus a narrow local
routing section. Task-file guidance is maintained as Markdown and delivered
through the task-enabled developer-message layer. Maintainers can inspect the
source, effective compiled instruction, evaluation provenance, and current
accepted state without reading historical task chronology.

## Goals

- Map reusable roles to Crystal Lattice packages and shared domains.
- Keep public package docs separate from non-public maintainer material.
- Compile root guidance and preserve canonical task-guidance synchronization.
- Assemble package docs into the documentation site from maintained sources.
- Preserve compatible public routes during bounded migration.
- Provide human-led contribution and review guidance.
- Validate reusable behavior through realistic Crystal Lattice evaluation while
  keeping interpreted results outside the specification.

## Non-goals

- Repeating the complete reusable guide.
- Publishing maintainer specifications or evaluation records.
- Reconstructing undocumented behavior merely to complete a directory shape.
- Treating one model result as proof of correctness.
