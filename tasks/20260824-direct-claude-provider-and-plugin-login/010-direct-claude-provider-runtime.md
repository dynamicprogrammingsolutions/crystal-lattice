# Anthropic-Compatible Provider Runtime

Implement the API-key baseline for the `anthropic` provider and its stable
credential, request, streaming, extension, compatibility, and error contracts.

## Requirements checklist

### Functional requirements

- [x] `AnthropicProvider` supports ordinary and streaming requests through the
  standard provider plugin interfaces.
- [x] API-key authentication consumes resolved `config["api_key"]` as the
  primary credential input, with direct environment lookup only as a secondary
  fallback.
- [ ] Official Anthropic model discovery uses `/v1/models`, retains published
  capability metadata, and derives capability tags and model UI options from
  the response.
- [ ] Configurable base and model-discovery URLs support the documented
  Anthropic-compatible subset through providers such as local Ollama.
- [x] `AnthropicToolsExtension` owns tool schema injection, streamed tool-call
  reconstruction, tool-call/result mapping, and tool interop declarations.
- [x] `AnthropicReasoningExtension` owns streamed thinking, redacted thinking,
  public reasoning metadata, native-history reconstruction, and signature
  preservation without owning request-body configuration or UI.
- [x] Anthropic reasoning request fields use the generic request-options
  config/UI contract, while provider beta selection and beta-header composition
  remain explicit `AnthropicProvider` configuration.
- [ ] `AnthropicUsageExtension` owns public usage metadata, cache accounting,
  formatting, turn/session totals, duration/TPS interoperability, and usage
  UI.
- [ ] `AnthropicPromptCachingExtension` is included in the baseline and owns
  automatic caching configuration, selectable supported TTL, UI, request
  shaping, and cache-usage collection.
- [x] Claude-compatible tool schemas, calls, native history, reasoning, usage,
  and cancellation map through existing application/core contracts.
- [x] Provider configuration distinguishes direct Anthropic access,
  Anthropic-compatible endpoints, and OpenRouter access.
- [x] Provider failures are sanitized, redacted, and emitted through the
  current generic request-error event; cancellation retains its existing typed
  outcome.

### Non-functional requirements

- [x] Provider code does not embed OAuth login UI, credential acquisition,
  refresh, or persistence logic.
- [x] Credential and authorization values are redacted from logs, errors, and
  diagnostics.
- [x] Direct-provider failures never silently fall back to OpenRouter or
  another paid provider.
- [x] The provider works for ordinary text requests without optional
  extensions or tools.
- [x] Request-body feature controls use `RequestOptionsFeature` when they map
  directly to provider request keys; provider extensions retain
  interpretation, native-history, public-metadata, and feature-test ownership,
  while provider config owns SDK/beta transport selection.
- [x] Provider request retry remains owned by `AnthropicProvider`.
- [ ] Unsupported compatible-endpoint features are omitted or fail explicitly
  according to a compatibility profile.
- [x] Deterministic unit/contract coverage precedes local Ollama and selective
  hosted Anthropic tests.
- [x] Batch processing and structured outputs are outside this task.
- [x] Image attachments, model-price cost estimation, and the portable
  structured provider-error contract are outside this task.

Parent Task:
`tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`

Specification:

- `plugins/anthropic-compatible/docs/development/specifications/anthropic-provider/index.md`
- `docs/development/specifications/portable-provider-implementation/index.md`

Primary requirement IDs:

- `ANTH-001` through `ANTH-009`
- `ANTH-012` through `ANTH-015`
- `PPI-001` through `PPI-007`
- `PPI-009` through `PPI-011`

## Scope

The baseline package directory is `plugins/anthropic-compatible`. Runtime names
use the shorter Anthropic form:

- provider ID: `anthropic`
- provider class: `AnthropicProvider`
- Python module: `anthropic_plugins`
- extension classes: `AnthropicToolsExtension`,
  `AnthropicReasoningExtension`, `AnthropicUsageExtension`,
  and `AnthropicPromptCachingExtension`

The initial provider configuration follows OpenAI Responses naming where the
concepts align:

