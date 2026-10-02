# Run model: labels, identity, and consolidation

The `agent_eval.runner` package is the reusable layer between the generic
kernel and an evaluation suite. The kernel (`AgentEval`) owns one
execution; the run model owns the *selection* semantics that a
multi-cell evaluation needs: which request a run answers, which
invocation produced it, and which records a consolidated dataset
contains.

## The pieces

| Piece | Meaning |
|---|---|
| `RunModel` | Owns one run label and executes requests through the kernel. `run()` is cache-aware (an unchanged request replays from the execution cache and records the cache hit); `run_samples(count)` executes N genuine runs as variance samples. |
| `request_identity(...)` | The structural cache and evidence key of one request: a namespace, a version, and a mapping of components (stage, agent, model, scenario, effort, variant, workspace fingerprint, prompt or target hashes, a parent identity for continuations). Run labels are **not** components — relabeling never changes identity. |
| `generate_run_label()` | A fresh label for one invocation. One invocation normally uses one label across every stage, so a freeze can select the whole invocation. |
| `publish_when_no_provider_errors` | The default publish predicate: a run whose value carries provider errors is not cached and re-executes naturally on a later invocation. |
| `select_cell_records(...)` | The consolidation core: groups raw records by a caller-supplied cell identity, resolves each record's label from its `run-model.json` provenance sibling (falling back to the legacy `run_attempt` field), and returns every sample of the listed labels — or the latest label per cell when no labels are given. |
| `render_selection`, `completeness`, `cell_statistics`, `aggregate_metric` | The shared reporting helpers over a selection: a human-readable selection string, expected/present/missing status, and per-cell mean and spread for multi-sample cells. |

Every executed run records a `run-model.json` provenance sibling next to
its records: the schema, the run label, the request identity, whether the
run replayed from cache, the sample index, and the run id. That sibling —
not fields on the record — is the provenance of a current run.

## Labels versus identity

Identity answers *what request is this*; a label answers *which
invocation produced it*. Because labels are provenance only:

- an unchanged request replays from the cache under any label;
- `--fresh` re-executes deliberately under the same identity;
- `--samples N` produces N genuine samples that share a cell and differ
  by sample index;
- a freeze with `--labels` selects every sample of the listed
  invocations, so multi-sample cells freeze with per-sample provenance.

## The fixture mini-evaluation

`tests/fixtures/run_model_scenario.py` is a complete, deterministic
mini-evaluation over the echo provider. It proves the whole mechanism in
short-running tests: labels are recorded and absent from identity, cached
replay is visible, a changed guidance compilation misses the cache, a
provider-error value is not cached and re-executes, `--fresh` re-executes,
samples execute genuinely, and a multi-label freeze aggregates per-cell
mean and spread with per-sample provenance while single-sample datasets
stay unchanged.

`tests/fixtures/crystal_mini_scenario.py` runs the same mechanism through
the real Crystal Lattice runtime: an echo agent produces the no-tool
scenario and assesses every subject with one request per subject, a
scripted provider failure retries naturally under the same identity, and
`agent_eval`-marked tests run both local Ollama models through the real
tool loop.

## How suites consume it

A suite composes identities from its own configuration and wraps the
kernel through `RunModel`; it never re-implements selection. The
task-guidance suite is the reference consumer:

- stage methods take `fresh`/`samples` and return one run per sample;
- each stage's identity function composes `request_identity` with the
  suite's namespace and components, and continuations carry the parent
  run's identity read from its provenance sibling;
- its freeze and results adapters are thin: they call
  `select_cell_records` with a cell-identity function per record group
  and render the selection with the shared helpers;
- its per-subject assessments load subjects through the same selection,
  so every sample of a cell is judged.

The layer contains no evaluation-specific names — no stages, scenarios,
or dataset identifiers — which a dedicated test enforces.