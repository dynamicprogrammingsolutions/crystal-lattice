# Documentation TODO

This file tracks documentation gaps introduced on the `slice_and_fork` branch. Each item notes **what** to document and **where** it should live.

---

## Core SDK / AgentCore

- Document session slicing and deletion APIs (`slice_session`, `fork_session`).
  - Content:
    - Semantics of `start`, `end`, and `remove_indices` (including negative indices).
    - When native provider history is preserved vs. dropped.
    - Behavior of `fork_session(..., upto_index, new_session_id)` and when it reuses vs. changes the session id.
  - Target docs:
    - `docs/api/core-sdk.md` (AgentCore methods section).
    - `docs/reference/agent_core/core.md` (detailed API reference for `AgentCore`).

- Document native-history retention and integrity checks.
  - Content:
    - Meaning of `session.metadata["native_messages"]` and `native_messages_integrity`.
    - How integrity is computed (`message_count`, `total_chars`) and enforced.
    - How to intentionally reset/bypass native history (removing `native_messages` / `native_messages_integrity`).
  - Target docs:
    - `docs/reference/agent_core/core.md` (session lifecycle & persistence).
    - `core/python/README.md` (short "Native history" subsection under AgentCore concepts).

- Document core-native round‑trip helpers.
  - Content:
    - Purpose of `_core_messages_to_native_for_config` and `_rebuild_core_from_native`.
    - When these are used (modify, slice, and native-history reconstruction paths).
  - Target docs:
    - `docs/reference/agent_core/core.md` (advanced internals section).

- Document tool streaming APIs and semantics.
  - Content:
    - `iter_tool_messages`: mixed stream of `{"part": ...}` payloads and final `role="tool"` messages.
    - `execute_tool_calls`: built on `iter_tool_messages`, behavior when tools emit no result.
    - `stream_tool_call`: low-level streaming API for a single tool call.
  - Target docs:
    - `docs/api/core-sdk.md` (AgentCore tool APIs: `get_tool_schemas`, `iter_tool_messages`, `execute_tool_calls`, `stream_tool_call`).
    - `docs/plugins/development.md` (how ToolPlugins participate in streaming and display).

- Document tag-based plugin dependency resolution.
  - Content:
    - How providers, features, tools, and extensions expose capabilities via `get_tags` and `required_tags`.
    - How `_resolve_plugins_for_config` uses tags to decide which plugins are active for a config.
    - Impact of caches (`_models_cache`, `_dependency_cache`, `_tags_cache`) on dynamic config changes.
  - Target docs:
    - `docs/reference/agent_core/plugin/provider.md` (provider + extension tags).
    - `docs/plugins/development.md` (section on `get_tags` / `required_tags` usage).

- Document multi-provider selection rules.
  - Content:
    - Detailed behavior of `_select_provider_for_config` with multiple providers registered.
    - Accepted identifiers (short name vs. fully-qualified class path).
    - Structure of error messages and how they list available providers.
  - Target docs:
    - `docs/api/core-sdk.md` (AgentCore configuration & provider selection).
    - `core/python/README.md` ("Provider Selection" subsection already exists; extend with new behavior).

---

## Provider Wrapper / Extensions Infrastructure

- Document provider wrapper streaming pipelines.
  - Content:
    - `ProviderWrapper.stream_messages` / `stream_messages_async` event protocol:
      - `{"type": "partial", "message": ...}`.
      - `{"type": "final_messages", "messages": [...]}`.
    - Contract for `get_last_native_messages()` and when it is valid to call.
  - Target docs:
    - `docs/reference/agent_core/plugin/provider.md` (streaming section).

- Document extension config/UI aggregation APIs.
  - Content:
    - `get_extension_config_schemas()` and `get_extension_ui_elements()`.
    - How these feed into `AgentCore.get_config_schema()` and `get_ui_schema()`.
  - Target docs:
    - `docs/reference/agent_core/plugin/provider.md`.
    - `docs/api/core-sdk.md` (brief note under `get_config_schema` and `get_ui_schema`).

- Document tool wrapper streaming behavior.
  - Content:
    - `ToolWrapper.stream_tool()` expectations (iterator over partial RESULT/part payloads).
    - `ToolWrapper.to_display_format()` and `metadata.display` convention.
  - Target docs:
    - `docs/plugins/development.md` (ToolPlugin section).

---

## New Tool Plugins

- Document `ApplyPatchTool` (Codex-style apply_patch tool).
  - Content:
    - Purpose: apply `*** Begin Patch` / `*** End Patch` diffs to files.
    - Config: `allowed_paths`, `working_directory`, `max_patch_bytes` and sandboxing behavior.
    - Error modes (`DiffError`, invalid patches, missing files, path access denied).
    - Tool schema: function name `apply_patch`, `patch_text` parameter, and return payload (`success`, `fuzz`, `changes`).
    - Example usage from an agent (simple patch example).
  - Target docs:
    - `docs/plugins/development.md` (tool catalog / examples).
    - `EXAMPLES.md` (brief mention under tooling examples, pointing to tests).