```json
{
  "provider": "anthropic",
  "auth_mode": "api",
  "api_key": "${env:ANTHROPIC_API_KEY}",
  "base_url": "https://api.anthropic.com",
  "model": "<discovered model id>",
  "anthropic_version": "2023-06-01",
  "timeout": 300
}
```

OAuth-compatible configuration names may be reserved, but OAuth token
acquisition, refresh, identity headers, persistence, and actions belong to
subtask 020.

## Supporting facts

- No direct Anthropic provider plugin currently exists in the repository.
- Existing provider projects demonstrate streaming-first provider packaging,
  provider extensions, hosted test markers, credential redaction, and
  compatibility testing against local and hosted providers.
- `plugins/claude-tools` already contributes Anthropic-native tool schema,
  call, and result interop.
- The official Models API exposes capability metadata that can replace
  hardcoded model-name checks for official Anthropic models.
- Ollama's Anthropic-compatible API covers ordinary messages, streaming,
  tools, tool results, thinking, images, and usage but omits prompt caching,
  PDFs, citations, token counting, request metadata, and some tool-choice
  controls. Image integration is owned by subtask 017.
- The local `../pi` Anthropic provider demonstrates indexed SSE content-block
  reduction, partial tool JSON, thinking signatures, cache compatibility
  controls, and multiple Anthropic-compatible endpoints.
- Local Ollama currently has `qwen3:0.6b` installed with completion, tools, and
  thinking capabilities. It is the preferred low-cost Stage 1 integration
  model.
- Local Ollama also has `qwen3.5:0.8b` installed with completion, tools, and
  thinking capabilities. It is the local fallback only when the preferred
  0.6B model cannot reliably exercise a required behavior.
- Hosted Stage 1 verification assumes `ANTHROPIC_API_KEY` will be present in the
  repository-root `.env` before hosted tests are run.

## Execution plan

Status: Approved

Create the first-party package under `plugins/anthropic-compatible` using the
Anthropic SDK, current provider-plugin conventions, and the approved package
specification. Deliver 010 through three independently reviewable checkpoints.

#### Stage 1: core provider, tools, reasoning, and usage

Implement API-key configuration, basic model discovery, ordinary and streaming
Messages requests, native conversion/history, cancellation, Claude tool
interop, thinking/signature continuity, a simple reasoning-effort UI, and
usage parsing/formatting with per-message, turn, and session totals.

The initial effort UI exposes a small common selector and does not claim that
every endpoint or model honors every value.

Verify deterministic ordinary, streamed, tool-loop, reasoning/tool-loop,
usage, reload, and cancellation behavior. Stage 1 does not calculate monetary
cost.

##### Stage 1 detailed execution plan

###### 1. Package and SDK boundary

- Create the Python package, descriptor, `pyproject.toml`, source modules, and
  package-local tests.
- Implement provider ID `anthropic`, `AnthropicProvider`, and registration of
  `AnthropicToolsExtension`, `AnthropicReasoningExtension`, and
  `AnthropicUsageExtension`.
- Build the Anthropic SDK client from resolved config:
  - `api_key`;
  - `base_url`;
  - `anthropic_version` and supported extra headers;
  - timeout;
  - provider-owned retry count.
- Keep SDK objects inside request runtime state and normalize persisted
  messages/events to plain mappings.
- Register active SDK streams/clients by request ID and close the matching
  operation on cancellation.
- Convert SDK exceptions into bounded redacted generic request-error detail.
  Do not add the subtask 019 structured error contract.

###### 2. Core Messages protocol

- Implement basic `/v1/models` discovery for IDs and display names. Full
  official capability-driven tags remain Stage 3.
- Convert leading system messages into the provider system field.
- Convert ordinary user and assistant text while preserving complete
  provider-native history.
- Implement ordinary response finalization before streaming.
- Implement indexed stream reduction for:
  - message start/stop;
  - text block start/delta/stop;
  - thinking and redacted-thinking blocks;
  - signature deltas;
  - tool-use start/input JSON delta/stop;
  - message usage deltas;
  - safe terminal errors and premature termination.
- Ensure partials are chunk-local and scratch buffers never enter native
  history.

###### 3. Tools

