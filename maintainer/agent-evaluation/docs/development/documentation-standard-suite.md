# Documentation-standard behavioral suite

The suite under `suites/documentation_standard/` checks whether agents apply the
authored documentation and specification guidance during ordinary repository
tasks.

Seeds are guidance-neutral. Branches select an explicit guidance source:

- `develop`: the previous guidance from pinned revision `f81f3632`;
- `followup-baseline`: the two-page guidance immediately before the
  September 14 root-routing and specification-approval edits, pinned at
  `cdeb50a7`;
- `baseline`: the older historical calibration from `3a62b6fc`;
- `candidate`: files from the current repository working tree;
- another name plus `AGENT_EVAL_GUIDANCE_DIR`: files from an explicit directory.

Each seed prompt names the exact bounded files needed for its reusable
investigation. Do not make seeds depend on broad directory discovery or
filename guessing. Profiles expose file read/write plus an allowlisted array
shell so scenarios can run focused tests and approved generators; exact paths
keep seed setup fast and reproducible.

The guidance source name, revision, file hashes, and combined hash participate
in workspace/cache identity and are recorded with the run. After restoring the
guidance-neutral seed, the suite delivers the selected files at native
instruction priority and then adds the unchanged task as a user message.
ChatGPT account mode uses a late suite-owned feature: after normal agent
instructions and request options are compiled, the feature combines them with
the exact selected guidance in endpoint `instructions` and removes the leading
historical instruction item from the request input. Persistent session history
is unchanged. The Ollama profile uses a leading `system` message. The strategy,
role, position, and injection-strategy version are retained in evidence.

## Baseline-first comparison

For new guidance-clarity cases:

1. Run the unchanged task against `develop`.
2. Confirm that a representative run exhibits the targeted undesirable
   behavior.
3. Run the same seed, prompt, fixture, assertions, and model profile against
   `candidate`.
4. Try an expanded directory-backed variant only when the concise candidate is
   insufficient.

A baseline that already passes can provide robustness evidence, but cannot show
that candidate wording fixed a regression.

Use `followup-baseline` for the paired Tests 6 and 27 follow-up. It differs from
the candidate only in the root consolidation and substantial-specification
approval paragraph being evaluated.

Test 27 uses a routing-only variation: root AGENTS guidance is injected while
the two current guidance pages remain ordinary workspace files. Legacy Test 20
retains the former four-page route for direct comparison only.

## Run GLM-5.3 Flash

The GLM profile targets `glm-5.3-flash:cloud` for every seed and branch.
Confirm that the local Ollama service can resolve that exact identifier before
starting a real-model matrix.

Previous guidance with the legacy 21-test suite:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
AGENT_EVAL_GUIDANCE_VARIANT=develop \
pytest maintainer/agent-evaluation/suites/documentation_standard/test_consumers.py \
  -m "agent_eval" -q
```

Current guidance with the same legacy suite:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
AGENT_EVAL_GUIDANCE_VARIANT=candidate \
pytest maintainer/agent-evaluation/suites/documentation_standard/test_consumers.py \
  -m "agent_eval" -q
```

Tests 01, 15, 17, 20, and 21 are intentionally included in that comparison
even though their README-only restriction, ban on every early user-doc draft,
full package profile, old route, or literal terminology assertion is obsolete.

Current guidance with the revised suite:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
AGENT_EVAL_GUIDANCE_VARIANT=candidate \
pytest \
  maintainer/agent-evaluation/suites/documentation_standard/test_consumers.py \
  maintainer/agent-evaluation/suites/documentation_standard/test_revised_consumers.py \
  -m "agent_eval and not obsolete" -q
```

Use `AGENT_EVAL_GUIDANCE_VARIANT=develop` with the same revised command for
baseline-first evidence on Tests 22–29.

## Run GPT-5.6-luna

Hosted runs require the explicit hosted gate:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_ALLOW_HOSTED=1 \
AGENT_EVAL_PROFILE=gpt \
AGENT_EVAL_GUIDANCE_VARIANT=develop \
pytest maintainer/agent-evaluation/suites/documentation_standard \
  -m "agent_eval and routine" -q
```

Use `AGENT_EVAL_GUIDANCE_VARIANT=candidate` for the paired candidate run.

For a focused scenario at an explicit supported reasoning effort, add:

```bash
AGENT_EVAL_REASONING_EFFORT=max
```

Focused terminology comparisons use low, high, and max with both the GLM and
GPT profiles. The effort value participates in branch cache identity and is
recorded in canonical evidence.

The current suite collects:

- 21 legacy consumers for direct comparison;
- 18 revised routine branches;
- 14 revised extended branches;
- 32 revised branches over 12 guidance-neutral seeds.

## Run a custom wording variant

The directory must contain every guidance path listed by the suite:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
AGENT_EVAL_GUIDANCE_VARIANT=expanded-1 \
AGENT_EVAL_GUIDANCE_DIR=/absolute/path/to/guidance-root \
pytest maintainer/agent-evaluation/suites/documentation_standard \
  -m "agent_eval and routine" -q
```

Do not change the task prompt, fixture, or assertions between guidance variants.

Committed terminology candidates live under
`suites/documentation_standard/fixtures/destination_terminology_guidance_sets/sets/`.
For example:

```bash
GUIDANCE_SET_ROOT="$PWD/maintainer/agent-evaluation/suites/documentation_standard/fixtures/destination_terminology_guidance_sets/sets"

AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
AGENT_EVAL_GUIDANCE_VARIANT=contextual-generic \
AGENT_EVAL_GUIDANCE_DIR="$GUIDANCE_SET_ROOT/contextual-generic" \
pytest maintainer/agent-evaluation/suites/documentation_standard \
  -m "agent_eval and routine" -q
```

The complete sets and their manifests are committed for reproduction.
Regenerate them from their maintained source sections with
`fixtures/destination_terminology_guidance_sets/compile.py` and use
`compile.py --check` in deterministic verification. See the fixture README and
destination-terminology test plan before running the terminology matrix.

For a fresh stochastic repetition with the same seed, task, fixture, guidance,
assertions, and model, set a unique branch cache label:

```bash
AGENT_EVAL_BRANCH_CACHE_VARIANT=repeat-1 \
...
```

The label changes only branch cache identity and is recorded in run evidence.

Each model profile runs from a generated projection of the configured Crystal
Lattice application. It retains the selected agent, providers, mixins,
application settings, and direct in-process feature plugins, but includes only
the selected profile's global path-based provider, instruction/request, and
authentication packages. The selected agent definition remains intact,
except that its broad agent-specific tool bundle is replaced by the core
`FileReaderTool`, `FileWriterTool`, and the existing `codex-tools` array shell.
All three use the isolated workspace and allowlist. MCP, web, image, skills,
and unrelated tool bundles remain disabled.
Other agents and their tool packages are absent. Each profile also gets a
separate plugin cache.

Path-installed evaluation providers use
`constraints/plugin-runtime.txt` through `PIP_CONSTRAINT`. This prevents a
fresh plugin cache from silently changing the provider SDK used by an
otherwise identical model run. The constraint file is part of the environment
fingerprint and must record why each pin is needed.

## Evidence

Artifacts are written under:

```text
tmp/agent-evaluation/documentation-standard/
```

Review `result.md`, `records/assertions.json`, `records/manual-review.md`, and
`records/semantic-assessment-input.json` first. Raw session and workspace
evidence remains available for diagnosing tool execution or mutation causes.