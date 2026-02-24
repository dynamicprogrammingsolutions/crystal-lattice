# JavaScript Tool Plugins (Node.js) — detailed investigation + implementation plan

## Implementation notes (landed)

This plan has been implemented.

Key pieces:

- Tool host protocol: `docs/reference/tool-host-protocol.md` (NDJSON; per-message `v` field, no handshake).
- Node host runner + SDK: `packages/tool-host-node/host.mjs`, `packages/tool-host-node/sdk.mjs`.
- Python proxy tool plugin: `core/python/agent_core/tool_hosts/node_tool_plugin.py`.
- Application plugin source (caching + install/build): `core/python/agent_app/plugin_sources/node_tool.py`.
- PluginManager integration: `core/python/agent_app/plugin_manager.py` (adds `NodeToolSource`).

Notable decisions / deltas vs the original plan:

- Default behavior is **install + build** (MVP ergonomics):
  - `node_install_deps` default `true`
  - `node_build` default `true`
  - `node_allow_install_scripts` default `true`
  - All are globally disable-able via `plugin_policy`.
- Package manager is inferred from the plugin repo (`package.json#packageManager` or lockfiles), with optional global override via `plugin_policy.node_package_manager`.
- Build uses the repo’s `package.json#scripts.build` (`<pm> run build`) by default; `plugin_policy.node_build_command` remains an optional global override.
- Tools can be exported as:
  - default export object,
  - named export object (selected via `agent.tools[].export`),
  - a class (auto-instantiated), or
  - a factory function (called to get the tool object).

Examples + tests:

- Example plugins: `plugins/js-echo-tool`, `plugins/js-multi-tools`, `plugins/js-fs-tools`, `plugins/js-single-file-tool`, `plugins/js-class-tool`.
- Core tests: `core/python/tests/test_node_tool_plugins.py`, `core/python/tests/test_application_layer_integration_node_tools_ollama.py`.
- App regression test: `application/python/tests/test_agent_terminal_app_server_ollama_js_fs_tools.py` using `application/python/agent_terminal_app/config_ollama_js_fs_tools.json`.

## Description

Enable **tool plugins** to be authored in **JavaScript/TypeScript** (executed by Node.js) while keeping the existing Python `agent_core` orchestration unchanged.

This repo already has:

1) A **core tool plugin protocol** (`ToolPlugin`) and wrappers/adapters.
2) A dedicated **application-level plugin loader/manager** (`agent_app.plugin_manager.PluginManager`) that resolves a flat `plugins` list from config.

The approach below adds a **language-neutral “tool host” protocol** and a Python `ToolPlugin` implementation that delegates tool calls to a Node subprocess.

---

## What exists today (key findings + code pointers)

### Tool plugin contract and streaming semantics

* `ToolPlugin` protocol: `core/python/agent_core/types.py`.
  * See lines **849–1026** (init, tags, schemas, execute, formatting, preview, streaming, display conversion).
  * `stream_tool(...) -> Iterator[dict]` is optional; tools can yield partial payloads and/or a final result dict.
  * `to_display_format(text, result, state)` is optional UI-only payload conversion.
  * Source: `core/python/agent_core/types.py` (use `nl -ba` to confirm exact ranges).

* Tool execution pipeline:
  * `AgentCore.get_tool_schemas`: `core/python/agent_core/core.py` lines **2255–2279**.
  * `AgentCore.iter_tool_messages`: lines **2281–2440**.
    * Chunks with a key `"part"` are forwarded as *partials*.
    * A dict containing `"success"` is treated as the **final result**.
    * After the final result, the core calls `format_tool_result`, then `to_display_format`, and attaches `metadata.display`.

Implication: a JS tool adapter must support:
* returning OpenAI-style tool schemas
* executing tools and producing a `{"success": ...}` result dict
* optionally producing `{"part": ...}` partial chunks
* formatting and display conversion hooks (or let Python provide defaults)

### Wrappers/adapters

* Tool wrapper (`ToolWrapper`): `core/python/agent_core/plugin/tool.py`.
  * Instantiates `plugin_class()` and wraps in `ToolDefaultsAdapter`.
  * Holds `self.state` but **core initializes tool state per request** and passes `state` around.

