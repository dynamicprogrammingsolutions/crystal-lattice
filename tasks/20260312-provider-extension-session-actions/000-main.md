# Provider-Extension Session Actions

Short description: Extract the generic provider-extension session-action capability into its own task bundle, then follow through on frontend wiring and documentation so extension-owned session/message actions are discoverable, executable, and documented across the stack.

## Subtasks

- [x] `tasks/20260312-provider-extension-session-actions/010-core-capability-and-contract.md`
- [x] `tasks/20260312-provider-extension-session-actions/020-frontend-wiring-provider-extension-actions.md`
- [ ] `tasks/20260312-provider-extension-session-actions/030-docs-provider-extension-session-actions.md`

## Why this task bundle exists

The generic provider-extension session-action capability was introduced while completing:

1. `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`

That subtask successfully delivered the capability and used it for OpenAI Responses native compaction, but it mixed together:

1. the reusable core/app/plugin contract addition
2. one concrete extension implementation (`openai_responses` compaction)
3. the still-open frontend wiring follow-up

This task bundle separates the reusable capability from the `openai_responses` implementation details so future work can reason about the framework feature directly.

## Relationship to existing tasks

1. This task bundle is extracted from the prerequisite/core-capability portion of:
- `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`

2. The frontend follow-up expands and supersedes the more narrowly scoped task draft at:
- `tasks/20260310-openai-responses-provider/110-wire-provider-extension-session-actions-into-frontend.md`

3. The concrete `openai_responses` native compaction implementation remains in the original task lineage, but future changes to the generic action framework should be tracked here.

## Current state at handoff

What already exists in code:

1. provider extensions can define `get_actions(state)` and `execute_action(action_id, session, native_messages, params, state)`
2. `AgentCore` supports generic session-scoped provider-extension actions
3. server/app routing can execute those actions through existing `POST /actions`
4. `openai_responses` native compaction is implemented on top of that mechanism

What is still incomplete at a product/integration level:

1. the frontend/mobile UI does not yet surface those session/message actions from session UI schema in the visible action menus
2. the capability is not yet documented as a first-class framework feature

## Recommended order

1. `010` core-capability-and-contract
2. `020` frontend-wiring-provider-extension-actions
3. `030` docs-provider-extension-session-actions

## Global acceptance criteria

1. The provider-extension session-action capability is documented as a reusable framework concept, not only an OpenAI-specific behavior.
2. Frontends can discover and execute extension-owned `session_action` and `message_action` UI elements without a bespoke action pathway.
3. Existing application-plugin actions continue to coexist with provider-extension actions.
4. The `openai_responses` native compaction action remains a verified concrete example of the capability.

## Key references

1. Extracted source task:
- `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`

2. Follow-up frontend draft to fold in:
- `tasks/20260310-openai-responses-provider/110-wire-provider-extension-session-actions-into-frontend.md`

3. Core/app implementation points:
- `core/python/agent_core/types.py`
- `core/python/agent_core/core.py`
- `core/python/agent_core/plugin/adapters.py`
- `core/python/agent_core/plugin/extension.py`
- `core/python/agent_core/plugin/provider.py`
- `core/python/agent_app/application_future.py`
- `application/python/agent_terminal_app/server.py`

4. Current concrete example:
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py`

5. Backend tests already covering discovery/dispatch:
- `application/python/tests/test_provider_extension_session_actions_endpoints.py`
- `core/python/tests/test_provider_extension_session_actions.py`