- Reuse the request-bound `claude-tools` schema/call/result interop.
- Add Anthropic tool schemas to the request only when the tools extension is
  enabled.
- Preserve tool-use block order and exact call IDs.
- Accumulate partial JSON without exposing invalid final arguments.
- Convert core tool messages into provider `tool_result` user blocks.
- Complete a multi-request application tool loop and persist/reload the native
  history before a later follow-up.

###### 4. Original core reasoning and simple effort UI

This original Stage 1 boundary was delivered and then replaced by the approved
config-first Stage 1 follow-up below.

- Expose:
  - `enable_reasoning`;
  - a simple `reasoning_effort` selector;
  - reasoning display enabled/disabled.
- Treat the initial effort selector as request configuration, not a claim that
  every model honors every value.
- Stream visible thinking through the reasoning extension.
- Preserve thinking, redacted-thinking, signatures, and block ordering through
  tool rounds and native-history reload.
- Defer model-specific effort choices, adaptive/manual selection,
  interleaved-versus-preserved capability UI, and behavioral effort validation
  to Stages 2 and 3.

###### 5. Usage and formatting

- Normalize per-generation input, output, total, reasoning, cache-read, and
  cache-creation token fields when present.
- Add formatted per-message usage metadata and usage UI.
- Calculate turn-cumulative and session-cumulative token totals across
  tool-call generations.
- Persist normalized internal usage metadata so reload produces the same
  visible totals.
- Produce the standard turn input/output fields needed by
  `DurationExtension`, but defer the combined duration/TPS acceptance test to
  Stage 2.
- Do not calculate monetary cost or cached-token estimates in 010.

###### 6. Deterministic acceptance

Use an injected/fake Anthropic SDK transport or local HTTP fixture behind the
SDK for the primary acceptance suite. Cover:

- config and API-key precedence/redaction;
- SDK client construction;
- model discovery success, malformed response, and failure fallback;
- ordinary request and native conversion;
- every supported stream event and malformed/premature streams;
- tools, partial JSON, tool results, and full tool loop;
- thinking, redacted thinking, signatures, and tool-round continuity;
- usage formatting and cumulative totals;
- cancellation before connect and during streaming;
- provider-owned retry before visible output;
- safe generic request-error detail;
- operation with each optional extension disabled;
- application persistence/reload.

Deterministic tests are the source of truth for exact event shapes, edge cases,
and failure behavior. Real-model tests do not replace them.

###### 7. Local Ollama verification

Use:

```text
base_url: http://localhost:11434
model: qwen3:0.6b
api_key: ollama
```

Run focused `integration` + `ollama` tests for:

- one ordinary non-streaming response;
- one streamed text response;
- one simple tool call, tool result, and final response;
- one response containing non-empty thinking;
- input/output usage presence;
- cancellation/stream closure where deterministic timing is practical.

The prompts and tool schema should be minimal and deterministic. Do not assert
reasoning quality or exact prose.

If `qwen3:0.6b` repeatedly fails to exercise a required advertised capability,
confirm the failure is model behavior rather than provider code, then use
`qwen3.5:0.8b` for that local smoke. Do not use an Ollama cloud model as the
fallback and do not weaken deterministic acceptance to accommodate a small
model.

Stage 1 local tests prove that the SDK/provider can traverse a real compatible
endpoint. Exhaustive profile differences, unsupported-field omission, and
effort-level behavior remain Stage 2.

###### 8. Minimal hosted Anthropic verification

Before running hosted tests:

- require `ANTHROPIC_API_KEY` from the repository-root `.env`;
- allow `ANTHROPIC_TEST_MODEL` to override the test model;
- otherwise use the current low-cost supported Haiku test model after model
  discovery confirms it is available;
- use short prompts and bounded `max_tokens`;
- mark tests `integration`, `api`, and `anthropic`.

Run only:

1. Model discovery and one tiny ordinary non-streaming request. This verifies
   official authentication, SDK endpoint behavior, and the non-streaming
   response shape.
2. One compact streamed reasoning-plus-tool loop ending in a final answer.
   This verifies official stream events, thinking/signature handling,
   tool-use/result continuity, usage, and finalization in one hosted scenario.