* Default adapters: `core/python/agent_core/plugin/adapters.py`.
  * `ToolDefaultsAdapter` provides default behavior for optional hooks.
  * Important for multilingual tools: the JS proxy class must be “ToolPlugin-like” (duck-typed) so it can be wrapped normally.

### Dedicated application-level plugin loader/manager (must be extended)

* `agent_app.plugin_manager.PluginManager`: `core/python/agent_app/plugin_manager.py`.
  * Default sources list (in order):
    1. `DottedClassSource` (no install)
    2. `LocalPathRepoSource` (pip install --target + agent_plugin.json)
    3. `GitRepoSource` (clone + pip install --target + agent_plugin.json)
  * References: `core/python/agent_app/plugin_manager.py` lines **24–40**.

* `AgentApplication` uses PluginManager to resolve a flat `plugins` list:
  * `core/python/agent_app/application_future.py` lines **96–168**.
  * After resolution, plugin classes are classified via duck-typing (`validate_plugin_for_kind`).

Implication: to load JS tools from config, we add a **new PluginSource** to the app-level plugin manager.

---

## Goal / non-goals

### Goal

Allow a plugin author to write a tool plugin in JS/TS and configure it in the app config so that:
* The tool schemas appear in `AgentCore.get_tool_schemas(config)`.
* Tool calls execute via Node and results/partials flow through `iter_tool_messages` exactly like Python tools.
* The solution integrates with the **existing application-level plugin loader** (so JS tools can be resolved from local path and git, cached, and policy-controlled).

### Non-goals (for first iteration)

* Cross-language providers/extensions/features (possible later with same pattern, but bigger surface).
* Strong sandboxing (containers/VMs) — we’ll provide policy hooks and safe defaults but assume plugins are trusted code.
* Perfect parity with Python “in-process” performance (subprocess overhead is acceptable initially).

---

## Proposed design (high level)

1) Define a **language-neutral Tool Host protocol** over **NDJSON** (newline-delimited JSON) on stdin/stdout.
2) Implement a **Node tool host runner** that loads a JS plugin module and serves Tool Host RPC requests.
3) Implement a Python `ToolPlugin` proxy (`NodeToolPlugin`) that:
   * spawns the Node host
   * calls `get_tool_schemas`, `execute_tool`, etc via RPC
   * maps streaming partials into the core’s `{ "part": ... }` convention
4) Extend the **application PluginManager** with a new source `NodeToolSource` so config can reference JS tool plugins.
5) Add an example JS tool plugin + integration tests.

---

## Detailed design

### 1) Tool Host protocol (NDJSON stdin/stdout)

**Transport**: a subprocess speaking NDJSON on stdin/stdout.

**Request envelope** (one JSON per line):

```json
{ "id": "uuid", "method": "execute_tool", "params": { ... } }
```

**Response envelope**:

```json
{ "id": "uuid", "ok": true, "result": { ... } }
{ "id": "uuid", "ok": false, "error": { "type": "...", "detail": "...", "stack": "..." } }
```

**Streaming events** (0..N before final response):

```json
{ "id": "uuid", "event": { "type": "part", "payload": { ... } } }
```

Mapping to core:
* For each streaming `event` with `type: "part"`, the Python adapter yields `{"part": <payload>}`.
* The final `execute_tool` result must contain a `success` key (mirrors Python tools).

**Protocol versioning**:

Include in an initial handshake or include per message:

```json
{ "id": "uuid", "method": "handshake", "params": { "protocolVersion": 1 } }
```

Minimum methods to support:

* `get_config_schema()` → `Dict`
* `get_ui_elements()` → `List[Dict]`
* `init(config)` → `state` (JSON-serializable)
* `get_tags(config, models)` → `List[str]` (optional)
* `required_tags()` → `List[str]` (optional)
* `get_tool_schemas(state)` → `List[Dict]`
* `execute_tool(tool_name, arguments, state)` → `{success: bool, ... , state?: any}`
* `format_tool_result(result, state)` → `str`
* `format_tool_call_preview(tool_name, arguments, state)` → `str`
* `to_display_format(text, result, state)` → `Dict`

Notes (important: align with existing plugin semantics):
* **There is no “internal persistent plugin state” contract.** Existing Python tools treat `state` as **per-request working state** and store config under `state["config"]` in `init`. Tool authors should not rely on data surviving beyond the current request/tool-loop.
  * Example: `ShellTool.init` returns `{ "config": config }` and later methods read `state["config"]`.