- Document `ShellTool` (sandboxed shell execution tool).
  - Content:
    - Purpose and security model: `bash -lc` with `allowed_paths` sandbox, default `working_directory`, and per-call `workdir`.
    - Config: `timeout_seconds`, `max_output_chars` and truncation format.
    - Tool schema: params `command`, optional `workdir`, optional `timeout_seconds`, optional `env` map.
    - `execute_tool` result shape and error reporting (non-zero exit, timeout, invalid workdir).
    - Streaming semantics via `stream_tool`: text partials and final result, behavior on timeout.
  - Target docs:
    - `docs/plugins/development.md` (tool examples).
    - `docs/api/core-sdk.md` (short note in tools section pointing to shell tool docs).

---

## New Provider Extensions

- Document `DelayExtension` (artificial delay).
  - Content:
    - Config keys: `enable_delay_extension`, `delay_seconds`.
    - Behavior: sleeps during `initialize_request` when enabled; negative values coerced to 0.
    - Intended usage: testing cancellation and UI behavior under latency.
  - Target docs:
    - `docs/plugins/development.md` (provider extensions section).
    - `core/python/README.md` (brief mention under "Debug / testing extensions").

- Document `RandomFailureExtension` (simulated failures).
  - Content:
    - Config keys: `enable_random_failure`, `random_failure_every`.
    - Behavior: global counter, raises from `finalize` on every Nth request.
    - Caveat: module-level mutable state `_RF_STATE` and its persistence across requests/tests.
  - Target docs:
    - `docs/plugins/development.md` (provider extensions).

- Document OpenAI/OpenRouter tool extensions.
  - Content:
    - `OpenAIToolsExtension` and `OpenRouterToolsExtension` behaviors:
      - Tag requirements (`required_tags`) and when they activate.
      - How they inject `tools` and `tool_choice` into request payloads.
      - How they map `tool_call_id`, `tool_calls`, and extra metadata via native `_metadata`.
      - Streaming accumulation of tool_calls using the `index` field.
  - Target docs:
    - `docs/reference/providers/openai_provider.md` (for OpenAI-compatible tools behavior).
    - New short section in `docs/reference/agent_core/plugin/provider.md` ("Tool-calling extensions").

---

## Provider Implementations

- Document updated OpenAI-compatible provider behavior.
  - Content:
    - Capability tags (`supports_streaming`, `supports_tools`, `supports_thinking`).
    - Stricter `_validate_message_list` behavior and example error messages.
    - Use of `state["request"]["messages"]` as an override for native history.
    - Stripping of internal `_metadata` before sending to the API.
  - Target docs:
    - `docs/reference/providers/openai_provider.md`.

- Document updated OpenRouter provider behavior.
  - Content:
    - Capability tags including `openrouter` and `supports_reasoning`.
    - `_sanitize_history` rules (dropping `refusal=None`, removing `index` from `tool_calls`, stripping `_metadata`).
    - Improved error reporting for `call_api` and `stream_api` (payload and server error logging).
  - Target docs:
    - `PLAN_OPENROUTER_PROVIDER.md` (ensure behavior matches the plan or update notes).
    - `docs/reference/providers/openai_provider.md` (OpenRouter-specific section / sibling doc).

---

## Application Layer (AgentApplication + ToolLoopRunner)

- Document `AgentApplication` as the primary application-layer API.
  - Content:
    - Constructor parameters: `config_path`, `session_root`, optional `core_factory`, optional `event_store`.
    - How config is loaded, placeholders resolved, plugins loaded, and errors collected (`get_config_errors`).
    - Relationship between the long-lived core in the session store and per-request cores from `_new_core`.
  - Target docs:
    - `docs/api/core-sdk.md` (new section: "Application Layer: AgentApplication").
    - `EXAMPLES.md` (pointer to Example 13 app-layer usage).

- Document typed helpers and session lifecycle.
  - Content:
    - `create_session(agent_id)`, `load_session(session_id)`, `save_session`, `delete_session`, `list_agents`.
    - Requirement that `session.metadata["agent_id"]` is present and how errors are raised if missing.
  - Target docs:
    - `docs/api/core-sdk.md` (AgentApplication API subsection).
    - `core/python/examples/example13_openrouter_tools_app_layer.py` (ensure inline comments/README match).

- Document core-first request API (`AgentApplication.send_request`).
  - Content:
    - Event protocol and all event types with their fields:
      - `request_started`, `partial`, `final`, `tool_calls`, `tool_partial`, `tool_results`, `request_completed`, `request_cancelled`, `error`.
    - Difference between `stream=False` and `stream=True` at the LLM phase, and that the outer tool loop is the same.
    - Responsibility split: caller persists sessions; AgentApplication only yields events.
  - Target docs:
    - `docs/api/core-sdk.md` (detailed section on event-driven request handling).
    - `docs/reference/agent_core/core.md` (cross-reference from streaming section).

