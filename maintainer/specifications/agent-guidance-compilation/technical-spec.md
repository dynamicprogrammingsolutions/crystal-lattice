# Agent guidance source and compilation technical specification

## Source layout

The target maintained layout is:

```text
maintainer/guidance/
├── README.md
├── compiler/
│   └── <compiler implementation>
├── current/
│   ├── bundle.toml
│   └── sections/
│       ├── requirements.md
│       ├── testing-strategy.md
│       └── <other shared sections>.md
├── candidates/
│   └── <candidate-name>/
│       ├── candidate.toml
│       ├── README.md
│       └── sections/
│           └── <overridden sections>.md
└── targets/
    └── crystal-lattice/
        ├── target.toml
        ├── AGENTS.md.in
        ├── agents/
        │   └── TASKS-v7.md.in
        └── sections/
            └── <repository-specific sections>.md

maintainer/agent-evaluation/suites/documentation_standard/
└── guidance_targets/
    ├── eleventy/
    ├── fastapi/
    └── flask-vue/
```

The generic compiler accepts arbitrary target directories. Production targets
belong under `maintainer/guidance/targets/`; evaluation-only project bases
remain with their owning evaluation suite.

## Section bundles

The current bundle maps stable section identifiers to Markdown source files:

```toml
format = 1
id = "current"

[sections]
requirements = "sections/requirements.md"
testing-strategy = "sections/testing-strategy.md"
```

A candidate extends a selected current bundle and overrides only changed
sections:

```toml
format = 1
id = "root-requirements-testing-v2"
extends = "../../current"

[overrides]
requirements = "sections/requirements.md"
testing-strategy = "sections/testing-strategy.md"
```

Candidate directories are maintained guidance sources. They are not
evaluation fixtures. A candidate README may state the tested question,
changed sections, preserved behavior, and evaluation route; it does not store
run progress or model output.

## Targets and slots

A target manifest declares compiled outputs, base files, and section
resolution. A base uses one explicit placeholder form:

```markdown
<!-- guidance-slot:requirements -->
```

Sections include their own headings and are independently readable.

The initial compiler:

- replaces named slots only;
- requires every declared slot exactly once;
- rejects missing, duplicate, unknown, and unused slot mappings;
- does not support nested includes, conditionals, interpolation, or arbitrary
  code;
- normalizes UTF-8 and final newlines deterministically;
- preserves all ordinary base and section text byte-for-byte apart from
  defined newline normalization.

Portable strategy and local mechanics use distinct slots. For example:

```text
testing-strategy
repository-testing-rules
```

The first can be shared across targets. The second is resolved from
target-local Crystal Lattice, Eleventy, FastAPI, or Flask/Vue content.

## Compilation

Compilation accepts:

- bundle directory;
- target directory;
- optional Git reference;
- output directory or repository-write mode.

Without a Git reference, sources are read from the current checkout. With a
reference, the compiler reads the named bundle and target paths from that Git
tree without requiring a checkout change.

Compilation produces:

- compiled files;
- a lock with compiler version, selected source, resolved commit, dirty-state
  information when applicable, input file hashes, output file hashes, and one
  compilation hash.

The compilation hash participates in evaluation cache and dataset identity.

The normal compiled files do not contain generated comments because those
comments would also become model instructions. Provenance remains in the lock
and evaluation records.

## Current repository files

The current bundle and Crystal Lattice target compile the maintained
repository files, initially:

- root `AGENTS.md`;
- canonical `agents/TASKS-v7.md` when its source migration is included.

Migration first proves byte-identical compilation of current files. A check
mode fails when a repository output differs from current source compilation.

The existing synchronization from canonical `agents/TASKS-v7.md` to the
bundled application copy remains responsible for the bundled runtime file
unless a later approved change integrates that copy as another compiler
output.

## Test selection

Evaluation code receives selection through shared harness options rather than
test constants:

```text
--guidance-bundle <directory>
--guidance-target <directory>
--guidance-ref <optional Git reference>
```

Defaults are:

```text
bundle: maintainer/guidance/current
target: scenario-owned current target
ref: current checkout
```

Tests do not permanently name a candidate or commit. Scenario definitions name
only their appropriate target base.

## Evaluation snapshots

Each run records the compilation lock. A selected experiment may freeze:

```text
maintainer/agent-evaluation/guidance-snapshots/<experiment-id>/
├── lock.json
└── compiled/
    └── <target>/<output>
```

Snapshots are evidence for inspection and reproduction. Tests do not use them
as the default current source.

## Corrected project targets

Eleventy, FastAPI, and Flask/Vue receive separate bases describing only their
actual project, important paths, and relevant commands. They compile the same
shared requirement and testing sections selected for Crystal Lattice.

The corrected evaluation labels the September 17, 2026 matrix as legacy and
runs:

- the current baseline bundle;
- the latest combined-v2 candidate bundle;
- all three projects;
- all seven model/effort profiles;
- root-only and root-plus-TASKS modes;
- semantic effort-aware assessment;
- pairwise requirement, testing, and plan-usability review.

## Promotion

Promotion is manual:

1. freeze the tested compilation and evidence;
2. obtain human approval;
3. merge candidate section changes into the current bundle;
4. compile current source into repository outputs;
5. run compiler check and affected deterministic/model tests;
6. commit source sections and compiled files together.

The compiler never changes the current bundle or repository output merely
because evaluation passes.

Accepted candidate directories may be removed after promotion. Git history and
the accepted evaluation snapshot preserve the reviewed version.

## Migration compatibility

During migration:

- Python string candidates remain only until equivalent bundle compilation is
  proven;
- hardcoded baseline commits and variant names are removed from tests after
  runtime selection is available;
- legacy frozen records remain unchanged;
- current repository files stay byte-identical until an approved guidance
  change is promoted.