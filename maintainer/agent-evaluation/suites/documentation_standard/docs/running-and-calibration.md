# Documentation-guidance behavioral suite

The suite under `suites/documentation_standard/` checks whether agents apply the
authored documentation and specification guidance during ordinary repository
tasks.

## Common Crystal Lattice runner contract

This is the baseline setup for every documentation-guidance real-model test.
It is not a separate test case, candidate, or optional evaluation mode.

- Derive a reduced test config from the normal Crystal Lattice default config.
  Keep only the selected agent and needed plugins, but preserve that agent's
  normal mixins and the production `feature-system-message` path.
- GPT uses the standard Codex developer-message template selected for
  `gpt-5.6-luna`. GLM uses the standard Claude system-message template through
  the `glm-ollama` agent.
- Preserve the selected agent's normal tool package as well as its message:
  GPT/Codex uses the Codex array-shell interface, while GLM/Claude uses the
  Claude Bash string-command interface. A model-family message paired with a
  different tool schema is not a default-runner result.
- Write the selected compiled `AGENTS.md` into the scenario workspace. The
  normal Codex or Claude helper reads that file while compiling the effective
  message.
- Use `include_tasks=false` for root-only planning and `include_tasks=true` for
  task-file planning. The normal `TASKS` template variable reads canonical
  `${CONFIG_DIR}/TASKS_v7.md`.
- Do not inject AGENTS or TASKS through a suite-owned feature unless direct
  injection itself is the historical behavior under test.
- Before model execution, inspect the effective message through the existing
  system-message feature and assert the standard model-family content, exact
  AGENTS and TASKS source hashes, expected occurrence counts, template order,
  absence of suite wrapper text, active tool family, and shell-command schema.
- Assert the initialized request carries the inspected content through the
  provider's normal representation: Responses `instructions` for the ChatGPT
  Codex profile and a leading system message for the GLM/Claude profile.

The projected config deliberately does not load the complete default agent
catalog. Fidelity comes from retaining the selected production agent,
model-family mixins, system-message feature, tool package, source files, and
request path.

Downstream semantic assessment starts only when every requested producer record
exists, matches the selected repeat variant, and passes deterministic producer
findings. Pairwise review starts only from semantic records whose own
deterministic findings pass. Process completion alone is not an upstream
success condition.

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
in workspace/cache identity and are recorded with the run. Source files and
delivery are separate evidence. The suite may deliver selected text through a
leading system message or endpoint `instructions`, leave a page in the
workspace for routed discovery, or use another explicitly versioned profile.
The unchanged task is then added as a user message. Strategy, role, position,
availability, and observed reads must be retained in evidence.

See
[Instruction delivery and authority](../../../../docs/instruction-delivery-and-authority.md).

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

## Compiled Requirements and Testing calibration

Guidance producers compile one selected bundle into the base owned by each
scenario. The default bundle is:

```text
maintainer/guidance/current
```

The latest candidate is:

```text
maintainer/guidance/candidates/root-requirements-testing-v2
```

The complete September 17 matrix that injected Crystal Lattice root guidance
into unrelated projects is frozen as legacy comparison evidence. Corrected
portable-guidance evaluation defaults to test-only targets colocated with the
Eleventy, FastAPI, and Flask/Vue fixtures. Those targets contain fixture facts
only. A real consuming repository supplies its own target path through an
explicit override, and its files are not stored here.

It supports two normal system-message modes:

- `root-only`: compile workspace `AGENTS.md` with `include_tasks=false`; ask
  for requirements and a plan in the response without task-file creation;
- `task`: compile the same workspace `AGENTS.md` with
  `include_tasks=true`; ask for one Draft task file.

The September 18 provisional matrix used the older suite-owned direct
injection path and is retained only as historical diagnostic evidence. The
[corrected default-runner matrix](../../../../docs/evaluations/documentation-guidance/20260918-default-runner-results.md)
replaces it for current interpretation.

Record current-bundle producer cells with:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
AGENT_EVAL_ROOT_GUIDANCE_MODE=root-only \
AGENT_EVAL_ROOT_GUIDANCE_CANDIDATES=glm-low,glm-high \
AGENT_EVAL_ROOT_GUIDANCE_CACHE_VARIANT=default-runner-r2 \
pytest maintainer/agent-evaluation/suites/documentation_standard/test_root_requirement_testing_guidance.py \
  -m "agent_eval and root_requirement_testing" -q