- Document request cancellation.
  - Content:
    - `cancel_request(request_id)` API, validation of `request_id`.
    - How `send_request`/`ToolLoopRunner` check cancellation and emit `request_cancelled` events.
    - Limitations: long-running non-streaming provider calls may not stop immediately.
  - Target docs:
    - `docs/api/core-sdk.md` (AgentApplication section: "Cancellation").

- Document `ToolLoopRunner` behavior.
  - Content:
    - Role as per-request helper that runs the LLM + tools loop.
    - Detection of pending tool_calls already in the session before the first LLM call.
    - Loop depth limiting via `_ToolLoopConfig.max_loops` and emitted `error` events when exceeded.
    - Tool streaming behavior (usage of `AgentCore.iter_tool_messages`, `tool_partial` and `tool_results` events, session updates with tool results).
  - Target docs:
    - `docs/api/core-sdk.md` (advanced application-layer behavior; may be a subsection under AgentApplication).
    - `DEVELOPMENT.md` (internal architecture notes on the application layer).

---

## Terminal Application & API Server

- Document `agent_terminal_app` package as a canonical example app.
  - Content:
    - High-level architecture: FastAPI backend + prompt_toolkit console.
    - Shared `AgentApplication` and `InMemoryEventStore` when running server+console in one process.
  - Target docs:
    - `application/python/README.md` (top-level context already present; expand with explicit architecture diagram/description).
    - `EXAMPLES.md` (link this as a larger end-to-end example).

- Document CLI entrypoint behavior for `python -m agent_terminal_app`.
  - Content:
    - Flags: `--console`, `--server`, `--host`, `--port`, `--log-file`.
    - Modes:
      - server-only (default, no flags),
      - console-only (`--console`),
      - combined (`--console --server`) with shared event store and two AgentApplication instances.
    - Logging behavior and interaction with structlog when `--log-file` is set.
  - Target docs:
    - `application/python/README.md` (extend "Running the API server" and "Running the terminal client" with a dedicated "CLI options" section).

- Document server HTTP API details.
  - Content:
    - `POST /sessions`: accepted body (`agent_id`, `system_message`), returned `session` and `errors` (from `get_config_errors`).
     - `POST /sessions/{session_id}/messages`: request (`role`, `content`, optional `metadata`), role normalization rules, event emission.
    - `POST /sessions/{session_id}/send`: `config_overrides` mapping, how it flows to `AgentApplication.send_request`, returned `session`, `messages`, `request_id`.
    - `GET /events`: filters (`since_id`, `request_id`, `session_id`, `limit`) and returned `events` structure.
  - Target docs:
    - `application/python/README.md` (API reference section per route).
    - New small reference file under `docs/api/` (e.g. `docs/api/terminal-app.md`) if more detail is desired.

- Document terminal commands and shortcuts beyond the basics.
  - Content:
    - Slash commands:
      - `/agent`, `/session`, `/set`, `/send`, `/append`, `/cancel`, `/delete`, `/modify`, `/list`, `/ui_schema`, `/help`, `/new`, `/exit`/`/quit`.
      - Semantics of each, including index/range handling for `/delete` and `/list`, and `/modify` prefill behavior.
    - Shortcuts:
      - `Ctrl-N`, `Ctrl-Q` (already in README), plus `Ctrl-X S` (send), `Ctrl-X A` (append), `Ctrl-X C` (cancel request), `Ctrl-J` (insert newline).
    - Autocompletion behavior for `/agent`, `/session`, `/set`.
  - Target docs:
    - `application/python/README.md` (expanded "Running the terminal client" section with a commands/shortcuts table).

- Document terminal event rendering behavior.
  - Content:
    - How reasoning, assistant partials, tool streaming output, and request boundaries are rendered (colored headers, grouping by `request_id`/`tool_call_id`).
    - Use of the `terminal_event` logger to debug raw event flow.
  - Target docs:
    - `application/python/README.md` (subsection: "How streaming output is rendered").

- Document configuration UI integration from the terminal.
  - Content:
    - `/ui_schema` as a debug command exposing `core.get_ui_schema()` for the current agent.
    - `/set` as the user-facing way to apply per-session config overrides based on UI schema elements (`key`, `options`, type coercion for checkboxes).
  - Target docs:
    - `application/python/README.md` (configuration section).
    - `docs/api/core-sdk.md` (cross-reference from `get_ui_schema`).

---

## Config / Agents / Examples

- Document example configs used by the terminal app.
  - Content:
    - `config_openrouter_app_layer.json` and `config_echo_app.json` structure:
      - `agents` section (agent ids and base configs).
      - `plugins` section listing providers, extensions (including delay/random_failure), tools (shell/apply_patch).
    - How these configs are intended to be used by AgentApplication and the terminal/server.
  - Target docs:
    - `application/python/README.md` ("Configuration" section with brief walkthrough and links to the JSON files).

- Document that `application/python` is a separate installable package.
  - Content:
    - `application/python/pyproject.toml` and its relation to the core SDK.
    - Installation instructions (already partially in `application/python/README.md`; ensure they match `pyproject.toml`).
  - Target docs:
    - `application/python/README.md` ("Installation" section; confirm wording and update as needed).

