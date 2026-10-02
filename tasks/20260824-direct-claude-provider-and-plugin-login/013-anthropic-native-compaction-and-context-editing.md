# Anthropic Native Compaction And Context Editing

Add provider-native compaction and context editing without replacing generic
prompt-based summarization in other providers.

## Requirements checklist

### Functional requirements

- [x] `AnthropicCompactionExtension` owns compaction configuration, UI,
  enablement, request shaping, native block interpretation, and public
  compaction metadata.
- [x] `AnthropicContextEditingExtension` owns thinking-retention and tool-use
  clearing configuration, UI, request shaping, and applied-edit metadata.
- [x] Server-side compaction blocks are preserved in canonical native history
  and reused on subsequent requests.
- [x] Users can opt into automatic request-time compaction at a supported token
  threshold and continue the conversation after compaction.
- [x] Context editing can clear supported stale tool results or other eligible
  context according to explicit policy.
- [x] Compaction and context-editing usage is reported completely through
  normalized message, turn, and session usage without double counting.

### Non-functional requirements

- [x] Native compaction does not redefine or replace provider-independent
  prompt summarization.
- [x] A cancelled or incomplete ordinary request cannot persist a partial
  compaction result.
- [x] Visible transcript projections do not become the canonical continuation
  state.
- [x] Compatible endpoints without compaction support omit the feature.
- [x] Managed `pause_after_compaction: true` auto-resume is not claimed by the
  initial implementation.

Parent Task:
`tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`

Depends On:

- `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md`

Specification:

- `plugins/anthropic-compatible/docs/development/specifications/anthropic-provider/index.md`

## Resolved requirement decisions

1. Anthropic compaction uses automatic request-time compaction rather than an
   OpenAI-style manual full/prefix action or separate background process.
2. Managed `pause_after_compaction: true` auto-resume is deferred. The initial
   extension uses the server-continuing `false` mode.
3. Context editing uses a separate `AnthropicContextEditingExtension` so
   models such as Haiku can expose supported context editing without falsely
   exposing compaction.

## Supporting facts

- Official Anthropic compaction is currently the beta
  `compact-2026-01-12`, configured with a
  `context_management.edits[*].type` of `compact_20260112`.
- Automatic compaction defaults to a 150,000-input-token trigger, accepts a
  minimum trigger of 50,000 tokens, and supports optional summarization
  instructions.
- A successful compaction returns an assistant `compaction` content block with
  summary content and opaque `encrypted_content`. The complete block must be
  sent back on later requests.
- Streaming compaction uses `compaction_delta`. Compaction work is reported
  separately in `usage.iterations`; its tokens are not included in the
  response's top-level usage totals.
- With `pause_after_compaction: false`, the server continues the same request
  after compaction. With `true`, the response stops with
  `stop_reason: "compaction"` and the client must resubmit the returned
  compaction block to continue the interrupted turn.
- Context editing is a separate beta,
  `context-management-2025-06-27`, with independent
  `clear_thinking_20251015` and `clear_tool_uses_20250919` strategies.
  Applied edit statistics are response metadata; context editing does not
  return a replacement client transcript.
- The official model catalog inspected on 2026-09-10 advertises compaction,
  tool-use clearing, and thinking clearing for `claude-sonnet-5`,
  `claude-sonnet-4-6`, and `claude-opus-4-6`. It advertises tool-use and
  thinking clearing, but not compaction, for
  `claude-haiku-4-5-20251001`.
- The current provider already transports raw beta `context_management`
  request options and preserves non-streaming applied-edit metadata. It does
  not yet:
  - define compaction or context-editing extensions;
  - select the compaction beta by edit type;
  - reduce `compaction_delta`;
  - preserve streaming applied-edit metadata;
  - expose compaction iteration usage;
  - present extension-owned compaction/context-editing configuration and UI.
- OpenAI Responses native compaction remains useful as a reference for opaque
  native-history preservation and continuation tests. Its manual session
  action, dedicated compaction transport, background process, and visible
  prefix replacement are not reusable Anthropic protocol behavior.
