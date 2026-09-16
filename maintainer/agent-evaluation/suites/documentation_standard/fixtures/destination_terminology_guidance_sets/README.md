# Documentation-standard guidance sets

This fixture contains complete guidance roots for comparing destination
terminology wording without editing the repository's current `AGENTS.md` or
documentation guide between runs.

## Layout

- `sources/` contains the maintained replacement sections and the shared
  comprehensive rule section.
- `sets/` contains complete compiled guidance roots used directly by the
  evaluation suite.
- `compile.py` regenerates every compiled set deterministically.
- `DESTINATION_TERMINOLOGY_TEST_PLAN.md` defines the behavioral comparison and
  review gates.
- `DESTINATION_TERMINOLOGY_REVIEW.md` records compiled-file inspection,
  corrections, and pending empirical checks.

Do not edit files under `sets/` directly. Change a source section, compile the
sets, and review the complete generated files.

## Compiled sets

`sets/option-a-checkpoint/` is the maintained snapshot from which the candidate
sets are compiled. Repository-current guidance is tested separately through
the evaluator's `candidate` guidance mode.

Five wording families are compiled in generic and specific modes:

| Family | Generic | With comprehensive rules |
|---|---|---|
| Abstract grouping terms | `abstract-generic` | `abstract-specific` |
| Explicit action-first | `action-first-generic` | `action-first-specific` |
| File- and reader-centered | `file-centered-generic` | `file-centered-specific` |
| Explicit maintained contexts | `explicit-contexts-generic` | `explicit-contexts-specific` |
| Defined `context` and `audience` | `contextual-generic` | `contextual-specific` |

Each directory under `sets/` contains:

- `AGENTS.md`;
- `docs/development/index.md`;
- `docs/development/documentation.md`;
- `docs/development/crystal-lattice-documentation.md`;
- `plugins/AGENTS.md`;
- `plugins/docs/AGENTS.md`;
- `guidance-set.json`.

The manifest records the set ID, wording family, rule mode, base revision,
source hashes, individual guidance hashes, combined guidance hash, and relevant
word counts.

## Compile and check

From the repository root:

```bash
python \
  maintainer/agent-evaluation/suites/documentation_standard/fixtures/destination_terminology_guidance_sets/compile.py
```

Verify that committed output matches the sources:

```bash
python \
  maintainer/agent-evaluation/suites/documentation_standard/fixtures/destination_terminology_guidance_sets/compile.py \
  --check
```

Compilation reads `sets/option-a-checkpoint/`, writes all sets to a temporary
directory, and replaces `sets/` only after successful generation. The output
is stable and contains no generation timestamp or required Git revision.

## Select guidance for a run

Use the repository's current guidance:

```bash
AGENT_EVAL_GUIDANCE_VARIANT=candidate
```

Use a committed fixture set:

```bash
GUIDANCE_SET_ROOT="$PWD/maintainer/agent-evaluation/suites/documentation_standard/fixtures/destination_terminology_guidance_sets/sets"

AGENT_EVAL_GUIDANCE_VARIANT=contextual-generic \
AGENT_EVAL_GUIDANCE_DIR="$GUIDANCE_SET_ROOT/contextual-generic" \
pytest maintainer/agent-evaluation/suites/documentation_standard \
  -m "agent_eval and routine" -q
```

`GuidanceSource` reads the six supported paths from the selected directory,
hashes them, copies them into each isolated scenario workspace, and injects the
same content into model instructions. The guidance name and combined hash are
part of branch cache identity and run evidence.

## Review and reproduction

Mechanical checks are necessary but not sufficient. Before a set enters the
full model matrix:

1. Review its complete generated `AGENTS.md` and portable guide.
2. Review its pairwise diff against `option-a-checkpoint`.
3. Confirm that unchanged guidance files remain byte-identical.
4. Run one real-model branch and confirm that recorded guidance provenance
   matches `guidance-set.json`.
5. Inspect the first output before launching the remaining scenarios for that
   set.

The compiled sets remain committed after the comparison so results can be
reproduced even after the public guide changes.

Parallel orchestration for this comparison is temporary task-local code. It is
not part of this fixture unless later work demonstrates a reusable,
non-trivial need.
