# Generic Tool Call Interceptor Capability

Add a generic, provider-neutral interceptor capability to the application tool loop (`ToolLoopRunner` in `agent_app`) so provider extensions can observe, modify, and short-circuit tool calls before and after execution without embedding provider-specific logic in the application layer.

## Requirements checklist

- [ ] Define a generic interceptor protocol in `agent_app` with pre-execution and post-execution hooks supporting parameter modification, short-circuit (any result), and result modification.
- [ ] `ToolLoopRunner` consults interceptors and applies their decisions as a thin orchestrator with no provider-specific knowledge.
- [ ] `AgentApplication` discovers interceptors from active provider extensions and passes them to `ToolLoopRunner`.
- [ ] Interceptors are provider-scoped: non-active providers' interceptors are never consulted.
- [ ] A per-phase state object is maintained by `ToolLoopRunner`, reset per LLM phase, and made available to interceptors via namespaced keys.
- [ ] Direct calls (no interceptors or all defer) behave identically to today (regression-safe).
- [ ] The post-execution hook is invoked for every tool message: executed, short-circuited, and "no tool handled" errors.
- [ ] Handle `inspected_call is None` gracefully.
- [ ] Focused unit tests with no provider-specific references.
- [ ] Existing application and core test suites pass with no regressions.
- [ ] Document the capability as a generic application-layer extension point.

## Goal

Add a generic, provider-neutral interceptor capability to the application tool loop (`ToolLoopRunner` in `agent_app`) that allows provider extensions to observe, modify, and short-circuit tool calls before and after execution. This keeps `ToolLoopRunner` free of provider-specific logic while enabling provider-specific features (such as OpenAI Responses Programmatic Tool Calling) to enforce per-call policies, modify call parameters, and modify or synthesize results through a standard hook.

The exact protocol shape (class names, method names, dataclass shapes) is left to the implementer. The requirements below describe what the capability must support, not how it is named.

## Requirements

1. **Interceptor protocol with three capabilities**:
   - **Pre-execution parameter modification**: an interceptor can modify the tool call's parameters (payload) before the tool executes, without changing the call identity (`call_id`, `tool_name`) or provider-specific metadata.
   - **Pre-execution short-circuit**: an interceptor can return a full tool-result message (success, error, or any other shape) instead of executing the tool, for any reason the interceptor decides — not limited to errors.
   - **Post-execution result modification**: an interceptor can observe or modify the tool-result message after execution or after short-circuit, before it enters the session.

2. **Thin orchestrator**: `ToolLoopRunner` consults registered interceptors before and after each tool call and applies their decisions (proceed, proceed with modified parameters, short-circuit with result, post-execution modification) without understanding the semantics. All decision logic, parameter modification, and result synthesis live in the interceptor implementations. `ToolLoopRunner` is a thin orchestrator that calls hooks and applies their results.

3. **Provider scoping**: Interceptors are discovered per-request from the active provider's extensions. Interceptors from non-active providers are never consulted. This ensures an OpenAI Responses interceptor does not affect an Anthropic request, etc. The discovery mechanism (method name, registration path) is left to the implementer.

4. **Per-phase state**: `ToolLoopRunner` maintains a per-phase state object (reset at the start of each LLM phase) and makes it available to interceptors. Interceptors use namespaced keys to track per-phase state. `ToolLoopRunner` does not interpret the contents.

5. **Provider neutrality**: `ToolLoopRunner` does not reference any provider-specific config keys, metadata keys, tool names, or concepts. It only calls interceptor hooks and applies their results.

6. **Regression safety**: When no interceptors are registered, or all interceptors defer (return no opinion), the tool loop behaves identically to today. Direct calls are unaffected.

7. **Post-execution coverage**: The post-execution hook is invoked for every tool message produced by the loop: executed calls, short-circuited results, and "no tool handled" errors. Interceptors can observe and modify all of them.

8. **Edge cases**: The loop handles `inspected_call is None` (malformed call dicts) gracefully — it falls through to the existing "no tool handled" synthesis and still invokes the post-execution hook.

9. **Tests**: Focused unit tests for the generic capability, with NO references to any provider-specific concept (no `programmatic_tool_names`, no `openai_responses_caller`, no OpenAI Responses). Tests cover: pre-execution proceed, pre-execution with modified parameters, pre-execution short-circuit with a success result, pre-execution short-circuit with an error result, post-execution modification, post-execution chaining (multiple interceptors), per-phase state reset, non-active-provider isolation, `inspected_call is None` handling, and regression safety for direct calls.

## Definition of done

- A generic interceptor protocol exists in `agent_app` with pre-execution and post-execution hooks supporting parameter modification, short-circuit (any result), and result modification.
- `ToolLoopRunner` consults interceptors and applies their decisions as a thin orchestrator with no provider-specific knowledge.
- `AgentApplication` discovers interceptors from active provider extensions and passes them to `ToolLoopRunner`.
- Generic unit tests pass with no provider-specific references.
- Existing application and core test suites pass with no regressions.
- The capability is documented as a generic application-layer extension point.
- A provider-specific feature (the 070 Programmatic Tool Calling task) can implement its interceptor using this capability without further `agent_app` changes.

## Out of scope

- Any provider-specific interceptor implementation (belongs in provider-specific tasks like 070).
- Phase-level hooks (pre-phase / post-phase) — not needed unless a concrete use case requires them.
- Wrap-style try/finally interception — not needed; pre + post covers the use cases.
- Call identity modification (`call_id`, `tool_name`) — interceptors modify parameters, not identity.
- Tool plugin changes — the interceptor operates at the tool-loop level, not the tool-plugin level.

## Dependencies

- This task is a **prerequisite** for `tasks/20260713-openai-responses-gpt-5-6-support/070-programmatic-tool-calling.md`. The 070 task's allowlist enforcement, per-phase call limit, and caller preservation on short-circuited results depend on this interceptor capability. The 070 task references this task as a dependency and implements only the provider-specific interceptor.