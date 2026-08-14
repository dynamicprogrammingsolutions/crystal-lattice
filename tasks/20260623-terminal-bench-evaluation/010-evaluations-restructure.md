# Restructure evaluations/ For Multiple Independent Evaluations

Move RepoQA into the new code/data-split layout and update discovery, tests,
scripts, and docs so `evaluations/` can hold multiple independent evaluations
side-by-side.

Parent Task: `tasks/20260623-terminal-bench-evaluation/000-main.md`

## Requirements checklist

- [ ] RepoQA code lives under `evaluations/src/agent_evaluations/evaluations/repoqa/`
  as importable package modules (`benchmark_prompted.py`, `benchmark_agentic.py`,
  `logic_prompted.py`, `logic_agentic.py`, `common.py`).
- [ ] RepoQA data lives under `evaluations/evaluations/repoqa/` with `config/`,
  `workflows/`, `scripts/`, and unified `AGENTS.md` + `README.md`.
- [ ] `benchmark_registry.py` discovers `benchmark_*.py` modules under
  `agent_evaluations.evaluations.*` subpackages; external
  `AGENT_EVALUATIONS_BENCHMARKS_DIR` override and legacy
  `agent_evaluations.benchmarks` fallback are preserved.
- [ ] All test files under `evaluations/tests/` pass against the new layout
  with no references to `evaluations/benchmarks/`, `repoqa_shared`, or
  `agent_evaluations_external_benchmark_*` module names.
- [ ] All runner scripts (top-level and config-embedded) reference the new
  `evaluations/evaluations/repoqa/` paths with correct `REPO_ROOT` depth.
- [ ] `evaluations/README.md` and `evaluations/AGENTS.md` document the new
  multi-evaluation layout and the per-evaluation contract.
- [ ] `evaluations/evaluations/repoqa/AGENTS.md` and `README.md` are unified
  from the 4 split files and reference the new code/data locations.
- [ ] `evaluations/pyproject.toml` includes the new `agent_evaluations.evaluations`
  subpackage in its packaged namespace (verified via editable install import).

## Scope and intent

This is a structural refactor. No new benchmark semantics, no behavior change
to RepoQA runs. The goal is to make room for terminal-bench (and future
evaluations) by establishing a clear code/data split:

- **Code** (importable, packaged): `evaluations/src/agent_evaluations/evaluations/<name>/`
- **Data** (co-located, not packaged): `evaluations/evaluations/<name>/`

The previous layout (`evaluations/benchmarks/<benchmark>/` with
`importlib.util` dynamic loading) is replaced. The `tasks/20260508-agentic-evaluations-codex/018-benchmark-owned-layout-and-run-profiles.md`
task file describes the old layout as the target; that task file is now
partially obsolete because it says "Remove concrete benchmark implementation
modules from `evaluations/src/agent_evaluations/`" which this restructure
reverses.

## Execution plan

Status: Approved

### Remaining work after commit `8ee24d20`

1. **Fix 3 test files** that still reference old paths:
   - `tests/test_repoqa_openai_api_integration.py` — uses
     `sys.modules["agent_evaluations_external_benchmark_repoqa_shared_common"]`
     and `..._repoqa_agentic`. Replace with direct imports from
     `agent_evaluations.evaluations.repoqa.*`.
   - `tests/test_repoqa_prompted_resume_and_seed.py` — loads `logic.py` and
     `chained_workflow.py` via `Path(__file__).parents[1] / "benchmarks" /
     "repoqa_prompted" / ...`. Replace with direct imports from
     `agent_evaluations.evaluations.repoqa.logic_prompted` and
     `agent_evaluations.evaluations.repoqa.workflows.chained_workflow`.
   - `tests/test_repoqa_prompted_filter_manifest.py` — loads
     `filter_manifest_by_success.py` via the old path. Replace with a direct
     import (the file is a sibling script in `workflows/`, not a package
     module; either keep `importlib.util` with the corrected path or import
     it as a package module if we move it — simplest is to keep it as a
     sibling script and fix the path).

