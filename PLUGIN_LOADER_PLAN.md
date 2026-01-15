PLUGIN LOADER DESIGN & IMPLEMENTATION PLAN
=========================================

Status: finalized plan (interfaces, tests, implementation stages) for a split plugin loader
architecture where the core provides a small, dependency-free loader interface and the
application implements concrete installers (git/pip, local paths, wheels). This file
captures decisions you provided, recommended defaults for remaining choices, and a
step-by-step implementation/test plan.

Principles & constraints (from your choices)
- "Split" architecture: core contains only lightweight interfaces and validation helpers;
  application implements heavy installers and policy.
- Application MUST provide all runtime params (cache dir, policies). The manager will NOT
  resolve environment variables itself.
- For Python compatibility and build failures: try to install and report errors (no
  pre-validation of python_requires).
- sys.path precedence: core_first always. Core must not be overridden by plugins.
- Install on startup: the application will perform installs before initializing the core.
- Tests: do not mock git/pip. The layer that invokes git/pip will not be unit tested; instead
  lower pure-computation layers will have unit tests and integration tests will verify
  installation (git/pip) end-to-end.
- Remove existing directory-based plugin discovery from core (no module scanning in core).

Goals
- Provide a stable, minimal core-facing plugin loader interface usable across apps.
- Let application own policy and installation lifecycle (cache dir, allow_remote, install_on_startup).
- Allow plugins colocated in git repositories or local development directories; support
  future extension (wheels, RPC isolation) without changing core interfaces.
- Report structured errors the same way the application currently expects (list of dicts)
  so migration is straightforward.

High-level architecture
- agent_core (core)
  - Provide: plugin type definitions (existing), lightweight loader interface & datatypes,
    dotted-path loader implementation only, plugin id derivation and plugin-kind validation.
  - No network, no pip/git subprocess calls, no heavy dependencies.

- agent_app (application)
  - Provide: PluginManager that composes concrete PluginSource implementations:
    - LocalPathSource (dev-only sys.path insertion or optional editable install)
    - GitInstallerSource (clone + pip install --target into per-plugin cache)
    - WheelSource (future)
  - Own configuration and policy; read resolved config and pass explicit parameters to manager.
  - Orchestrate installation at startup, collect errors, then initialize core and register plugins.

Plugin kinds (5 total)
- Provider
- Provider Extension
- Feature
- Tool
- Application-level plugin (application-only type)

Core API (finalized interfaces)
--------------------------------
File: core/python/agent_core/plugin/loader.py (interface-only)

Python sketches (these are the canonical signatures to implement in core):

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Protocol, Tuple

@dataclass
class PluginMetadata:
    id: str
    kind: Optional[str]
    origin: str                # e.g. git URL or local path
    ref: Optional[str]
    commit: Optional[str]
    install_dir: Optional[Path]
    installed_at: Optional[str]
    entry: str                 # module.Class string
    raw_spec: Any

@dataclass
class PluginLoadResult:
    cls: Optional[type]
    metadata: Optional[PluginMetadata]
    error: Optional[Dict[str, Any]]

class PluginSource(Protocol):
    def supports(self, raw_spec: Any) -> bool: ...
    def load(self, raw_spec: Any, *, cache_dir: Path, policy: Mapping[str, Any]) -> PluginLoadResult: ...

def get_plugin_id(plugin_class: type) -> str:
    """Return stable plugin id (use `name` attribute or class name)."""

def validate_plugin_for_kind(plugin_class: type, expected_kind: str) -> Optional[Dict[str,Any]]:
    """Duck-type validate plugin_class implements methods for expected_kind.
    Return None on success or an error dict on mismatch."""