* **Therefore the Node protocol MUST round-trip state.** Since Node runs out-of-process, the Python proxy cannot rely on in-process mutation; it must:
  1. Send the current `state` to Node with each call.
  2. Receive an updated `state` back.
  3. Update the Python `state` dict **in-place** (clear + update) so subsequent core calls in the same request see the updated values.
* Practical requirement for v1: tool state must be **JSON-serializable**.

**Cancellation** (optional v1.1):
* Add `cancel(id)` requests; Python wrapper can terminate the subprocess per call as a coarse cancel.

### 2) Node tool host runner + JS SDK

Add a small Node package (suggested location):

* `packages/tool-host-node/` (or `core/node/tool_host/`)

Responsibilities:
* Read stdin line by line (NDJSON)
* Validate envelope, dispatch `method`
* Catch exceptions and return structured errors (include stack in `error.stack`)
* Support streaming events from the plugin (either via async iterator or callback)

**JS plugin author experience**

Provide a tiny SDK that plugin authors use:

```ts
export const plugin = {
  name: "my_js_tool",
  version: "0.1.0",
  getToolSchemas(state) { ... },
  async executeTool(toolName, args, state, emit) {
    emit({ type: "part", payload: { message: "working..." } })
    return { success: true, result: ... }
  },
}
```

Define a supported module shape:
* Single-plugin entrypoint:
  * `export default plugin` (preferred)
  * (optional) `module.exports = plugin` for CJS
* Multi-plugin entrypoint (preferred mechanism per user feedback):
  * Named exports: `export const toolA = { ... }`, `export const toolB = { ... }`
  * The resolver selects which named export to use via an `export` field in the descriptor.

### 3) Python: `NodeToolPlugin` (ToolPlugin proxy)

Add in `core/python/agent_core/` (suggested):

* `core/python/agent_core/tool_hosts/node_tool_plugin.py`
  * Implements the `ToolPlugin` protocol.
  * Has class attributes:
    * `name`, `version`
    * `node_entry` (path to plugin JS file)
    * `node_workdir` (plugin root)
    * optional `node_args`, `env`

**Lifecycle model (recommended v1): ephemeral subprocess per RPC call**

Because tool/plugin state is explicitly passed around (and not preserved by the protocol), and because `ToolPlugin` currently has no explicit “close/shutdown” hook, the simplest robust model is:

* For each call to `get_tool_schemas`, `execute_tool`, etc:
  * Spawn `node tool-host-runner.js <plugin_entry>`
  * Send one request
  * Read streaming events + final response
  * Exit

Pros:
* No resource leaks (no need for new core hooks)
* Easy cancellation (kill process)

Cons:
* Higher overhead than a persistent host

**State handling (must match how existing Python tools work)**

In Python today, tools mutate the `state: Dict[str, Any]` they receive, and that state only matters for the current request/tool-loop execution. For Node tools we must simulate that mutation by round-tripping state through RPC.

Plan:
* `init(config)` (Python) → RPC `init(config)` (Node) → returns a JSON object `state`.
  * Convention: Node tools should store config under `state.config`.
* For every other method that receives `state` (`get_tool_schemas`, `execute_tool`, `format_tool_result`, etc):
  * Python sends current `state`.
  * Node returns `{ result, state }`.
  * Python updates the caller-provided state dict in-place (`state.clear(); state.update(new_state)`) and then returns the method result.

This ensures that within a single `AgentCore.iter_tool_messages(...)` run (which initializes a tool once and then executes potentially multiple tool calls), state updates are visible to subsequent tool calls.

Implement these methods in Python proxy (all must round-trip state):
* `get_config_schema`, `get_ui_elements` (call Node or default empty)
* `init`
* `get_tags`, `required_tags`
* `get_tool_schemas`
* `execute_tool`
* `stream_tool`: should yield partials + final result dict.
  * The final response should include updated state; apply it at end.
  * For non-streaming tools, Python can call `execute_tool` and yield the final dict (mirrors `ToolDefaultsAdapter`).
* `format_tool_result`
* `format_tool_call_preview`
* `to_display_format`

**Timeouts and error mapping**

* Add config/policy driven timeouts:
  * `plugin_policy.node_timeout_seconds` (default e.g. 60)
* On timeout: kill process; return `{"success": false, "error": "timeout"}`.
* On protocol error: return `{"success": false, "error": "protocol violation"}` + log detail.