Do not duplicate the full deterministic or Ollama matrix on the paid API.
Stage 1 does not require hosted cancellation, error-taxonomy matrices,
repeated effort comparisons, cache tests, attachments, or cost tests. Those
behaviors are deterministic, compatible-endpoint, later-stage, or separate-task
responsibilities.

If Haiku cannot exercise a Stage 1 official protocol requirement, use the
lowest-cost discovered Anthropic model that advertises the required capability
for that one hosted test rather than upgrading the whole hosted matrix.

###### 9. Stage 1 checkpoint and handoff

Stage 1 is ready for review when:

- the fast deterministic suite passes;
- the public application flow completes ordinary and tool-enabled requests;
- native reasoning/tool history survives reload and a follow-up request;
- enabled local `qwen3:0.6b` tests pass or a documented
  `qwen3.5:0.8b` capability fallback passes;
- the two minimal hosted Anthropic scenarios run successfully with the API gate
  enabled;
- package docs describe only delivered Stage 1 behavior;
- Anthropic requirements contain concrete implementation and verification
  evidence.

Stop for review before Stage 2. Record any SDK/compatible-endpoint mismatch,
small-model limitation, or provider-native history change that would alter the
approved Stage 2 compatibility plan.

##### Stage 1 follow-up: config-first reasoning and continuity conformance

###### 1. Reasoning extension boundary

- Remove Anthropic reasoning request configuration and UI from
  `AnthropicReasoningExtension`.
- Remove automatic `thinking.type`, budget, effort, enablement, and display
  request shaping from the extension.
- Keep thinking/redacted-thinking extraction, visible reasoning metadata,
  streaming deltas, signature preservation, provider-native reconstruction,
  and reload behavior in the extension.
- Surface visible reasoning whenever Anthropic returns it. Provider-native
  omitted or redacted blocks remain preserved even when they contribute no
  visible reasoning text.
- Keep the extension usable without `RequestOptionsFeature`; request options
  control how reasoning is requested, not whether returned reasoning can be
  interpreted.

###### 2. Raw request options and provider beta configuration

- Use `request_options` and `request_options_ui` for request-body fields such
  as `thinking`, `output_config`, `context_management`, cache controls, and
  compatible-endpoint-specific fields.
- Reserve provider-owned `messages`, `system`, and `stream` fields so request
  options cannot bypass native-history or execution-mode invariants.
- Add provider config arrays for SDK beta features and raw beta-header
  features.
- Select `client.beta.messages.create` when SDK beta features are configured;
  otherwise use `client.messages.create`.
- Compose beta identifiers deterministically, de-duplicate them, and allow an
  explicit raw `anthropic-beta` header to take precedence.
- Reject beta-only request fields without the required beta configuration
  before transport.
- Forward SDK-supported request fields normally and place unknown compatible
  request-body fields in `extra_body` without overwriting explicit
  `extra_body`.

###### 3. Default request profiles

- Keep `claude-anthropic` as the low-cost Haiku 4.5 manual-thinking profile
  using raw `request_options.thinking.type=enabled` plus a bounded budget.
- Expose Haiku request-options UI only for its supported manual/disabled
  thinking shape; do not expose unsupported effort or interleaved controls.
- Add `claude-sonnet-anthropic` using the current official Sonnet model,
  adaptive thinking, request-options effort UI, the context-management beta,
  and a keep-all thinking strategy.
- Keep structured context-management edits as raw config until the generic
  request-options UI supports editing arrays of objects.
- Update default-config inspection and hosted smoke tests for both profiles
  without moving reasoning UI back into the Anthropic extension.

###### 4. Provider-package reasoning/tool continuity

- Reuse the canonical bank-file fixture under
  `core/python/tests/reasoning_test`.
- Add Anthropic provider-package hosted tests for the standard reasoning/tool
  continuity scenario in non-streaming and streaming modes. Require `Clock`,
  non-empty first reasoning, valid file-read tool execution, complete
  thinking/signature retention, and scratch-free native history.
- Add the interrupted-user bank-file preservation scenario using adaptive
  thinking and context management. The positive keep-all profile requires:
  - final content containing `Clock`;
  - non-empty first reasoning;
  - absent or shorter second reasoning, demonstrating reuse rather than full
    recomputation;
  - unchanged client-side native thinking blocks and signatures.
