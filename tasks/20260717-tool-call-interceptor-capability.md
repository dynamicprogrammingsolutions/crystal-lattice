# Generic Tool-Call Interceptor Capability

Add a generic provider-neutral tool-loop hook that can inspect, modify,
short-circuit, and post-process tool calls without owning notification,
interaction, waiting, or request-continuation semantics.

## Requirements checklist

### Functional requirements

- [ ] Active provider extensions can contribute pre-execution and
  post-execution tool-call interceptors.
- [ ] A pre-execution interceptor can observe a call and allow it unchanged.
- [ ] A pre-execution interceptor can modify call parameters without changing
  call identity or provider metadata.
- [ ] A pre-execution interceptor can short-circuit execution with a complete
  success, error, pending, or other valid tool result.
- [ ] Post-execution interceptors can observe or replace executed,
  short-circuited, and unhandled-call results before persistence.
- [ ] Multiple interceptors compose in deterministic order.
- [ ] Interceptors receive namespaced per-phase state that resets for each LLM
  phase.
- [ ] Only interceptors contributed by the active provider/extensions
  participate.
- [ ] Malformed or uninspectable calls retain existing unhandled-call behavior
  and still pass through post-processing.

### Non-functional requirements

- [ ] `ToolLoopRunner` remains provider-neutral and interprets only generic
  interceptor decisions.
- [ ] No-interceptor and all-defer behavior remains compatible with the
  existing tool loop.
- [ ] Interceptor state cannot leak across phases, requests, sessions, or
  provider instances.
- [ ] Interceptor failures have explicit containment behavior and cannot leave
  partially persisted tool results.
- [ ] Generic contract tests contain no provider-specific names, metadata, or
  policy assumptions.
- [ ] The capability remains independently useful for provider policy and
  interactive request-suspension consumers.

## Scope

The interceptor is an execution hook only. It does not implement:

- notification or interaction persistence;
- user-response actions or forms;
- timeout or cancellation policy;
- waiters or background processes;
- request restart/continuation;
- provider-specific allowlists or programmatic-tool policy.

Those behaviors belong to consumers such as:

- `tasks/20260824-interactive-notifications-and-request-suspension/000-main.md`
- `tasks/20260713-openai-responses-gpt-5-6-support/070-programmatic-tool-calling.md`

## Supporting facts

- `ToolLoopRunner` is the application-owned tool execution orchestrator.
- Active provider extensions are available while each request core/tool loop
  is built.
- The prior task design remains conceptually valid but predates current shared
  request coordination, operation admission, and notification interaction
  planning.
- Interactive tool approval requires a pre-execution hook, but its persisted
  lifecycle must remain in the notification/interaction service.

## Execution plan

Status: Draft

Define small immutable pre/post decision types in `agent_app`. Discover
interceptors from active provider extensions when the request tool loop is
constructed. Apply pre decisions in order, preserving call identity and
provider metadata while allowing parameter replacement or complete
short-circuit.

Pass every produced tool result through post interceptors, including executed,
short-circuited, and existing unhandled-call error results. Maintain one
namespaced phase-state mapping owned by the tool loop and reset it at the
current LLM-phase boundary.

Add generic unit/application tests first. Exercise the capability through one
real provider-specific consumer only after the generic contract is stable; do
not move consumer policy into `agent_app`.

### Implementation decisions and open questions

- Decision: call identity is immutable.
- Decision: pre short-circuit supplies a complete normal tool-result message.
- Decision: post interceptors compose in registered order.
- Recommendation: interceptor exceptions fail the affected call through a
  stable tool error while preserving request/tool-loop cleanup; approve during
  implementation planning.

### Documentation

- Add an application-layer interceptor development guide or extend the owning
  tool-loop guide.
- Update provider-extension authoring docs with generic pre/post examples and
  explicit scope exclusions.
- Cross-link interaction and provider-specific consumers without duplicating
  their semantics.

### Task checklist

- [ ] Approve decision types, ordering, and failure containment.
- [ ] Add generic interceptor protocols/types.
- [ ] Add active-provider discovery and tool-loop wiring.
- [ ] Implement pre parameter replacement and short-circuit.
- [ ] Implement post-processing for every tool-result path.
- [ ] Add per-phase namespaced state.
- [ ] Add generic unit and application integration tests.
- [ ] Verify one real consumer without `agent_app` policy leakage.
- [ ] Run core/application regression suites and update documentation.

### Requirement verification

- Tests prove defer, parameter modification, success/error/pending
  short-circuit, post replacement, chaining, and phase reset.
- Non-active provider interceptors are never called.
- Uninspectable calls preserve existing result behavior and receive post
  processing.
- No-interceptor application flows remain unchanged.

### Additional implementation verification

- Cancellation and exception paths release phase/interceptor state.
- Modified parameters preserve original call ID, tool name, and opaque
  metadata.
- Interceptor order is stable across plugin discovery and application reload.