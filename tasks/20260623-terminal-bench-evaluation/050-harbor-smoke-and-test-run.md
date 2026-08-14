# Harbor Smoke Test And Ollama Test-Run

Verify the local environment works with harbor (oracle smoke), then run a
5-task slice of Terminal-Bench 2.1 with our adapter + Ollama + GLM-5.2 and
confirm the harness produces artifacts.

Parent Task: `tasks/20260623-terminal-bench-evaluation/000-main.md`

Depends On:
- `tasks/20260623-terminal-bench-evaluation/020-terminal-bench-adapter.md`
- `tasks/20260623-terminal-bench-evaluation/030-ollama-glm52-config.md`
- `tasks/20260623-terminal-bench-evaluation/040-runner-script.md`

## Requirements checklist

- [ ] `harbor run -d terminal-bench/terminal-bench-2-1 --agent oracle
  --n-concurrent 2 --n-tasks 2` completes locally: harbor downloads the
  dataset, builds the task Docker images, runs the oracle solutions, and
  the verifier passes for both tasks.
- [ ] `ollama serve` is running and `ollama list` shows `glm-5.2:cloud`
  (or the user confirms the model is available).
- [ ] `bash evaluations/evaluations/terminal_bench/scripts/run_test_slice.sh`
  completes without crashing: harbor runs 5 tasks with our adapter, each
  trial produces `agent/trajectory.json` and `verifier/ctrf.json`.
- [ ] The harbor job directory (`jobs/<job-name>/`) contains `result.json`
  with per-trial outcomes and `config.json` recording the run.
- [ ] Our adapter's trajectory is visible in `harbor view jobs` (the viewer
  shows steps with bash tool calls and observations) — or, if the viewer is
  not run, the trajectory JSON has `Step` entries with tool calls.
- [ ] Any adapter bugs found during the test-run are fixed (iterating on
  020 if needed).

## Scope and intent

This is the integration validation. The goal is to prove the end-to-end
harness works: harbor + Docker + our adapter + Ollama + GLM-5.2 → artifacts
on disk. We are **not** aiming for a high pass rate on the 5 tasks — the
model may solve few or none. The success criterion is that the harness runs
without crashing and produces verifiable artifacts.

**In scope:**
- Oracle smoke test (harbor + Docker + dataset download).
- 5-task test-run with our adapter + Ollama.
- Inspecting artifacts.
- Fixing adapter bugs found during the run.

**Out of scope:**
- Full 89-task run (deferred).
- Pass-rate optimization.
- Leaderboard submission.
- Cloud sandbox (Daytona/Modal).

## Execution plan

Status: Approved

### Step 1: Pre-flight

```bash
# Docker running
docker info >/dev/null 2>&1 || { echo "Start Docker Desktop"; exit 1; }

# Harbor installed
harbor --version

# Ollama serving glm-5.2:cloud
ollama list | grep glm-5.2
curl -s http://localhost:11434/api/tags | grep glm-5.2
```

### Step 2: Oracle smoke

```bash
harbor run -d terminal-bench/terminal-bench-2-1 \
  --agent oracle \
  --n-concurrent 2 \
  --n-tasks 2
```

This runs the reference oracle solutions against 2 tasks. Expected: both
trials pass verification. This confirms harbor + Docker + dataset download
work without our adapter in the loop.

If this fails, debug harbor/Docker/network before proceeding.

### Step 3: Pick 5 fast tasks for the test slice

Inspect the 89 tasks and pick 5 that are expected to be fast (short
Dockerfile, short test suite, no heavy compilation). Candidates from the
registry:
- `build-cython-ext` (small Python build)
- `break-filter-js-from-html` (small JS task)
- `cancel-async-tasks` (async code task)
- 2 more TBD after inspecting the dataset

Finalize the list in `run_test_slice.sh` (subtask 040).

### Step 4: Test-run with our adapter

```bash
bash evaluations/evaluations/terminal_bench/scripts/run_test_slice.sh
```

Expected: harbor runs 5 trials with our adapter. Each trial:
1. Builds the task Docker image.
2. Starts the container.
3. Calls our adapter's `setup()` → constructs `AgentApplication`.
4. Calls our adapter's `run()` → drives our agent, which calls `bash` →
   `environment.exec`.
5. Verifier runs `test.sh` in the container.
6. Artifacts written to `jobs/<job-name>/<trial-name>/`.

### Step 5: Inspect artifacts

```bash
# Find the latest job
JOB_DIR=$(ls -td jobs/*/ | head -1)

# Job-level
cat "$JOB_DIR/result.json" | jq .stats
cat "$JOB_DIR/config.json" | jq .agents

# Per-trial
for trial in "$JOB_DIR"/*/; do
  echo "=== $(basename $trial) ==="
  cat "$trial/result.json" | jq '{reward, exception_info}'
  ls "$trial/agent/"
  ls "$trial/verifier/"
done
```

### Step 6: Iterate

If the adapter crashes, inspect the exception in `result.json` and the
trial's `agent/` logs. Fix in 020 and re-run.

### Implementation decisions and open questions

**Decided:**
- Oracle smoke before our adapter (isolates harbor/Docker issues from
  adapter issues).
- 5 tasks for the test slice.
- Pass rate is not a success criterion — harness completion is.

**Open:**
- Exact 5 task names (finalized in step 3).
- Whether harbor requires `--model` even when our adapter ignores it (will
  discover during step 4).
- Whether Ollama's `glm-5.2:cloud` tag is available locally or needs a
  `ollama pull` first (will check in step 1).

### Documentation

- Results of the test-run will be recorded in `000-main.md` Completion Notes.

### Task checklist

- [ ] Docker running, harbor installed, ollama serving glm-5.2:cloud
- [ ] Oracle smoke passes (2 tasks, both verified)
- [ ] 5 fast tasks selected and hardcoded in `run_test_slice.sh`
- [ ] `run_test_slice.sh` completes without crashing
- [ ] `jobs/<job-name>/result.json` exists with per-trial outcomes
- [ ] Each trial has `agent/trajectory.json` and `verifier/ctrf.json`
- [ ] Adapter bugs fixed (iterate on 020 if needed)

### Requirement verification

| Requirement | Evidence |
|---|---|
| Oracle smoke passes | `harbor run --agent oracle --n-tasks 2` exits 0; `result.json` shows 2/2 rewards = 1.0 |
| Ollama serving glm-5.2:cloud | `ollama list` shows `glm-5.2:cloud` |
| Test-run completes | `run_test_slice.sh` exits 0; `jobs/<job>/result.json` exists |
| Per-trial artifacts | Each trial dir has `agent/trajectory.json` and `verifier/ctrf.json` |
| Trajectory has our steps | `trajectory.json` contains `Step` entries with `bash` tool calls |
| No crashes | `result.json` `exception_info` is null for trials that reached verification |