- Run the latest/current-turn-only profile as a strict expected-failure or an
  evidence-backed negative assertion. The delivered Anthropic test verifies
  server-reported cleared thinking because a newer thinking turn may carry the
  checkpoint forward and still satisfy the semantic bank answer.
- Allow bounded semantic retries only for model variability. Authentication,
  request-shape, SDK-selection, and provider failures fail immediately.
- Run the existing OpenRouter Claude bank-file cases as comparison evidence;
  add only the missing interrupted-user preserved/negative profile coverage
  in the OpenRouter provider package if it is not already present.

###### 5. Portable conformance

- Require the canonical streaming and non-streaming bank-file reasoning/tool
  continuity test for every provider/profile that claims both reasoning and
  tools.
- Require the interrupted-user bank-file test when a profile claims reasoning
  preservation across requests.
- Define preserved acceptance as `Clock`, non-empty initial reasoning, and
  absent or materially shorter follow-up reasoning.
- Permit a strict expected-failure or documented negative test for a profile
  intentionally retaining insufficient reasoning history.
- Require provider-native reasoning state, signatures, and tool relationships
  to remain structurally intact even when the server removes older reasoning
  from active context.
- Record this behavior in the public provider authoring standard, portable
  technical specification and requirements, Anthropic package specification
  and requirements, and package verification guidance.

###### 6. Follow-up verification checkpoint

The Stage 1 follow-up is complete when:

- deterministic reasoning-extension and beta/request-options tests pass;
- Haiku manual-thinking and Sonnet adaptive-thinking request shapes are
  verified;
- standard and beta SDK selection is verified in ordinary and streaming paths;
- hosted Anthropic bank-file continuity passes in streaming and non-streaming
  modes;
- the keep-all adaptive/context-managed bank test passes with the standard
  reasoning-size assertions;
- the latest/current-turn profile has an evidence-backed negative assertion;
- existing OpenRouter Claude conformance still passes;
- default configuration, package docs, portable authoring guidance, and
  requirement evidence match delivered behavior.

#### Stage 2: compatibility and portable refinements

Implement official, Ollama, and custom compatibility profiles, conservative
capability precedence, compatible model discovery, header/request differences,
unknown-event tolerance, and unsupported-field omission.

Run enabled Ollama tests for ordinary requests, streaming, tools, reasoning,
usage, and effort-level behavior. Verify `DurationExtension` compatibility and
turn TPS through the standard cumulative usage metadata. Image attachments and
cost estimation remain separate subtasks.

#### Stage 3: Anthropic-specific capabilities

Apply official model capabilities to tags/UI. Distinguish interleaved thinking
from preservation of prior thinking, add official adaptive/manual effort and
budget behavior, and complete hosted thinking continuity.

Add simple automatic prompt caching with an enabled toggle and selectable
supported TTL (`5m` or `1h`). Report provider cache-read and cache-creation usage through
`AnthropicUsageExtension`. Complete selective hosted model-discovery,
streaming, tool, reasoning, caching, usage, error-message, retry, and
cancellation verification.

Run the existing Claude tool package through the provider and fix only
provider-boundary incompatibilities demonstrated by realistic tests. Do not
move provider-specific features from subtasks 011 through 019 into this
baseline.

### Implementation decisions and open questions

- Decision: API-key authentication is the only credential mode implemented by
  010.
- Decision: resolved config is the primary API-key source; direct
  `ANTHROPIC_API_KEY` lookup is fallback-only.
- Decision: official Anthropic and Anthropic-compatible endpoints use one
  provider with explicit compatibility profiles rather than separate provider
  classes.
- Decision: use the official Anthropic Python SDK for request, streaming,
  model, and error transport, configured with the selected base URL.
- Decision: provider transport and native mapping remain usable without
  extensions.
- Decision: tools, reasoning, usage, and prompt caching are separate provider
  extensions.
- Decision: automatic prompt caching is enabled by default for the official
  Anthropic profile, exposes a selectable supported TTL, and is disabled unless
  declared supported for compatible endpoints.
