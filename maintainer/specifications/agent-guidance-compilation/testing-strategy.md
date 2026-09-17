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
- explicit committed-ref selection without checkout mutation;
- candidate-directory selection at the same ref;
- missing paths at a selected ref fail clearly;
- dirty working-tree sources record HEAD, dirty state, and content hashes;
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
- Crystal Lattice package names and paths do not occur in external compiled
  files unless required by a literal test description;
- each target's local paths and commands occur only in that target;
- all required slots are present exactly once.

## Evaluation integration tests

The documentation-standard harness verifies:

- default current-bundle/current-checkout behavior;
- explicit candidate and optional Git-ref behavior;
- compilation lock inclusion in cache and dataset identity;
- exact injected files equal the compiled outputs;
- producer and semantic records include the same compilation hash;
- frozen snapshots regenerate byte-for-byte.

## Corrected real-model comparison

After deterministic migration passes:

1. compile current and combined-v2 for each project base;
2. run three projects, seven model/effort profiles, and both delivery modes;
3. preserve all 84 producer records for each variant pair;
4. obtain complete semantic assessments for requirement coverage, expansion,
   testing layers, crossings, focus, and unnecessary work;
5. score low/medium/high-assurance efforts separately;
6. compare exact paired outputs for requirement readability, testing
   decisiveness, proportionality, and plan usability;
7. inspect passing outputs as well as failures;
8. compare corrected patterns with the legacy matrix without combining their
   counts.

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