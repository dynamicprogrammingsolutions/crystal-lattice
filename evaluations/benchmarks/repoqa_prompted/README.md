# RepoQA Prompted

Single-prompt, no-tools RepoQA benchmark mode.

This benchmark:

- builds one large prompt from repository context plus the needle description
- requires `ToolGatingFeature` so `disable_all_tools: true` actually removes tools
- expects plain function source code output
- reuses the shared semantic RepoQA scorer

## Real OpenAI API Config

Committed config directory:

- `evaluations/benchmarks/repoqa_prompted/config/openai_api/`

Intended run preset:

- profile: `repoqa-prompted-gpt54mini-docker`
- agent: `repoqa-prompted-openai-api`
- model: `gpt-5.4-mini`
- runtime: Docker

## Installation

Install the shared runtime in editable mode:

```bash
pip install -e core/python
pip install -e evaluations
```

Then use:

```bash
agent-evaluations --help
```

## Config vs Profile

`config.json` contains only model-stack runtime setup:

- plugins
- providers
- agents
- provider-level flex/retry/cost settings

The profile contains the evaluation plan:

- manifest generation inputs
- Docker runtime selection
- schedule
- restart policy

## Real Run Flow

Generate the deterministic all-language slice:

```bash
agent-evaluations manifest repoqa-prompted \
  --config-dir evaluations/benchmarks/repoqa_prompted/config/openai_api \
  --profile repoqa-prompted-gpt54mini-docker \
  --output-path evaluations/benchmarks/repoqa_prompted/config/openai_api/manifests/repoqa-prompted-all-limit10-seed1.json
```

Build the Docker image:

```bash
agent-evaluations container build \
  --config-dir evaluations/benchmarks/repoqa_prompted/config/openai_api \
  --profile repoqa-prompted-gpt54mini-docker
```

Warm the Docker-side plugin cache once before a cold parallel run:

```bash
agent-evaluations container warm-cache \
  --config-dir evaluations/benchmarks/repoqa_prompted/config/openai_api \
  --profile repoqa-prompted-gpt54mini-docker
```

Run the benchmark:

```bash
agent-evaluations run repoqa-prompted \
  --config-dir evaluations/benchmarks/repoqa_prompted/config/openai_api \
  --profile repoqa-prompted-gpt54mini-docker \
  --manifest-path evaluations/benchmarks/repoqa_prompted/config/openai_api/manifests/repoqa-prompted-all-limit10-seed1.json
```

## Outputs

Look at:

- `results/.../run-manifest.json`
- `results/.../results.jsonl`
- `results/.../summary.json`

The prompted runner records cost/usage metadata when the OpenAI Responses usage extension surfaces it.