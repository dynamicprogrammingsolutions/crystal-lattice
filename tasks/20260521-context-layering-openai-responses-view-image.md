# Context Layering Refactor for OpenAI Responses View Image Rebuilds
Refactor context construction so `AgentCore` and `AgentApplication` each own one long-lived concrete context implementation, while fixing the `openai_responses` + `view_image` asset-backed rebuild bug and the related context propagation gaps discovered during investigation.

## Requirements checklist

- [x] Preserve the observed `openai_responses` + `view_image` failure details and root cause in the implementation notes and tests.
- [x] Move context-building logic out of the main `AgentCore` and `AgentApplication` flow code into one concrete core implementation and one concrete application implementation.
- [x] Keep the shared protocol simple and generic: dict-like input, dict-like output, no concrete `AgentCore`/`AgentApplication` types in the protocol surface.
- [x] Do not introduce a registry or multi-builder hierarchy; keep only two concrete implementations.
- [x] Create the concrete context objects during `AgentCore.__init__` and `AgentApplication.__init__`, then reuse them.
- [x] Allow free-form input both at object initialization time and at per-call build time.
- [x] Keep call-type distinctions as implementation details of the concrete classes, not as public protocol concepts.
- [x] Structure each concrete implementation internally with a generic layer plus specific call-type layers so the shape of each call path is easy to find in one file.
- [x] Make it easy to add new injected objects later with minimal duplication and no unnecessary abstraction.
- [x] Keep migration incremental and behavior-compatible unless an intentional widening is required to fix the bug.
- [x] Ensure request, lifecycle, session-action, response-finalize, rebuild, and edit paths receive the context they previously relied on or should have received.
- [x] Add regression coverage for the original failure and for the related context asymmetries discovered during the investigation.

## Observed bug

The original failure occurs with the `openai_responses` provider when Codex tools produced an asset-backed `view_image` tool result and the provider later tried to rebuild or re-expand the retained native history:

- The stored tool result contains an asset reference rather than an inline data URL.
- `openai_responses` later re-expands that asset reference back into an `input_image` during request preparation / native history rebuild.
- The expansion requires `session_asset_store` in the active context.
- On the failing path, the rebuild runs without that context and raises:

```text
RuntimeError: [openai_responses_provider] session asset attachment requires session_asset_store in context
```

The concrete failing chain observed during investigation:

1. `AgentApplication.send_request(...)`
2. `run_session_lifecycle("request_prepare", ...)`
3. `openai_responses_prompt_caching_extension.ensure_prompt_cache_key`
4. `AgentCore._apply_session_action_result(...)`
5. `AgentCore._rebuild_core_from_native(...)`
6. `OpenAIResponsesProvider.initialize_request(...)`
7. `_expanded_request_history(...)`
8. `_expanded_tool_output(...)`
9. `_image_part_to_input_image(...)`
10. `_session_asset_store(...)` raises because the rebuild context does not contain `session_asset_store`

Relevant files from the investigation:

- `core/python/agent_app/application_future.py`
- `core/python/agent_core/core.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_prompt_caching_extension.py`

## Broader findings from investigation

This was not just one missing key on one path. The investigation found a broader split between rich tool/session-action context and thinner request/rebuild/lifecycle context:

### 1. Request-path context is thinner than tool-path context

`AgentApplication.send_request(...)` currently builds a thin request context with fields like `session_id`, `request_id`, `stream`, and `overrides`, while tool preparation/execution uses a richer application context including:

- `app`
- `application`
- `base_config`
- `session_asset_store`
- `runtime_store`
- `tool_runtime`

As a result, fixing only lifecycle rebuilds would still leave the normal provider request path structurally inconsistent.

### 2. Session/lifecycle rebuilds drop caller context

`AgentCore._apply_session_action_result(...)` rebuilds from native history without forwarding the caller context into `_rebuild_core_from_native(...)`.

This affects:

- explicit session actions
- lifecycle-triggered actions

So the bug is broader than the prompt-caching extension itself.

### 3. `request_context` / `request_runtime` exist only on one action path

`execute_session_action(...)` currently prepares `request_context` and `request_runtime`, but:

- `execute_lifecycle_actions(...)` does not
- `execute_response_lifecycle_actions(...)` does not

This means plugins that need request-initialized state can behave differently depending on how they are triggered.

### 4. Some rebuild/edit paths do not even accept context today

The following core operations are currently structurally unable to preserve rich context through rebuilds:

- `modify_message(...)`
- `rebuild_native_history(...)`

The request/response streaming flows already thread request context into rebuilds more consistently than these manual edit/rebuild utilities.

### 5. Application callers are inconsistent

The HTTP append-message path explicitly passes `session_asset_store` into `core.add_message(...)`, but the terminal append path does not. Terminal/server modify paths also call `core.modify_message(...)` without a context object.

This means asset-backed native history can be fragile outside the original failing request path too.

## Agreed design requirements

The requested refactor direction from the discussion:

- Use a simple generic protocol for context construction.
- Keep the protocol surface generic and small.
- Avoid registries and avoid a family of builder objects.
- Use only two concrete implementations:
  - one for core
  - one for application
- Create those objects during `AgentCore.__init__` and `AgentApplication.__init__`.
- Keep call-type handling internal to each implementation.
- Accept free-form dict input both:
  - when constructing the long-lived context object
  - when building per-call context
- Keep the internal shape layered:
  - generic layer
  - specific layer per call type
- Make it easy to answer "what does this call path receive?" by opening one file per implementation.

Additional quality bar agreed during the discussion:

- new objects should be easy to add
- duplication should be minimal but not abstracted away so far that the shape becomes hard to audit
- abstraction should stay modest
- migration should be incremental
- existing behavior should be preserved where possible

## Proposed solution

Implement the refactor in two concrete classes and migrate existing helpers to delegate to them.

### Public shape

Add one small shared protocol, for example in `core/python/agent_core/types.py`:

```python
class ContextProtocol(Protocol):
    def build(
        self,
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        ...
```

The protocol should remain generic:

- input is free-form dict-like data
- output is a concrete dict
- no concrete object types appear in the protocol surface

### Concrete implementations

Add exactly two concrete implementations:

1. `CoreContext`
2. `ApplicationContext`

Recommended placement:

- `core/python/agent_core/context.py`
- `core/python/agent_app/context.py`

Each implementation should:

- capture init-time seed data in `__init__`
- expose a single `build(extra=...)` entry point
- internally apply:
  - a generic layer
  - a call-specific layer

The call type can remain an internal implementation detail, for example as a private string key in `extra` or via private helper methods inside core/application. The public protocol must not expose a call-type enum or dedicated profile API.

### Core ownership

In `AgentCore.__init__`, construct one long-lived core context object:

```python
self._context = CoreContext(core=self)
```

Then migrate core internals so request/action/rebuild contexts are derived through that object rather than assembled inline.

Expected call shapes that need explicit internal branches in the core implementation:

- request pipeline
- session action
- lifecycle action
- response finalize
- rebuild/edit

The core implementation is also the right place to standardize internal support objects such as:

- `request_context`
- `request_runtime`

Those should become available consistently on action-style paths, not only on explicit session actions.

### Application ownership

In `AgentApplication.__init__`, construct one long-lived application context object with stable init-time objects seeded once:

```python
self._context = ApplicationContext(
    app=self,
    seed={
        "session_asset_store": self._session_asset_store,
        "runtime_store": self._runtime_store,
        "tool_runtime": self._runtime_store,
    },
)
```

Then migrate application context assembly to route through that object for:

- request entry
- lifecycle
- tool prep / tool execution
- message append
- message edit

### Migration strategy

Perform migration incrementally:

1. Add protocol and concrete classes.
2. Add private core/application helper methods that delegate to the new context objects.
3. Repoint existing inline context construction to those helpers.
4. Only after behavior is stable, simplify/remove now-redundant inline dict assembly.

This keeps the change reviewable and lowers compatibility risk.

## Concrete behavior changes required to fix the bug

The refactor must also close the already-identified functional gaps:

### 1. Request path must receive application-level attachment context

Normal provider request paths must receive context that includes at least:

- `app`
- `application`
- `base_config`
- `session_asset_store`
- `session`
- `session_id`
- `request_id`
- `stream`
- `overrides`

This is required so `openai_responses` can re-expand retained asset-backed tool/image history during ordinary request preparation, not just tool execution.

### 2. Rebuild paths must preserve incoming context

Context must no longer be lost when rebuilding native history after session/lifecycle actions.

In practice that means threading context into:

- `_apply_session_action_result(...)`
- `_rebuild_core_from_native(...)` callers used by action results

### 3. Edit/rebuild utilities must accept context

Manual edit/rebuild paths should be updated to accept optional context and forward it through conversion/rebuild steps:

- `modify_message(...)`
- `rebuild_native_history(...)`

### 4. Lifecycle and response-finalize actions should get request support parity

Action-style core paths should expose the same request-initialization support on all relevant action flows:

- explicit session action
- lifecycle action
- response finalize

That includes consistent availability of:

- `request_context`
- `request_runtime`

## Compatibility expectations

Maintain previous behavior unless widening the context is necessary to fix the bug or to align already-documented expectations.

Important compatibility details to preserve:

- existing caller overrides should continue to win where current code effectively behaves like `setdefault`
- long-lived seeded objects should not accidentally be overwritten unless the path intentionally allows it
- current request/lifecycle/tool semantics should remain intact apart from the missing-context fixes

The safest way to do this is:

- start from caller-provided data
- apply generic layer with `setdefault`-like semantics
- apply specific layer with explicit rules for the keys that must always exist

## Testing requirements

Add or extend tests to cover both the original bug and the wider context behavior:

### Required regressions

- `openai_responses` + asset-backed `view_image` tool result + `request_prepare` lifecycle should no longer fail with missing `session_asset_store`
- normal request path with retained asset-backed native history should also succeed

### Context coverage

Extend application/core context tests so lifecycle actions assert the presence of:

- `session_asset_store`
- `request_context`
- `request_runtime`

Add response-finalize coverage for `request_context` / `request_runtime` parity.

### Edit/rebuild coverage

Add tests for sessions containing asset-backed native history to exercise:

- `modify_message(...)`
- `rebuild_native_history(...)`

### Migration safety

Prefer targeted tests that pin current behavior for non-buggy paths so the refactor does not silently change context precedence or remove previously available keys.

## Likely files to touch

- `core/python/agent_core/types.py`
- `core/python/agent_core/core.py`
- `core/python/agent_core/context.py` (new)
- `core/python/agent_app/application_future.py`
- `core/python/agent_app/context.py` (new)
- `application/python/agent_terminal_app/server.py`
- `application/python/agent_terminal_app/terminal_app.py`
- `application/python/tests/test_feature_plugin_context_enrichment.py`
- `application/python/tests/test_openai_responses_prompt_caching_endpoints.py`
- additional regression test files as needed for edit/rebuild coverage

## Completion target

The finished change should leave the codebase in a state where:

- the original `view_image` asset rebuild bug is fixed
- context shape is easier to audit from one file per implementation
- there are only two concrete context implementations
- both are long-lived objects owned by core/application
- behavior remains compatible except where widened context is the intended fix

## Execution plan

Added during investigation/planning.

### Context ownership policy

- Keep exactly two long-lived concrete builders:
  - `CoreContext`
  - `ApplicationContext`
