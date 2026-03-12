# Core Capability And Contract

Short description: Track the generic provider-extension session-action capability as its own framework feature, separate from the OpenAI Responses native compaction use case that first introduced it.

Parent Task: `tasks/20260312-provider-extension-session-actions/000-main.md`

Depends On:
- `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`

## Origin of this subtask

This subtask is extracted from the prerequisite/core-capability portion of:

1. `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`

Specifically, it pulls out the reusable framework work that had originally been bundled into that OpenAI-specific task.

## Scope

Define, document, and validate the generic framework capability that lets provider extensions own session-scoped actions over provider-native history.

This is not about one specific extension implementation. It is about the reusable contract that enables implementations such as native compaction.

## Capability summary

The framework now supports provider-extension session actions with these core ideas:

1. provider extensions can declare session-scoped actions
2. those actions receive the current session and provider-native history
3. they return a replacement provider-native history plus optional result metadata
4. the core rebuilds visible session messages from the returned native history
5. higher layers execute them through the existing action transport path rather than a separate bespoke RPC

## Main framework concepts to preserve

1. Session scope only.
- these actions operate on one session’s provider-native history, not on application-global state

2. Provider ownership.
- the transformation logic lives in the provider extension, not in an application plugin

3. Existing action transport reuse.
- UI elements remain normal `session_action` / `message_action` style elements
- backend execution remains compatible with `POST /actions`

4. Native-history-first invariant.
- visible session history must be reconstructed from provider-native history after action execution

## Relevant implementation points

1. Protocol surface:
- `core/python/agent_core/types.py`

2. Wrapper/adapters:
- `core/python/agent_core/plugin/adapters.py`
- `core/python/agent_core/plugin/extension.py`
- `core/python/agent_core/plugin/provider.py`

3. Core orchestration:
- `core/python/agent_core/core.py`

4. App/server execution routing:
- `core/python/agent_app/application_future.py`
- `application/python/agent_terminal_app/server.py`

## Current behavior that should be treated as the baseline

1. provider extensions may implement:
- `get_actions(state)`
- `execute_action(action_id, session, native_messages, params, state)`

2. `AgentCore` exposes generic discovery/execution for extension-owned session actions

3. `action_owner: "provider_extension"` is used to distinguish routing where needed

4. backend tests already verify:
- session UI schema discovery for extension-owned actions
- `POST /actions` execution through the new session-action path

## Open questions for future refinement

1. Should provider-extension session actions have a more explicit schema/type surface than free-form dicts?
2. Should global application action discovery endpoints eventually expose extension-owned actions too, or should they remain strictly application-plugin scoped?
3. Should there be a shared helper/model for session-action validation so application actions and provider-extension actions stay aligned?
4. Should terminal/desktop UIs expose these actions as first-class interactive commands in addition to HTTP/mobile flows?

## Test baseline

Current tests that cover this capability:

1. `core/python/tests/test_provider_extension_session_actions.py`
2. `application/python/tests/test_provider_extension_session_actions_endpoints.py`

These should be treated as the starting point for any future changes to the generic session-action framework.

## Acceptance criteria

1. The provider-extension session-action mechanism is clearly tracked as a reusable framework capability.
2. References point back to the OpenAI-specific task where it originated.
3. Future work can build on this task without needing to rediscover the capability from the native-compaction task.

## References

1. Source task and completion notes:
- `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`

2. Existing backend tests:
- `core/python/tests/test_provider_extension_session_actions.py`
- `application/python/tests/test_provider_extension_session_actions_endpoints.py`

3. Current concrete example implementation:
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py`