- Decision: usage remains separate from prompt caching; cache-read/write
  counts are surfaced by the usage extension.
- Decision: image attachments and multimodal image-result handling belong to
  subtask 017; PDF and Files API support belongs to subtask 014.
- Decision: maintained model-price cost estimation and cached-token estimation
  belong to subtask 018.
- Decision: 010 uses the current generic request-error event. It sanitizes
  provider failures but does not add the cross-layer structured provider-error
  contract owned by subtask 019.
- Decision: retries are provider-owned; authentication lifecycle remains owned
  by auth plugins rather than frontends.
- Decision: Stage 3 models interleaved thinking and preserved prior thinking as
  separate capabilities.
- Decision: Anthropic request-body reasoning parameters are raw request
  options, not a second normalized configuration API in
  `AnthropicReasoningExtension`.
- Decision: `AnthropicReasoningExtension` owns output interpretation and
  provider-native reasoning continuity but contributes no config schema or UI.
- Decision: provider `betas` and beta-header arrays select SDK/beta transport
  mechanics; structured beta request bodies remain ordinary request options.
- Decision: the canonical bank-file reasoning-size contract is the standard
  reasoning/tool and cross-request preservation acceptance test.
- Decision: server web search and web fetch belong to subtask 011.

### Documentation

- Implement against the package-owned specification and update its requirements
  throughout delivery.
- Add the package README and current user docs for installation,
  configuration, API keys, model discovery, compatibility profiles, tools,
  reasoning, usage, caching, errors, and hosted tests when those
  behaviors are delivered.
- Add package development documentation mapping implementation entry points to
  the specification without redefining the contract.
- Update the public portable provider standard only for behavior that is
  actually delivered and reusable.

### Task checklist

- [x] Create provider package, descriptor, metadata, and test configuration.
- [x] Complete Stage 1 core provider, tools, reasoning, usage, and deterministic
  acceptance.
- [x] Complete the approved Stage 1 config-first reasoning, beta transport,
  bank-file continuity, and portable conformance follow-up.
- [ ] Complete Stage 2 compatibility profiles, Ollama effort/usage coverage,
  duration/TPS interoperability, and unsupported-field acceptance.
- [ ] Complete Stage 3 official capability, interleaved/preserved thinking,
  automatic caching/TTL, and hosted acceptance.
- [x] Add safe generic error messages and provider-owned retry behavior.
- [x] Document delivered behavior and limitations.
- [x] Update package and portable requirements with concrete evidence.

### Requirement verification

- Provider contract tests prove request construction, native conversion,
  content-block streaming, finalization, cancellation, and error redaction.
- Extension contract tests prove feature ownership, enablement, request
  shaping, metadata, usage formatting, and operation without unrelated
  extensions.
- Application integration proves ordinary and tool-enabled requests.
- Ollama integration proves the `messages-basic`, `messages-agent`, and
  `compatible-local` profiles, effort behavior, usage, and duration/TPS
  interoperability for supported capabilities.
- Hosted Anthropic tests prove capability discovery, caching, thinking
  continuity, and official authentication/error behavior.
- Cancellation and sanitized provider failures produce the current expected
  application events without secret disclosure.

### Additional implementation verification

- Multi-turn native history survives application persistence/reload.
- Thinking and redacted-thinking blocks remain ordered and signatures survive
  tool rounds.
- Tool-result payloads do not lose display or provider-native metadata.
- Usage degrades safely when compatible providers omit cache or partial-stream
  fields.
- Prompt-cache settings are omitted for Ollama and other profiles that do not
  declare support.
- Interleaved thinking and preserved prior thinking are independently
  capability-gated and verified.
- Unknown model capability fields are preserved or ignored safely without
  weakening conservative defaults.

## Implementation Notes

### 2026-08-30 Stage 1 implementation

Implemented:

- package metadata and descriptor under `plugins/anthropic-compatible`;
- Anthropic SDK 1.x transport with configured base URL, timeout, API key,
  provider-owned retries, model discovery, ordinary requests, streaming, and
  request-ID cancellation;
- lossless ordered text, thinking, redacted-thinking, signature, tool-use, and
  unknown content-block accumulation;