- Treat context ownership as explicit:
  - each builder owns a reserved set of keys for each call path
  - free-form caller input is allowed for additive keys
  - caller input should not redefine builder-owned keys
- Do not raise on clashes for this refactor.
- Warn on clashes instead, with deterministic precedence:
  - builder-owned values beat caller-provided values
  - call-specific builder values beat generic builder values
- Apply this warning policy inside the concrete context builders so all call paths use one consistent rule.

### Precedence rules to implement

- Build context in three layers:
  - generic owner layer
  - call-specific owner layer
  - caller-provided extra layer
- If the generic owner layer and call-specific owner layer define the same key:
  - keep the call-specific value
  - emit a warning describing the key, call path, and both sources
- If caller-provided extra data defines a builder-owned reserved key:
  - keep the builder-owned value
  - emit a warning describing the key, call path, and that the caller value was ignored
- Only additive caller keys should survive unchanged.
- Avoid silent merging rules such as `setdefault`, `dict.update`, or `{**a, **b}` at call sites once the builders exist; centralize precedence inside the builders.

### Planned refactor steps

1. Add a tiny generic context protocol in `core/python/agent_core/types.py` with a single `build(extra=None) -> dict[str, Any]` shape.
2. Add `core/python/agent_core/context.py` with one concrete `CoreContext` implementation.
3. Add `core/python/agent_app/context.py` with one concrete `ApplicationContext` implementation.
4. Construct one long-lived `CoreContext` in `AgentCore.__init__`.
5. Construct one long-lived `ApplicationContext` in `AgentApplication.__init__`, seeded with stable application-owned objects such as:
   - `app`
   - `application`
   - `base_config`
   - `session_asset_store`
   - `runtime_store`
   - `tool_runtime`
6. Replace inline application context assembly with private helper methods backed by `ApplicationContext`, covering:
   - lifecycle
   - request entry
   - tool preparation / tool loop
   - message append
   - message edit
7. Replace inline core context assembly with private helper methods backed by `CoreContext`, covering:
   - request pipeline
   - session actions
   - lifecycle actions
   - response-finalize actions
   - rebuild/edit flows
8. Remove direct per-call merge logic after the builder-backed helpers are in place, so warning behavior is controlled from one file per owner.

### Reserved-key direction

- `ApplicationContext` should own application-layer keys such as:
  - `app`
  - `application`
  - `base_config`
  - `session_asset_store`
  - `runtime_store`
  - `tool_runtime`
- `CoreContext` should own core/runtime keys such as:
  - `core`
  - `config`
  - `session`
  - `session_id`
  - `request_id`
  - `stream`
  - `trigger_source`
  - `lifecycle`
  - `request_context`
  - `request_runtime`
- Adjust the exact reserved-key list per call path so ownership is clean and builders are not redundantly redefining each other's keys.
- The application-to-core handoff should pass additive extras, not a second copy of keys the core builder already owns.

### Bug-fix changes required during the refactor

- Widen normal request-path context so retained asset-backed native history has access to:
  - `session_asset_store`
  - session/request identifiers
  - effective request metadata needed by providers/extensions
- Preserve incoming context through session-action and lifecycle-triggered rebuilds by threading builder-produced context into:
  - `_apply_session_action_result(...)`
  - `_rebuild_core_from_native(...)`
- Add optional context parameters and forwarding to manual edit/rebuild utilities:
  - `modify_message(...)`
  - `rebuild_native_history(...)`
- Standardize `request_context` / `request_runtime` availability across:
  - explicit session actions
  - lifecycle actions
  - response-finalize actions

### Compatibility guardrails

- Preserve behavior except where widened context is required to fix the identified bug or close the already-documented asymmetry gaps.
- Prefer warning-backed ownership cleanup over caller-visible hard failures for this refactor.
- Keep the migration incremental:
  - introduce builders first
  - delegate existing helpers to builders
  - repoint call sites
  - remove redundant inline merges last

### Test plan