```

Concrete minimal implementation in core:
- DottedPathSource: implements PluginSource and performs importlib import of
  `module.Class` strings. Returns PluginLoadResult (no metadata beyond entry + raw_spec).

Notes (core)
- The core must NOT run pip/git or call subprocesses. Keep dependencies minimal.
- The core provides validation rules used by application-side loaders to ensure
  consistent type checks.

Application API (finalized interfaces)
--------------------------------------
File: core/python/agent_app/plugin_manager.py (suggested)

Class: PluginManager
- __init__(self, loaders: Optional[List[PluginSource]], cache_dir: Path, policy: Mapping[str,Any])
  - `loaders` defaults: [DottedPathSource (from core), LocalPathSource, GitInstallerSource]
  - `cache_dir` is REQUIRED (application must pass resolved value). Manager must not
    resolve env vars.
  - `policy` example keys:

```python
{
    "allow_remote": bool,
    "sys_path_precedence": "core_first",   # fixed by your choice
    "install_on_startup": bool,              # true by your choice
    "pip_args": List[str]                    # optional extra pip args
}
```

- load_one(self, raw_spec: Any, kind: Optional[str] = None) -> PluginLoadResult
  - Determine a suitable loader by calling loader.supports(raw_spec) in order.
  - Call loader.load(raw_spec, cache_dir=self.cache_dir, policy=self.policy)
  - If result.cls is present, call core.validate_plugin_for_kind(cls, kind) if kind provided
    and return PluginLoadResult (error populated on mismatch).

 - normalize_plugins(self, plugins_raw: Any) -> List[Dict[str, Any]]
  - NEW helper (optional for applications): rewrites input configuration into a canonical list
    `[{ "spec": <string|object>, "kind": <"providers"|"extensions"|"features"|"tools"|"application"|null> }, ...]`.
  - Accept mapping form (rewrite with known kind), flat list form (wrap with `kind=None`), or canonical items.
  - Short canonical entries (plain strings/objects) are treated as `{ "spec": value, "kind": null }`.

 - load_plugins(self, canonical_items: Iterable[Dict[str, Any]]) -> Tuple[Dict[str, List[type]], List[type], List[Dict[str,Any]]]
  - NEW main method. Expects the canonical list described above. For each item, loads classes from `spec` via loaders.
  - If an item includes `kind`, enforce via `validate_plugin_for_kind`; otherwise auto-detect.
  - Returns `(core_kinds, application_classes, errors)`.

- prefetch_all(self) -> List[Dict[str,Any]]
  - Trigger installs for every configured plugin (used when install_on_startup True).

- list_cached(self) -> List[PluginMetadata]
- purge(self, plugin_id_or_path: str) -> None

Loader implementations (application-side)
- LocalPathSource
  - supports: raw_spec string starting with `path:` or dict with `path` key.
  - behavior: if path points to a package dir, default behavior is fast-dev mode:
    append path to sys.path (append to end to keep core_first). Optionally support
    `editable_install: true` via policy to run `pip install -e` into a dedicated
    per-plugin dir if application requests reproducibility.

- GitInstallerSource
  - supports: dict with `git` key or string `git+<url>[#<ref>]::module.Class`.
  - load steps (synchronous, subprocesses):
    1. Validate `policy["allow_remote"]` true for remote git URLs; otherwise error.
    2. Create `src_tmp = cache_dir / "src" / tmpdir` and `git clone <url> src_tmp`.
    3. If ref provided, call `git -C src_tmp checkout <ref>`.
    4. Get commit SHA: `git -C src_tmp rev-parse HEAD` (or 'unknown').
    5. Compute safe_id: explicit `id` in spec else sanitized repo name.
    6. Install dir: `install_dir = cache_dir / f"{safe_id}@{commit}"`.
    7. If install_dir exists, skip install. Otherwise run:
         python -m pip install --upgrade --target <install_dir> <src_tmp/[subdirectory]> + pip_args
       Capture stdout/stderr. On failure, remove install_dir (if partially populated)
       and return error dict `plugin_install_error` (include stderr text if available).
    8. Write `install_dir / plugin_metadata.json` with origin, ref, commit, entry, installed_at.
    9. For core_first precedence append str(install_dir) to `sys.path` (i.e., add to end)
       so core packages take precedence.
   10. Import the requested entry `module.Class` (use importlib) and return PluginLoadResult.

  - Important: Manager does not attempt to pre-validate python version — it tries install and
    surfaces any failure (user choice #6). The error dict must include `stderr` or `detail`.

- WheelSource (future)
  - Accept wheel paths or prebuilt wheel caches and install/add to sys.path.

Config keys (application-level)
- Top-level keys you should add to application config schema (application is authoritative):
  - `plugin_cache_dir` (string path) — REQUIRED by PluginManager; app must resolve any env placeholders.
  - `plugin_policy` (object, optional):

```json
{
  "allow_remote": true,
  "install_on_startup": true,   # you chose install-on-startup
  "sys_path_precedence": "core_first",  # fixed
  "pip_args": [],
  "editable_local_installs": false
}
```
  - `plugins` (auto-detected by default):
    - Mapping form (backwards compatible): `{ "providers": [...], "features": [...], "tools": [...], "extensions": [...] }`.
    - NEW flat list form: `plugins: [ <spec>, <spec>, ... ]` — kinds are auto-detected (including application plugins).
      In this mode, application plugins may be listed together with core plugins; the manager returns them separately
      so the app can register appropriately.
  - `application_plugins` (back-compat): still accepted; when `plugins` is a flat list containing application plugins,
    this separate key can be omitted.
  - Canonical form (advanced/explicit; input to `load_plugins`): `plugins: [ { "spec": <string|object>, "kind": <string|null> }, ... ]`.
    - The application is responsible for parsing raw config into this canonical list (optionally using `normalize_plugins`).
    - When `kind` is provided for an item, validation is enforced for that item. Plain strings/objects are equivalent to canonical items with `kind=null`.

Plugin spec formats supported (recommended)
- Dotted path (backwards compatible):
    "plugins.openai_provider.OpenAICompatibleProvider"

- Local dev path (string):
    "path:../dev/myplugin::myplugin.provider.DevProvider"

- Local dev path (dict):
    { "path": "/home/dev/plugins", "entry": "my_dev_plugins.PluginClass" }

- Git compact string (shorthand):
    "git+https://github.com/org/myplugin.git#v1.2::mypkg.provider.PluginClass"

   - Git dict (preferred for precise installs):

```json
{
  "git": "https://github.com/org/myplugin.git",
  "ref": "v1.2.3",
  "subdirectory": "python",
  "entry": "mypkg.provider.PluginClass",
  "id": "myplugin"
}
```

- Multiple classes and module-only entries (NEW):
  - `entry` may be a module without class (e.g., `"mypkg.plugins"`); the loader imports the module
    and auto-discovers all plugin classes by duck-typing.
  - Dict form may include `entries` as a list of dotted class strings to import multiple classes.

```json
{
  "git": "https://github.com/org/myplugin.git",
  "ref": "v1.2.3",
  "entry": "mypkg.plugins",
  "entries": ["mypkg.a.ProviderA", "mypkg.b.FeatureB"],
  "id": "myplugin"
}
```

- Optional plugin descriptor (NEW):
  - Repos may include `agent_plugin.json` (or `.yaml`) with an `entries` array of dotted classes and
    optional metadata. When a spec omits class entries (e.g., provides only repo/module), the loader
    will attempt to read this descriptor to load multiple classes. If the user config points to a single
    class directly, the descriptor is skipped (it may still be read for metadata only).

Error types (standardized)
- `plugin_path_invalid` — malformed spec or missing required fields
- `plugin_install_error` — git/pip subprocess failed (include `stderr` if available)
- `plugin_import_error` — importlib import of the entry failed
- `plugin_python_mismatch` — (OPTIONAL) if manager chooses to enforce; per your choice we will not pre-check
- `plugin_type_mismatch` — imported class does not satisfy expected plugin-kind

Caching & naming
- Cache layout (app-owned `plugin_cache_dir`):
  - `<cache_dir>/src/` — temporary clones and working directories
  - `<cache_dir>/<safe_id>@<commit>/` — installed plugin and its dependencies (pip --target)
  - `<cache_dir>/metadata/registry.json` (optional): application-level index of installed plugins

- Naming: `safe_id` is either explicit `id` in the spec or a sanitized repo-name. Use commit SHA
  for exact reproducibility. If commit cannot be resolved, you may use `unknown` but prefer failing
  the install if `rev-parse` fails.

Sys.path policy (core_first)
- To guarantee core-first behavior: always append plugin install dirs to the end of `sys.path`.
  For local `path:` dev mode, append the path rather than inserting at front. This ensures core
  runtime packages are used ahead of plugin-provided packages.

Install lifecycle & startup sequence (application)
1. Read raw config and resolve placeholders (application is responsible for resolving env and file placeholders).
2. Extract `plugin_cache_dir` and `plugin_policy` and instantiate `PluginManager(loaders=..., cache_dir=Path(plugin_cache_dir), policy=plugin_policy)`.
3. If `policy["install_on_startup"]` is True (per your choice), call `manager.prefetch_all()`; collect errors and populate `application._config_errors`.
4. Build a canonical plugins list and register via a unified path:
   - Convert raw `plugins` config (mapping or flat list) to canonical items (either within your app config code or by
     calling `manager.normalize_plugins(plugins_raw)`).
   - Call `manager.load_plugins(canonical_items)`; the manager enforces `kind` when provided and auto-detects otherwise.
   - Register returned `core_kinds` on `AgentCore` and wrap `application_classes` with `ApplicationPluginWrapper`.

Concurrency / atomic install notes
- To avoid race conditions, install into a temporary target directory and rename/move atomically into the final `<safe_id>@<commit>` directory when install succeeds.
- If install fails, remove temporary artifacts. Consider using a file lock per `safe_id@commit` to avoid concurrent installs.

Testing strategy
----------------
Unit tests (core-only, no git/pip subprocesses)
- Test `get_plugin_id()` and `validate_plugin_for_kind()` behaviors and edge cases.
- Test `DottedPathSource` import behavior using local test modules already in the repo (no network or subprocess).
- Test helper pure functions: `safe_id` generation from git URL, path normalization, metadata serialization.

Integration tests (verify installation steps; DO NOT mock git/pip)
- Provide integration tests under `core/python/tests/integration_plugin_install.py` (or similar) that:
  - Create a temporary directory and initialize a local git repo in it (`git init`), add a minimal Python package (pyproject.toml or setup.py) exposing a plugin class under a module path.
  - Commit the package and tag/branch if desired.
  - Configure a plugin spec using the local `file://` or `git+` path pointing at the temp repo; run `PluginManager` with a temp `plugin_cache_dir` and `install_on_startup` behavior.
  - Assert that `python -m pip` succeeded (i.e., `install_dir` exists and contains expected package files) and that importing `entry` returns the expected class.
  - Clean up the cache dir.

- Integration tests must be marked (e.g., pytest marker `integration`) because they:
  - Use subprocesses (`git`, `pip`).
  - May require build backends (PEP 517) available in the test environment.

Test notes by your choice (#16)
- Do not mock git/pip. The GitInstallerSource invocation layer (the code that calls subprocess) is not unit-tested; instead rely on integration tests to validate full install flow.

Implementation stages (concrete tasks)
--------------------------------------
Stage 0 — Design & plan
- (this file) PLUGIN_LOADER_PLAN.md (done)

Stage 1 — Core: interfaces & lightweight loader (low risk)
- Add `core/python/agent_core/plugin/loader.py` with dataclasses PluginMetadata, PluginLoadResult, PluginSource Protocol, `DottedPathSource`, `get_plugin_id`, and `validate_plugin_for_kind`.
- Add unit tests covering validation and dotted-path import behavior.
- Remove `discover_and_register` from `AgentCore` (per your choice #18):
  - Search for usages in the repo and migrate tests to use the manager in later stages.
  - Note: Removal is a breaking change; update tests and docs accordingly.

Stage 2 — Application: PluginManager and LocalPathSource
- Add `core/python/agent_app/plugin_manager.py` implementing `PluginManager` and `LocalPathSource`.
- Wire `agent_app/config.py` and `application_future.py` to call into `PluginManager` to load plugins.
  - NEW: implement canonicalization helper `normalize_plugins` and the unified `load_plugins(canonical_items)` (expects canonical list only).
    Ensure multiple entries for the same plugin (same repo) are handled: cache install once; import multiple classes; maintain first-wins policy for duplicate ids while allowing distinct classes to load.
- Add unit tests for pure computation helpers (safe_id generation etc.).

Stage 3 — Application: GitInstallerSource (integration)
- Implement `GitInstallerSource` in `agent_app`.
- Implement caching and atomic install semantics.
- Implement metadata file writing (`plugin_metadata.json`).
- Implement `prefetch_all()` integration path (called during app startup before core init).
- NEW: implement module-only `entry` and multi-class loading (`entries` list / module discovery). If descriptor `agent_plugin.json` exists, use it to populate multiple classes when explicit entries are not provided.
- Add integration tests as described above; mark them `integration` and ensure CI configuration can run them when requested.

Stage 3.5 — E2E Integration: LocalPath + GitInstaller with permanent fixtures
- Permanent fixtures (two plugins in one directory):
  - Create a persistent test fixture directory under `core/python/tests/fixtures/dev_plugins/` that contains two plugins
    implemented as if they lived in their own repos but colocated for convenience:
    - `dev_plugins/file_reader_tool.py` — copy of the built-in file reader tool plugin (namespaced under `dev_plugins`).
    - `dev_plugins/file_writer_tool.py` — copy of the built-in file writer tool plugin (namespaced under `dev_plugins`).
  - Include `__init__.py` so they import as `dev_plugins.file_reader_tool.FileReaderTool` and `dev_plugins.file_writer_tool.FileWriterTool`.

- Config fixtures (on-disk, real files):
  - `core/python/tests/fixtures/configs/localpath_plugins.json` — application config using LocalPathSource, e.g.:
    - `plugin_cache_dir`: set to `${env:PLUGIN_CACHE_DIR}` (tests set env var to a temp dir).
    - `plugins`: flat list canonical entries using `path:${env:DEV_PLUGINS_DIR}::dev_plugins.file_reader_tool.FileReaderTool` and `.file_writer_tool.FileWriterTool`.
  - `core/python/tests/fixtures/configs/git_plugins.json` — application config using GitInstallerSource, e.g.:
    - `plugin_cache_dir`: `${env:PLUGIN_CACHE_DIR}`.
    - `plugins`: flat list canonical git entries with `${env:DEV_PLUGINS_GIT_DIR}` for the repo path and `entry` fields pointing
      to the two classes (two items referencing the same repo to exercise multi-class import and single install).

- Test harness behavior:
  - Tests read the config fixture, resolve placeholders via the app’s existing `resolve_placeholders` (env + file placeholders),
    set `DEV_PLUGINS_DIR` to the permanent fixture path, and `PLUGIN_CACHE_DIR` to a fresh temp dir.
  - For the git test, copy the `dev_plugins` fixture to a temp location, `git init && git add . && git commit -m init` to produce a
    local repository; set `DEV_PLUGINS_GIT_DIR` to that path.
  - Invoke the application (AgentApplication) with the resolved config to verify that plugins load and register correctly via
    LocalPathSource and GitInstallerSource, respectively.

- End-to-end scenario (with Ollama):
  - Base the scenario on an existing working test that uses qwen 0.6B with tools and reasoning enabled:
    - Reference: `core/python/tests/test_application_layer_integration.py`
      - `test_application_layer_ollama_file_reader_non_streaming`
      - `test_application_layer_ollama_file_reader_streaming`
    - These use `qwen3:0.6b` (MODEL env default), `OpenAIToolsExtension` + `OllamaThinkingExtension`, and exercise `FileReaderTool`.
  - Adapt the scenario to also use `FileWriterTool` from fixtures and verify a read-then-write flow (optional small delta to the base scenario).
  - Mark these tests with `@pytest.mark.ollama` (and optionally `@pytest.mark.integration`).
  - Skip when Ollama is unavailable (reuse the existing `ensure_model`/`MODEL_TOOLS` patterns) to keep CI stable.

- Assertions and validations:
  - Confirm both tools load from the same repo path (GitInstaller installs only once; two canonical entries import both classes).
  - Confirm tool schemas are surfaced and both tools can be executed.
  - Confirm end-to-end behavior: target file is created with expected contents.
  - Confirm metadata written for Git installs (`plugin_metadata.json` present, `entry` fields as expected).

- Notes:
  - Ensure sys.path core_first remains honored (LocalPathSource/GitInstallerSource append to sys.path, not insert at front).
  - Use canonical plugin entries in configs to match the new `load_plugins` API; tests are responsible for converting
    any raw placeholders to canonical entries via the application’s config resolution.

Stage 4 — Migration & cleanup
- Update examples and docs to show new plugin spec forms and `plugin_cache_dir` config.
- Update or remove tests that previously relied on `discover_and_register` to use PluginManager-produced classes.
- Add a migration note in CHANGELOG / README.

Stage 5 — Ops & extras (optional)
- CLI: `agent plugin fetch|list|purge` to prefetch/purge plugins.
- Wheel caching: add `pip wheel` to speed repeated installs and support offline installs.
- Optional Process/venv-based isolation loader (RPC) if you later need isolation.

Backwards compatibility & migration notes
- Existing dotted-path plugin specs remain supported unchanged.
- Add support for the new `git+...::entry` forms and dict form for richer workflows.
- When `discover_and_register` is removed from core, use the unified `load_plugins` path: supply the canonical list
  (the application should convert mapping/flat-list config to canonical first). The manager handles discovery and
  categorization (module-only entries allowed).

Open issues (recommendations applied)
- The manager will not attempt to read/resolve environment variables. The application must resolve placeholders and pass resolved parameter values (cache_dir and policy) into the manager API.
- Python build-time failures and binary wheels: per your choice we will try installs and surface errors. Document that compiled extensions must be built for the shipped runtime.
- Concurrency: recommend atomic moves and optional file locks for robust concurrent startup (not required in MVP).

Example application startup sketch (pseudo-code)

```python
from pathlib import Path
from agent_core.plugin.loader import DottedPathSource, get_plugin_id, validate_plugin_for_kind
from agent_app.plugin_manager import PluginManager

# App resolves env/file placeholders and loads JSON config first
resolved_config = resolve_placeholders(raw_config)
cache_dir = Path(resolved_config.get("plugin_cache_dir"))
policy = resolved_config.get("plugin_policy", {})

mgr = PluginManager(loaders=[DottedPathSource()], cache_dir=cache_dir, policy=policy)

# Install on startup (per policy) before core is created/initialized
if policy.get("install_on_startup", True):
    errors = mgr.prefetch_all()
    app._config_errors.extend(errors)

# Now load plugin classes and register them with core exactly as the current code does
plugins_by_kind, load_errors = mgr.load_plugins_config(resolved_config.get("plugins", {}))
app._config_errors.extend(load_errors)

for provider_cls in plugins_by_kind.get("providers", []):
    core.register_provider(provider_cls, extensions=plugins_by_kind.get("extensions", []))
```

Next steps
- If you confirm this plan I will implement Stage 1 (core interface module and unit tests), then Stage 2 (PluginManager and LocalPathSource). You asked earlier to avoid code edits until planning was done; this file completes the planning phase.

If you want any change to the plan (e.g., different config key names, an additional policy flag, or different sys.path handling) tell me now before I start implementing Stage 1.