2. **Fix config-embedded runner scripts** that still reference
   `evaluations/benchmarks/repoqa_prompted/...`:
   - `evaluations/evaluations/repoqa/config/openai_chatgpt_reasoning_none_minimal_system_balanced/run-comparable-limit50-repeat5-chatgpt-minimal-chain.sh`
   - Any other `run-*.sh` inside config dirs with the same pattern.
   - Update `REPO_ROOT` depth and path references to
     `evaluations/evaluations/repoqa/...`.

3. **Unify RepoQA docs**:
   - Merge `AGENTS_agentic.md` + `AGENTS_prompted.md` → single `AGENTS.md`.
   - Merge `README_agentic.md` + `README_prompted.md` → single `README.md`.
   - Update all internal path references to the new locations.
   - Remove the 4 split files.

4. **Update top-level docs**:
   - `evaluations/README.md` — document the new layout, the per-evaluation
     contract, and how to add a new evaluation.
   - `evaluations/AGENTS.md` — update the discovery section and the "where to
     change what" section for the new paths.

5. **Verify `pyproject.toml`** packages the new subpackage:
   - `[tool.setuptools.packages.find]` has `where = ["src"]` and
     `include = ["agent_evaluations*"]` — this should already include
     `agent_evaluations.evaluations.*`. Verify with an editable install and
     `python -c "import agent_evaluations.evaluations.repoqa"`.

6. **Run tests**:
   - `pip install -e evaluations` (re-install to pick up new subpackage).
   - `pytest evaluations/tests -q` — all tests must pass.

### Implementation decisions and open questions

**Decided:**
- Keep `filter_manifest_by_success.py` as a sibling script in `workflows/`
  (not a package module) — it's a standalone CLI tool, not imported by the
  package. Tests load it via `importlib.util` with the corrected path.

**Open:**
- Whether to update historical artifact JSON files under
  `config/*/artifacts/*/reports/*.json` that contain absolute paths to the
  old `evaluations/benchmarks/repoqa_prompted/...` location. These are
  recorded run reports, not active code. **Recommendation:** leave as-is;
  they're historical data and updating them would be cosmetic.

### Documentation

- `evaluations/README.md` (updated)
- `evaluations/AGENTS.md` (updated)
- `evaluations/evaluations/repoqa/AGENTS.md` (unified)
- `evaluations/evaluations/repoqa/README.md` (unified)

### Task checklist

- [ ] Fix `tests/test_repoqa_openai_api_integration.py`
- [ ] Fix `tests/test_repoqa_prompted_resume_and_seed.py`
- [ ] Fix `tests/test_repoqa_prompted_filter_manifest.py`
- [ ] Fix config-embedded `run-*.sh` scripts
- [ ] Unify RepoQA `AGENTS.md` from 2 split files
- [ ] Unify RepoQA `README.md` from 2 split files
- [ ] Update `evaluations/README.md`
- [ ] Update `evaluations/AGENTS.md`
- [ ] Verify `pyproject.toml` packages new subpackage
- [ ] `pip install -e evaluations` succeeds
- [ ] `pytest evaluations/tests -q` passes

### Requirement verification

| Requirement | Evidence |
|---|---|
| RepoQA code under `src/agent_evaluations/evaluations/repoqa/` | `ls` shows `benchmark_*.py`, `logic_*.py`, `common.py` |
| RepoQA data under `evaluations/evaluations/repoqa/` | `ls` shows `config/`, `workflows/`, `scripts/`, `AGENTS.md`, `README.md` |
| Registry discovers new layout | `python -c "from agent_evaluations.benchmark_registry import load_benchmarks; b=load_benchmarks(); assert 'repoqa' in b and 'repoqa-prompted' in b"` |
| Tests pass | `pytest evaluations/tests -q` exits 0 |
| No old path references | `grep -rn "evaluations/benchmarks\|repoqa_shared\|agent_evaluations_external_benchmark" evaluations/tests/ evaluations/evaluations/repoqa/scripts/ evaluations/evaluations/repoqa/config/*/run-*.sh` returns empty |
| Docs updated | `evaluations/README.md` mentions multi-evaluation layout; `evaluations/evaluations/repoqa/AGENTS.md` exists as single file |

## Implementation Notes

### 2026-06-23 — Partial work committed in `8ee24d20`

See `000-main.md` Implementation Notes for the full list of what was done in
that commit. The remaining work is captured in the Task checklist above.