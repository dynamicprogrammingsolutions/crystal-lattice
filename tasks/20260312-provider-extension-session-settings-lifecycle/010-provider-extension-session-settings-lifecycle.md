# Provider-Extension Session Settings Lifecycle

Short description: Implement a generic shared capability that allows non-application plugins to initialize and mutate per-session settings/overrides through lifecycle-triggered paths, while preserving the current architecture where provider-specific behavior remains outside the application layer.

Parent Task: `tasks/20260312-provider-extension-session-settings-lifecycle/000-main.md`

Depends On: None

## Goal

Introduce the minimal generic core/application/server capability needed so provider extensions and similar non-application plugin types can participate in session-settings lifecycle.

This should make it possible for a feature such as `openai_responses` prompt caching to ensure a session-owned setting exists at the right time, without implementing that feature as an application plugin.

## Scope

This task is about the shared capability only.

In scope:

1. generic lifecycle-triggered session settings/override writes for non-application plugins
2. create-time initialization support for new sessions
3. request-time fallback support for legacy sessions missing required session-owned settings
4. preservation of existing session-owned settings on fork unless a feature explicitly chooses to replace them
5. generic tests covering the new capability across core/application/server paths

Out of scope:

1. OpenAI prompt caching request shaping itself
2. OpenAI-specific config keys or UI labels
3. provider-specific feature logic in application code

## Requirements

1. The capability must be generic and reusable by non-application plugin types.
2. It must support at least two lifecycle moments:
- session creation
- request-send fallback/repair for existing sessions
3. It must integrate with the existing session settings / per-session override model rather than inventing a parallel storage location when the feature being enabled is a user-visible session setting.
4. Forked sessions must preserve existing session-owned settings by default.
5. The application/core/server layers must not hardcode feature-specific behavior.

## Design constraints

1. Keep the provider transport/native-history focused.
2. Keep request shaping and feature ownership in provider extensions/features.
3. Prefer one generic capability over feature-specific hooks.
4. Avoid forcing provider-owned capabilities into application plugins just to mutate session settings.

## Candidate implementation directions

The implementation should choose the smallest generic mechanism that satisfies the requirements.

Acceptable directions include:

1. lifecycle hooks for non-application plugins that can return session-settings/session-metadata patches
2. a generic lifecycle action path for non-application plugins that is triggered by application/session events
3. another comparably generic mechanism that allows create-time and pre-send fallback mutation while preserving layering

The chosen implementation must be documented in code/tests and in the follow-up docs subtask.

## Acceptance criteria

1. There is a generic way for non-application plugins to initialize session-owned settings during session creation.
2. There is a generic way for non-application plugins to repair/add missing session-owned settings during a request lifecycle path.
3. Fork keeps session-owned settings intact by default.
4. Existing session settings surfaces can still expose and edit the resulting values when those values are stored as session settings/overrides.
5. Tests cover create-time initialization, request-time fallback, and fork preservation.

## Test expectations

1. Core/application tests for create-time lifecycle writes.
2. Core/application/server tests for request-time fallback writes on legacy sessions.
3. Regression tests that fork preserves the existing session-owned values.
4. Tests should use a generic dummy plugin/extension fixture rather than an OpenAI-specific implementation.

## References

- `tasks/20260128-sandboxing-prereqs/030-add-session-override-helper-apis.md`
- `tasks/20260128-sandboxing-prereqs/040-session-aware-app-plugin-ui-and-conditions.md`
- `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`
- `core/python/agent_app/application_future.py`
- `application/python/agent_terminal_app/server.py`
- `application/python/agent_terminal_app/terminal_app.py`

## Approved plan (added during completion)

1. Keep the existing action concept and method names in sync across plugin families.
- application plugins continue to use `get_actions(state)` and `execute_action(app, action_id, params, state)`
- provider extensions will use the same conceptual pattern for this capability via `get_actions(state)` and `execute_action(action_id, session, native_messages, params, state)`
- lifecycle-triggered work is represented as ordinary actions that declare lifecycle triggers in the action definition, rather than introducing a second naming scheme just for lifecycle execution

