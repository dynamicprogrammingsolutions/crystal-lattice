# Docs For Provider-Extension Session Actions

Short description: Document provider-extension-owned session/message actions as a first-class framework capability, including protocol hooks, execution flow, UI element expectations, and the `openai_responses` native compaction action as a concrete example.

Parent Task: `tasks/20260312-provider-extension-session-actions/000-main.md`

Depends On:
- `tasks/20260312-provider-extension-session-actions/010-core-capability-and-contract.md`
- `tasks/20260312-provider-extension-session-actions/020-frontend-wiring-provider-extension-actions.md`

## Why docs are needed

The generic provider-extension session-action capability currently exists mostly as implementation plus tests. It is not yet documented as a reusable platform feature.

That creates a discoverability problem for future plugin authors because the capability could easily be mistaken for an `openai_responses` one-off, rather than a general framework contract.

## Documentation goals

1. Explain the protocol hooks.
- `ProviderExtensionPlugin.get_actions(state)`
- `ProviderExtensionPlugin.execute_action(action_id, session, native_messages, params, state)`

2. Explain the execution path.
- session UI schema can contribute `session_action` / `message_action` elements
- frontend/backend transport uses existing action infrastructure
- backend dispatch may use `action_owner: "provider_extension"`
- core rebuilds visible session messages from returned native history

3. Explain ownership boundaries.
- application plugins own app-level actions over app/session-store concerns
- provider extensions own provider-native session actions over one session’s native history

4. Provide a concrete example.
- `openai_responses` native compaction should be described as the canonical example of the capability in use

## Candidate docs to update

1. `plugins/docs/provider-extensions.md`
- add a section on session-scoped extension actions

2. `plugins/docs/plugin-execution-order.md`
- clarify where session-action execution conceptually fits relative to request-time plugin hooks

3. `plugins/docs/provider-plugins.md`
- mention the interaction point between providers and provider extensions for session actions when relevant

4. Potential API/app docs if needed:
- `docs/api/core-sdk.md`
- any app/server docs describing `/actions` and session UI schema behavior

5. Plugin/example docs if helpful:
- `plugins/openai_responses/README.md` if a README exists or is added later
- config/example documentation showing how the compaction action becomes available through the plugin bundle

## Topics the docs should cover

1. What shape action definitions should have.
2. What inputs are supplied by higher layers versus declared by the extension.
3. What result shape the core expects back.
4. The invariant that visible messages are rebuilt from returned native history.
5. How frontend discovery differs between global application actions and session UI schema actions.
6. How `action_owner` is used in routing.

## Acceptance criteria

1. The provider-extension session-action capability is documented in the framework/plugin docs.
2. The docs clearly distinguish provider-extension actions from application-plugin actions.
3. The docs include at least one concrete example, ideally the native compaction flow.
4. A future plugin author could discover this feature from docs alone without reading `095` implementation details.

## References

1. Generic capability extraction:
- `tasks/20260312-provider-extension-session-actions/010-core-capability-and-contract.md`

2. Frontend integration follow-up:
- `tasks/20260312-provider-extension-session-actions/020-frontend-wiring-provider-extension-actions.md`

3. Source implementation and tests:
- `core/python/agent_core/types.py`
- `core/python/agent_core/core.py`
- `core/python/agent_app/application_future.py`
- `application/python/agent_terminal_app/server.py`
- `core/python/tests/test_provider_extension_session_actions.py`
- `application/python/tests/test_provider_extension_session_actions_endpoints.py`

4. Concrete example:
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py`