- Extend the prompt-caching / OpenAI Responses request-prepare regression coverage to reproduce the original failure shape:
  - retained native history contains an asset-backed `view_image`-style tool result
  - request-prepare lifecycle triggers a native rebuild / expansion path
  - the request no longer fails for missing `session_asset_store`
- Add a normal request-path regression with retained asset-backed native history so ordinary request preparation also proves the widened context works.
- Extend context-enrichment tests to assert parity for lifecycle and response-finalize paths, including:
  - `session_asset_store`
  - `request_context`
  - `request_runtime`
- Add edit/rebuild regressions for sessions containing asset-backed native history to cover:
  - `modify_message(...)`
  - `rebuild_native_history(...)`
- Add focused assertions for the new warning-backed precedence policy:
  - caller clash with reserved key logs a warning and builder value wins
  - generic/core clash logs a warning and call-specific value wins

### Existing real API baseline verified before implementation

Added during investigation/planning.

- Ran `application/python/tests/test_terminal_default_config_codex_view_image_real_api.py -k openai`
  - passed
  - covers application request flow, Codex tool loop, real `view_image` use, asset-backed tool-result persistence, and a real OpenAI-backed response
- Ran `application/python/tests/test_openai_responses_attachment_endpoints.py -k uploaded_pdf_endpoint_real_api`
  - passed
  - covers real OpenAI Responses attachment handling through the application/server HTTP flow
- Ran `application/python/tests/test_openai_responses_attachment_endpoints.py -k test_openai_responses_add_message_then_send_uploaded_pdf_endpoint_real_api`
  - passed
  - covers a two-call retained-history style flow where a message with an attachment is added first and sent later through the real application/provider stack
- Treat these as end-to-end smoke coverage for the surrounding application behavior, while still adding targeted regression tests for:
  - the exact `request_prepare` + retained native history rebuild bug
  - `modify_message(...)` and `rebuild_native_history(...)` with asset-backed native history

## Completion Notes

Added during implementation.

- Introduced a small shared `ContextProtocol` plus exactly two concrete long-lived builders:
  - `core/python/agent_core/context.py`
  - `core/python/agent_app/context.py`
- Repointed core request, rebuild, session-action, lifecycle-action, response-finalize, and tool-context assembly through the core builder.
- Repointed application lifecycle/tool/request handoff assembly through the application builder.
- Preserved clean ownership by passing application-owned extras into core rather than re-layering core-owned keys at normal handoff boundaries.
- Implemented warning-backed clash handling:
  - call-specific builder keys beat generic builder keys
  - builder-owned keys beat caller-provided duplicates
- Fixed the original `openai_responses` retained-asset rebuild bug by ensuring request/lifecycle rebuild paths carry `session_asset_store` and related application context where needed.
- Added optional context threading for:
  - `modify_message(...)`
  - `rebuild_native_history(...)`
- Updated terminal/server edit and append callers to pass builder-backed application context into core mutation paths.
- Added regression coverage for:
  - prompt-caching request-prepare rebuilds with asset-backed retained native history
  - request/lifecycle/response-finalize request-context parity
  - retained asset-backed native history through `modify_message(...)`
  - retained asset-backed native history through `rebuild_native_history(...)`
- Updated plugin authoring and API docs to document:
  - additive caller context
  - builder-owned reserved keys
  - warning-on-clash behavior
  - `request_context` / `request_runtime` availability on action-style flows

### Verification run

- Passed:
  - `pytest core/python/tests/test_feature_plugin_context_enrichment.py -q`
  - `pytest core/python/tests/test_tool_plugin_context.py -q`
  - `pytest application/python/tests/test_feature_plugin_context_enrichment.py -q`
  - `pytest application/python/tests/test_tool_plugin_context.py -q`
  - `pytest application/python/tests/test_openai_responses_prompt_caching_endpoints.py -q`
  - `pytest application/python/tests/test_openai_responses_session_asset_send_path.py -q`
  - `pytest application/python/tests/test_terminal_default_config_codex_view_image_real_api.py -k openai -q`
  - `pytest application/python/tests/test_openai_responses_attachment_endpoints.py -k 'uploaded_pdf_endpoint_real_api or test_openai_responses_add_message_then_send_uploaded_pdf_endpoint_real_api' -q`
