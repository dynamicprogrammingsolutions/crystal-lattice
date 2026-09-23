Parent Task: tasks/20260922-duration-and-human-time-tracking/000-main.md

# Tool Call Duration

Add the general framework act-point around tool calls (execution-scoped `prepare_tool_call`/`finalize_tool_call` plus append-scoped `prepare_appended_message`) and stamp per-tool-call and per-turn tool duration on tool-result messages, including the timestamp workaround correction. Measurement is plugin-owned; the framework only provides hook points and context-carried facts. No store is involved in this subtask — store rows and store-backed tool totals are subtask 025 (phase 2, with the store from 010).

## Requirements checklist

- [ ] Tool call duration measurement is owned by a plugin; the framework does not compute durations, stamp duration fields onto tool messages, or record tool stats.
- [ ] The framework provides a general way for plugins to act around tool calls, not only after LLM responses; expanding the existing prepare/finalize contracts is the chosen shape.
- [ ] The tool-call prepare hook lets plugins transform the tool call before execution (sanitizing and interception are planned use-cases); the framework re-inspects the transformed call before executing it.
- [ ] Provider (LLM) call contexts carry the same raw started/finished timestamp facts as tool-call contexts, for symmetry; plugins own the measurement in both scopes.
- [ ] Framework-provided facts (e.g. execution timestamps, tool call descriptors) reach plugins via context; the framework does not modify tool messages directly on the plugins' behalf.
- [ ] The new mechanism replaces the `TimestampExtension` single-message `to_native_messages` append workaround (append-time stamping migrates to the new hook).
- [ ] Per-tool-call duration is stamped on the corresponding tool-result message metadata by the duration measurement plugin and flows to frontends through the existing tool events (`tool_partial` end, `tool_results`).
- [ ] Per-turn tool call duration (sum of tool-call durations within the current turn) is stamped on tool-result message metadata, computed from the session history available in the tool-call context — no store required.
- [ ] Existing LLM duration fields and semantics remain unchanged; tool call duration uses separate fields, not merged into LLM duration.
- [ ] The mechanism works for all providers and all tool plugins without per-tool changes, in streaming and non-streaming requests.

## Supporting details

### Facts: current tool execution path

- `AgentCore.iter_tool_messages` (core.py:4507) executes each call: `registry.inspect_call` → `_resolve_tool_handler_for_call` → `_build_tool_runtime_context(config, context)` → `tool.stream_tool(...)` with that context → `format_tool_result` → builds the final core tool message with core-managed metadata (`tool_call_id`, `tool_name`, `tool_schema`, `tool_plugin`, `display`) merged with tool-supplied `result["metadata"]` (core.py:4720–4730). It yields partial payloads (`part`) and the final tool message; it has no plugin hook points beyond the owning tool plugin.
- `ToolLoopRunner._apply_tool_calls` (tool_loop.py:380) drives the loop per call: iterates `core.iter_tool_messages([call], ...)`, keeps the last final, appends it via `core.add_message` (tool_loop.py:503), emits `tool_partial` start/stream/end events and one aggregate `tool_results` event carrying the tool messages (tool_loop.py:530–536), then a `session_checkpoint`. Metadata stamped before these events is visible to frontends for free.
- The tool context already flows end-to-end: the app builds it via `build_tool_context(session, request_id, base_config, config, extra)` (tool_loop.py:429–439) and core enriches it via `_build_tool_runtime_context` (core.py:4596). `add_message` also accepts a `context` argument (core.py:667).
- `add_message` appends through `_append_single_message_with_native`, which converts the single message via `to_native_messages` — this is the conversion hook `TimestampExtension` abuses as an append hook.
- Append-path inventory: in the app layer `add_message` is called only from `request_execution.py:330` (user/system messages) and `tool_loop.py:503` (tool results). Assistant finals enter the session through the request pipeline's native-history rebuild, not `add_message`. So an append-scoped act-point covers exactly user/system + tool messages — precisely the messages the timestamp workaround covers (assistant messages are stamped in `finalize`).
- Tool result metadata survives native conversion (core metadata → native `_metadata`), so plugin-stamped duration persists in retained history and is visible to later requests.
- The tool context carries the full session: `build_tool_context` puts `session.to_dict()` (including `messages`) into the context (app_context.py:186–203), and the tool loop rebuilds it per call with the current session (tool_loop.py:429–439). A `finalize_tool_call` implementation can therefore compute per-turn tool duration by scanning already-appended tool messages since the last turn separator — the same scan pattern `DurationExtension` uses for LLM turn totals (`_sum_assistant_durations_since_turn_start`) — and adding the current call. Only `role == "tool"` messages are scanned, so tool-duration fields cannot be confused with LLM duration fields on assistant messages.

### Facts: stamping ownership (phase 1)

