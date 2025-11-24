# Refactor Plan: Make Plugin Protocols Instance-Based and Align Wrappers

Goal
- Convert all plugin protocol methods in `core/python/agent_core/types.py` from `@staticmethod` to instance methods, one plugin type at a time, updating all usages and implementations.
- After the plugins are migrated, align wrapper protocol types to be fully compatible with the plugin types so wrappers can be removed in a follow-up step.

Ground rules
- For plugin protocols: keep method parameters identical aside from adding `self`; retain existing `state`, `config`, etc.
- For wrappers/adapters: align method names and signatures exactly to the plugin protocols (including renames like `initialize` -> `init` and adding explicit `state` parameters). Update AgentCore call sites in the same slice to keep tests green.
- Migrate in safe, testable slices: one plugin type per commit where possible; keep tests green after each slice.
- Avoid unrelated changes; update docs/tests/examples alongside code.

0) Baseline
- Run: `pytest core/python/tests -q` and `pytest core/python/examples/tests -qs` to ensure green baseline.
- Run: `ruff check core/python/agent_core tests examples` and `pyright`.

1) Prepare code search and inventory
- Use ripgrep to inventory call sites and implementations for each protocol method.
- Focus files likely impacted:
  - Protocols: `core/python/agent_core/types.py`
  - Wrappers/adapters: `core/python/agent_core/plugin/provider.py`, `core/python/agent_core/plugin/extension.py`, `core/python/agent_core/plugin/feature.py`, `core/python/agent_core/plugin/tool.py`
  - Provider implementations: `core/python/agent_core/providers/openai_compatible.py`, `core/python/plugins/openai_provider.py`
  - Dummy plugins used by tests: `core/python/tests/dummy_provider.py`, `core/python/tests/dummy_extension.py`, `core/python/tests/dummy_feature.py`, `core/python/tests/dummy_tool.py`
  - Orchestrator: `core/python/agent_core/core.py`

2) Migrate BasePlugin (shared methods: config/ui/update_state)
- Change `BasePlugin` in `core/python/agent_core/types.py` to instance methods:
  - Remove `@staticmethod` from `get_config_schema`, `get_ui_elements`, `update_state`.
- Update wrappers to call instance methods for these shared operations:
  - Provider: switch `ProviderWrapper` to instantiate plugin class, e.g., `self.plugin = plugin_class()`; change `get_config_schema`, `get_ui_elements`, `update_state` to call `self.plugin.<method>(...)`.
  - Feature/Extension/Tool wrappers: same pattern for shared methods.
- Update dummy plugins to define these as instance methods; keep signatures otherwise identical.
- Run tests and linters.

3) Migrate ProviderPlugin
- Change `ProviderPlugin` methods in `core/python/agent_core/types.py` to instance methods (remove `@staticmethod`).
- Update implementations:
  - `core/python/agent_core/providers/openai_compatible.py`
  - `core/python/plugins/openai_provider.py`
  - `core/python/tests/dummy_provider.py`
- Update wrapper `core/python/agent_core/plugin/provider.py`:
  - Instantiate the plugin class once in `__init__` and hold `self.plugin`.
  - Replace all `self.plugin_class.<method>(...)` calls with `self.plugin.<method>(...)`.
  - Keep state handling unchanged (continue passing `state` explicitly).
- Verify `AgentCore.register_provider` path still works (wrapper constructs the instance).
- Run tests and fix call sites if any direct static usage was present.

4) Migrate ProviderExtensionPlugin
- Change `ProviderExtensionPlugin` methods in `core/python/agent_core/types.py` to instance methods.
- Update `core/python/tests/dummy_extension.py` to instance methods.
- Update wrapper `core/python/agent_core/plugin/extension.py` to instantiate once and call `self.plugin.<method>(...)` for all methods.
- Run tests.

5) Migrate FeaturePlugin
- Change `FeaturePlugin` methods in `core/python/agent_core/types.py` to instance methods.
- Update `core/python/tests/dummy_feature.py` to instance methods.
- Update wrapper `core/python/agent_core/plugin/feature.py` to instantiate and call instance methods.
- Run tests.

6) Migrate ToolPlugin
- Change `ToolPlugin` methods in `core/python/agent_core/types.py` to instance methods.
- Update `core/python/tests/dummy_tool.py` to instance methods.
- Update wrapper `core/python/agent_core/plugin/tool.py` to instantiate and call instance methods for all operations (`init`, `get_tool_schemas`, `execute_tool`, `format_tool_result`, config/ui, `update_state`).
- Ensure `AgentCore.get_tool_schemas` path remains correct.
- Run tests.

7) Update duck-typed discovery
- `core/python/agent_core/core.py` uses `hasattr(obj, "stream_api")`/`"call_api"` to classify providers. Instance migration keeps attributes on the class, so discovery logic can remain unchanged. Verify by running example discovery tests.

