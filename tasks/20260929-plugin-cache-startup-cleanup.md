# Clean plugin installation caches safely at startup

Remove unused plugin installation cache entries on each application startup while protecting entries used by other running processes. Coordinate cleanup with installation and keep an expiring, periodically refreshed ownership record for each process.

## Requirements checklist

- [x] Each `AgentApplication` startup cleans unused plugin installation entries, including abandoned installation and clone directories, so old revisions do not accumulate indefinitely.
- [x] After the upgrade restart boundary, cleanup and installation protect entries used by other lease-aware processes, including concurrent startups and installs; old processes sharing the cache must be restarted before the first updated startup.
- [x] Cache use is recorded by a process-owned lease with an expiry refreshed periodically; abandoned ownership can be reclaimed after a process exits or crashes without allowing a delayed refresh to evict a live process.
- [x] Installation-related pip cache growth is addressed for the default cache layout without deleting a separately configured pip cache belonging to another owner.

## Open questions affecting scope or outcomes

None identified. The user approved the pip cache and locking direction and explicitly requested immediate cleanup of legacy entries with restart instructions for the initial rollout.

## Supporting details

- **Fact:** `AgentApplication` selects `plugin_cache_dir` and builds `PluginManager` during construction (`core/python/agent_app/application_future.py`). The default path is `<config>/.plugin_cache/plugins`. `AgentApplication.close()` and application-owner reload provide lifecycle hooks.
- **Fact:** Python installs use `<cache>/<id>@<revision>` and have an OS file lock only while installing (`core/python/agent_app/plugin_sources/install.py`). An existing install may be removed when its metadata does not match. Git installation metadata includes a temporary clone's `project_dir`, which can make the same revision appear different on the next startup.
- **Fact:** Node and Bash tool sources create `node/<id>@<revision>` and `bash/<id>@<revision>` copies, including single-file tools. Their current copy/build paths are not all coordinated with other processes. Git source clones live temporarily under `src/`; Python installation temp directories live under the plugin cache.
- **Fact:** `PluginManager` sets a default pip cache next to `plugins` (or underneath a differently named cache directory). Existing tests expect that default to be passed to pip. An explicitly configured `plugin_policy.pip_cache_dir` may be shared with software outside this cache.
- **Decision already suggested in conversation:** Startup cleanup should use a cache-wide lock and process leases; a lease expiry alone must not authorize deletion while the owner still holds an OS process-lifetime lock. The user asked to record this plan, not to implement it yet.

## Execution plan
Status: Approved

Put coordination in the application plugin-cache ownership layer and use it from all cache-writing plugin sources. On application construction, take an OS cache-wide lock, inspect live leases, remove unused completed install directories and sufficiently old abandoned temporary directories (including legacy entries), resolve plugins, and register every cache directory selected by Python, Node, and Bash sources in this process's lease before releasing the lock. Standalone `PluginManager` uses and cache writers must obey the same coordination protocol so a startup sweep cannot race a standalone install or a fast-path reuse. Keep locks and ownership records outside install directories; do not traverse links or delete paths outside the configured cache root.

Use a unique lease per application/process owner with an atomic heartbeat update and a process-lifetime OS lock. Refresh the expiry while the app is alive, release on close, and reclaim an expired lease only if its OS lock can be obtained. Serialize cleanup against registering use and replacement. Prevent an installer from replacing a path protected by another live lease; fix unstable Git metadata/cache identity so a cached commit is reused instead of needlessly replaced. Account for multiple applications in one process and orderly reload where old and new applications overlap. Log cleanup failures and preserve entries when ownership cannot be established safely.

Handle the default pip cache separately from plugin install directories. Stop populating the automatically configured pip download cache for plugin installs, and remove its existing contents on startup under the cache-wide lock. Honor an explicit `pip_cache_dir` or explicit pip cache arguments without cleaning that external path. Reassess any pip caching performance tradeoff and existing documented expectations before implementation.

