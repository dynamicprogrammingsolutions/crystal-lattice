# Application-Scoped Model Discovery Cache

Implement a shared model-discovery cache so fresh `AgentCore` instances created by `AgentApplication` do not repeatedly call provider `get_models()` for the same effective provider/config/plugin set.

## Requirements checklist

- [x] Add an application-scoped model discovery cache that can be shared across fresh `AgentCore` instances.
- [x] Keep standalone `AgentCore()` usage working without requiring an application object.
- [x] Replace cache keys based on `id(provider)` with stable provider/plugin/config signatures suitable for cross-core reuse.
- [x] Avoid caching transient empty/failure results for too long.
- [x] Ensure concurrent callers for the same cache key do not all perform live model discovery.
- [x] Keep dependency/tag/prepared-tool caches core-local unless there is a separate reason to share them.
- [x] Add focused regression tests proving repeated app operations reuse cached model discovery across fresh cores.

## Background

Creating a new frontend session can hang on slow internet because backend session creation runs model discovery synchronously. The observed interrupted stack trace showed:

- `POST /sessions` or terminal `/new` reaches `AgentApplication.create_session_ephemeral(...)`.
- `run_session_lifecycle("session_create", ...)` calls `AgentCore.execute_lifecycle_actions(...)`.
- `AgentCore._build_request_context(...)` resolves tool interop and plugins.
- `_resolve_plugins_for_config(...)` calls `_get_models_for_config(...)`.
- `provider.get_models(config)` enters the OpenAI Responses ChatGPT discovery path.
- `openai_responses_codex_models._fetch_json(...)` blocks on `response.read()` while fetching from GitHub/raw GitHub.

The exact blocking line is:

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_codex_models.py:76`
  - `payload = response.read().decode(charset, errors="replace")`

This is external network I/O, but the product issue is that model discovery is performed on the critical path for local session operations and repeatedly re-run across fresh cores.

## Current Cache Problem

`AgentCore` currently owns model discovery caching locally:

- `core/python/agent_core/core.py:584`
  - `AgentCore.__init__()` initializes `self._models_cache = {}`.
- `core/python/agent_core/core.py:1491`
  - `_get_models_for_config(...)` returns cached or freshly computed model descriptors.
- `core/python/agent_core/core.py:1492`
  - The current key starts with `id(provider)`, which is only stable for one provider wrapper instance.

`AgentApplication` often creates fresh cores:

- `core/python/agent_app/application_future.py:296`
  - Comment says the core factory is stored so per-session cores can be created without sharing state across requests.
- `core/python/agent_app/application_future.py:847`
  - `_build_core_with_enabled_ids(...)` calls `self._core_factory()`.
- `core/python/agent_app/application_future.py:2316`
  - `load_session(...)` explicitly documents that a fresh `AgentCore` is constructed for each call.
- `core/python/agent_app/application_future.py:2528`
  - `create_session_ephemeral(...)` builds a fresh core for a new session.

Therefore, `_models_cache` usually survives only within one core object and does not help enough for frontend operations such as create, load/send, delete, modify, or fork.

## Existing App-Scoped Runtime Pattern

There is already an app-owned generic runtime store:

- `core/python/agent_app/application_future.py:167`
  - `RuntimeStore` is a generic application-owned store for opaque long-lived runtime objects.
- `core/python/agent_app/application_future.py:486`
  - `AgentApplication` creates `self._runtime_store = RuntimeStore()`.
- `core/python/agent_app/app_context.py:21`
  - `ApplicationContext` exposes `runtime_store` and `tool_runtime`.
- `plugins/codex-tools/src/codex_tools/mcp_tool.py:555`
  - MCP tools retrieve `runtime_store`/`tool_runtime` from context.
- `plugins/codex-tools/src/codex_tools/mcp_tool.py:578`
  - MCP uses `store.get_or_create(...)` to create an app-scoped `MCPRegistry`.

This pattern can inform the model-cache work, but model discovery is core-owned behavior. Prefer injecting an explicit cache dependency into `AgentCore` rather than having core fish a cache out of request context.

## Recommended Implementation Direction

Add a small app-shareable model discovery cache object and pass it into every `AgentCore` created by `AgentApplication`.

Recommended shape:

```python
class AgentCore:
    def __init__(self, model_cache: ModelDiscoveryCache | None = None):
        self._model_cache = model_cache or InMemoryModelDiscoveryCache()