8) Align Wrappers/Adapters to Plugin Signatures
- Update wrapper protocols and adapters to exactly match plugin protocol method names and signatures while preserving current wrapper-managed state behavior.
- Provider wrapper/adapters: rename and add explicit state parameters to match `ProviderPlugin`.
  - `initialize(config)` -> `init(config)` -> `Dict[str, Any]` (return initial state)
  - `update_state(updates)` -> `update_state(state, updates)` -> `Dict[str, Any]`
  - `to_native_messages(messages)` -> `to_native_messages(messages, state)` -> `List[Dict]`
  - `initialize_request(native_messages)` -> `initialize_request(native_messages, state)` -> `Dict[str, Any]`
  - `call_api(native_messages)` -> `call_api(native_messages, state)` -> `Tuple[..., Dict]`
  - `stream_api(native_messages)` -> `stream_api(native_messages, state)` -> `Iterator[...]`
  - `process_chunk(native_chunk, native_messages)` -> `process_chunk(native_chunk, native_messages, state)` -> `Tuple[..., Dict]`
  - `finalize(native_messages)` -> `finalize(native_messages, state)` -> `Tuple[..., Dict]`
  - Expose `from_native_messages(native_messages, state)` and `to_display_format(message, state)` to match `ProviderPlugin` (no-op or `NotImplementedError` if not used yet).
  - Keep capability detection consistent: plugin keeps `@staticmethod detect_capabilities(config) -> List[str]`; wrapper/adapter provides an instance `detect_capabilities(config)` passthrough.
- Tool wrapper/adapters: rename and add explicit state parameters to match `ToolPlugin`.
  - `initialize(config)` -> `init(config)` -> `Dict[str, Any]`
  - `update_state(updates)` -> `update_state(state, updates)` -> `Dict[str, Any]`
  - `get_tool_schemas()` -> `get_tool_schemas(state)` -> `List[Dict]`
  - `execute_tool(tool_name, arguments)` -> `execute_tool(tool_name, arguments, state)` -> `Dict`
  - `format_tool_result(result)` -> `format_tool_result(result, state)` -> `str`
- Extension and Feature wrappers: already aligned; verify wrappers implement `ProviderExtensionPlugin` and `FeaturePlugin` directly.
- Adapters: ensure `ProviderAdapter` and `ToolAdapter` pass through and return state per the new signatures.
- AgentCore call sites: update to the new signatures and thread state explicitly.
  - Replace `_provider.initialize(config)` with `state = _provider.init(config)`.
  - Replace `_provider.update_state(ui_state)` with `state = _provider.update_state(state, ui_state)`.
  - Pass `state` into `to_native_messages`, `initialize_request`, `call_api`/`stream_api`/`process_chunk`/`finalize`, capturing and threading returned state.
- Wrapper-only helpers remain wrapper-specific orchestration utilities and can coexist with plugin parity:
  - `get_state`/`set_state`/`reset_state`, `apply_extension_transforms`, extension UI/config aggregation.
- Tests/types: adjust affected tests and type hints; keep observable behavior unchanged.
- Run full test suite and type checks.

9) Documentation and examples
- Update API docs and references where they mention "static methods" for plugins:
  - `docs/api/core-sdk.md`, `ARCHITECTURE.md`, `TYPES_AND_PROTOCOLS.md`, `EXAMPLES.md` as needed.
- Update example implementations under `core/python/examples/` if any directly use static methods.

10) Cleanup and readiness for wrapper removal (follow-up PR)
- Confirm wrapper protocols are identical to plugin protocols (method names, parameters, return types).
- Note any remaining deltas; remove them or file tasks to reconcile.
- Prepare a follow-up step to remove wrapper types and collapse adapters where they are pure pass-throughs.

11) Validation
- Run: `pytest core/python/tests -q` and `pytest core/python/examples/tests -qs`.
- Stream tests: `pytest core/python/tests/test_async.py -q`.
- Lint/format/typecheck: `ruff`, `black`, `pyright` per `AGENTS.md`.

12) Remove passthrough adapters and use wrappers directly
- Delete `ProviderAdapter`, `FeatureAdapter`, and `ToolAdapter` classes.
- Update `core/python/agent_core/plugin/__init__.py` to export only wrappers.
- Update `AgentCore` to store and use wrappers directly for provider, features, and tools.
- Update any tests importing adapters to use wrappers instead.

13) Provider streaming mixin and core integration
- Create a `ProviderStreamMixin` mixed into `ProviderWrapper` that adds optimized streaming APIs:
  - `stream_messages(native_messages, state)` -> yields dict events without raw chunks:
    - `{"type": "partial", "message": <partial_message>}` per partial
    - `{"type": "final_messages", "messages": <list_of_final_messages>}` when available
  - `stream_messages_async(native_messages, state)` -> async variant.
  - Internally consumes `plugin.stream_api`/`plugin.stream_api_async`, calls `process_chunk` on each chunk, updates wrapper state, and tracks the latest `native_messages`.
  - Adds `get_last_native_messages()` to expose the latest accumulated native messages after streaming.
- Update `AgentCore.send_request_stream` and `send_request_stream_async` to use `ProviderWrapper.stream_messages*` and forward yielded events to the caller; aggregate finals as before. Use `wrapper.get_last_native_messages()` for provider `finalize`.
- Keep the finalize chain unchanged: provider `finalize` then feature `finalize`.

14) Re-run validation
- Run tests and examples. Fix any test that referenced adapters (`test_tool_adapter.py` -> use `ToolWrapper`).
- Ensure streaming behavior and output shape remain consistent for consumers.

Risk mitigation
- Maintain message/event shapes in the core API so example and integration tests continue to pass.
- Keep the provider wrapper responsible for native message accumulation; the core relies on `get_last_native_messages()` only during finalize.

Notes
- The mixin keeps raw chunk handling within the wrapper hot path to reduce crossings and repeated plumbing, improving performance in high-chunk scenarios.