2. Make lifecycle names dynamic while standardizing a built-in baseline.
- action definitions may declare any string lifecycle name in `trigger`; lifecycle support must not be limited to a fixed enum baked into the contract
- future application implementations should be able to call `AgentApplication` with arbitrary lifecycle names, and future plugins should be able to handle arbitrary lifecycle names
- `AgentApplication` should still provide a standard built-in lifecycle set for normal flows; the complete documented set should include `session_create`, `session_save_prepare`, `request_prepare`, `request_complete`, `request_error`, `session_fork`, `agent_switch_prepare`, `agent_switch_complete`, and `session_delete_prepare`
- docs should present those built-ins as the standard lifecycle vocabulary while still making clear that arbitrary lifecycle names remain supported

3. Put lifecycle dispatch in `AgentApplication`, not `AgentCore`.
- `AgentApplication` owns when lifecycle actions run, because it owns session creation, request entrypoints, persistence, locks, and event/checkpoint behavior
- the existing server-only `trigger: "session_list"` pattern is the precedent, but the new capability should move the lifecycle idea into shared application-layer orchestration rather than leaving it HTTP-specific
- `AgentApplication` should expose a generic lifecycle-dispatch entry point that accepts a lifecycle name and optional extra context so future callers are not limited to the built-in flows wired today

4. Add a high-level `AgentCore` helper for core-side lifecycle action execution.
- `AgentApplication` will call a high-level `AgentCore` method with `session`, effective `config`, lifecycle trigger, and additional context
- `AgentCore` will resolve the enabled provider/extensions/features for that config, find matching triggered actions, execute them, and return an updated `Session`
- `AgentCore` should not own persistence, locks, or app-level side effects; it only executes core-side actions for one session in one config context

5. Keep application-plugin and non-application-plugin response capabilities intentionally different.
- application plugin actions keep their current app-level result semantics and may request reloads, navigation, session creation/deletion, and similar UI/application effects
- provider extensions and similar non-application plugins remain single-session oriented and must follow the existing mutation style: return replacement native history and/or session metadata patches that the core converts into a modified `Session`
- for this subtask, the important supported mutation surface is `session.metadata`, including `session.metadata["overrides"]`, so lifecycle actions can initialize or repair session-owned settings without becoming application plugins

6. Add serializable extra lifecycle context.
- lifecycle execution should accept arbitrary additional context under caller-provided keys, separate from action input params
- this extra context must be serializable so the contract remains language-neutral if extensions or other plugins are implemented outside Python in the future
- for fork flows, actions that run on the forked session should be able to receive the original session in serialized form under a context key such as `original_session`
- docs should clearly distinguish action params from execution context and note that `original_session` and similar values must be passed as serialized data, not live Python objects

7. Wire the shared lifecycle dispatcher into the required built-in lifecycle moments.
- run lifecycle actions during `AgentApplication.create_session_ephemeral(...)` so newly created sessions can be initialized before first persistence using the `session_create` lifecycle
- run lifecycle actions during `AgentApplication.send_request(...)` before the tool loop starts so legacy sessions can be repaired on first use using the `request_prepare` lifecycle
- when fork flows are wired, use the `session_fork` lifecycle on the new forked session and include serialized `original_session` data in the extra context
- if `request_prepare` changes the session, persist it through the existing app-level save/checkpoint path rather than through feature-specific server code

8. Implement the capability with generic dummy-plugin coverage across shared layers.
- add focused tests for create-time initialization and request-time repair
- cover application/core/server behavior with generic dummy plugins or fixtures rather than OpenAI-specific logic
- verify that resulting values still appear through existing session override/settings surfaces
- fork-specific verification does not need a dedicated metadata-preservation regression because metadata preservation on fork is already the default behavior