### 4) Application-level plugin loader: `NodeToolSource` (installation + caching)

Add a new source in `core/python/agent_app/plugin_sources/`:

* `node_tool.py` implementing `PluginSource` (`supports`, `resolve`).

Then update `PluginManager` default source order:

* `NodeToolSource()` should be **before** `LocalPathRepoSource`/`GitRepoSource` so it can claim JS specs.

#### Relationship to existing plugin installation (local dir + git repo)

Today, `PluginManager` supports three source types:
* `DottedClassSource`: import a Python class directly (no install)
* `LocalPathRepoSource`: copy repo → `pip install --target <cache>` → import Python classes listed in `agent_plugin.json`
* `GitRepoSource`: clone repo → `pip install --target <cache>` → import Python classes listed in `agent_plugin.json`

This works for the existing plugin repos under `./plugins/*` (they are Python packages with `agent_plugin.json`).

For JavaScript/TypeScript tool plugins, **we cannot use pip install**. The plan must add a parallel install/caching mechanism that is consistent with the current caching+policy model:

* For `path` JS plugins:
  * fingerprint the project (git-scoped when possible, otherwise file hash) similarly to `LocalPathRepoSource`
  * copy the project into the cache dir under something like:
    * `<plugin_cache_dir>/node/<safe_id>@<revision>/...`
  * (optionally) run Node dependency install + build in that cached copy

* For `git` JS plugins:
  * enforce `plugin_policy.allow_remote` and `allowed_git_hosts` similarly to `GitRepoSource`
  * clone to a temp dir, check out ref, compute commit hash
  * copy to cache dir:
    * `<plugin_cache_dir>/node/<safe_id>@<commit>/...`
  * (optionally) run Node dependency install + build in that cached copy

This keeps the same “pinned revision → immutable cache install dir” property as the Python plugin installer.

#### Proposed config spec formats

Because current `plugins` list entries are either dotted strings or dicts with `path`/`git`, add a new dict form:

**Local path JS tool**

```json
{
  "node_tool": {
    "path": "./path/to/js-tool-repo",
    "entry": "dist/index.js",
    "name": "my_js_tool",
    "version": "0.1.0"
  }
}
```

**Git JS tool**

```json
{
  "node_tool": {
    "git": "https://github.com/acme/my-js-tool.git",
    "ref": "v0.1.0",
    "subdirectory": "optional/subdir",
    "entry": "dist/index.js",
    "name": "my_js_tool"
  }
}
```

Rationale:
* Keep existing Python plugin specs unchanged.
* Avoid overloading `path:`/`git+` string prefixes, which currently imply pip-installable Python.

#### JS/TS plugin descriptor via `package.json` (preferred)

Python plugins use `agent_plugin.json` with a list of concrete dotted class paths.

For JS/TS plugins, prefer storing descriptor info in `package.json` under a dedicated key.

Example `package.json` (one tool plugin module exporting one “tool plugin” object):

```json
{
  "name": "@acme/my-js-tool",
  "version": "0.1.0",
  "main": "dist/index.js",
  "agent": {
    "kinds": ["tools"],
    "tools": [
      {
        "id": "my_js_tool",
        "entry": "dist/index.js"
      }
    ]
  }
}
```

Notes:
* `id` should map to the Python-visible plugin id (`ToolPlugin.name`).
* `entry` is a path relative to the repo root/subdirectory.
* Support multiple tool plugins per package by allowing multiple entries.
* If config provides `name/version/entry`, it overrides `package.json`.

If you want the simplest possible descriptor, you can also accept:
* `agent.tools: ["dist/index.js"]` and derive `id` from `name`.

##### Multiple plugins from one directory (multi-class equivalent) using named exports (preferred)

To define more than one plugin “class” (plugin id) in a single JS/TS package directory:

* Put multiple entries in `package.json#agent.tools[]`.
* Each entry can optionally specify which **named export** to bind to.

Example `package.json`:

```json
{
  "name": "@acme/my-js-tools",
  "version": "0.2.0",
  "agent": {
    "kinds": ["tools"],
    "tools": [
      { "id": "echo", "entry": "dist/index.js", "export": "echoTool" },
      { "id": "reverse", "entry": "dist/index.js", "export": "reverseTool" }
    ]
  }
}
```

