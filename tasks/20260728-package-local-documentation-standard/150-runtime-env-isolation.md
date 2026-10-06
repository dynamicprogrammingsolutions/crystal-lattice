# 150 — Isolated runtime environment per evaluation run

Status: Draft (requirement recorded by the user on October 6, 2026; must be
done before the next evaluation run, including the approved b1v4 evaluation)

Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

The application runtime installs resolved environment values
(`REPO_ROOT`, `WORKING_DIR`, …) into the real process environment via a
process-global, reference-counted overlay (`RuntimeEnvOverlay` in
`core/python/agent_app/runtime_env.py`). Two simultaneously-live
applications with different roots raise
`Conflicting runtime environment overlay` and the run fails. Every
evaluation case runs in its own workspace, so sibling cases in one
process cannot run concurrently; the first mixed-agent matrix run
(`d-trial-tg01-r3`, October 5, 2026) failed exactly this way and the
current workaround is the runner's `--max-concurrent 1` cap.

## Requirements checklist

- [ ] The framework must not install values into the global process
  environment in a way that can collide between sibling runs in one
  process: either runs are cleanly separated (for example one runtime
  process per run) or the framework uses a non-global mechanism and
  nothing needed at runtime is only reachable through `os.environ`.
- [ ] Plugins and core code must not depend on global environment
  variables for per-run values; whatever mechanism replaces the overlay
  must deliver per-run values to plugins without process-global state.
- [ ] Two sibling evaluation cases with different workspaces must be
  able to run concurrently in one process (or one runtime process each)
  without overlay conflicts; verified by a real concurrent run, not
  only unit-level assertions.
- [ ] Matrix-wide evaluation runs no longer require
  `--max-concurrent 1`; the two-agent default concurrency works.

## Open requirement questions

- **Isolation approach (material design decision, user to approve):**
  (a) process isolation — one runtime process per run/workspace, the
  overlay stays as-is inside each process; (b) context-passing — pass
  per-run values explicitly (request context / plugin state) and stop
  writing them to `os.environ`; (c) namespaced overlay keyed per
  application instance, with plugins migrated off raw `os.environ`
  reads. Tradeoffs: (a) is the strongest separation but changes
  execution/teardown shape and costs process startup per case; (b) is
  the cleanest long-term contract but touches every plugin that reads
  `REPO_ROOT`/`WORKING_DIR`; (c) is incremental but keeps a global
  registry. Recommendation deferred until the plugin-side inventory
  exists.

## Supporting facts

- `RuntimeEnvOverlay` (`core/python/agent_app/runtime_env.py:10-56`)
  installs into `os.environ`, is reference-counted via weakrefs, and
  raises on conflicting live values by design ("process-global
  environment variables cannot represent multiple different
  application roots at once").
- Failure evidence: `d-trial-tg01-r3` child runs failed in
  `environment.open_or_close` with `Conflicting runtime environment
  overlay for 'REPO_ROOT'` when a gpt planning app and a glm
  from-plan child were live simultaneously
  (`tmp/agent-evaluation/task-guidance/*/runs/*from-plan*/raw/errors/environment-open_or_close.txt`,
  October 5, 2026).
- Past full-matrix runs never hit this because they were single-agent
  (zai-only retests); the per-agent semaphore (`{glm:1, gpt:1}`)
  serializes cases within an agent, so the conflict only fires on
  cross-agent (or raised-cap) overlap.
- Interim mitigations already committed (October 5, 2026):
  `ce64b642` cross-config continuation support;
  `af1f73a2` in-process planning memo (dependent executors reuse the
  shared planning run) and runner `--max-concurrent` cap.
- `b1v3-gpt6-r1` (the baseline retest) ran 229 serialized cases
  successfully over ~9 hours with `--max-concurrent 1`, proving the
  workaround but also its cost.

## Execution plan

Status: Draft

1. Inventory: every reader of the overlay-managed keys
   (`REPO_ROOT`, `WORKING_DIR`, and any other resolved config env
   values) across `agent_app`, `agent_core`, repo-root `plugins/`, and
   the evaluation harnesses; record which consumers truly need
   process-env visibility (for example subprocess-spawned tools) versus
   which can take values from plugin state or request context.
2. Present the isolation options with the inventory-informed tradeoffs
   and get a decision on the open question above.
3. Implement the chosen approach end-to-end, including plugin migration
   where required, keeping backward compatibility for single-run
   embeddings that set env values deliberately.
4. Verify: a concurrent mixed-agent run (two live cases with different
   workspaces, real runtime) completes without overlay errors, plus
   deterministic tests covering the new mechanism at its public
   boundary; then remove the `--max-concurrent` requirement from
   matrix-run guidance.

### Implementation decisions and open questions

- None beyond the open requirement question above; no implementation
  has started.

### Documentation

- Update the task-guidance reproduction docs (runner concurrency
  guidance) and the application/plugin documentation that describes
  runtime environment resolution, in the same change as the behavior.

### Task checklist

- [ ] Inventory overlay-key consumers across the runtime and plugins
- [ ] Present isolation options; user decides the approach
- [ ] Implement chosen isolation approach
- [ ] Concurrent mixed-agent verification run
- [ ] Update concurrency guidance and related docs

### Requirement verification

- Concurrent-run requirement: one real mixed-agent evaluation run (or
  equivalent two-runtime concurrent harness exercise) with both cases
  live and different roots, asserting no overlay error and both runs
  valid.
- No-global-env requirement: inventory result (no remaining
  per-run value readable only via `os.environ` for in-process
  consumers) plus focused tests at the mechanism's public boundary.
- Matrix concurrency requirement: a matrix-slice run under default
  two-agent concurrency completes without `--max-concurrent`.
