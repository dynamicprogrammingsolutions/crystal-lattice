# OpenAI Responses Benchmark And Snapshot Refresh

This directory holds the OpenAI Responses plugin's benchmark runners and the
checked-in snapshot refresh scripts. These tools are not part of the runtime
plugin; they are maintainer utilities for measuring tier/latency behavior and
for refreshing the checked-in model and pricing snapshots the plugin ships.

## Scripts

### Tier matrix benchmark

`run_openai_responses_tier_matrix.py` runs a matrix of OpenAI Responses
requests across auth modes (`api`, `chatgpt`), service tiers (`default`, `flex`,
`priority`), and models. It records per-run usage, latency, and status into a
cumulative JSON results store and writes a text artifact under `artifacts/`.

Useful options:

- `--model` or `--models` (comma-separated)
- `--repeat`
- `--execution-mode sequential|parallel`
- `--run-scope api|chatgpt|both`
- `--desired-input-tokens`
- `--desired-output-tokens`
- `--profile` (free-form label recorded in the results store)
- `--agent-config-json` (path to a benchmark agent config JSON; see
  `kimi_ollama_benchmark_agent.json` for an Ollama-cloud example)

The script saves a text artifact under `artifacts/` containing:

- the benchmark configuration
- one section per model/tier/repeat run
- actual usage and duration metrics
- aggregate summaries per model/tier row

Cumulative results are appended to
`artifacts/openai_responses_tier_runs.json` (see
`openai_responses_tier_matrix_store.py` for the store helpers).

### Tier run summarizer

`summarize_openai_responses_tier_runs.py` reads the cumulative results store
and prints aggregate summaries filtered by profile, model, and case name.

```bash
python plugins/openai_responses/benchmark/summarize_openai_responses_tier_runs.py
python plugins/openai_responses/benchmark/summarize_openai_responses_tier_runs.py \
  --profiles standard-3k-500 --models gpt-5.4,gpt-5.6-sol
```

### Ollama cloud benchmark sequence

`run_ollama_cloud_benchmark_sequence.py` runs the tier matrix runner against a
local Ollama cloud endpoint for a fixed set of models and profiles. It uses
`kimi_ollama_benchmark_agent.json` as the benchmark agent config. State and
logs are written under `/tmp/`.

### Codex models snapshot refresh

`refresh_openai_responses_models.py` refreshes the checked-in Codex models
snapshot at
`src/openai_responses_plugins/data/openai_codex_models.json` from the live
GitHub Codex catalog. Run this when upstream publishes new GPT-5.6 family
entries or when the checked-in snapshot is stale.

```bash
python plugins/openai_responses/benchmark/refresh_openai_responses_models.py
```

### Pricing snapshot refresh

`refresh_openai_responses_pricing.py` refreshes the checked-in OpenAI pricing
snapshot at `src/openai_responses_plugins/data/openai_model_pricing.json` from
the official OpenAI pricing page. The parser supports both legacy three-price
rows and the newer four-price rows (with cache-write pricing).

```bash
python plugins/openai_responses/benchmark/refresh_openai_responses_pricing.py
```

## Running the unit tests

The benchmark scripts have unit tests in the plugin test suite that load them
via `importlib.util.spec_from_file_location`:

```bash
pytest plugins/openai_responses/tests/test_run_openai_responses_tier_matrix_unit.py -q
pytest plugins/openai_responses/tests/test_openai_responses_tier_matrix_store_unit.py -q
```

## Environment

The benchmark runner loads the repo-root `.env` via `python-dotenv` so
`OPENAI_API_KEY` and other credentials can live there. ChatGPT-auth benchmark
cases use saved credentials under
`plugins/chatgpt-auth-app/tests/.manual-state` by default, or
`CHATGPT_TEST_STATE_DIR` when overridden.