And `dist/index.js`:

```js
export const echoTool = {
  name: "echo",
  version: "0.2.0",
  getToolSchemas(state) { /* ... */ },
  executeTool(toolName, args, state, emit) { /* ... */ }
};

export const reverseTool = {
  name: "reverse",
  version: "0.2.0",
  getToolSchemas(state) { /* ... */ },
  executeTool(toolName, args, state, emit) { /* ... */ }
};
```

Resolver behavior:
* If `export` is present, the Node host runner loads `entry` and selects `module[export]`.
* If `export` is omitted, the Node host runner uses `default` export.

#### Install/caching strategy for JS (npm/pnpm/yarn) + security policy

`LocalPathRepoSource`/`GitRepoSource` currently rely on pip installing into `plugin_cache_dir/<id>@<revision>`.

For JS tools, implement analogous caching:
* Cache directory: `plugin_cache_dir/node/<safe_id>@<revision>/...`
* Copy (or clone) source into cache (like existing sources do with temp dirs).
* Install deps/build (MVP defaults are on; controlled by policy):
  * defaults:
    * `node_install_deps: true`
    * `node_build: true`
    * `node_allow_install_scripts: true`
  * disable via policy:
    * `plugin_policy.node_install_deps: false`
    * `plugin_policy.node_build: false`
    * `plugin_policy.node_allow_install_scripts: false`
  * package manager selection:
    * override: `plugin_policy.node_package_manager: "npm" | "pnpm" | "yarn"`
    * otherwise infer from `package.json#packageManager` (preferred) or lockfiles (fallback)
  * install command:
    * `<pm> install` (uses `corepack` automatically for `pnpm`/`yarn` when available)
  * build command:
    * default: `<pm> run build` when `package.json#scripts.build` exists
    * override: `plugin_policy.node_build_command` (global escape hatch)

Security defaults:
* Mirror current stance: remote Git disabled unless `plugin_policy.allow_remote = true`.
* Node dependency installs run with scripts enabled by default (MVP assumes plugins are trusted); disable scripts globally via `plugin_policy.node_allow_install_scripts=false`.

#### Resolving returns a Python class

`PluginManager.resolve_all(...)` must return **Python classes**.

So `NodeToolSource.resolve(...)` should create a dynamic proxy class:

```py
NodeToolProxy = type(
  "MyJsToolProxy",
  (NodeToolPlugin,),
  {
    "name": "my_js_tool",
    "version": "0.1.0",
    "node_entry": "/abs/path/to/cache/dist/index.js",
    "node_workdir": "/abs/path/to/cache",
  },
)
```

This class:
* Has a no-arg constructor (so existing wrappers work)
* Duck-types as a tool plugin (`get_tool_schemas` + `execute_tool`) so `AgentApplication._classify_plugin_class` will classify it as `"tools"`.

### 4.1) TypeScript support

TypeScript can be supported in two modes; recommend (A) for production-like usage.

**(A) Precompiled TS (recommended)**
* The plugin repo ships compiled JS (e.g. `dist/`) and `package.json` points `main`/`agent.tools[].entry` at a JS file.
* The plugin manager does not need a TS runtime.
* Optional: plugin manager may still run `node_install_deps` to install runtime deps.

**(B) Build-in-cache TS (optional; controlled by policy)**
* Plugin repo contains TS source and a `build` script.
* When `plugin_policy.node_build=true`, after copying/cloning into the cache dir:
  1. run deps install
  2. run build command
  3. resolve `entry` to the build output (`dist/index.js`), or use `package.json` `main` after build.

**Not recommended for v1: runtime transpilation (ts-node)**
* Possible, but adds complexity and runtime deps; treat as dev-only option.

### 5) Example JS tool plugin

Add example fixtures covering three cases:

1) **Single-plugin JS tool directory (no `export` field)**
   * Path: `plugins/js-echo-tool/`
   * `package.json` contains `agent.tools: [{ id, entry }]` without `export`
   * `dist/index.js` uses `export default { ... }`

2) **Multi-plugin JS tool directory (uses `export` field with named exports)**
   * Path: `plugins/js-multi-tools/`
   * `package.json` contains two entries under `agent.tools[]`, each with `export`
   * Single JS file `dist/index.js` exports `export const echoTool = {...}` and `export const reverseTool = {...}`

