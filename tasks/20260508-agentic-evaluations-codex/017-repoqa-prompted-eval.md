# RepoQA Prompted Evaluation

Add a second RepoQA benchmark mode on top of the shared `evaluations/` package and the benchmark registry refactor. This mode should keep the current semantic evaluation/scoring logic, but switch the task format from an agentic/tool-based workspace flow to a single large prompt with no tools.

Parent Task: `tasks/20260508-agentic-evaluations-codex/000-main.md`

Depends On:

- `tasks/20260508-agentic-evaluations-codex/010-repoqa-agentic-eval.md`
- `tasks/20260508-agentic-evaluations-codex/015-benchmark-registry-refactor.md`

## Requirements checklist

- [ ] Add a second RepoQA benchmark identity, recommended name: `repoqa-prompted`.
- [ ] Register it through the benchmark registry so it exposes:
  - `download repoqa-prompted`
  - `manifest repoqa-prompted`
  - `run repoqa-prompted`
  - `internal run-single repoqa-prompted`
- [ ] Reuse the existing RepoQA dataset download/cache support and deterministic task selection where possible.
- [ ] Change the execution mode to a single large prompt with no tools.
- [ ] Keep the current semantic evaluation/scoring logic rather than introducing a new official-style scorer.
- [ ] Do not require JSON output from the model; prefer plain function text/code output closer to the original RepoQA format.
- [ ] Add parsing that normalizes plain code output into the answer shape expected by the current scorer.
- [ ] Support both host and Docker backends through the shared evaluation runtime.
- [ ] Add tests covering prompt construction, plain-code parsing, scoring reuse, and at least one fixture-backed end-to-end run.

## Scope and intent

This task is intentionally **not** about exact parity with upstream RepoQA.

The intended behavior is:

- closer to original RepoQA prompting style
- single prompt
- no tools
- no workspace inspection loop

But:

- keep the current local semantic function evaluation logic
- keep the shared artifact/result model
- keep this benchmark clearly distinct from official RepoQA results

## Functional target

The current RepoQA benchmark should remain intact as the custom/agentic mode.

This new prompted benchmark should instead:

1. build a large prompt from repo code context plus the needle description
2. send one request through `AgentApplication`
3. receive plain function text/code output from the model
4. parse that output into the normalized answer form expected by the current scorer
5. score it with the existing semantic code comparison logic

## Prompting requirements

Use the original RepoQA structure where it makes sense:

- instruction
- repository code context
- function description
- instruction again or final response reminder

Do **not** prompt the model to:

- inspect files with tools
- use a workspace
- return JSON unless naturally unavoidable

The desired answer shape from the model is:

- plain function source code
- optionally fenced code if the model chooses

The harness should handle normalization/parsing after the fact.

## Evaluation requirements

Reuse the evaluation logic already developed for the current RepoQA runner.

That means:

- reuse current function/code comparison logic
- preserve current semantic Python comparison behavior
- preserve current normalized-text fallback behavior for other languages

Do **not** implement a second upstream-style similarity/threshold evaluator in this task.

If parsing needs normalization into:

- `path`
- `symbol`
- `code`

that normalization should happen in the new prompted benchmark parser before passing the result into the shared scorer.

## Parsing requirements

Because the model output should be closer to the original RepoQA format, the prompted benchmark must support parsing:

- plain code output
- fenced code block output
- leading/trailing explanation noise when recoverable

Recommended normalization behavior:

- extract the main returned function code
- infer `symbol` from the function declaration where possible
- infer or fill `path` conservatively using task metadata if the output does not include it

The parser should be benchmark-specific, while the scorer should be shared/reused.

## Context construction requirements

The new prompted benchmark should build a single deterministic code context from the repo.

Initial implementation requirements:

- deterministic ordering
- stable truncation behavior
- configurable context budget

Suggested config additions under `agentic_evaluations`:

```json
{
  "repoqa_prompted": {
    "context_budget_chars": 120000,
    "max_files": null,
    "prompt_template_version": "v1"
  }
}
```

Exact field names may change, but prompted-mode settings should live under an explicit benchmark-specific subtree.

## Reuse expectations

This task should reuse the shared infrastructure from the earlier RepoQA and registry work:

- config-dir loading
- `.env`
- profiles
- scheduler
- Docker image build/runtime config
- result-writing helpers
- benchmark registry

This task should also reuse RepoQA-specific shared data helpers where practical:

- release download/cache
- dataset loading
- task iteration
- task metadata extraction

## Suggested module layout

Recommended new files:

- benchmark logic:
  - `evaluations/src/agent_evaluations/repoqa_prompted.py`
- benchmark registration:
  - `evaluations/src/agent_evaluations/benchmarks/repoqa_prompted.py`

If needed, a small shared RepoQA helper module may be introduced for scoring/data helpers, but avoid large restructuring unless clearly beneficial.

## Docker behavior

This benchmark should run through the same shared host/docker framework as other benchmarks.

The Docker path should work via:

- `internal run-single repoqa-prompted`

registered through the benchmark registry, without new hardcoded CLI wiring.

No special Docker packaging changes should be required beyond benchmark registration and internal dispatch.

## Artifacts

The prompted benchmark should emit the same family of artifacts as the current RepoQA runner:

- `run-manifest.json`
- `results.jsonl`
- `summary.json`

Per-task results should include enough debugging information for prompted runs:

- raw prompt metadata or prompt construction summary
- raw assistant output
- parsed normalized answer
- parse errors if any
- score and scoring details

The benchmark metadata should make clear that this is a custom prompted RepoQA mode, not the official benchmark.

## Tests

Add tests covering at minimum:

- prompt construction determinism
- context truncation behavior
- plain function code parsing
- fenced code parsing
- normalization into the existing scorer input shape
- one fixture-backed end-to-end host run
- one fixture-backed Docker smoke run if practical

## Notes

- Keep the current agentic RepoQA benchmark unchanged.
- The main difference from current RepoQA should be prompting/execution style, not evaluation semantics.
- Do not force JSON output when the original benchmark style does not.
- Prefer plain function text output and robust harness-side normalization.