For rollout, remove unleased legacy entries as requested. Before the first startup of the updated code against a shared cache, stop/restart all processes using that cache that still run the old code, including a runtime hosting the current session if it uses the same cache and runtimes from other projects only if they share it. New code cannot discover an old process's use of an unleased installation. Subsequent new-code processes coordinate through leases. Make the heartbeat/expiry and temporary-entry age rules concrete when implementing, with realistic intervals and no dependency on a request being processed.

### Implementation decisions and open questions

- **Approved:** Serialize startup cleanup and plugin resolution under the cache-wide lock; simultaneous startups may wait for a clone or build. Keep heartbeats independent of this lock.
- **Approved:** Disable the automatically configured pip download cache and clear the old managed default cache on startup; preserve user configured pip caching. This changes existing default behavior and may increase download traffic when installs change.
- **Approved:** Use both expiry and an OS lifetime lock for stale-lease reclamation. If a lock cannot be checked, retain the entry; do not infer safety from an expired timestamp alone.
- **Approved rollout change:** Clean unleased legacy entries; tell the user to stop/restart old-code runtimes sharing a cache before its first new-code startup, including this session's runtime when applicable. No blanket restart is needed for separate cache roots.
- **Implementation choice to settle locally:** Select heartbeat interval, expiry, and the age threshold for lease-managed temporary entries based on tested recovery and realistic long installs; document those values.

### Documentation

- Update the plugin packaging/loading user guide (`plugins/docs/plugin-packaging-and-loading.md`) for startup reclamation, pip cache policy, and any operator-visible configuration or limitations.
- Update Core development documentation under `core/python/docs/development/` with cache layout, lock/lease lifetime, failure behavior, and ownership across plugin sources.

### Task checklist

- [x] Implement coordinated cache ownership, startup sweep, refresh, and close/reload release.
- [x] Integrate Python, Node, Bash, Git clone, and standalone manager operations with the coordination protocol; correct unstable install identity and protected-path replacement.
- [x] Implement the approved default pip cache handling and adjust existing expectations.
- [x] Add focused process-level regression coverage, update documentation, and run relevant Core checks.

### Requirement verification

- **Startup reclamation:** From a public `AgentApplication` construction using a temporary config/cache, verify obsolete completed Python, Node, and Bash entries and old abandoned temp/clone directories, including legacy entries, are reclaimed, while selected installs load and remain usable.
- **Live usage protection:** Run two actual processes against the same cache. Hold a loaded plugin in one while the other starts, reloads or installs, and sweeps; verify the first process can still import/use Python code and execute cached Node/Bash tools, and that a same-revision metadata mismatch cannot overwrite its files. Verify standalone manager activity is protected from the sweep.
- **Lease recovery:** With short test-controlled intervals, verify refresh prevents expiry during a live process pause, clean close releases ownership, and an exited/crashed process with expired ownership becomes reclaimable on the next startup. An expired heartbeat with the lifetime lock still held must not permit deletion.
- **Pip cache:** Exercise an actual plugin pip install using the default layout and inspect cache state after restart; verify an explicitly configured pip cache is neither cleared nor silently disabled.

### Additional implementation verification

- Run focused `core/python/tests` plugin-source and application-layer tests; check reload behavior and packaging/startup smoke expectations affected by a previously empty plugin cache. Use real processes where lock semantics matter, rather than only threads or mocked locks.
- Review unsafe filesystem cases (symlinks, partial installs, invalid metadata, Windows lock behavior), and run available platform-specific checks or report any unverified platform boundary.

## Implementation Notes

- Application startup claims selected installations before its sweep, preserving warm-cache reuse. Each `PluginManager.resolve_all()` call and the final sweep take the same cache-wide lock. This uses shorter critical sections than the draft's one lock across the entire application constructor while preserving the claim-before-cleanup invariant across processes.
- Coordination files are beside the plugin cache so runtimes containing only preinstalled plugins do not populate the plugin installation directory.
- The first post-upgrade startup removes unleased legacy revision directories. Older runtimes using the same cache must be stopped/restarted before this startup; this was explicitly requested instead of retaining legacy installations.
- Existing Core expectations for an automatically populated pip download cache were changed to the approved disabled-default behavior. Explicitly supplied pip cache paths and pip arguments still take precedence.
- The revised process-aware requirement reflects the user's explicit decision to reclaim legacy entries after a coordinated restart. The code uses one lock per `resolve_all` call and one for the sweep, since claiming each selected path under its resolution lock already prevents deletion by another lease-aware process.

