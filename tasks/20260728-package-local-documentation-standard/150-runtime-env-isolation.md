# 150 — Isolated runtime environment per evaluation run

Status: Draft (requirement recorded by the user on October 6, 2026; must be
done before the next evaluation run, including the approved b1v4 evaluation.
Approach decided by the user on October 6, 2026: option (a) process
isolation — one runtime process per run; no plugin changes, evaluation
harness owns spawn/IPC/teardown)

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

- [x] The framework must not install values into the global process
  environment in a way that can collide between sibling runs in one
  process: either runs are cleanly separated (for example one runtime
  process per run) or the framework uses a non-global mechanism and
  nothing needed at runtime is only reachable through `os.environ`.
- [x] Plugins and core code must not depend on global environment
  variables for per-run values; whatever mechanism replaces the overlay
  must deliver per-run values to plugins without process-global state.
- [x] Two sibling evaluation cases with different workspaces must be
  able to run concurrently in one process (or one runtime process each)
  without overlay conflicts; verified by a real concurrent run, not
  only unit-level assertions.
- [x] Matrix-wide evaluation runs no longer require
  `--max-concurrent 1`; the two-agent default concurrency works.

## Open requirement questions

- **Isolation approach — DECIDED October 6, 2026: option (a) process
  isolation.** One runtime process per run/workspace; plugins keep
  reading their process environment unchanged; the evaluation
  (crystal-lattice) environment gains worker-process spawn, IPC for
  value/snapshot/traceback transport, and teardown handling. Option
  (b) context-passing remains a possible future product direction but
  is out of scope for this task.
- ~~Isolation approach (was open, now decided):~~
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

Status: Approved (user directed execution start on October 10, 2026)

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

## Implementation Notes

- October 10, 2026 (execution started): inventory of overlay-managed
  key readers (`REPO_ROOT`/`WORKING_DIR`, excluding tests): framework
  — `agent_core/utils.py`, `agent_app/config.py`,
  `agent_terminal_app/cloud_runtime.py`; plugins — the
  `plugins/claude-tools/investigation/scripts/*` family (web search,
  compaction, read, glob, web fetch, write, task stop, mcp, mcp
  output, and more). Process-isolation (option a) requires NO changes
  to any of these readers — they keep reading their per-process
  environment; the isolation work is confined to the
  `agent_eval.crystal_lattice` environment (worker spawn, IPC for
  value/snapshot/traceback, teardown). Next: design the worker
  protocol in the crystal-lattice environment (the eval kernel stays
  in the parent).

- October 10, 2026 (worker design analysis): two viable shapes for
  option (a), decided: **fork-based worker with a context proxy** in
  `CrystalLatticeEnvironment.open` — the kernel contract
  (`environment.open → program(context) → snapshot/finalize`) stays
  unchanged; `open()` forks a child that owns the application and its
  `os.environ` copy (overlay installs per-process, so sibling forks
  with different roots coexist); the parent-side context becomes a
  pipe-backed proxy forwarding the CrystalLatticeContext surface the
  suite programs use (start, config updates, add_message, request
  event stream, session/workspace access, services.record). Rejected:
  full-case worker (running whole executors in the child) — it would
  move cache/artifact/evidence ownership across the process boundary
  and couple the framework to suite code; and spawn-based workers —
  suite programs are closures and not picklable, and fork preserves
  them without suite refactoring. Implementation order: (1) fork+pipe
  skeleton in the crystal-lattice environment behind a constructor
  flag (`isolated=True` default opt-in until verified), (2) proxy
  surface with pickling of values/observations/snapshots and traceback
  capture for worker crashes, (3) deterministic two-concurrent-runs
  test with different roots, (4) flip the task-guidance harnesses to
  `isolated=True`, re-run a mixed-agent slice without
  `--max-concurrent`, (5) remove the cap requirement from docs.

- October 11, 2026 (implementation landed, commit `7ae24039`):
  kernel extension — environments may expose `isolated_execute`
  (detected via getattr; `IsolatedExecutionOutcome` in
  `agent_eval.environment`) running the whole open → program →
  snapshot → finalize lifecycle in a forked worker
  (`crystal_lattice/isolated.py`); evidence is drained from the
  worker journal and merged into the parent's; snapshots cross as
  bytes via serialize/deserialize; worker failures arrive as
  phase-labeled RunErrors, worker death as `IsolatedWorkerDied`
  captured under `environment.isolated_execute`. Worker hygiene:
  fresh journal/services (no inherited locks), inherited fd close
  except the report pipe, pre-fork `gc.collect()` (SQLite
  descriptors), SIGINT ignored, logging disabled,
  `RuntimeEnvOverlay._managed` cleared in-child, `os._exit` (no
  parent atexit). Three fork-safety hazards found and fixed on
  macOS: (1) SQLite `os_signpost` crash in forked children once the
  PARENT ever opened sqlite — evaluation configs now set
  `application.cached_background_session_list.persistent_cache_enabled:
  false` (the session-list cache is the runtime's only SQLite user;
  no evaluation program lists sessions; one-time env-fingerprint
  cache rotation); (2) ObjC `+initialize` fork abort under
  concurrent sibling threads — the task-guidance runner re-execs
  itself once with `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES`
  (libobjc reads it only at process start); (3) `--max-concurrent`
  removed from the live-slice invocation. Task-guidance harnesses
  flipped to `isolated=True`. Deterministic tests:
  `tests/test_isolated_crystal_runtime.py` (full kernel path with
  cache replay + evidence merge + artifacts; two concurrent
  isolated siblings with different config roots whose INLINE
  control raises the overlay conflict; worker failure capture).
  Live verification `d-iso-tg01-r4` (uncapped, mixed-agent,
  planning + from-plan, tg01) in flight — first cases green
  including a cross-model continuation in a worker.

- October 11, 2026 (verification complete): live uncapped mixed-agent
  slice `d-iso-tg01-r4` — `--stages
  planning-session,task-creation-from-plan --scenarios
  tg01-eleventy-archive-handoff`, default two-agent parallelism, NO
  `--max-concurrent` — finished **11 cases: 11 ok**, zero overlay
  conflicts. Run-start evidence shows genuine cross-agent overlap
  (glm from-plan child at 10:58:24 while gpt planning-unguided at
  10:58:27; same-second glm+gpt from-plan starts at 11:04:22,
  11:14:09, 11:25:40) — precisely the pattern that failed
  `d-trial-tg01-r3`. Cross-model continuations (glm children from
  gpt planning) pass inside workers. Failed attempts en route:
  r1/r2 aborted with the ObjC fork guard before the re-exec fix; r3
  died to a re-exec argv bug (relative import without `-m`).
  `parse_max_concurrent` docstring updated: the cap is now optional
  debugging tooling, not a safety requirement. Full framework suite:
  183 passed (incl. 3 new isolated tests), 3 pre-existing
  cleanup-fallout failures unchanged (doc-standard preflight ×2,
  requirement-quality frozen datasets).

### Implementation decisions and open questions

- None beyond the open requirement question above; no implementation
  has started.

### Documentation

- Update the task-guidance reproduction docs (runner concurrency
  guidance) and the application/plugin documentation that describes
  runtime environment resolution, in the same change as the behavior.

### Task checklist

- [x] Inventory overlay-key consumers across the runtime and plugins
- [x] Present isolation options; user decides the approach
- [x] Implement chosen isolation approach
- [x] Concurrent mixed-agent verification run
- [x] Update concurrency guidance and related docs

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
