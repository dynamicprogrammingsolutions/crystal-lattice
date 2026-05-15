# RepoQA Prompted Balanced OpenAI Config

This config directory is a separate `repoqa-prompted` setup for:

- balanced per-language task slices
- OpenAI Responses API runs
- `reasoning_effort: "none"`
- Docker-backed benchmark execution
- profile-driven result separation by setup

## Config / Profile / Manifest split

- `config.json`: runtime stack, plugins, provider behavior, reasoning settings
- `profiles/`: run defaults such as model, repeat count, backend, schedule
- `profiles[].paths`: setup-specific `results_root` and `workspace_root`
- `manifests/`: concrete task slices with `language`, `limit`, `seed`, and frozen task lists

## Sample workflow

Generate the balanced sample manifest:

```bash
agent-evaluations manifest repoqa-prompted \
  --config-dir evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced \
  --language all \
  --limit 20 \
  --seed 1 \
  --output-path evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced/manifests/repoqa-prompted-balanced-all-limit20-seed1.json
```

Build and warm the Docker runner:

```bash
agent-evaluations container build \
  --config-dir evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced \
  --profile repoqa-prompted-gpt54nano-balanced-sample-docker
```

```bash
agent-evaluations container warm-cache \
  --config-dir evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced \
  --profile repoqa-prompted-gpt54nano-balanced-sample-docker
```

Run nano on the 20-task sample:

```bash
agent-evaluations run repoqa-prompted \
  --config-dir evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced \
  --profile repoqa-prompted-gpt54nano-balanced-sample-docker \
  --manifest-path evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced/manifests/repoqa-prompted-balanced-all-limit20-seed1.json
```

Create the follow-up manifest that excludes tasks solved on every repeat:

```bash
python evaluations/benchmarks/repoqa_prompted/filter_manifest_by_success.py \
  --input-manifest evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced/manifests/repoqa-prompted-balanced-all-limit20-seed1.json \
  --task-aggregate-jsonl <run-dir>/task-aggregate.jsonl \
  --output-manifest evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced/manifests/repoqa-prompted-balanced-all-limit20-seed1-unsolved-by-nano.json
```

Run mini on the filtered manifest:

```bash
agent-evaluations run repoqa-prompted \
  --config-dir evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced \
  --profile repoqa-prompted-gpt54mini-balanced-sample-docker \
  --manifest-path evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced/manifests/repoqa-prompted-balanced-all-limit20-seed1-unsolved-by-nano.json
```

Run the final `gpt-5.4` sample pass on tasks still unsolved by mini:

```bash
agent-evaluations run repoqa-prompted \
  --config-dir evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced \
  --profile repoqa-prompted-gpt54-balanced-sample-docker \
  --manifest-path evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced/manifests/repoqa-prompted-balanced-all-limit20-seed1-unsolved-by-mini-sample.json
```

## Chained workflow helper

Use the workflow wrapper for the repeatable staged sample process:

```bash
python evaluations/benchmarks/repoqa_prompted/chained_workflow.py status
python evaluations/benchmarks/repoqa_prompted/chained_workflow.py refilter-next nano
python evaluations/benchmarks/repoqa_prompted/chained_workflow.py report
```

To isolate one chain's outputs without new profiles, pass `--artifact-root`. Example:

```bash
python evaluations/benchmarks/repoqa_prompted/chained_workflow.py \
  --artifact-root artifacts/run1 \
  run-stage nano
```

This places stage results under `artifacts/run1/results/...`, workspaces under `artifacts/run1/workspaces/...`, and workflow reports under `artifacts/run1/reports/...`.

The default workflow config is:

- `evaluations/benchmarks/repoqa_prompted/chained_sample20_workflow.json`

Supported commands:

- `prepare-base-manifest`
- `run-stage nano|mini|full`
- `seed-run nano|mini|full`
- `refilter-next nano|mini`
- `status`
- `report`

Example: expand the nano sample from 20 tasks to 25 tasks without rerunning the original 20-task instances:

```bash
python evaluations/benchmarks/repoqa_prompted/chained_workflow.py seed-run nano \
  --source-run-dir evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced/results/nano-sample/repoqa-prompted/<old-run-id> \
  --manifest-path evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced/manifests/repoqa-prompted-balanced-all-limit25-seed1.json
```

Then resume that seeded run:

```bash
python evaluations/benchmarks/repoqa_prompted/chained_workflow.py run-stage nano \
  --manifest-path evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced/manifests/repoqa-prompted-balanced-all-limit25-seed1.json \
  --run-manifest <new-run-dir>/run-manifest.json
```

The `report` command writes:

- a detailed JSON summary
- a compact task CSV
- a compact stage CSV

## Full workflow

Generate the balanced 200-task manifest:

```bash
agent-evaluations manifest repoqa-prompted \
  --config-dir evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced \
  --language all \
  --limit 200 \
  --seed 1 \
  --output-path evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced/manifests/repoqa-prompted-balanced-all-limit200-seed1.json
```

Then run:

- profile `repoqa-prompted-gpt54nano-balanced-full-docker` for the 5-repeat nano pass
- profile `repoqa-prompted-gpt54mini-balanced-full-docker` for the filtered 5-repeat mini pass