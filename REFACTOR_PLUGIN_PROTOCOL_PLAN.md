# Refactor Plan: Make Plugin Protocols Instance-Based and Align Wrappers

Goal
- Convert all plugin protocol methods in `core/python/agent_core/types.py` from `@staticmethod` to instance methods, one plugin type at a time, updating all usages and implementations.
- After the plugins are migrated, align wrapper protocol types to be fully compatible with the plugin types so wrappers can be removed in a follow-up step.

Ground rules
- Keep signatures the same aside from adding `self` (retain existing parameters like `state`, `config`, etc.).
- Migrate in safe, testable slices: one plugin type per commit, keep tests green after each slice.
- Avoid unrelated changes; update docs/tests/examples alongside code.

0) Baseline
- Run: `pytest core/python/tests -q` and `pytest examples/tests -qs` to ensure green baseline.
- Run: `ruff check core/python/agent_core tests examples` and `pyright`.

1) Prepare code search and inventory
- Use ripgrep to inventory call sites and implementations for each protocol method.
- Focus files likely impacted:
  - Protocols: `core/python/agent_core/types.py`
  - Wrappers/adapters: `core/python/agent_core/plugin/provider.py`, `core/python/agent_core/plugin/extension.py`, `core/python/agent_core/plugin/feature.py`, `core/python/agent_core/plugin/tool.py`
  - Provider implementations: `core/python/agent_core/providers/openai_compatible.py`, `plugins/providers/openai/python/openai_provider.py`
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
  - `plugins/providers/openai/python/openai_provider.py`
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

8) Align Wrapper Protocol Types with Plugin Protocols
- In `core/python/agent_core/types.py`, update `BaseWrapper`, `ProviderWrapperProtocol`, `ExtensionWrapperProtocol`, `FeatureWrapperProtocol`, and `ToolWrapperProtocol` so their instance method signatures mirror the instance-based plugin protocols.
- Ensure no wrapper-only methods remain that differ in name/signature from plugin types unless required by orchestration; aim for 1:1 compatibility.
- Update adapters (`provider.py`, `extension.py`, `feature.py`, `tool.py`) and any `AgentCore` usage to satisfy the updated wrapper protocols without changing observable behavior.
- Run full test suite and type checks.

9) Documentation and examples
- Update API docs and references where they mention "static methods" for plugins:
  - `docs/api/core-sdk.md`, `ARCHITECTURE.md`, `TYPES_AND_PROTOCOLS.md`, `EXAMPLES.md` as needed.
- Update example implementations under `examples/` if any directly use static methods.

10) Cleanup and readiness for wrapper removal (follow-up PR)
- Confirm wrapper protocols are identical to plugin protocols (method names, parameters, return types).
- Note any remaining deltas; remove them or file tasks to reconcile.
- Prepare a follow-up step to remove wrapper types and collapse adapters where they are pure pass-throughs.

11) Validation
- Run: `pytest core/python/tests -q` and `pytest examples/tests -qs`.
- Stream tests: `pytest core/python/tests/test_async.py -q`.
- Lint/format/typecheck: `ruff`, `black`, `pyright` per `AGENTS.md`.

Risk mitigation
- Make each slice self-contained (protocol change + wrapper + implementations + tests).
- Keep method signatures stable (add only `self`).
- Avoid changing state shape or control flow.

Notes
- If third-party plugins exist, consider a temporary shim in wrappers to support both styles (detecting `@staticmethod` vs instance) during the transition window; remove once internal migration completes.