## Completion Notes

- Startup reclaims unclaimed Python, Node, Bash, temporary clone/install, and obsolete Python lock entries. The default pip download cache is disabled and its old contents removed; explicit pip cache settings and arguments remain untouched. Live owners refresh a lease every 30 seconds, with a 120-second expiry and an OS lifetime lock.
- Requirement evidence: `core/python/tests/test_plugin_cache_cleanup.py` exercises public application startup cleanup, retained selected installs, cross-process Bash/Node/Python use, heartbeat refresh, crashed-owner reclamation, and explicit pip cache preservation. `core/python/tests/test_plugin_manager_git_install.py` verifies reuse of the same commit and refusal to replace a claimed revision. Other plugin source tests and application owner tests passed.
- Verification: 54 focused Core default tests passed; 2 selected Core integration tests passed with the `integration` marker enabled; 42 terminal/runtime-layout tests passed with this workspace on `PYTHONPATH`. Ruff, Black for the new cache code/tests, `pyright` for cache/manager/context types, and `git diff --check` passed. A broader `pyright` invocation reported existing type errors in application and plugin source files. Windows locking was reviewed but not tested on this macOS runner.
- Plan deviation: Cache resolution and the final sweep each acquire the same OS cache lock, instead of holding one lock for the entire application constructor. The selected paths are claimed while each resolution lock is held, so the sweep cannot delete another participating process's installation. Coordination files are beside the install directory to preserve packaging checks that expect an empty plugin directory for bundled-only runtimes.
- Rollout action: Before the first updated application startup using a shared `plugin_cache_dir`, stop/restart every process running older code against that directory. This includes a process hosting the current session only if it uses that directory; processes for other projects with separate cache roots do not need restarting. No process was restarted or cache on a live runtime cleaned during this work.

## Post-completion follow-up

- A real startup exposed that two checkouts/worktrees can request the same
  `<plugin-id>@<content-revision>` directory with different descriptive
  `path` or `project_dir` metadata. The first implementation treated every
  metadata field as install identity, then rejected replacement because
  another process correctly leased the directory.
- Corrected Python install reuse to validate the content-addressed directory
  by plugin ID and declared local dependency versions, without treating source
  provenance or entry-point metadata as installed-content identity.
- Extended the process-level Python regression test so one process installs
  and leases a plugin from one source directory while another
  `AgentApplication` starts from an identical copy at a different path and
  shares the installation. Updated Git coverage likewise verifies that
  different refs resolving to the same commit reuse the installed directory.
- The plugin changes were restored from `stash@{0}` into the dedicated
  worktree `/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260929-plugin-cache-cleanup`
  on branch `task/20260929-plugin-cache-cleanup`. Unrelated desktop changes
  from the same stash were restored to the original checkout. The stash was
  retained as a backup.
- Verification after the correction:
  - The exact two affected worktree plugins successfully started against
    `/Users/ferenci84/.crystal/cache/plugins` while the existing process held
    their leases. Their `installed_at` metadata remained unchanged, proving
    reuse rather than replacement.
  - Core non-integration: 599 passed, 1 expected failure, 27 deselected.
  - Application non-integration excluding one confirmed pre-existing failure:
    456 passed, 1 skipped, 89 deselected. The excluded
    `test_default_config_claude_system_message_renders_sections_tasks_and_agents`
    assertion also fails on the original checkout without these changes.
  - Focused cross-process/default tests: 54 passed; focused real-install
    integration tests: 2 passed.
  - Focused Ruff, Black, Pyright, and whitespace checks passed.