# Unified Runner Script For Terminal-Bench

Create a shell script that invokes `harbor run` with our adapter, config, and
profile, plus a test-slice variant for the 5-task smoke.

Parent Task: `tasks/20260623-terminal-bench-evaluation/000-main.md`

Depends On:
- `tasks/20260623-terminal-bench-evaluation/020-terminal-bench-adapter.md`
- `tasks/20260623-terminal-bench-evaluation/030-ollama-glm52-config.md`

## Requirements checklist

- [ ] `evaluations/evaluations/terminal_bench/scripts/run_terminal_bench.sh`
  accepts a config name (default `ollama_glm52`) and a profile name (default
  `terminal-bench-2-1-ollama-glm52-local`), loads `.env`, verifies harbor
  is installed, and invokes `harbor run` with our adapter and config.
- [ ] `evaluations/evaluations/terminal_bench/scripts/run_test_slice.sh`
  wraps `run_terminal_bench.sh` with `--n-tasks 5 --include-task-name <list>`
  for the 5-task smoke.
- [ ] Both scripts use `set -euo pipefail` and resolve `REPO_ROOT` from the
  script location (4 levels up).
- [ ] Both scripts check that `harbor` is on `PATH` and print a helpful
  install hint if not.
- [ ] Both scripts pass extra args through to `harbor run` via `$@` or an
  `EXTRA_ARGS` env var.

## Scope and intent

A single entrypoint so a user can run the terminal-bench evaluation with one
command, without remembering the full `harbor run` incantation. The script
handles path resolution, env loading, and pre-flight checks.

**In scope:**
- `run_terminal_bench.sh` — full run.
- `run_test_slice.sh` — 5-task smoke wrapper.

**Out of scope:**
- The config and profile themselves (subtask 030).
- The adapter (subtask 020).
- Actually running the benchmark (subtask 050).

## Execution plan

Status: Approved

### `run_terminal_bench.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

CONFIG_NAME="${1:-ollama_glm52}"
PROFILE="${2:-terminal-bench-2-1-ollama-glm52-local}"
EXTRA_ARGS="${EXTRA_ARGS:-}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
CONFIG_DIR="$REPO_ROOT/evaluations/evaluations/terminal_bench/config/$CONFIG_NAME"

if [[ ! -f "$CONFIG_DIR/.env" ]]; then
  echo "Warning: $CONFIG_DIR/.env not found; copy from .env.example" >&2
else
  set -a; . "$CONFIG_DIR/.env"; set +a
fi

command -v harbor >/dev/null 2>&1 || {
  echo "harbor not installed. Run: pip install harbor" >&2
  exit 1
}

exec harbor run \
  -d terminal-bench/terminal-bench-2-1 \
  -a "agent_evaluations.evaluations.terminal_bench.adapter:OurTerminalBenchAgent" \
  -c "$CONFIG_DIR/profiles/$PROFILE.json" \
  $EXTRA_ARGS
```

**Notes:**
- `SCRIPT_DIR` is `evaluations/evaluations/terminal_bench/scripts/` →
  `../../..` = repo root.
- The profile is a harbor `JobConfig` (passed via `-c`), so all harbor
  options (n_concurrent, n_tasks, include/exclude, timeouts, retries) live
  in the profile JSON and can be overridden via `EXTRA_ARGS`.
- `--agent` is our adapter's import path. Harbor imports it because
  `agent_evaluations` is installed.
- `--model` is not passed because our adapter ignores it (our config has
  the real model). Harbor may require a model arg; if so, pass a placeholder
  like `--model ollama/glm-5.2:cloud`.

### `run_test_slice.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# 5 fast tasks from the 89 (picked in subtask 050)
TASKS="build-cython-ext,break-filter-js-from-html,cancel-async-tasks,<2 more>"

EXTRA_ARGS="--n-tasks 5 --include-task-name $TASKS ${EXTRA_ARGS:-}" \
  exec "$SCRIPT_DIR/run_terminal_bench.sh" "$@"
```

**Notes:**
- The exact 5 task names will be finalized in subtask 050 after inspecting
  the dataset. The script will hardcode them for reproducibility.
- `EXTRA_ARGS` is prepended so the caller can still append more.

### Implementation decisions and open questions

**Decided:**
- Bash (not zsh) for portability — the existing RepoQA scripts use zsh,
  but harbor's own examples use bash. We'll use `#!/usr/bin/env bash`.
- Profile via `-c` (harbor `JobConfig` JSON) rather than individual `--flag`
  args, so all run settings are in one versioned file.
- `--model` placeholder if harbor requires it.

**Open:**
- Whether harbor requires `--model` even when the agent ignores it. Will
  test during 050; if required, add `--model ollama/glm-5.2:cloud` to the
  script.
- Exact 5 task names for the test slice — finalized in 050.

### Documentation

- `evaluations/evaluations/terminal_bench/README.md` (in subtask 060) will
  document the script usage.

### Task checklist

- [ ] Create `scripts/run_terminal_bench.sh`
- [ ] Create `scripts/run_test_slice.sh`
- [ ] `chmod +x` both scripts
- [ ] Verify `run_terminal_bench.sh --help` or a dry run resolves paths
      correctly (after 020/030 are done)

### Requirement verification

| Requirement | Evidence |
|---|---|
| `run_terminal_bench.sh` invokes harbor with adapter + config | Script contains `harbor run -d terminal-bench/terminal-bench-2-1 -a agent_evaluations...:OurTerminalBenchAgent -c .../profiles/...json` |
| `run_test_slice.sh` wraps with `--n-tasks 5 --include-task-name` | Script passes those flags via `EXTRA_ARGS` |
| `REPO_ROOT` resolves correctly | `cd "$SCRIPT_DIR/../../.." && pwd` returns repo root |
| Harbor install check | Script has `command -v harbor` check with helpful error |
| Extra args pass-through | `EXTRA_ARGS` env var is forwarded to `harbor run` |