```

`AgentApplication` should create one shared model cache during initialization and wrap or replace the core factory so every fresh core receives it.

The cache may be stored in `RuntimeStore` under a reserved key such as `agent_core.model_discovery_cache`, but `AgentCore` should receive the cache explicitly. This keeps model discovery deterministic for core code paths where request context is unavailable.

## Cache Key Requirements

Do not reuse the current key unchanged. `id(provider)` is not valid for app-scoped caching because provider wrappers are rebuilt per core.

Use a stable key that includes at least:

- Provider plugin identity: module, qualname/name, version.
- Active provider extension identities: module, qualname/name, version, order if order affects results.
- Active feature identities: module, qualname/name, version, order if order affects results, because features can transform model descriptors.
- Normalized config, using the existing `_normalize_config(...)` behavior or a shared equivalent.
- Cache schema/version marker so future key-shape changes invalidate cleanly.

Avoid including tool wrappers unless a code read shows tool plugins can alter model descriptors directly. At the time of investigation, `_get_models_for_config(...)` calls provider, provider extensions, and features.

## TTL / Failure Handling Requirements

Once model results are app-scoped, transient bad results must not poison the running app.

Recommended policy:

- Non-empty successful model lists: longer TTL, for example 5-30 minutes.
- Empty lists: short TTL, for example 15-60 seconds.
- Exceptions: do not cache exceptions unless there is a deliberate short negative-cache policy.
- Optional explicit invalidation/clear method for app shutdown or future config/plugin reload flows.

The OpenAI Responses provider currently catches discovery failures and returns `[]`, so the shared cache must treat empty model lists carefully.

## Concurrency Requirements

Implement single-flight behavior per cache key so concurrent requests for the same provider/config do not all call live model discovery.

The app/server can process simultaneous frontend requests. Without single-flight, an app-scoped cache will still allow duplicate in-flight GitHub/OpenAI discovery calls on a cold key.

## Affected User Flows To Verify

Regression risk and performance impact span:

- `POST /sessions` new session creation.
- Terminal `/new`, including `persist=False` ephemeral session creation.
- `PATCH /sessions/{id}/messages/{index}` modify message.
- `DELETE /sessions/{id}/messages` delete message.
- `POST /sessions/{id}/fork` fork session.
- Normal send/request preparation paths, especially paths that call `load_session(...)`.

## Suggested Test Plan

Add core/application tests with a fake provider whose `get_models(...)` increments a counter and returns a fixed model list. The tests should prove:

1. Two fresh `AgentCore` instances with the same shared cache and same provider/config call provider `get_models(...)` once total.
2. Two fresh `AgentCore` instances without an injected shared cache preserve existing standalone behavior and do not share state unexpectedly.
3. Different normalized configs produce separate cache entries.
4. Different provider/plugin signatures produce separate cache entries.
5. Empty model lists use a short TTL or otherwise become eligible for refresh sooner than successful non-empty results.
6. Concurrent same-key discovery performs only one underlying provider call.
7. `AgentApplication.create_session(...)` followed by another operation that builds a fresh core does not re-run provider `get_models(...)` for the same config.
8. Message delete/modify/fork paths do not re-run model discovery when a shared cache entry already exists.

Recommended test locations:

- Core cache unit tests: `core/python/tests`, likely a new focused test file or adjacent to existing core cache/plugin resolution tests.
- Application integration/regression tests: `core/python/tests` for `AgentApplication` behavior, using local fake plugins/fixtures under `core/python/tests/fixtures` if needed.
- HTTP route behavior can be covered in `application/python/tests` if the application-layer regression tests do not exercise the route-level fresh-core sequence enough.

Suggested commands:

```bash
pytest core/python/tests -q
pytest application/python/tests -q
```

For a narrower first pass, run the new/changed test files directly, then the broader suites above if time permits.

## Notes / Non-Goals

- This task should not move dependency cache, tag cache, or prepared-tool caches to app scope unless investigation shows they have the same repeated-network problem. They are more tightly tied to wrapper/runtime state.
- This task does not need to eliminate the first cold model discovery call. A provider-side follow-up could use the checked-in Codex model snapshot immediately and refresh live Codex models in the background, but that is separate from fixing repeated `get_models()` calls across fresh cores.
- Preserve current public `AgentCore()` construction ergonomics.

## Execution plan

Added during completion after user approval.

1. Add a typed synchronous model discovery cache abstraction in `agent_core` with TTL policy and per-key single-flight behavior.
2. Inject the cache into `AgentCore.__init__`, while preserving standalone `AgentCore()` usage by creating a private cache when no cache is supplied.
3. Replace `_models_cache` with the injected cache and change cache keys from provider wrapper identity to stable provider/extension/feature/config signatures.
4. Create one shared cache in `AgentApplication` and ensure every fresh default `AgentCore` created by the application receives it.
5. Add focused tests for shared-cache reuse across fresh cores, standalone isolation, config/signature separation, short empty-result TTL, and concurrent single-flight behavior.
6. Add application-level regression coverage showing fresh cores created by `AgentApplication` reuse model discovery.
7. Run targeted tests first, then broaden to relevant core/application test suites as time permits.

## Completion Notes

Added during completion.

Implemented an application-scoped model discovery cache:

- Added `core/python/agent_core/model_cache.py` with `ModelDiscoveryCache`, TTL-aware positive/empty-result caching, exception non-caching, and per-key single-flight behavior.
- Updated `AgentCore.__init__` to accept `model_cache: ModelDiscoveryCache | None`, preserving standalone `AgentCore()` behavior with a private cache.
- Replaced the old per-core `_models_cache` with the injected cache.
- Replaced `id(provider)` cache keys with stable provider/extension/feature/config signatures plus a cache key schema version.
- Left dependency, tag, and prepared-tool caches core-local.
- Updated `AgentApplication` to create one shared `ModelDiscoveryCache` and pass it into default/factory-compatible fresh cores.
- Stored the shared cache in `RuntimeStore` under `agent_core.model_discovery_cache` for app-scoped visibility while still injecting it explicitly into core.
- Added focused core tests in `core/python/tests/test_core_models_caching.py`.
- Added an application regression test in `core/python/tests/test_application_model_discovery_cache.py`.

Verification:

- Passed: `pytest core/python/tests/test_core_models_caching.py -q`
- Passed: `pytest core/python/tests/test_application_model_discovery_cache.py -q`
- Passed: `ruff check core/python/agent_core/core.py core/python/agent_core/model_cache.py core/python/agent_core/__init__.py core/python/agent_app/application_future.py core/python/tests/test_core_models_caching.py core/python/tests/test_application_model_discovery_cache.py`
- Passed: `pytest core/python/tests/test_plugin_dependency_tags.py core/python/tests/test_application_session_lifecycles.py -q`
- Full core suite attempted: `pytest core/python/tests -q`
  - Result: 375 passed, 5 failed, 26 deselected, 1 xfailed.
  - The 5 failures appeared unrelated to this model-cache change:
    - `test_application_layer_tools.py` has two `ToolLoopRunner.__init__()` signature mismatches for missing `app_context` and `base_config`.
    - `test_core.py::test_modify_message_shared_indices_cardinality_change_removes_first` has a monkeypatched helper that does not accept the existing `context` keyword.
    - `test_default_system_instructions_docs.py::test_portable_default_config_is_self_contained` fails on default config text expectations.
    - `test_node_tool_plugins.py::test_node_tool_multiple_exports_resolve_and_execute` fails because the `reverse` node tool call is not handled.
- `pyright` on touched modules was attempted and reported existing broad module errors in `application_future.py` and `core.py`; no errors were reported for the new `model_cache.py`.