- provider-native history persistence and reload;
- independent `AnthropicToolsExtension`, `AnthropicReasoningExtension`, and
  `AnthropicUsageExtension` plugin classes;
- self-contained Anthropic tool schema/call accessors so tool execution does
  not depend on `claude-tools` being importable merely to inspect a provider
  call;
- explicit `thinking: disabled` request shaping when reasoning is off, needed
  for local Qwen models that otherwise think by default;
- simple reasoning effort/budget UI and request shaping;
- formatted per-message usage plus tool-turn and session cumulative totals;
- safe generic request errors, API-key redaction, and SDK-owned pre-output
  retries;
- package user documentation and contributor implementation documentation.

Verification completed:

- `pytest plugins/anthropic-compatible/tests -q`: 24 passed, 6 deselected;
- `pytest plugins/anthropic-compatible/tests -m 'integration and ollama' -q`:
  4 passed, 24 deselected using local `qwen3:0.6b`;
- local coverage includes ordinary/streaming text, reasoning, a complete tool
  call/result/follow-up round, usage, reload, descriptor loading, and
  `AgentApplication.send_request`;
- `python -m pyright plugins/anthropic-compatible/src
  plugins/anthropic-compatible/tests`: 0 errors;
- Black and Ruff package checks pass;
- documentation preparation and MkDocs build pass with existing repository
  warnings.

Hosted verification:

- `pytest plugins/anthropic-compatible/tests -m 'integration and api and
  anthropic' -q`: 2 passed, 26 deselected;
- official model discovery, API-key authentication, a tiny non-streaming
  request, streamed thinking, tool use, tool-result continuation, usage, and
  finalization passed on 2026-08-30;
- Stage 1 is complete and stops at its approved checkpoint before Stage 2.

Findings:

- `qwen3:0.6b` reliably exercised text, streaming, tools, thinking, and usage;
  the `qwen3.5:0.8b` fallback was not needed;
- the official API rejects thinking when `tool_choice` forces a tool; the
  hosted reasoning/tool scenario therefore uses normal automatic tool
  selection with a strict tool-use prompt;
- official Claude tool smoke testing found and fixed double-wrapping of
  provider-native `tool_result` blocks; the extension now preserves an
  already-native outer result block instead of nesting it;
- the terminal default config now exposes `claude-openrouter` and
  `claude-anthropic`, registers the Anthropic-compatible package, and maps
  `ANTHROPIC_API_KEY` through application configuration;
- the paid `claude-anthropic` default-config Read-tool smoke and the focused
  `claude-openrouter` Read/reasoning smoke both pass;
- `pytest application/python/tests -q`: 359 passed, 91 deselected;
- default-config binary asset selection includes `anthropic-compatible` as a
  preinstalled plugin with the `anthropic_plugins` hidden import;
- Anthropic provider and reasoning configuration elements now use the
  canonical UI shape (`type` for the control kind rather than `ui_type`);
- the reasoning effort selector exposes `low`, `medium`, `high`, `xhigh`, and
  `max`, keeps the default value unset, and labels availability as
  model-specific;
- the paid `claude-anthropic` default-config smoke asserts that the flattened
  session UI exposes renderable reasoning controls before executing the tool
  round;
- Ollama accepted the simple `reasoning_effort` request field, but comparative
  effort behavior remains Stage 2;
- duration/TPS integration remains Stage 2 even though Stage 1 now emits its
  required cumulative input/output fields;
- official capability-driven tags and compatibility profiles remain Stages 2
  and 3.

### 2026-08-31 Stage 1 follow-up

Completed follow-up scope:

- remove request configuration and UI from `AnthropicReasoningExtension`;
- use raw request options for all request-body reasoning and context-management
  controls;
- add provider beta-feature and beta-header configuration plus standard/beta
  SDK selection;
- keep Haiku manual and add current Sonnet adaptive/context-managed default
  profiles;
- port the canonical bank-file reasoning/tool and interrupted-user
  preservation tests to the Anthropic provider package;
- use the bank test's first-versus-second reasoning-size assertions for
  preservation acceptance;
- represent the latest/current-turn-only profile through an evidence-backed
  negative assertion;