- Official references:
  - [Anthropic compaction](https://platform.claude.com/docs/en/build-with-claude/compaction)
  - [Anthropic context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)

## Execution plan

Status: Approved

Define a package-owned compaction/context-editing specification refinement
before implementation, then deliver the approved automatic request-time
compaction and separate context-editing extensions.

The implementation should extend the existing Anthropic Messages request
lifecycle rather than add a second compaction transport:

```text
Official model descriptors or explicit optional capabilities
  -> compaction/context-editing support tags
  -> AnthropicContextEditingExtension composes clearing edits
  -> AnthropicCompactionExtension appends automatic compaction last
  -> RequestOptionsFeature remains the final request-body override
  -> AnthropicProvider selects/composes required beta transport
  -> content-block reducer preserves compaction blocks and deltas
  -> AnthropicUsageExtension accounts for all reported iterations
  -> complete native history is persisted and reused
```

### Checkpoint 1: specification, capabilities, and extension boundaries

1. Add a package-owned specification refinement under
   `plugins/anthropic-compatible/docs/development/specifications/` for native
   compaction and context editing.
2. Add stable requirements for:
   - extension ownership and opt-in behavior;
   - official model-descriptor and explicit compatible-endpoint gating;
   - request composition and beta selection;
   - lossless compaction block/delta round-tripping;
   - context-editing policy and applied-edit reporting;
   - complete iteration usage;
   - cancellation, reload, and continuation;
   - compatible endpoint omission;
   - deterministic and selective hosted verification.
3. Add package-private capability normalization for the official
   `context_management` descriptor:
   - compaction support from `compact_20260112`;
   - thinking clearing from `clear_thinking_20251015`;
   - tool-use clearing from `clear_tool_uses_20250919`.
4. Add only optional feature booleans:
   - `capabilities.anthropic_compaction`;
   - `capabilities.anthropic_context_editing`.
   Official model descriptors remain primary. Compatible endpoints can opt in
   explicitly. No unknown/rejected profile values or preventive request
   filtering are added.
5. Register two provider extensions:
   - `AnthropicCompactionExtension`;
   - `AnthropicContextEditingExtension`.
   The provider remains transport-focused.
6. Remove context-management capability ownership from
   `AnthropicReasoningControlsExtension`; that extension continues to own only
   thinking mode, effort, interleaving, and their UI/request mapping.

### Checkpoint 2: automatic compaction and native continuation

1. `AnthropicCompactionExtension` contributes:
   - `enable_anthropic_compaction`, default `false`;
   - `anthropic_compaction_trigger_tokens`, default `150000`, minimum `50000`;
   - optional `anthropic_compaction_instructions`;
   - ordinary config UI for enablement, trigger, and instructions.
2. When enabled and supported, the extension appends this edit after any
   context-editing strategies:

   ```json
   {
     "type": "compact_20260112",
     "trigger": {
       "type": "input_tokens",
       "value": 150000
     },
     "pause_after_compaction": false
   }
   ```

   The extension adds `instructions` only when configured.
3. The extension declares the request-local beta requirement
   `compact-2026-01-12`. The provider composes feature-required betas with
   configured `betas` and `beta_headers` while preserving the existing
   explicit-header precedence and final request validation.
4. Update beta validation so final request edits require the matching beta:
   - `compact_20260112` requires `compact-2026-01-12`;
   - clearing edits require `context-management-2025-06-27`;
   - mixed requests require both.
5. Extend the content-block reducer:
   - preserve `compaction` block starts;
   - replace `content` and `encrypted_content` from
     `compaction_delta`;
   - retain null-content failed compaction blocks as valid no-op native
     blocks;
   - never expose encrypted content in public footer/status metadata.
6. Add safe public metadata indicating that compaction occurred, its block
   count, and whether a readable summary was returned. The visible transcript
   remains the existing conversation plus the ordinary assistant result.
7. Do not prune prior native or visible history in the initial implementation.
   The returned compaction block is canonical continuation data and is
   round-tripped exactly. Anthropic documents pruning prior client history as
   optional; retaining it avoids introducing a Core-wide automatic history
   rewrite contract in this task.
8. Treat request cancellation during compaction as ordinary request
   cancellation. A cancelled/incomplete stream cannot finalize or persist a
   partial compaction block.

### Checkpoint 3: context-editing policy and usage

1. `AnthropicContextEditingExtension` contributes extension-owned policy
   rather than requiring users to construct beta request objects for common
   cases.
2. Thinking-retention configuration:
   - `anthropic_thinking_retention`: `provider_default`, `all`, or `turns`;
   - `anthropic_thinking_turns_to_keep`: positive integer used by `turns`.
   Mapping:
   - `provider_default` emits no thinking-clearing edit;
   - `all` emits `keep: "all"`;
   - `turns` emits a `thinking_turns` keep object.
3. Tool-use-clearing configuration:
   - `enable_anthropic_tool_use_clearing`, default `false`;
   - `anthropic_tool_use_clear_trigger_tokens`, default `100000`, minimum
     `10000`;
   - `anthropic_tool_uses_to_keep`, default `3`;
   - optional `anthropic_tool_use_clear_at_least_tokens`;
   - `anthropic_clear_tool_inputs`, default `false`;
   - `anthropic_tool_use_excluded_tools`, default empty.
4. Add straightforward UI for the retention mode/turn count and the common
   tool-clearing enable/trigger/keep controls. Keep exclusions and minimum
   clearing as documented advanced config if the existing portable config UI
   cannot present them cleanly without a new UI contract.
5. Compose context edits in deterministic order:
   - thinking clearing;
   - tool-use clearing;
   - compaction.
   Anthropic requires thinking clearing to precede tool-use clearing when both
   clearing strategies are present.
   Generic `request_options.context_management` runs afterward and remains the
   final complete override.
6. Preserve `message_delta.context_management.applied_edits` for streaming as
   well as ordinary responses. Publish bounded non-sensitive clearing counts
   in assistant metadata and message footers; do not mutate or hide the local
   transcript because server-side context editing does not return replacement
   client history.
7. Migrate the default direct Anthropic configuration from raw
   `request_options` to extension-owned thinking retention while preserving
   current `keep: "all"` behavior. Keep native compaction disabled by default.
   For the one-million-token direct Claude profile, set the visible configured
   compaction trigger to the documented recommended `800000` value without
   enabling compaction automatically.
8. Extend `AnthropicUsageExtension` so `usage.iterations` is authoritative
   when present:
   - sum all message and compaction iterations for billable normalized
     per-message, turn, and session input/output/cache totals;
   - do not double-count the top-level usage fields;
   - expose compaction iteration count plus compaction input, output,
     cache-read, cache-write, 5-minute-cache-write, and
     1-hour-cache-write details;
   - preserve existing duration/TPS fields and verify their behavior when a
     compaction iteration is present.
   The cost-estimation subtask can later consume these reported token classes.

### Checkpoint 4: compatibility, verification, and current documentation

1. Deterministic provider/extension tests cover:
   - capability-descriptor normalization and explicit booleans;
   - independent Haiku context-editing enablement without compaction;
   - omission for unsupported compatible models;
   - config schema and UI;
   - edit composition/order and raw request-option precedence;
   - exact beta composition and missing-beta validation;
   - non-streaming and streaming compaction blocks;
   - `compaction_delta`;
   - null-content blocks;
   - streaming and ordinary applied-edit metadata;
   - iteration usage without double counting;
   - cancellation before a compaction block finishes.
2. Core stack tests use scripted SDK responses to prove:
   - a compacted assistant response persists complete native history;
   - reload and a following request resend the complete compaction block;
   - text, reasoning, tool calls/results, prompt caching, and compaction can
     coexist in one request lifecycle;
   - public messages never contain encrypted compaction content;
   - duration/TPS consumes the revised normalized turn totals.
3. Ollama verification uses `qwen3.5:0.8b` and proves that:
   - no compaction or context-editing tag is invented;
   - neither extension adds request fields or UI by default;
   - the baseline local text/tools/reasoning/usage behavior remains unchanged.
   Do not add request filtering. Explicitly opting an incompatible endpoint in
   may produce the provider's normal sanitized endpoint error.
4. Hosted Anthropic verification is intentionally narrow:
   - reuse the existing official model-catalog test to assert current
     compaction/context-editing descriptors;
   - one slow streaming Sonnet test uses the minimum supported 50,000-token
     trigger, asserts a complete compaction block and compaction iteration,
     persists/reloads the session, and completes a follow-up request;
   - reuse/extend the existing bank-file context-management tests for
     thinking-retention policy instead of adding redundant paid requests;
   - add at most one focused tool-use-clearing hosted case if deterministic
     fixtures cannot establish server-applied edit reporting.
5. The long-context compaction test is marked `integration`, `api`,
   `anthropic`, and `slow_integration`; it is not part of the fast or ordinary
   hosted smoke suite.
6. Update current package documentation only with behavior delivered in the
   same implementation commit series.

### Implementation decisions and open questions

- Decision: provider-native history remains canonical.
- Decision: native compaction and context editing are opt-in even when the
  selected model advertises support.
- Decision: official model capability descriptors are primary; explicit
  optional capability booleans are the fallback for compatible endpoints.
  No compaction model-name regex fallback is planned.
- Decision: compatible endpoints without support omit tags, extensions, and
  UI. Explicit incompatible configuration is allowed to reach the endpoint
  and fail normally.
- Decision: request-options fields remain the final request-body override.
- Decision: context editing changes server input context only; it does not
  rewrite visible or canonical client history.
- Decision: compaction blocks are retained exactly in canonical native
  history. Public metadata never copies `encrypted_content`.
- Decision: automatic local pruning before a compaction block is not part of
  the first implementation.
- Decision: feature-required beta identifiers are request-local extension
  contributions consumed by provider transport; configured beta arrays remain
  visible and additive.
- Decision: the existing manual/background requirements are replaced by
  automatic request-time compaction.
- Decision: managed `pause_after_compaction: true` is deferred.
- Decision: compaction and context editing use separate extensions.

### Documentation

- Create
  `plugins/anthropic-compatible/docs/development/specifications/native-compaction-and-context-editing/`
  as the package-owned durable refinement:
  - `index.md`: ownership, scope, relationship to the main Anthropic and
    portable provider specifications, and document map;
  - `product-spec.md`: user-visible opt-in behavior, automatic compaction,
    context-editing controls, transcript behavior, compatibility, and
    non-goals;
  - `technical-spec.md`: extension/provider boundaries, capability gating,
    beta composition, request ordering, streaming reduction, usage,
    cancellation, compatibility, and verification architecture;
  - `protocol.md`: exact edit, block, delta, stop-reason, applied-edit, and
    iteration-usage contracts;
  - `requirements.md`: stable implementation, verification, documentation,
    and evidence state.
- Link the refinement from the main Anthropic provider specification and
  package development index. Add a concise main Anthropic requirement that
  points to the refinement instead of duplicating its full contract.
- Extend the portable-provider target with optional native context-maintenance
  ownership, opaque continuation-state, usage, compatibility, and conformance
  requirements.
- Add a public provider-authoring page under
  `plugins/docs/provider-implementation-standard/` explaining how
  provider-native compaction/context editing differs from generic prompt
  summarization, which layer owns each concern, and the standard continuation
  tests. Link it from the authoring-standard index and relevant ownership and
  conformance pages.
- Add `plugins/anthropic-compatible/docs/context-management.md` as the
  package-user guide for enablement, trigger thresholds, instructions,
  thinking retention, tool-use clearing, beta behavior, compatible endpoints,
  usage, limitations, and troubleshooting.
- Keep the package README concise and link the new user guide. Update the
  current implementation map with concrete classes and test entry points.
- Do not expose task stages, requirement IDs, or target-only behavior in
  package-user documentation.

### Task checklist

- [x] Resolve the three open requirement questions with the user.
- [x] Revise the requirements checklist to the approved Anthropic protocol
      scope.
- [x] Define the package compaction/context-editing specification refinement
      and stable requirements.
- [x] Define the portable optional native context-maintenance refinement and
      public authoring guidance.
- [x] Add compaction and context-editing extension registration and capability
      gating.
- [x] Move context-management capability ownership out of the reasoning
      controls extension.
- [x] Implement extension-owned compaction and context-editing request
      composition.
- [x] Implement request-local beta contributions and strategy-specific beta
      validation.
- [x] Implement lossless compaction block/delta and streaming applied-edit
      reduction.
- [x] Implement safe public compaction/edit metadata and complete iteration
      usage.
- [x] Migrate the default direct Anthropic context-management configuration.
- [x] Add deterministic provider, extension, and Core stack tests.
- [x] Add Ollama omission/regression coverage with `qwen3.5:0.8b`.
- [x] Run the selective hosted model-capability, long-context compaction, and
      continuation coverage.
- [x] Add package-user and implementation documentation.
- [x] Update package/portable requirement evidence and this task throughout
      execution.

### Requirement verification

- Feature ownership and gating:
  - supported official descriptors or explicit booleans expose only the
    applicable compaction/context-editing extension and UI;
  - Haiku can expose context editing without compaction;
  - unsupported compatible endpoints remain unchanged.
- Native compaction:
  - the configured ordinary request contains the exact compaction edit and
    required beta;
  - non-streaming and streaming responses retain complete compaction blocks;
  - a persisted/reloaded real compacted session completes a follow-up request.
- Context editing:
  - configured thinking/tool-use policies map exactly to ordered provider
    edits;
  - streaming and ordinary applied-edit counts are available without local
    transcript mutation.
- Usage:
  - iteration totals include compaction work exactly once and preserve
    normalized turn/session and duration/TPS behavior.
- Safety:
  - cancellation cannot persist a partial compaction result;
  - encrypted compaction content remains confined to canonical native
    history;
  - raw request options remain authoritative and compatible-endpoint failures
    remain sanitized provider errors.

### Additional implementation verification

- Fast package suite:
  `pytest plugins/anthropic-compatible/tests -q`.
- Static verification:
  Ruff, Black check, Pyright, and `git diff --check` for touched package and
  application files.
- Local compatibility:
  `pytest plugins/anthropic-compatible/tests -m "integration and ollama and not slow_integration" -q`
  with `qwen3.5:0.8b`.
- Hosted focused verification:
  model capabilities and existing context-editing tests under
  `integration and api and anthropic`, plus the explicit
  `slow_integration` long-context compaction test.
- Application/default-config tests verify extension discovery, effective
  settings, UI visibility, and migrated direct Anthropic configuration.
- Documentation preparation and MkDocs build run after authored docs are
  complete; generated prepared/dist output is not edited.
- Regression assertions retain tool IDs, thinking signatures, prompt-cache
  request behavior, native-history integrity, and provider switching after a
  compaction block is present.

## Implementation Notes

### 2026-09-10 native context-management implementation

- Official model discovery currently distinguishes the two optional features:
  Sonnet 5, Sonnet 4.6, and Opus 4.6 advertise compaction plus context editing;
  Haiku 4.5 advertises context editing without compaction.
- The implementation therefore uses separate support tags and extensions
  rather than one combined context-management gate.
- Feature extensions contribute request-local required beta identifiers. The
  provider validates the final edit list after raw request options and keeps
  the established explicit `anthropic-beta` header precedence.
- Streaming reduction now preserves `compaction_delta` and top-level
  `message_delta.context_management` metadata.
- Hosted Anthropic can return a valid null/no-op compaction block containing
  only `{"type": "compaction"}`. The SDK documents this as round-trippable
  continuation state, so deterministic and hosted coverage preserve the block
  rather than requiring summary or encrypted content.
- The first delivered implementation retains pre-compaction local/native
  history and does not manage `pause_after_compaction: true`, matching the
  approved scope.

## Completion Notes

Completed on 2026-09-10.

Outcome:

- Added independently gated `AnthropicCompactionExtension` and
  `AnthropicContextEditingExtension`.
- Automatic compaction is opt-in, uses `compact_20260112`, always requests
  `pause_after_compaction: false`, and preserves returned compaction blocks in
  canonical native history.
- Thinking retention and tool-use clearing use extension-owned settings and
  deterministic protocol ordering.
- Provider transport composes request-local beta requirements with configured
  betas and validates the final edit list after raw request options.
- Streaming preserves compaction deltas and context-editing response metadata.
- Usage iteration accounting includes compaction exactly once and exposes
  separate compaction token classes.
- Default direct Anthropic configuration uses extension-owned keep-all
  thinking retention and a separate 800,000-token trigger variant for current
  one-million-token Sonnet/Opus models; compaction remains disabled by
  default.
- Package specifications, portable provider requirements, public authoring
  guidance, package-user docs, implementation docs, and application config
  guidance describe the delivered behavior.

Requirement evidence:

- ANCM-001 through ANCM-011 are implemented, automatically verified, and
  documented in the package refinement.
- ANTH-020 and PPI-016 link the package and portable delivered state.
- Deterministic exact-request replay and the hosted follow-up both preserve
  provider-native compaction blocks without copying encrypted continuation
  data into public metadata.

Verification:

- `pytest plugins/anthropic-compatible/tests -q` with the worktree package on
  `PYTHONPATH`: 74 passed, 26 deselected.
- Local Ollama `qwen3.5:0.8b` suite: 12 passed.
- Official model-capability test: 1 passed.
- Hosted streaming compaction, persistence, replay, and follow-up: 1 passed.
- Hosted context-editing bank profiles: 2 passed.
- Hosted default-config Anthropic smoke and UI assertions: 1 passed.
- Deterministic default-config variant integration: 1 passed.
- Application fast suite: 419 passed, 1 skipped, 81 deselected.
- Ruff, Black, Pyright, JSON validation, and `git diff --check` pass.
- Documentation preparation and MkDocs build pass with existing repository
  navigation, test-link, and griffe warnings.

Plan deviations and findings:

- A separate hosted tool-use-clearing case was unnecessary: deterministic
  tests define the complete request/applied-edit contract, while the hosted
  bank profiles prove extension-owned context editing and the hosted
  compaction test proves native continuation.
- Hosted Anthropic returned a null/no-op compaction block in the long-context
  test. The SDK documents this as valid round-trippable state; the test
  therefore verifies exact preservation/replay and successful continuation
  instead of requiring readable or encrypted summary content.
- The parent task file was not edited because the original worktree still has
  concurrent uncommitted changes owned by another agent.

## Post-completion follow-up

### 2026-09-10 default context maintenance and OpenAI parity

Status: Approved

This user-approved scope expansion makes the delivered Anthropic context
maintenance useful by default in the shipped configuration, simplifies its
session settings, and adds the corresponding provider-native capabilities to
the OpenAI Responses package where OpenAI exposes a real equivalent.

#### Follow-up requirements

- [x] The default direct Anthropic provider enables supported automatic
      compaction, keep-all thinking retention, and conservative tool-use
      clearing without sending unsupported fields to models or compatible
      endpoints that do not advertise the corresponding capability.
- [x] Anthropic session settings expose the primary controls for automatic
      compaction, thinking retention, and tool-use clearing while keeping
      low-value or expert-only fields available through configuration.
- [x] The OpenAI Responses native-compaction extension supports ordinary
      request-time automatic compaction through the official
      `context_management` request field while preserving the existing manual
      full/prefix compaction action.
- [x] OpenAI reasoning retention uses the existing `reasoning_context`
      contract with clearer user-facing terminology and transparent
      supported-model defaults.
- [x] OpenAI's lack of an independent provider-native tool-use-clearing
      strategy is documented rather than hidden behind an inaccurate
      emulation.
- [x] Package specifications, portable guidance, default-config documentation,
      and tests describe and verify the expanded behavior.

#### Implementation decisions and open questions

- Decision: default Anthropic configuration enables all three supported
  context-maintenance strategies. Capability-gated extensions remain the
  boundary that prevents unsupported request fields.
- Decision: general Anthropic defaults use a 150,000-token compaction trigger,
  a 100,000-token tool-clearing trigger, keep-all thinking, and five retained
  tool uses.
- Decision: current one-million-token Sonnet/Opus variants override the
  compaction trigger to 800,000 tokens and the tool-clearing trigger to
  200,000 tokens.
- Decision: Anthropic UI keeps the compaction toggle and trigger, thinking
  retention selector, and tool-clearing toggle, trigger, and retained-use
  count. Compaction instructions, exact thinking-turn count, minimum clear
  size, input clearing, and excluded-tool names remain configuration-only.
- Decision: context-maintenance settings remain session settings and are not
  pinned into the message composer.
- Decision: OpenAI automatic compaction extends
  `OpenAIResponsesNativeCompactionExtension`; it is not a second compaction
  plugin or application action.
- Decision: the OpenAI request contract uses
  `context_management: [{"type": "compaction", "compact_threshold": N}]`.
- Decision: the existing OpenAI `reasoning_context` setting remains the
  implementation contract; its UI label and option labels describe reasoning
  retention.
- Decision: `truncation: "auto"` is not presented as tool-use clearing.
- Decision: public OpenAI API behavior is implemented and verified first.
  ChatGPT-hosted automatic compaction is enabled by default only if focused
  compatibility verification proves that the hosted endpoint accepts the
  official request-time contract. Existing ChatGPT remote manual compaction
  remains available either way.

#### Documentation

- Update the Anthropic context-management user guide and package refinement
  to describe shipped defaults and the simplified UI/config boundary.
- Extend the OpenAI native-compaction product, technical, and requirements
  documents with automatic request-time compaction alongside the existing
  manual protocols.
- Update the OpenAI package README with automatic compaction configuration,
  reasoning-retention terminology, authentication compatibility, and the
  absence of independent tool-use clearing.
- Extend the portable native context-maintenance guidance with a capability
  matrix that distinguishes compaction, reasoning retention, and selective
  tool-use clearing.
- Update default-config consumer documentation without exposing task status or
  requirement IDs.

#### Task checklist

- [x] Apply conservative Anthropic defaults and one-million-token overrides.
- [x] Simplify Anthropic context-management UI.
- [x] Add deterministic Anthropic default/UI regression coverage.
- [x] Add OpenAI automatic compaction config, UI, and request shaping to the
      existing extension.
- [x] Verify automatic compaction output persistence and continuation without
      regressing manual compaction.
- [x] Refine OpenAI reasoning-retention UI and supported-model defaults.
- [x] Add focused public API automatic-compaction coverage.
- [x] Verify ChatGPT-hosted request compatibility and apply the approved
      default boundary.
- [x] Update package, portable, and default-config documentation and
      specifications.
- [x] Run package, application, static, and documentation verification.

#### Requirement verification

- Default configuration resolves supported Anthropic models to the approved
  compaction, thinking-retention, and tool-clearing values, while unsupported
  feature UI remains absent.
- Anthropic UI contains only the six approved context-maintenance controls and
  continues to expose event status footers.
- OpenAI ordinary requests include the exact automatic compaction object only
  when enabled; raw request options retain final authority.
- Automatically returned OpenAI compaction items remain canonical native
  continuation state and survive a follow-up request.
- Existing OpenAI manual full/prefix compaction, cancellation, and transcript
  projection tests continue to pass.
- OpenAI reasoning-retention UI presents `auto`, `current_turn`, and
  `all_turns` through user-facing retention language without changing the
  underlying request contract.
- Documentation states that provider-native tool-use clearing is available
  for Anthropic but not currently exposed by OpenAI Responses.

#### Additional implementation verification

- Anthropic package fast suite and focused context-management tests.
- OpenAI Responses package fast suite and focused native-compaction/reasoning
  tests.
- Default-config deterministic and hosted smoke coverage where credentials
  are available.
- Focused public OpenAI API automatic-compaction test, with cost kept to the
  minimum request size accepted by the provider.
- Saved-login ChatGPT compatibility test when the local credential is
  available; absence of that credential is reported as not run rather than
  success.
- Ruff, Black check, Pyright, JSON validation, `git diff --check`,
  documentation preparation, and MkDocs build.

#### Follow-up implementation notes

- The shipped Anthropic provider now enables supported compaction, keep-all
  thinking retention, and tool-use clearing. Known one-million-token models
  retain the approved 800,000/200,000 trigger overrides.
- Anthropic UI exposes six controls. Compaction instructions, exact
  recent-thinking count, clear-at-least threshold, tool-input clearing, and
  excluded tools remain configuration-only.
- `OpenAIResponsesNativeCompactionExtension` now adds ordinary request-time
  `context_management` before `RequestOptionsFeature`; raw request options
  remain the final complete override.
- The OpenAI package now requires SDK 2.46 or newer, where
  `context_management` is a typed Responses request parameter.
- A low-cost public API probe with a 1,000-token trigger returned native
  compaction items and a normal answer. The maintained hosted test proves
  persistence and a follow-up request.
- Saved-login ChatGPT automatic compaction passed on `gpt-5.6-luna`, including
  native compaction items and a follow-up turn. `gpt-5.4-mini` is not accepted
  by the ChatGPT Codex endpoint at all, so it did not provide a compaction
  compatibility result.
- Default variants therefore enable automatic compaction for GPT-5.6 across
  authentication modes and for GPT-5.2-and-later models when API auth is
  explicit. Auto-auth GPT-5.4 defaults remain unchanged.
- OpenAI `reasoning_context` remains the request contract and is presented as
  Reasoning retention. No tool-use-clearing emulation was added.

#### Follow-up completion notes

Completed on 2026-09-10.

Outcome:

- Anthropic context maintenance is useful by default while remaining
  capability-gated.
- OpenAI Responses now supports automatic ordinary-request compaction in
  addition to its existing manual full/prefix compaction operation.
- Both public OpenAI API and supported saved-login ChatGPT requests preserve
  and replay automatically returned native compaction items.
- OpenAI reasoning retention has clearer session UI and explicit GPT-5.6
  defaults.
- Package and portable documentation distinguish automatic compaction,
  reasoning retention, selective tool-use clearing, and manual compaction as
  independent upstream capabilities.

Verification:

- Anthropic package fast suite: 75 passed, 26 deselected.
- Focused OpenAI compaction and reasoning unit suites: 110 passed.
- OpenAI package fast suite excluding the inherited attachment-history
  regression file: 419 passed, 94 deselected.
- Application fast suite: 420 passed, 1 skipped, 82 deselected.
- Focused Anthropic/OpenAI default-config effective-config and UI coverage:
  4 passed.
- Hosted direct Anthropic default-config smoke: 1 passed.
- Hosted public OpenAI automatic compaction and follow-up: 1 passed.
- Hosted saved-login ChatGPT automatic compaction and follow-up: 1 passed.
- Ruff, Black check, JSON validation, and `git diff --check` pass.
- Anthropic scoped Pyright: 0 errors.
- Documentation preparation and MkDocs build pass with existing navigation,
  test-link, and griffe warnings.

Inherited verification limits:

- The full OpenAI package run has three failures in
  `test_openai_responses_native_history_regressions.py` concerning attachment
  upload metadata. The same three tests fail identically in the original
  checkout; no compaction or reasoning file participates in those failures.
- Scoped Pyright reports the same 20 existing errors in the OpenAI native
  compaction and reasoning extensions in both the original checkout and this
  worktree. The new automatic-compaction method introduced no additional
  error.
- A broad default-config integration test still stops on an unrelated
  session-search assertion expecting an explicit `main_search: false`; the
  focused provider tests pass.

### 2026-09-14 configuration-variant correction

Status: Approved

This approved correction replaces maintained production-config examples with
stable representative documentation and broadens transparent OpenAI model
fallbacks for GPT-6 Astra and future model generations.

Requirements:

- [x] Public configuration-variant examples are fictional, complete, and
      representative of exact matching, regex matching, logical AND,
      overlapping variants, precedence, merge policies, nesting, and
      provider/agent composition without copying live provider defaults.
- [x] Automatic OpenAI compaction applies to GPT-5.2 and later numeric model
      families with arbitrary hyphen suffixes, including GPT-6 Astra and
      future major versions.
- [x] GPT-5.6 and later model families additionally receive
      `reasoning_context: "all_turns"` through a separate overlapping variant.
- [x] Repository and personal configuration use the same simplified variant
      structure, while personal agent customizations remain unchanged.
- [x] Automated tests prove overlap semantics, future-model boundaries, and
      default effective configuration.

Implementation decisions:

- One broad variant owns automatic compaction for GPT-5.2 and later,
  independent of authentication mode.
- A second, narrower GPT-5.6-and-later variant owns only reasoning retention.
- Both variants intentionally match GPT-5.6-and-later models. They compose
  because they write different keys.
- Future model matching accepts optional numeric patch segments and arbitrary
  hyphen suffixes.
- Documentation examples use fictional provider/model names and are validated
  as complete JSON.

Task checklist:

- [x] Replace production-like configuration-variant documentation examples.
- [x] Simplify repository OpenAI model variants.
- [x] Migrate the personal OpenAI model variants with a new backup.
- [x] Add overlap, boundary, and effective-config tests.
- [x] Run focused configuration tests, JSON validation, documentation
      preparation, and MkDocs build.

Correction completion notes:

- `configuration-variants.md` now uses fictional, stable examples throughout.
  Its complete example demonstrates exact and regex conditions, logical AND,
  three simultaneous matches, deep composition, and later scalar precedence.
- Seven JSON documentation blocks were extracted and parsed successfully.
- The first OpenAI variant enables automatic compaction for GPT-5.2 and later
  numeric families. The second adds all-turn reasoning retention for GPT-5.6
  and later. GPT-5.6-and-later models intentionally match both.
- Reasoning-context extension gating now follows the GPT-5.6-and-later
  numeric-family rule. Reasoning effort and Pro-mode inference remain
  unchanged.
- Boundary coverage includes GPT-5.1, GPT-5.2, GPT-5.5 Pro, GPT-5.6 Sol,
  GPT-5.10 preview, GPT-6 Astra, GPT-6.1 custom, GPT-10 next, and non-GPT
  models.
- The personal config was migrated with backup
  `~/.crystal/config.json.bak-20260914-future-model-variants`; its existing
  GPT-5.6 Sol agent retains friendly personality and high effort while
  resolving both compaction and all-turn reasoning retention.
- Configuration-composition module: 27 passed.
- Default-config non-integration coverage: 13 passed.
- Future-model variant cases: 10 passed.
- OpenAI reasoning extension unit suite: 93 passed.
- Application-level GPT-5.6 and GPT-6 Astra effective-config/UI test: passed.
- Ruff, Black, repository/personal JSON validation, and `git diff --check`
  pass.
- Documentation preparation and MkDocs build pass with existing navigation,
  test-link, and griffe warnings.

### 2026-10-02 develop integration and OpenAI opt-in correction

Status: Completed.

- Merged `develop` at `dfe6acd7` into
  `task/20260824-anthropic-native-compaction` as merge commit `ab237242`.
  The worktree changes were preserved in a named stash before the merge,
  replayed afterward, and remain uncommitted for review.
- Rechecked `develop` immediately before final integration and merged its
  newer `c52db305` tip, including GPT-6.1 Sol support, as merge commit
  `83a20923`. The reconciled task changes were preserved and replayed again;
  GPT-6.1 model assets, pricing, reasoning controls, and tests were retained.
- Resolved the OpenAI package dependency conflict by combining the new
  `openai>=2.46.0` requirement with develop's `<3.0.0` cap and `requests`
  dependency.
- Resolved the OpenAI README conflict by retaining develop's GPT-6 effort
  and Pro-mode guidance and the provider's GPT-5.6-and-later numeric
  reasoning-context contract.
- OpenAI automatic compaction is now explicitly false on the default
  provider, with a 200,000-token configurable threshold. Both fields have
  session config UI. The model variant now selects reasoning retention only;
  an explicit user setting enables compaction for any selected model.
- Retained develop's GPT-6 Sol, Luna, and Astra prompt selections and
  versioned instruction assets in the default configuration.
- Focused default-config tests, including the opt-in session override,
  passed. The merged OpenAI fast suite passed with 516 tests; the Anthropic
  fast suite passed with 78 tests. Ruff, Black, JSON parsing, and
  `git diff --check` passed.
- Migrated `~/.crystal/config.json` with backup
  `~/.crystal/config.json.bak-20261002-openai-compaction-opt-in`. The
  compaction-enabling model variant was removed, provider-level automatic
  compaction is false with a 200,000-token adjustable threshold, and the
  GPT-5.6-and-later reasoning variant remains. The user's GPT-5.6 Sol model,
  friendly personality, high effort, GPT-6/6.1 mappings, and July 13
  GPT-5.6 instruction references were preserved exactly.