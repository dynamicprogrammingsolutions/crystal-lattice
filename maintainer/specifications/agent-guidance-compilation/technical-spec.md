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

<consuming repository>/
└── maintainer/
    └── guidance/
        └── target/
            ├── target.toml
            ├── AGENTS.md.in
            └── sections/
                └── <project-specific sections>.md

maintainer/agent-evaluation/suites/documentation_standard/fixtures/
└── requirement_quality/
    └── <scenario>/
        └── guidance/
            ├── target.toml
            ├── AGENTS.md.in
            └── sections/
                └── project-context.md
```

The generic compiler accepts an arbitrary target directory, including an
absolute path in another repository. Crystal Lattice stores only its own
project target. Every consuming repository stores its own templates and local
sections. Evaluation sample projects are repository-owned fixtures and store
their test-only targets beside the fixture that they describe.

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
- output directory or repository-write mode.

The compiler reads each directory directly. To compile a historical portable
guidance version, a maintainer points the bundle argument at a checkout or
worktree for that revision. Bundle and target may belong to different Git
repositories.

Compilation produces:

- compiled files;
- a lock with compiler version, selected bundle and target, optional Git
  revision/dirty metadata detected independently for each source, input file
  hashes, output file hashes, and one location-independent compilation hash.

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

Evaluation or compilation commands receive selection through paths rather than
test constants:

```text
--guidance-bundle <directory>
--guidance-target <directory>
```

The bundle normally points into a Crystal Lattice checkout. The target points
into the consuming repository. Tests do not permanently name a candidate or
commit.

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

## Consuming-project targets

Each consuming repository owns a base describing its project, important paths,
and relevant commands. The same machine-local command can be rerun after the
Crystal Lattice checkout advances to an accepted portable-guidance version.

The command may be saved outside version control because it contains
computer-specific absolute paths:

```bash
python /absolute/path/to/ai-agent-platform/maintainer/guidance/compiler.py \
  write \
  --bundle /absolute/path/to/ai-agent-platform/maintainer/guidance/current \
  --target /absolute/path/to/consumer/maintainer/guidance/target \
  --destination /absolute/path/to/consumer
```

Task guidance is not compiled into the consuming repository. Crystal Lattice
runtime configuration supplies the updated canonical task guidance when its
develop branch is updated.

Evaluation target selection uses an explicit external target path when one is
provided. Otherwise a requirement-quality scenario uses its fixture-owned
target. Fixture context contains facts only and does not repeat the expected
requirement or testing behavior.

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
- hardcoded baseline commits and variant names are removed from active tests
  after path selection is available;
- legacy frozen records remain unchanged;
- current repository files stay byte-identical until an approved guidance
  change is promoted.