3) **Single-file JS tool (testing/local equivalent of `core/python/plugins/*.py`)**
   * Provide a minimal example that is a single `.js` file with `export default` tool plugin.
   * Intended for quick dev/testing without packaging.
   * Config spec should support something like:
     * `{ "node_tool": { "file": "./tmp/my_tool.js", "name": "my_tool" } }`
       - `NodeToolSource` copies that file into the cache dir and uses it as `entry`.
       - Alternatively, treat it as `path` with a synthesized temporary package directory.

For each tool:
* Expose one tool function (e.g. `echo` / `reverse`) with a strict-ish JSON schema.
* Implement streaming by emitting 1–2 partials before returning the final `{ success: true, result: ... }`.

### 6) Tests

Add tests similar to existing application-layer plugin tests:

1) **PluginManager resolution test**
   * Create a temp dir with a minimal JS plugin + manifest.
   * Use `PluginManager(cache_dir=tmp_path, policy={"base_dir": ...})`.
   * Resolve with `{"node_tool": {"path": <tmp>, ...}}` and assert no errors.

2) **AgentCore integration test**
   * Build config JSON containing:
     * dummy provider (`tests.dummy_provider.DummyProvider`)
     * JS tool spec
   * Create `AgentApplication` and verify `list_plugins()` includes the JS tool plugin id.
   * Call `core.get_tool_schemas(config)` and verify `echo` schema present.

3) **Tool execution test**
   * Simulate a tool call dict (`{"id": "1", "function": {"name": "echo", "arguments": {"value": "hi"}}}`)
   * Run `AgentCore.iter_tool_messages` and assert:
     * partial chunks are yielded (contain `part`)
     * final tool message contains formatted content and `metadata.display`.

Test environment note:
* If CI may not have Node available, tests should either:
  * skip when `node` executable missing (`shutil.which("node") is None`), or
  * vendor a minimal node runtime (unlikely).

### 7) Documentation

Update:
* `docs/plugins/application-config.md`: add `node_tool` spec examples + policy knobs.
* `docs/plugins/development.md`: add “JavaScript tool plugins” section.
* Add a protocol reference doc (e.g. `docs/reference/tool-host-protocol.md`).

---

## Implementation steps (suggested order)

1) **Protocol spec doc**
   * Write the NDJSON RPC contract, methods, event shapes, error schema.

2) **Node host package**
   * Add `packages/tool-host-node/`:
     * `host.js/ts` (stdin/out runner)
     * `sdk.ts` (types + helper wrapper)
     * small smoke test script.

3) **Python Node RPC client + `NodeToolPlugin`**
   * Add `agent_core/tool_hosts/node_tool_plugin.py`:
     * spawn node subprocess
     * send request
     * parse events
     * enforce timeouts

4) **Application plugin loader integration**
   * Add `agent_app/plugin_sources/node_tool.py`.
   * Extend `agent_app/plugin_manager.PluginManager` to include `NodeToolSource`.
   * Implement caching + optional npm install.

5) **Example JS tool plugin**
   * Add a minimal repo under `plugins/js-echo-tool`.

6) **Tests**
   * Add plugin manager resolution test.
   * Add AgentCore + AgentApplication integration tests.

7) **Docs**
   * Update config docs and development docs.

---

## Open questions / decisions (resolved)

1) **Do we accept JSON-only tool state for JS plugins in v1?**
   * Yes. State is round-tripped as JSON via the tool-host protocol.

2) **Where should the Node host live?**
   * `packages/tool-host-node`.

3) **Which package manager and install behavior?**
   * Defaults are install + build:
     * `node_install_deps=true`, `node_build=true`, `node_allow_install_scripts=true`
     * package manager inferred from `package.json#packageManager` or lockfiles (override via `plugin_policy.node_package_manager`)
     * install is `<pm> install`; build is `<pm> run build` when `scripts.build` exists

4) **Manifest naming**
   * Node tools use `package.json#agent.tools` (no separate manifest file).

---

## Future enhancements

* Persistent Node host per request (or per session) for performance, which likely requires:
  * a tool plugin cleanup hook (e.g. `close(state)`), and
  * `AgentCore` calling it after tool loop.
* Generalize to “external tool hosts” for other languages (Rust, Go, etc) by keeping the protocol stable.
* Sandboxing: run tool hosts in containers with filesystem/network policies.