9. Document the agreed post-update action model before implementation details expand further.
- add a `plugins/docs` page describing the shared action concept, dynamic lifecycle triggers, dispatcher ownership, serializable execution context, and the difference between application-plugin action results and single-session core-side action results
- treat that page as forward-looking guidance for the follow-up docs subtask and implementation review

## Completion notes (added during completion)

Implemented the lifecycle-triggered action system with dynamic lifecycle names and shared action naming across application plugins and core-side plugins.

What changed:

- `AgentApplication` now owns generic lifecycle dispatch via `run_session_lifecycle(...)`, accepts arbitrary lifecycle names plus serializable context, and wires built-in lifecycle calls into:
  - `create_session_ephemeral(...)` via `session_create`
  - `save_session(...)` via `session_save_prepare`
  - `send_request(...)` via `request_prepare`, `request_complete`, and `request_error`
  - `fork_session(...)` via the new shared application helper and `session_fork`
  - `update_agent(...)` via `agent_switch_prepare` and `agent_switch_complete`
  - `delete_session(...)` via `session_delete_prepare`

- `AgentCore` now supports triggered core-side lifecycle execution via `execute_lifecycle_actions(...)`.
  - provider extensions participate through their existing `get_actions(...)` / `execute_action(...)` pattern
  - feature plugins now support the same optional action pattern and share the same single-session mutation contract
  - action execution supports optional serializable `context`

- Backward compatibility was preserved for existing plugins.
  - application-plugin wrappers accept both old and new `execute_action(...)` signatures
  - provider-extension and feature adapters accept both old and new action signatures with or without `context`

- Server/terminal fork flows were moved onto the shared application-layer fork helper so lifecycle hooks run consistently outside direct `AgentCore.fork_session(...)` usage.
  - updated `application/python/agent_terminal_app/server.py`
  - updated `application/python/agent_terminal_app/terminal_app.py`
  - updated `plugins/session-actions-app/src/session_actions_app/__init__.py`

- Added focused lifecycle fixtures/tests.
  - `core/python/tests/dummy_lifecycle_extension.py`
  - `core/python/tests/dummy_lifecycle_app_plugin.py`
  - `core/python/tests/test_application_session_lifecycles.py`
  - `application/python/tests/test_session_lifecycle_server_fork.py`

Docs updated:

- `plugins/docs/actions.md`
- `plugins/docs/index.md`

Focused tests run:

- `pytest core/python/tests/test_application_session_lifecycles.py application/python/tests/test_session_lifecycle_server_fork.py -q`
- `pytest application/python/tests/test_agent_terminal_app_server.py -k 'fork_session_endpoint_creates_truncated_copy' -q`
- `pytest core/python/tests/test_application_session_lifecycles.py core/python/tests/test_application_layer_app_plugins_basic.py core/python/tests/test_provider_extension_session_actions.py application/python/tests/test_session_lifecycle_server_fork.py application/python/tests/test_provider_extension_session_actions_endpoints.py application/python/tests/test_terminal_application.py -k 'fork_slash_command or test_session_ui_schema_includes_provider_extension_action or test_actions_endpoint_executes_provider_extension_session_action or test_create_load_and_delete_session_run_lifecycle_actions or test_request_prepare_and_complete_lifecycles_update_checkpoint_session or test_request_error_lifecycle_records_error_metadata or test_fork_and_agent_switch_run_lifecycle_actions' -q`

Notes / follow-up considerations:

- Application-plugin lifecycle results now support internal session mutation keys such as `session` and `session_metadata` so lifecycle actions can affect in-flight sessions before persistence. This is now part of the implemented behavior even though the main design discussion focused more on naming, dispatch, and context.
- Core-side lifecycle execution currently keeps the effective request config fixed for the duration of one lifecycle run. If a future lifecycle action needs to change provider selection or other config-dependent plugin resolution mid-run, that would need an additional iterative re-resolution step.
- Follow-up change after implementation review: `session_load` was intentionally removed from the standard lifecycle set and from runtime dispatch. Load paths should stay non-mutating because a session may already have a running request; standard lifecycle hooks are now limited to mutating flows.