```

Set the consuming repository's absolute target path:

```bash
AGENT_EVAL_GUIDANCE_TARGET=/absolute/path/to/consumer-project/maintainer/guidance/target
```

Select the candidate by adding:

```bash
AGENT_EVAL_GUIDANCE_BUNDLE=maintainer/guidance/candidates/root-requirements-testing-v2
```

To use a historical guidance revision, point the bundle path at a checkout or
worktree for that revision. Tests do not permanently name a candidate or
commit.

For GPT through ChatGPT login, set `AGENT_EVAL_PROFILE=gpt` and
`AGENT_EVAL_ALLOW_HOSTED=1`.

Semantically assess a recorded subset with:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
AGENT_EVAL_SEMANTIC_DATASET=compiled-guidance \
AGENT_EVAL_ROOT_GUIDANCE_MODE=root-only \
AGENT_EVAL_ROOT_GUIDANCE_CANDIDATES=glm-low,glm-high \
AGENT_EVAL_ROOT_GUIDANCE_PRODUCER_VARIANT=default-runner-r2 \
AGENT_EVAL_SEMANTIC_CACHE_VARIANT=default-runner-r2 \
pytest maintainer/agent-evaluation/suites/documentation_standard/test_requirement_quality_semantic_evaluator.py \
  -m "agent_eval and requirement_semantic" -q
```

Add the same candidate bundle variable when assessing candidate records.

Pairwise quality review uses both bundle directories after semantic records
exist:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
AGENT_EVAL_ROOT_GUIDANCE_PRODUCER_VARIANT=default-runner-r2 \
AGENT_EVAL_ROOT_GUIDANCE_SEMANTIC_VARIANT=default-runner-r2 \
AGENT_EVAL_ROOT_GUIDANCE_QUALITY_CACHE_VARIANT=default-runner-r2 \
pytest maintainer/agent-evaluation/suites/documentation_standard/test_root_guidance_quality.py \
  -m "agent_eval and root_guidance_quality" -q
```

Every producer record preserves the compilation lock, source hashes, observed
compiled-message and tool delivery, model/effort, response or task file,
mutations, and deterministic findings. The compilation hash participates in
cache and dataset identity.

The September 18 pre-Documentation-section fixture run is incomplete: 83 of
84 producers and 11 of 12 semantic batches completed before one GLM-max call
was terminated after exceeding the two-hour monitoring boundary. Do not use
that run as a complete current/candidate comparison. The portable
Documentation section creates new compilation hashes and requires a fresh
matrix.

The subsequent September 18 matrix is summarized in the
[portable root-guidance report](../../../../docs/evaluations/documentation-guidance/20260918-portable-root-guidance-results.md).
Its root-only evidence is complete. Its task-mode semantic and pairwise stages
are unavailable because the first recorder missed retained task-file content
and the delivery profile collapsed root and task guidance into one instruction
message.

Task-mode evaluation obtains canonical task guidance from Crystal Lattice
runtime configuration. The consuming repository's target compiles only its
own root guidance.

Guidance source, compiler commands, and manual promotion rules are documented
in `maintainer/guidance/README.md`.

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

The current suite collects:

- 21 legacy consumers for direct comparison;
- 18 revised routine branches;
- 8 extended consumers;
- 26 revised branches over 11 guidance-neutral seeds.

## Run the diverse requirement-quality baseline

Subtask 067 uses three fresh, seedless project fixtures and a dedicated
requirement-minimal guidance variant. It does not use the ordinary
baseline/candidate selector and does not inject `TASKS-v7`.

Run nine GLM cases:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
AGENT_EVAL_TASK_GUIDANCE_VARIANT=current \
pytest \
  maintainer/agent-evaluation/suites/documentation_standard/test_requirement_quality_baseline.py \
  -m "agent_eval and requirement_baseline" -q
```

Run twelve GPT cases through the saved ChatGPT login:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_ALLOW_HOSTED=1 \
AGENT_EVAL_PROFILE=gpt \
AGENT_EVAL_TASK_GUIDANCE_VARIANT=current \
pytest \
  maintainer/agent-evaluation/suites/documentation_standard/test_requirement_quality_baseline.py \
  -m "agent_eval and requirement_baseline" -q