- Recommended owner (confirm at plan approval): `DurationExtension` implements `finalize_tool_call`, keeping all duration measurement in the established duration plugin (010's "measurement stays in `DurationExtension`" principle). Phase 1 then touches only core and the timestamp-extension package; the `plugins/duration-tracking` package does not exist until the store phase.
- The stamps use the same field names as the assistant-message convention (`duration_ms`, `duration_formatted`, `duration_started_at`, `duration_finished_at`) plus `turn_tool_duration_ms`/`turn_tool_duration_formatted` for the turn total, mirroring `turn_duration_ms` (LLM-only) — distinct fields, never merged.
- Existing `message_footer` elements declared by `DurationExtension` (`metadata.duration_formatted` etc.) may start rendering on tool messages once they carry the fields; the plan must verify the footer conditions/config gating so tool durations surface intentionally (e.g. a `tool duration:` footer) rather than accidentally.
- Phase 2 (subtask 025) records store rows from these stamps in the same `finalize_tool_call` chain: the duration-tracking extension runs after `DurationExtension` (priority order) and reads the stamps from the message it receives — the cost pattern (usage extension stamps, cost extension records).

### Facts: the timestamp workaround to improve

- `TimestampExtension.to_native_messages` (timestamp_extension.py:50–93) detects "a single newly-appended message" via `len(messages) == 1` plus absence of `native_indices`, and allocates the `timestamp` there; the docstring itself warns about index-misalignment bugs with synthetic native messages. It exists because `to_native_messages` on the single-message append path is the only append-time hook today. User messages and tool results both rely on it.
- `TimestampExtension.finalize` stamps assistant finals separately (timestamp_extension.py:130–177) — the LLM-response path already has its act-point; the append path does not.

### Facts: the prepare/finalize precedent to expand

- `DurationExtension` shows the established prepare/finalize shape: `initialize_request` records start facts in shared state; `finalize` computes the measurement and stamps the owner message. Extensions/features are priority-sorted (lower first, provider.py:222–232); features finalize after provider + extensions (core.py:2455–2471).
- Shared provider state carries `_request_context` with `session_id`/`request_id` (provider.py:234). Tool plugins keep separate tool state; features/extensions share provider state.
- The superseded task's lifecycle-action design (application + feature actions with full-session rewrite freedom, reentrant session lock, same-thread save adoption, authoritative-session replacement) is recorded in `tasks/20260801-duration-and-stats-tracking/010-framework-stats-infrastructure.md`; it was assessed as far heavier than timing needs.

## Execution plan

Status: Approved

Approved by the user on 2026-09-22: mechanism (Direction C), protocol surface, phasing, testing strategy, and the test-first chunked implementation below. This subtask executes first (phase 1), before 010.

This plan records the hard constraints, the agreed mechanism (Direction C) and protocol surface, the approved testing strategy, and the test-first chunk breakdown.

### Hard constraints (from the direction decision)

1. Plugin owns measurement and stats. The framework may put raw facts into the context (e.g. `started_at` wall-clock and monotonic timestamps, tool call descriptor, session/request ids); it must not compute `duration_ms`, stamp duration fields, or write stats.
2. The mechanism is general: any plugin that needs to act around tool calls can use it, symmetric with how plugins already act around LLM responses (`initialize_request`/`finalize`).
3. The mechanism must also give `TimestampExtension` a proper append-time act-point so its `to_native_messages` workaround can be retired or reduced.
4. Whatever the tool loop itself contributes goes into the context, never by mutating the tool message directly.

### Candidate directions

**Direction A — per-tool-call prepare/finalize hooks on the request-pipeline plugin kinds.**
Add optional protocol hooks (working names `prepare_tool_call` / `finalize_tool_call`) to `FeaturePlugin` and possibly `ProviderExtensionPlugin`, dispatched in priority order around each tool execution, mirroring `initialize_request`/`finalize`. `finalize_tool_call` receives the final tool message (and call descriptor, shared state, context with framework facts) and returns a transformed message; the loop adopts the transformed message before appending and emitting events. The duration plugin records its own start (prepare) or reads a context-carried `started_at`, computes `duration_ms` in finalize, stamps the tool message, and records the store row.
Open sub-decisions:
- A1 Dispatch level: core `iter_tool_messages` (available to every core consumer, but the final message is yielded mid-generator and the app loop owns append/events) vs app `ToolLoopRunner._apply_tool_calls` (owns append + event emission; the natural place to guarantee stamp-before-event ordering; but core-only consumers would not get the hooks).
- A2 Whether prepare is needed at all: a context-carried `started_at` (framework fact, allowed) makes a finalize-only hook sufficient for duration; a prepare hook enables plugin-owned clocks and pre-execution facts at the cost of a second dispatch point.
- A3 Which plugin kinds participate: features only (simplest; matches where duration lives), features + provider extensions (symmetry with the LLM pipeline), and/or application plugins via a callback (adds the app-layer dispatch the superseded task designed).
- A4 Hook result shape: return a replacement message (immutable convention) vs receive a mutable draft; and whether the hook may also return state updates like `finalize` does.

**Direction B — general message-append hook.**
Dispatch a hook whenever `add_message` appends a message (any role), receiving the appended core message, the converted native message, and the append context. `TimestampExtension` migrates its timestamp allocation there, retiring the `to_native_messages` workaround for both user messages and tool results. Tool duration rides the append hook for tool results: the context (already flowing to `add_message`) carries the framework-provided `started_at` facts, and the duration plugin computes and stamps at append time.
Open sub-decisions:
- B1 Dispatch level: inside `add_message` (covers every append: user, tool, assistant saves) vs only in the tool loop (tool results only).
- B2 Hook signature: core message, native message, or both; and how the transformed result flows back into the append (the native-preserving helper owns the conversion).
- B3 Whether an append hook alone is enough for tool duration (no execution-scoped facts beyond `started_at` in context) or whether execution-scoped prepare/finalize is still wanted for other plugin needs.

**Fact shaping B**: the append scope (user/system + tool messages) is exactly the timestamp workaround's scope, and assistant messages already have their act-point (`finalize`). A single append hook therefore retires the workaround completely and gives every message entry point a plugin act-point; duration needs no execution-scoped hook because the tool loop can carry `started_at` facts in the context it already passes to `add_message`.

**Direction C — combined contract. — CHOSEN (user, 2026-09-22)**
Execution-scoped per-tool-call hooks (Direction A) for measurement and tool-call facts, plus an append-scoped hook (Direction B) for message stamping; the timestamp fix lands in the append hook, the duration measurement in the tool-call hooks. Expressed as new optional hooks on the request-pipeline plugin protocols. Rationale: cleanest separation of the two scopes for a protocol-touching change — execution facts and message-entry stamping are distinct concerns with distinct consumers (duration plugin: execution scope; timestamp plugin: append scope), and both become first-class, symmetric with the existing request lifecycle (`initialize_request`/`finalize` for LLM responses).

**Direction D — recorded alternative, not preferred.**
The superseded task's lifecycle actions with full-session rewrites (`tool_call_prepare`/`tool_call_complete` triggers, reentrant lock, save adoption). Heavy for timing; stays on record as a future option if plugins need arbitrary session transformations per tool call.

### Agreed protocol surface (user, 2026-09-22)

Three new optional hooks on both `ProviderExtensionPlugin` and `FeaturePlugin`, with default no-op implementations (no existing plugin breaks). Dispatch order everywhere: extensions before features (mirroring the request pipeline), priority-sorted within each kind (lower first); shared state is threaded through the chain so chained plugins read each other's state, and priority handling applies to all hook calls.

**`prepare_tool_call(tool_call, state, *, context) -> Tuple[tool_call, state]`**

- Dispatch: `AgentCore.iter_tool_messages`, after the initial `registry.inspect_call` (which supplies the context facts), before handler resolution and `tool.stream_tool`.
- The returned tool call replaces the one about to execute — sanitizing and interception are planned use-cases. The framework re-inspects the transformed call before resolving the handler; a transformed call that no longer inspects follows the existing synthesized-error path. Transformers own correlation: the tool-result message's `tool_call_id` reflects the transformed call, so a plugin that changes the id is responsible for keeping the call correlatable with the assistant's tool call.
- Context facts: `tool_call_id`, `tool_name`, `tool_plugin`, `started_at` (ISO UTC), `started_at_mono`, plus `session_id`/`request_id` from the caller's context.

**`finalize_tool_call(tool_message, state, *, context) -> Tuple[tool_message, state]`**

- Dispatch: `iter_tool_messages`, after the final tool message is built — the success path and both synthesized-error paths — immediately before yielding; therefore before the app loop appends it or emits `tool_partial` end / `tool_results`. Covers `execute_tool_calls` automatically (it wraps `iter_tool_messages`, core.py:4750).
- Runs for synthesized results too; the context carries a `tool_error` fact in those cases.
- Context facts: the prepare facts plus `finished_at`, `finished_at_mono` captured immediately after execution.
- The duration measurement plugin measures here (from the context facts or its own clock), stamps per-call duration and per-turn tool duration onto the tool message metadata, and returns the stamped message. Store-row recording from these stamps is subtask 025 (phase 2); in this subtask the hook chain ends with the stamped message.

**`prepare_appended_message(message, state | None, *, context) -> Tuple[message, state]`**

- Dispatch: `AgentCore.add_message`, end-appends only — `after_index` inserts are excluded; normal calls only use simple append. Runs before `_append_single_message_with_native` converts the message, so stamped core metadata persists into native `_metadata` through the conversion. No dispatch on the legacy no-config path.
- Takes and returns shared state like the other hooks (chained plugins read each other's state); the final state flows back to the provider wrapper, not the session — `add_message` stays a pure Session → Session function.
- Context facts: `session_id`, `request_id` when available; for appended tool results, the full tool-call fact set (call descriptor, started/finished timestamps).
- The timestamp plugin migrates here for user/system and tool messages, retiring the `to_native_messages` workaround entirely; assistant finals keep using `finalize`.

**Provider-call symmetry**

The same raw timestamp facts are added to provider (LLM) call contexts: `initialize_request` contexts gain `started_at`/`started_at_mono` captured before the request pipeline starts, and `finalize` contexts gain `finished_at`/`finished_at_mono` captured after the provider call completes. Plugins own the measurement in both scopes; `DurationExtension` may keep its own clock or read the facts (additive, no behavior change required).

**Framework-owned facts, plugin-owned measurement (both scopes)**

Raw timestamps (wall-clock ISO + `time.monotonic()`), tool call descriptor, session/request ids go into the context. Never in framework code: computed durations, stats, or direct message mutation.

### Approved testing strategy (user, 2026-09-22)

Test realism: everything through public boundaries (real `AgentCore.iter_tool_messages`/`execute_tool_calls`/`add_message`, real `AgentApplication.send_request`), fixture plugins instead of internal mocks, deterministic where possible (injected context facts, no sleeps), regression coverage for touched behavior.

- **Group A — framework hook contract** (`core/python/tests/test_tool_call_lifecycle_hooks.py`, fixtures in `core/python/tests/fixtures/`): backward compatibility (plugins without the hooks work); `prepare_tool_call` dispatch (per-call, pre-execution, context facts, no duration keys, ordering, state threading, sanitizing/interception with re-inspection, broken transformation → synthesized error); `finalize_tool_call` dispatch (exactly once per call on all four yield paths, `tool_error` fact, chained transforms, finished facts, `execute_tool_calls` coverage); `prepare_appended_message` dispatch (end-appends, transform lands in the session, native `_metadata` persistence + round-trip, tool-result facts, ordering/state threading/state back to the wrapper, no fire for `after_index` inserts, no fire on the no-config path); provider-call context symmetry (started facts in `initialize_request` contexts, finished facts in `finalize` contexts, no duration keys). No-framework-timing is source inspection evidence at review.
- **Group B — plugin units** (`plugins/timestamp-extension/tests/`): `DurationExtension.finalize_tool_call` (per-call stamping from injected fixed facts, graceful missing facts, turn accumulation, `role == "tool"`-only scan, malformed history); existing LLM tests stay green unmodified; footer/UI schema test; `TimestampExtension` migration (`prepare_appended_message` stamps, `to_native_messages` returns unchanged, end-to-end append stamping, assistant `finalize` unchanged).
- **Group C — integration**: `application/python/tests/test_application_tool_duration_stamping.py` — realistic `AgentApplication.send_request` with a tool-calling provider fixture and a real tool plugin: events (`tool_partial` end, `tool_results`), checkpoint session, and persisted reload all carry stamped metadata; multiple sequential calls; streaming and non-streaming; cancellation dispatches finalize via the synthesized-error path. Provider follow-up default suites (openai_responses, reference provider, openrouter) stay green.
- **Commands**: `pytest core/python/tests -q`, `pytest application/python/tests -q`, `pytest plugins/timestamp-extension/tests -q`, the three provider suites, ruff/black on changed files, pyright.

**Contract details pinned with the testing strategy:**

1. `prepare_tool_call` fires only for inspectable calls (a failed inspection has no facts and goes straight to the synthesized error); `finalize_tool_call` fires exactly once per call, on the single final message every call yields. Invariant: prepare once per inspectable call, finalize once per call.
2. Cancellation needs no special case: a cancelled/errored call that produced no result reaches the existing synthesized-error path and finalize fires there with `tool_error`. No cleanup-only dispatch.

### Test-first implementation chunks

Each chunk: write the tests first, verify they fail, implement, verify green.

1. **Protocol surface + wrappers** — red: protocol tests (both protocols expose the three hooks with default no-ops; `ExtensionWrapper`/`FeatureWrapper` pass through to the wrapped plugin; backward-compat guard for hookless plugins). Green: add the methods to `types.py` and pass-throughs to `plugin/extension.py`/`plugin/feature.py`.
2. **Tool-call dispatch in `iter_tool_messages`** — red: group A2/A3 tests. Green: resolve extensions + features via `_resolve_plugins_for_config`, capture started facts, prepare chain with re-inspection, capture finished facts, finalize chain before each of the four yield paths.
3. **Append dispatch in `add_message`** — red: group A4 tests. Green: dispatch on end-appends before `_append_single_message_with_native`, state back to the provider wrapper, skip no-config path and `after_index` inserts.
4. **Provider-call context facts** — red: group A5 tests. Green: started facts at request-context build, finished facts before the finalize chain.
5. **`DurationExtension` tool stamping** — red: B1 unit tests, B3 UI test, C1 integration test. Green: `finalize_tool_call` implementation (per-call + per-turn stamping) plus intentional footer elements.
6. **`TimestampExtension` migration** — red: B4 tests (including `to_native_messages` returning unchanged, which fails while the workaround exists). Green: migrate stamping to `prepare_appended_message`, remove the workaround.
7. **Full sweep + docs** — all suites (core, application, timestamp-extension, three provider suites), ruff/black/pyright, 020-scoped doc updates (timestamp-extension README, hook contract in plugin docs).

### Implementation decisions and open questions

- **Resolved — mechanism choice (user, 2026-09-22)**: Direction C, the combined contract. Execution-scoped per-tool-call hooks plus an append-scoped message hook, both dispatched at core level: the tool-call hooks in `AgentCore.iter_tool_messages` (covers the app tool loop and direct core consumers; the transformed message is what gets yielded, appended, and emitted in events), the append hook in `AgentCore.add_message` end-appends (covers the user/system and tool-result call sites). The duration measurement plugin measures and stamps in `finalize_tool_call`; the timestamp plugin migrates fully off the `to_native_messages` workaround onto the append hook.
- **Resolved with the mechanism — timestamp workaround scope**: retire entirely (the append hook covers user/system + tool messages, matching the workaround's exact scope).
- **Resolved — recording seam**: the store row is recorded at `finalize_tool_call` from the stamped message (measurement and row created together; no history scanning). With the phasing split, recording is subtask 025's scope: the duration-tracking extension hooks `finalize_tool_call` after `DurationExtension` (priority order) and records from the stamps it receives in the chain.
- **Resolved — execution phasing (user, 2026-09-22)**: this subtask is phase 1 and has no store dependency — it delivers the framework hooks, per-call and per-turn tool duration stamping, and the timestamp fix. Store rows and store-backed tool totals moved to new subtask 025, which depends on 010 and 020; 010 and 025 execute together in the store phase so the schema is designed once with both LLM and tool rows. 030 (human time) is report-only and depends only on 010.
- **Recommended, confirm at plan approval — stamping owner**: `DurationExtension` implements `finalize_tool_call` (all duration measurement stays in the established duration plugin; phase 1 touches only core and the timestamp-extension package; no new package until the store phase). Per-turn tool duration is computed by scanning `role == "tool"` messages in `context["session"]["messages"]` since the last turn separator, plus the current call — the same scan pattern as its LLM turn totals.
- **Resolved — hook surface (user, 2026-09-22)**: names `prepare_tool_call`, `finalize_tool_call`, `prepare_appended_message`; placed on both `ProviderExtensionPlugin` and `FeaturePlugin` (symmetric with the request lifecycle hooks); optional with default no-op implementations; dispatch order extensions → features, priority-sorted within each kind; state threaded through every chain.
- **Resolved — prepare may transform the call (user, 2026-09-22)**: `prepare_tool_call` returns `(tool_call, state)`; sanitizing and interception are planned use-cases. The framework re-inspects the transformed call before handler resolution; a non-inspectable transformed call follows the existing synthesized-error path; transformers own call correlation.
- **Resolved — append hook carries state (user, 2026-09-22)**: `prepare_appended_message` takes and returns shared state so chained plugins can read each other's state; priority handling applies to all hook calls; the final state flows back to the provider wrapper, not the session.
- **Resolved — insert appends excluded (user, 2026-09-22)**: the append hook fires for end-appends only; normal calls only use simple append.
- **Resolved — context facts (user, 2026-09-22)**: both started-at and finished-at facts (wall + monotonic) are provided in tool-call contexts, and the same facts are added to provider-call contexts (`initialize_request`/`finalize`) for symmetry. Plugins own the measurement in both scopes.
- No open contract decisions remain. The plan awaits approval; this subtask executes first (phase 1), before 010.
- Not open (already decided): plugin-owned measurement and stats; context-carried framework facts; separate fields from LLM duration; works across providers and tools. Store rows and store-backed totals are 025's requirements (same store and method as 010).

### Documentation

- Plugin docs for the new hook contract (likely `plugins/docs/feature-plugins.md` / `plugins/docs/provider-extensions.md` and, if app plugins participate, `plugins/docs/application-plugins.md`): hook names, ordering, context facts, result shape, and the "framework provides facts via context, plugins own measurement" rule.
- `plugins/timestamp-extension/README.md`: document the migrated append-time stamping and remove the workaround description.
- `plugins/duration-tracking/README.md` (with 010/030): tool-duration fields, config, and report columns.
- Core/tool-loop docstrings for the dispatch points.

### Task checklist

- [x] Obtain plan approval (mechanism, protocol surface, phasing, testing strategy, and test-first chunks approved 2026-09-22)
- [x] Add the three optional hooks to `ProviderExtensionPlugin` and `FeaturePlugin` with wrapper pass-throughs and default no-ops (chunk 1: red 9 → green 10; core suite 541 green)
- [x] Dispatch `prepare_tool_call`/`finalize_tool_call` in `iter_tool_messages` with context facts, call re-inspection after transformation, and the synthesized-error paths covered (chunk 2: red 9 → green 20; core suite 551 green; black applied)
- [x] Dispatch `prepare_appended_message` in `add_message` end-appends with state threading back to the provider wrapper; no dispatch on the no-config path (chunk 3: red 5 → green 27; app tool loop reuses one per-call context so tool-call facts flow to the append hook)
- [x] Add started/finished timestamp facts to provider-call contexts (`initialize_request`/`finalize`) for symmetry (chunk 4: red 2 → green 29; facts on request contexts only, rebuild contexts stay fact-free)
- [x] Implement per-call tool duration stamping in the duration measurement plugin (`finalize_tool_call`) (chunk 5: red 8 → green 19 in the package suite)
- [x] Implement per-turn tool duration stamping (history scan from the tool-call context plus the current call) (chunk 5)
- [x] Verify/add message-footer UI elements for tool durations with intentional config gating (chunk 5: existing `duration:` footer now renders on tool messages; new `tool turn:` footer, same config gate)
- [x] Migrate `TimestampExtension` append stamping onto `prepare_appended_message`; retire the `to_native_messages` workaround (chunk 6: red 3 → green 24 in the package suite; `to_native_messages` deleted entirely — the adapter default is the pass-through; both existing tests green unmodified; core suite 560 green; app suite 422 green + the known pre-existing failure)
- [x] Unit tests for the framework hooks (ordering, chained state, context facts, call transformation + re-inspection, no framework timing, cancellation, synthesized error results) (chunks 1–4: 29 tests in `core/python/tests/test_tool_call_lifecycle_hooks.py`)
- [x] Unit tests for the stamping plugin (per-call stamping, turn accumulation, malformed metadata, LLM fields unchanged) (chunk 5: 9 new unit tests; existing 10 LLM tests green unmodified)
- [x] Integration test through the application tool loop (events carry stamped metadata) (chunk 5: `application/python/tests/test_application_tool_duration_stamping.py` — checkpoint session, streaming `tool_partial` end + `tool_results`, reload round-trip, multi-call turn accumulation)
- [x] Cross-provider and streaming/non-streaming verification (chunk 7: provider follow-up default suites green — openai_responses 481, reference provider 113, openrouter 135; integration tests cover streaming and non-streaming)
- [x] Documentation updates (chunk 7: `core/python/docs/types-and-protocols.md` hook section; `plugins/docs/feature-plugins.md` protocol block + hook section; `plugins/docs/provider-extensions.md` lifecycle entries; timestamp-extension README rewritten for append-time stamping and tool duration)

## Implementation Notes

- **Chunk 1 done** (protocol surface + adapters + wrappers): `types.py` gained the three default no-op hooks on both protocols; `adapters.py` gained normalizing defaults on both adapters (`_get_impl_method` treats protocol stubs as missing); `plugin/extension.py`/`plugin/feature.py` gained pass-throughs. Red 9 → green 10.
- **Chunk 2 done** (tool-call dispatch): `iter_tool_messages` restructured with four new helpers (`_get_enabled_features_for_config`, `_tool_call_hook_participants`, `_dispatch_prepare_tool_call`, `_dispatch_finalize_tool_call`). Facts: `started_at`/`started_at_mono` captured before the prepare chain; `finished_at`/`finished_at_mono` after execution; `tool_error` on synthesized paths; prepare fires only for inspectable calls; transformed calls are re-inspected and re-resolved; finalize fires exactly once per call on all four yield paths. Red 9 → green 20; core suite 551 green; application suite green except one pre-existing failure (below).
- **Discovered — state semantics**: the request pipeline re-initializes provider state per request (`provider.init` at core.py:2016) and threads state explicitly between phases, so hook-state write-back to `provider.state` cannot persist into the next request. The contract's state guarantee is therefore the within-chain threading (chained plugins read each other's state) plus a `provider.state` write-back that benefits standalone `execute_tool_calls` sequences. Recorded in the dispatch docstring.
- **Decision — provider-gated dispatch**: the hooks dispatch only when the full plugin context resolves (a provider is registered and selected); bare-core tool execution without a provider keeps its current behavior (no dispatch). Mirrors `_resolve_tool_participants_for_config`'s existing no-provider behavior; pinned by `test_bare_core_tool_execution_does_not_dispatch_hooks`.
- **Decision — hook exceptions propagate** (no framework-level swallowing), consistent with the request pipeline's extension dispatch; plugins own their best-effort concerns (the cost-tracking precedent: the plugin wraps its store writes).
- **Pre-existing failure (not this task's)**: `application/python/tests/test_claude_system_message_helpers.py::test_default_config_claude_system_message_renders_sections_tasks_and_agents` fails at HEAD — commit `7472173b` rewrote `TASKS_v7.md` ("Task files are standalone handoffs...") but the test still asserts the v5 wording ("Task files are a handoff mechanism"). Reported to the user; fix pending their decision.
- **Chunk 3 done** (append dispatch): `add_message` end-appends dispatch `prepare_appended_message` before the native conversion via `_prepare_appended_message_with_hooks`; `iter_tool_messages` records the call facts into the caller's context; the app tool loop (`tool_loop.py`) now builds one tool context per call and reuses it for `add_message`, so tool-result appends carry the full fact set. Discovered: the append conversion re-initializes provider state (`_init_provider_and_features_for_config`), so the append hook's guaranteed state contract is the within-chain threading; the write-back happens but persistence past the conversion is not guaranteed (documented in the helper docstring).
- **Chunk 4 done** (provider-call facts): started facts are added to request contexts in `_build_request_context` (session branch only — internal rebuild contexts stay fact-free, pinned by the `session_id` filter in the tests); finished facts are added to a copied `finalize_context` before each of the three finalize chains (non-streaming + both streaming paths).
- **Chunk 5 done** (DurationExtension tool stamping): `finalize_tool_call` measures from the context facts (no facts → message unchanged, no fabricated values), stamps `duration_ms`/`_formatted`/`duration_started_at`/`_finished_at` plus `turn_tool_duration_ms`/`_formatted` via `_sum_tool_durations_since_turn_start` (core-message scan, `role == "tool"` only, same turn-separator rule as the LLM turn). UI: the existing `duration:` footer now renders on tool messages (data path exists) and a new `tool turn: {{data}}` footer was added under the same `duration_extension_show_duration` gate. `from_native_messages` projects the new turn-tool keys. Deviation from strict red-first: the integration test was written after the unit implementation (it still caught the `load_session` tuple API); the unit tests were red-first.
- **Chunk 6 done** (TimestampExtension migration): timestamp allocation moved from the `to_native_messages` single-message workaround to `prepare_appended_message` (stamps the core message before conversion; the provider conversion maps it into native `_metadata`). The workaround method was deleted rather than kept as a pass-through; the `native_indices` guard retired with it (the append hook never fires during request preparation or inserts). Module docstring updated.
- **Environment fix**: the installed `timestamp_extension` package pointed at the dropped worktree's copy (stale editable install); reinstalled from the main repo before chunk 5 testing.
- **Incident repaired**: an accidental `git stash pop` run from the wrong directory applied an old unrelated stash ("Cross platform markdown"), leaving merge conflicts in `application/python/*` and `tasks/20260827-*`; fully repaired via index reset + checkout to HEAD; the old stash entry was kept (nothing lost); the 020 changes were untouched. Lesson recorded: run git from the repo root.

### Requirement verification

| Requirement group | Verification evidence |
|---|---|
| Plugin-owned measurement | Source inspection of the dispatch points (`iter_tool_messages`, `add_message` dispatch, `_build_request_context`, finalize chains): no duration computation, no stamping, no stats writes in framework code; hook tests assert contexts carry only raw facts and no `duration` keys |
| General tool-call act-point | `test_tool_call_lifecycle_hooks.py`: recording fixture plugins act around tool calls through both tool-call hooks and the append hook; ordering (extensions before features, priority within kind) and chained state verified |
| Tool-call transformation in prepare | `test_prepare_tool_call_sanitizes_arguments` (tool received transformed payload), `test_prepare_tool_call_intercepts_tool_name` (other handler executed, result message reflects the transformed call), `test_prepare_tool_call_broken_transformation_follows_synthesized_error_path` |
| Provider-call context symmetry | `test_provider_call_contexts_carry_timestamp_facts` (+ streaming variant): `initialize_request` contexts carry started facts, `finalize` contexts carry finished facts, no duration keys |
| Context-carried facts | Hook tests assert timestamps, call descriptor, session/request ids, `tool_error` on synthesized paths; the framework never mutates the tool message (plugins return transformed copies) |
| Timestamp workaround retired | `test_to_native_messages_returns_native_messages_unchanged` (fails while the workaround exists — proven red-first); `to_native_messages` deleted from `TimestampExtension`; append-time stamping covered for user/system/tool messages including native `_metadata` persistence and rebuild survival |
| Per-call duration on tool messages | `test_application_tool_duration_stamping.py`: checkpoint session, streaming `tool_partial` end, and `tool_results` events all carry the plugin-stamped duration fields; reload round-trip keeps them |
| Per-turn tool duration | Unit tests: two prior tool results accumulate with the current call; user message and terminal assistant reset the turn; only `role == "tool"` scanned (assistant durations excluded); malformed values skipped. Integration: two sequential calls accumulate exactly |
| LLM duration unchanged | The 10 pre-existing `DurationExtension` tests pass unmodified; tool fields are distinct keys (`turn_tool_duration_*`); assistant fields untouched |
| All providers and tools | Integration tests with the echo provider + `FileReaderTool`, streaming and non-streaming; provider follow-up suites green (openai_responses 481, reference 113, openrouter 135) |

### Additional implementation verification

- Synthesized error results dispatch finalize with `tool_error` (failed inspection without prepare, no handler, stream error with started/finished facts) — `test_finalize_tool_call_dispatches_*` tests.
- Multiple sequential tool calls: facts correlated per call id, no cross-call leakage — `test_multiple_tool_calls_correlate_facts_per_call`.
- Existing tool-loop checkpoint/reconciliation behavior unchanged: core suite 561 green, application suite 422 green (one pre-existing failure unrelated to this task: `test_claude_system_message_helpers` asserts pre-v7 TASKS wording, stale since commit `7472173b`).
- Commands run: `pytest core/python/tests -q` (561 passed), `pytest application/python/tests -q` (422 passed), `pytest plugins/timestamp-extension/tests -q` (24 passed), `pytest plugins/openai_responses/tests -q` (481), `pytest plugins/reference-openai-compatible-provider/tests -q` (113), `pytest plugins/openrouter/tests -q` (135); ruff + black clean on all changed files; pyright — the 3 new `hook_context` errors introduced by chunk 2 were fixed; remaining pyright findings are pre-existing (the `logger = None` lazy-logger pattern in core.py, plugin signature drift vs the migrated protocol signatures, adapter `is_enabled` typing).
- Merge note: `task/20260728-core-python-documentation-migration` was merged into develop before the documentation chunk (user instruction); `core.py`/`types.py` auto-merged cleanly with the hook work; conflicts in `AGENTS.md`, `README.md`, `docs/index.md` were resolved toward the branch's post-migration doc locations; core (561) and timestamp (24) suites verified green after the merge.
## Completion Notes

Completed 2026-09-22. All ten requirements verified (see the requirement
verification table); every chunk followed the red-first discipline except the
chunk 5 integration test (written after the unit implementation; noted in the
Implementation Notes).

Delivered: the three optional hooks (`prepare_tool_call`,
`finalize_tool_call`, `prepare_appended_message`) on both
`ProviderExtensionPlugin` and `FeaturePlugin` with adapters, wrappers, and
core dispatch (tool-call paths with re-inspection and synthesized-error
coverage; append path with native persistence); provider-call context facts
for symmetry; `DurationExtension` per-call and per-turn tool duration
stamping with footer UI; the `TimestampExtension` append-time migration with
the `to_native_messages` workaround fully retired; framework hook tests (29),
plugin unit tests (9 new), and application integration tests (3).

Deferred to later subtasks: store rows and store-backed totals (025, phase 2
with 010), session LLM duration store (010), human time telemetry (030),
cross-subtask documentation pass (040). The pre-existing
`test_claude_system_message_helpers` failure (stale TASKS v5 assertion) was
reported to the user and left for the task-guidance owner.

## Post-completion follow-up

Approved follow-up (2026-09-22, same session): two refinements.

1. **UI element ordering moved into the core/app layers.** Every UI element
   now carries an effective `order` stamped by the owner: explicit numeric
   `order` wins, else a kind-and-position default (provider 1000,
   extension 2000, feature 3000, tool 4000, app plugin 5000; Nth plugin in
   a band defaults to `band + N*10`). `AgentCore.get_ui_schema` and
   `AgentApplication.get_application_ui_schema` return stable-sorted
   lists, so frontends need no sorting of their own (existing frontend
   `(order ?? 0)` sorts are idempotent). Tests:
   `core/python/tests/test_ui_schema_ordering.py` (6) and
   `core/python/tests/test_application_ui_schema_ordering.py` (2).
   Contract documented in `plugins/docs/ui-elements.md`.
2. **Turn tool duration relocated to the assistant message.** The
   per-turn tool total is now stamped by `DurationExtension.finalize` on
   the assistant owner message (native-history scan, `role == "tool"`
   only, same turn separators; absent for turns without tool results),
   rendered as `turn tool duration:` after `turn duration:`. Tool-result
   messages carry only their per-call `duration:` (the `tool turn:`
   footer and tool-message turn fields were removed; the dead
   core-message scan helpers were deleted). Unit tests reworked
   (8 new/changed), integration tests updated (accumulation asserted on
   the assistant message).

Verification: core 569, application 422 (+1 known pre-existing failure),
timestamp-extension 26, provider suites 729 (openai_responses +
reference + openrouter), frontend-sdk 343, frontend-rn-components 73;
ruff/black clean; pyright introduces no new findings. One visible
consequence flagged to the user: mobile composer config-toggle menu
entries previously defaulted to order 10 (top of the menu) and now carry
their core-stamped order (1000s+), so they render after the composer
builtins (order 100-120); previously-unordered backend actions keep
their position (the shared menu model sorts missing order last, and
1000s+ still sorts after local 0-120 items).
