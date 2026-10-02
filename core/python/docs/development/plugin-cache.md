# Plugin installation cache lifecycle

`AgentApplication` resolves plugins through `PluginManager`. The manager owns a `PluginCache` lease for the lifetime of the application. Standalone managers retain their own lease until `close()` or collection. A cache-wide OS file lock serializes plugin resolution and startup cleanup across processes. Python, Node, and Bash sources claim each selected installed directory while that lock is held; subsequent startups keep directories claimed by live processes. The startup sweep runs after the application has claimed its configured plugins so a warm startup reuses its installations.

The coordination files live beside the configured plugin cache, in `.<cache-name>.cache_control/`. A unique lease stores relative install paths and an expiry. A daemon refreshes it every 30 seconds with an atomic replacement; the expiry is 120 seconds. A process holds the lease's OS file lock until close. Cleanup treats a lease as abandoned only when its expiry has elapsed **and** its OS lock is free. An unreadable lease causes cleanup to keep entries. The cache lock remains independent of heartbeat writes, so long installs do not interrupt renewal.

The sweep removes unclaimed revision directories at the root and below `node/` and `bash/`, and removes known abandoned installation or Git clone temporary directories older than 24 hours. It also removes abandoned Python install lock files. It skips symlinks and other unrecognized entries. The default pip download cache is disabled for new installs; the previous default `pip` directory is removed under the cache-wide lock. Explicit pip cache configuration is left untouched.

Python's per-install lock still coordinates work on one revision. The install
directory name combines the plugin ID with a content revision, so source
provenance such as `path`, `project_dir`, Git URL, ref, and entry point does
not decide whether its contents can be reused. This lets different checkouts
or worktrees safely share the same content-addressed installation while one
process has it leased. Plugin ID, valid metadata, and declared local dependency
versions are still checked. Git plugin metadata uses a stable
source/subdirectory identity instead of a temporary clone path, avoiding
needless reinstall of the same commit. Node and Bash copy paths also check for
live use before replacing a directory; Node skips rebuilding a copy claimed by
another process.

**Upgrade boundary:** Older runtimes do not publish leases. Stop/restart all older processes sharing a cache before the first startup of this version using it; otherwise that startup can remove their installations. A runtime using a different cache root is unaffected. If plugin resolution or an OS cache lock cannot complete, do not delete uncertain files; report the error. The implementation is in `agent_app/plugin_cache.py`, `plugin_manager.py`, `plugin_sources/`, and `application_future.py`.