- Not run successfully:
  - `pytest application/python/tests/test_tool_image_asset_messages.py -q`
  - blocked by missing local dependency `mcp_shared` while importing `codex_tools.view_image_tool.ViewImageTool`

## Follow-up plan

Added after review feedback.

### Follow-up checklist

- [x] Remove the unused `ContextProtocol` abstraction from `core/python/agent_core/types.py`.
- [x] Extract the shared context merge logic into `core/python/agent_core/plugin/context_helper.py` under a more specific helper name.
- [x] Rename `core/python/agent_core/context.py` to `core/python/agent_core/core_context.py`.
- [x] Rename `core/python/agent_app/context.py` to `core/python/agent_app/app_context.py`.
- [x] Remove the generic `build(...)` method from the concrete context classes.
- [x] Make the concrete context `__init__` methods accept explicit keyword seeds instead of a generic `seed` mapping.
- [x] Repoint imports and owner wiring to the renamed files and shared helper.
- [x] Keep the current warning-backed precedence behavior unchanged.
- [x] Re-run the focused tests affected by the refactor and update these notes.

### Follow-up execution plan

1. Delete `ContextProtocol` from `core/python/agent_core/types.py` and remove protocol imports/usages from the concrete context files.
2. Create `core/python/agent_core/plugin/context_helper.py` with a shared helper named `merge_context_layers(...)` that owns:
   - generic-layer application
   - call-specific overwrite with warning
   - caller-extra additive merge with warning on reserved-key clashes
3. Rename the concrete files:
   - `core/python/agent_core/context.py` -> `core/python/agent_core/core_context.py`
   - `core/python/agent_app/context.py` -> `core/python/agent_app/app_context.py`
4. Update `CoreContext` and `ApplicationContext` so they:
   - keep only explicit `build_request_context(...)` / `build_lifecycle_context(...)` / etc.
   - no longer expose a generic `build(...)`
   - use explicit keyword-only constructor seeds instead of `seed=...`
5. Update `AgentCore` and `AgentApplication` imports/construction to match the renamed files and constructor signatures.
6. Remove any now-unused generic-builder code paths while preserving the existing behavior and warning semantics.
7. Re-run the focused tests around context enrichment and the OpenAI Responses regressions.

### Follow-up completion notes

Added after implementation.

- Removed `ContextProtocol` from `core/python/agent_core/types.py`.
- Added the shared helper `merge_context_layers(...)` in `core/python/agent_core/plugin/context_helper.py`.
- Renamed the concrete builder files to:
  - `core/python/agent_core/core_context.py`
  - `core/python/agent_app/app_context.py`
- Removed the unused generic `build(...)` methods.
- Switched the concrete constructors to explicit keyword-owned base context inputs.
- Repointed `AgentCore` and `AgentApplication` to the renamed files/helper without changing the warning-backed precedence behavior.
- Also corrected `application/python/tests/test_tool_image_asset_messages.py` to load `codex-tools` through the plugin manager (`path:` spec) so sibling dependency installation (`mcp-shared`) actually runs.

### Follow-up verification

- Passed:
  - `pytest core/python/tests/test_feature_plugin_context_enrichment.py -q`
  - `pytest application/python/tests/test_feature_plugin_context_enrichment.py -q`
  - `pytest application/python/tests/test_openai_responses_prompt_caching_endpoints.py -q`
  - `pytest application/python/tests/test_openai_responses_session_asset_send_path.py -q`
  - `pytest application/python/tests/test_tool_image_asset_messages.py -q`