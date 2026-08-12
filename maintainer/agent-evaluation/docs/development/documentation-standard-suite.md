# Documentation-standard behavioral suite

The suite under `suites/documentation_standard/` checks whether agents apply the
authored documentation and specification guidance during ordinary repository
tasks.

Seeds are guidance-neutral. Branches select an explicit guidance source:

- `baseline`: files from pinned revision `3a62b6fc`;
- `candidate`: files from the current repository working tree;
- another name plus `AGENT_EVAL_GUIDANCE_DIR`: files from an explicit directory.

The guidance source name, revision, file hashes, and combined hash participate
in workspace/cache identity and are recorded with the run. After restoring the
guidance-neutral seed, the suite adds the selected files in one delimited
guidance-context message and then adds the unchanged task as a separate user
message. The provider-neutral context message is used because not every
supported account/provider path accepts a historical `system` message.

## Baseline-first comparison

For new guidance-clarity cases:

1. Run the unchanged task against `baseline`.
2. Confirm that a representative run exhibits the targeted undesirable
   behavior.
3. Run the same seed, prompt, fixture, assertions, and model profile against
   `candidate`.
4. Try an expanded directory-backed variant only when the concise candidate is
   insufficient.

A baseline that already passes can provide robustness evidence, but cannot show
that candidate wording fixed a regression.

## Run GLM-5.2

Routine baseline:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
AGENT_EVAL_GUIDANCE_VARIANT=baseline \
pytest maintainer/agent-evaluation/suites/documentation_standard \
  -m "agent_eval and routine" -q
```

Routine candidate:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
AGENT_EVAL_GUIDANCE_VARIANT=candidate \
pytest maintainer/agent-evaluation/suites/documentation_standard \
  -m "agent_eval and routine" -q
```

Replace `routine` with `extended`, or use `agent_eval`, for broader runs.

## Run GPT-5.6-luna

Hosted runs require the explicit hosted gate:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_ALLOW_HOSTED=1 \
AGENT_EVAL_PROFILE=gpt \
AGENT_EVAL_GUIDANCE_VARIANT=baseline \
pytest maintainer/agent-evaluation/suites/documentation_standard \
  -m "agent_eval and routine" -q
```

Use `AGENT_EVAL_GUIDANCE_VARIANT=candidate` for the paired candidate run.

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

## Evidence

Artifacts are written under:

```text
tmp/agent-evaluation/documentation-standard/
```

Review `result.md`, `records/assertions.json`, `records/manual-review.md`, and
`records/semantic-assessment-input.json` first. Raw session and workspace
evidence remains available for diagnosing tool execution or mutation causes.