```

The two commands together produce exactly 21 model runs. Non-selected profile
cases are collected and skipped by each command. Deterministic findings cover
completion, specification/requirements presence, mutation scope, and exact
model/effort provenance; they do not judge requirement quality.

Each successful run writes `records/requirement-baseline.json` with the
project, approved target, generated files, response, producer profile, and
integrity findings. Interpret these records directly before designing an
automated semantic judge or changing guidance.

The September 14 accepted records are frozen for evaluator calibration:

```bash
PYTHONPATH=maintainer/agent-evaluation/src:maintainer/agent-evaluation:core/python:application/python \
python -m suites.documentation_standard.freeze_requirement_quality_baseline
```

## Run the current task-guidance requirement matrix

This matrix reuses the three projects, hidden requirement targets, and seven
producer profiles. The prompt asks only for one task file with a Draft
execution plan. It does not request a testing strategy; requirement
verification is elicited by the exact maintained `agents/TASKS-v7.md` guidance.

Run nine GLM cases:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
pytest \
  maintainer/agent-evaluation/suites/documentation_standard/test_requirement_quality_task_guidance.py \
  -m "agent_eval and requirement_task_current" -q
```

Run twelve GPT cases through the saved ChatGPT login:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_ALLOW_HOSTED=1 \
AGENT_EVAL_PROFILE=gpt \
pytest \
  maintainer/agent-evaluation/suites/documentation_standard/test_requirement_quality_task_guidance.py \
  -m "agent_eval and requirement_task_current" -q
```

Each run writes `records/requirement-task-current.json` with the task file,
exact current documentation/task guidance and effective message hash,
producer provenance, prompt, target, mutation paths, and structural findings.

For the paired working-tree candidate, use the same commands with:

```bash
AGENT_EVAL_TASK_GUIDANCE_VARIANT=candidate-v3
```

Candidate runs write `records/requirement-task-candidate-v3.json` and use a
separate dataset/cache identity. The current baseline guidance is pinned to
commit `73a2f4bf`; candidate guidance is read from the working tree.

## Run the semantic requirement and testing evaluator

The evaluator uses `glm-5.3-flash:cloud` at max effort and assesses all seven
producer outputs for one project in one call.

First verify the evaluator against the user-accepted baseline anchors:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_SEMANTIC_DATASET=accepted \
pytest \
  maintainer/agent-evaluation/suites/documentation_standard/test_requirement_quality_semantic_evaluator.py \
  -m "agent_eval and requirement_semantic" -q
```

Then evaluate requirement and testing-plan quality from the same task-file
outputs:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_SEMANTIC_DATASET=task-current \
pytest \
  maintainer/agent-evaluation/suites/documentation_standard/test_requirement_quality_semantic_evaluator.py \
  -m "agent_eval and requirement_semantic" -q
```

For candidate-v3 task files, use:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_SEMANTIC_DATASET=task-candidate-v3 \
pytest \
  maintainer/agent-evaluation/suites/documentation_standard/test_requirement_quality_semantic_evaluator.py \
  -m "agent_eval and requirement_semantic" -q
```

For a focused project batch, add a comma-separated subset such as:

```bash
AGENT_EVAL_SEMANTIC_CANDIDATES=glm-low,glm-max,gpt-high,gpt-max
```

Freeze the accepted comparison inputs after all producer and semantic records
exist:

```bash
PYTHONPATH=maintainer/agent-evaluation/src:maintainer/agent-evaluation:core/python:application/python \
python -m suites.documentation_standard.freeze_requirement_quality_candidate_results \
  --variant v3
```

Use `--variant v1` or `--variant v2` only to reproduce preserved earlier
candidate files.

The task-current command is expected to fail quality assertions when a
candidate omits required evidence, adds unsupported behavior, fragments
requirements materially, couples tests to implementation, or misses an
important crossing. A failed assertion does not discard the structured
semantic record.

After the producer and evaluator records are complete, freeze the current
dataset and both semantic comparisons:

```bash
PYTHONPATH=maintainer/agent-evaluation/src:maintainer/agent-evaluation:core/python:application/python \
python -m suites.documentation_standard.freeze_requirement_quality_current_results
```

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