- make these conditional tests part of the portable provider conformance
  standard.

Implementation:

- `AnthropicReasoningExtension` now contributes no config schema, UI, feature
  state, or request shaping. It always preserves and projects returned
  thinking/redacted-thinking blocks and signatures.
- Raw `request_options` now own manual, adaptive, disabled, display, effort,
  context-management, and compatible custom request-body fields.
- `AnthropicProvider` reserves `messages`, `system`, and `stream`; partitions
  typed SDK arguments from compatible unknown fields; preserves explicit
  `extra_body`; and forwards unknown fields through the SDK body escape hatch.
- Provider `betas` selects the beta SDK Messages resource. `beta_headers`
  supports raw beta-header features, identifiers are de-duplicated, and an
  explicit `anthropic-beta` header takes precedence.
- `context_management` fails before transport unless the required
  `context-management-2025-06-27` beta is configured.
- Non-streaming responses and streaming message starts preserve returned
  `context_management.applied_edits` metadata.
- Default config keeps `claude-anthropic` as the Haiku 4.5 manual-thinking
  profile and adds `claude-sonnet-anthropic` with Sonnet 5 adaptive thinking,
  summarized display, all effort levels, and keep-all context management.
- The public provider authoring standard and portable specification now
  require the canonical bank-file continuity tests conditionally for
  reasoning-and-tools and cross-request-preservation profiles.

Verification:

- `pytest plugins/anthropic-compatible/tests -q`: 29 passed, 10 deselected.
- `python -m pyright plugins/anthropic-compatible/src
  plugins/anthropic-compatible/tests`: 0 errors.
- Ruff and Black pass for all touched Python files.
- `pytest plugins/anthropic-compatible/tests -m 'integration and ollama' -q`:
  4 passed, 33 deselected with local `qwen3:0.6b`.
- `pytest
  plugins/anthropic-compatible/tests/test_anthropic_api_integration.py -m
  'integration and api and anthropic' -q`: 2 passed.
- The direct Anthropic bank-file suite passed Haiku 4.5 non-streaming,
  Haiku 4.5 streaming, and Sonnet 5 adaptive/context-managed keep-all
  preservation.
- The Sonnet latest-turn-only test passes by asserting
  `cleared_thinking_turns > 0` while complete client-side thinking history
  remains present.
- Existing OpenRouter Claude ordinary and streaming bank cases pass. Its
  interrupted-user profile structurally retains native `reasoning_details`
  but is recorded as a strict hosted expected failure because it recomputes
  the bank result.
- `pytest plugins/openrouter/tests/test_openrouter_reasoning_extension_unit.py
  -q`: 30 passed.
- The focused OpenRouter Claude hosted comparison produced two positive bank
  passes and one expected interrupted-user failure.
- `pytest
  application/python/tests/test_terminal_application_default_config_anthropic_integration.py
  -m 'integration and api and anthropic' -q`: 1 passed.
- `pytest application/python/tests -q`: 359 passed, 91 deselected.
- Documentation preparation and MkDocs build pass with existing repository
  navigation, absolute-link, and griffe warnings.
- `git diff --check` passes.

Findings:

- Sonnet 5 adaptive thinking may return an empty signed thinking block unless
  `thinking.display` is explicitly `summarized`; the default Sonnet profile
  sets that request option so reasoning-size conformance is observable.
- `keep: {"type": "thinking_turns", "value": 1}` does not clear anything
  when only one assistant thinking turn exists. The negative test adds a
  controlled intermediate `WAIT` turn so the original bank reasoning becomes
  eligible for clearing.
- Even after older reasoning is cleared, the newest reasoning turn can carry
  the bank checkpoint and still return `Clock`. Server-reported applied edits,
  not a specific wrong answer, are therefore the stable negative assertion.
- Hosted bank-test configs verify `ANTHROPIC_API_KEY` is present but use the
  provider's fallback lookup instead of storing the secret in pytest-local
  config that could be rendered in a failed assertion traceback.
- The repository-wide OpenRouter fast suite currently has three unrelated
  failures in provider tool-display metadata and web-search default-engine
  expectations. The touched OpenRouter reasoning unit and hosted comparison
  slices pass or xfail as documented.