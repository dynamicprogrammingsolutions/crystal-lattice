# Agent guidance source and compilation testing strategy

## Risks

The important risks are:

- compiled guidance silently differs from maintained source;
- a candidate unintentionally changes sections it does not override;
- target-specific content leaks into another project;
- historical selection reads a mixture of current and referenced files;
- uncommitted evaluation cannot be reproduced by content;
- tests or caches identify a human candidate name but not its exact content;
- promotion writes repository guidance before approval;
- migration changes current model instructions before byte identity is proven.

## Deterministic compiler tests

Focused unit tests cover:

- one valid slot replacement;
- missing, duplicate, unknown, and unused slots;
- deterministic newline and UTF-8 behavior;
- bundle inheritance and candidate overrides;
- rejection of override paths outside the selected bundle;
- target-local and shared section resolution;
- stable input, output, and compilation hashes;
- no conditions, interpolation, recursive includes, or executable templates.

## Source-selection tests

Temporary Git repositories verify:

- current-checkout selection;
- bundle and target directories in different repositories;
- identical content at different absolute paths has the same compilation hash;
- candidate-directory selection without test-code changes;
- dirty working-tree sources record optional Git metadata and content hashes;
- one test module can run current and candidate sources without code changes.

## Repository-output tests

Migration acceptance requires:

- current source compiles root `AGENTS.md` byte-for-byte;
- current canonical task source compiles byte-for-byte when migrated;
- check mode reports a useful diff for direct output drift;
- candidate compilation never writes the repository output unless explicit
  repository-write mode is selected;
- canonical-to-bundled task-guidance parity remains exact.

## Target-isolation tests

The Eleventy, FastAPI, Flask/Vue, and Crystal Lattice bases compile the same
portable sections. Assertions verify:

- shared section hashes match across targets;
- every target receives the same concise portable Documentation section;
- Crystal Lattice package names and paths do not occur in external compiled
  files unless required by a literal test description;
- each target's local paths and commands occur only in that target;
- all required slots are present exactly once.

Fixture target tests additionally verify that each target is colocated with its
sample-project fixture, is marked `kind = "fixture"`, and contains factual
context rather than the requirement or testing conclusion being evaluated.

## Evaluation integration tests

The documentation-standard harness verifies:

- default current-bundle/current-checkout behavior;
- explicit candidate and optional Git-ref behavior;
- compilation lock inclusion in cache and dataset identity;
- exact injected files equal the compiled outputs;
- producer and semantic records include the same compilation hash;
- frozen snapshots regenerate byte-for-byte.

## Consuming-project behavioral comparison

After deterministic migration passes, a consuming repository may compare
current and candidate portable guidance with its own target and representative
tasks. The comparison should preserve exact compilation locks, interpret
effort levels separately, inspect passing outputs as well as failures, and keep
legacy Crystal Lattice-context counts separate.

Low effort may have lower completeness without automatically invalidating the
guidance. High, xhigh, and max effort are warning conditions when completeness
regresses or scope expands materially.

## Deliberate exclusions

Initial migration does not:

- test automatic promotion, because promotion is intentionally manual;
- infer portable-guidance quality from the legacy matrix;
- add a general template language;
- require every existing `AGENTS.md` in the repository to migrate at once;
- rerun unrelated documentation consumer suites unless compiler ownership or
  injected guidance changes their inputs.