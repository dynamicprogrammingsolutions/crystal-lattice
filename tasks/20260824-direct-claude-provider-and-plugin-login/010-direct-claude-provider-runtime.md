# Anthropic-Compatible Provider Runtime

Implement the API-key baseline for the `anthropic` provider and its stable
credential, request, streaming, extension, compatibility, and error contracts.

## Requirements checklist

### Functional requirements

- [ ] `AnthropicProvider` supports ordinary and streaming requests through the
  standard provider plugin interfaces.
- [ ] API-key authentication consumes resolved `config["api_key"]` as the
  primary credential input, with direct environment lookup only as a secondary
  fallback.
- [ ] Official Anthropic model discovery uses `/v1/models`, retains published
  capability metadata, and derives capability tags and model UI options from
  the response.
- [ ] Configurable base and model-discovery URLs support the documented
  Anthropic-compatible subset through providers such as local Ollama.
- [ ] `AnthropicToolsExtension` owns tool schema injection, streamed tool-call
  reconstruction, tool-call/result mapping, and tool interop declarations.
- [ ] `AnthropicReasoningExtension` owns thinking configuration, UI,
  enablement, streamed thinking, redacted thinking, effort, and signature
  preservation.
- [ ] `AnthropicUsageExtension` owns public usage metadata, cache accounting,
  formatting, turn/session totals, duration/TPS interoperability, and usage
  UI.
- [ ] `AnthropicPromptCachingExtension` is included in the baseline and owns
  automatic caching configuration, selectable supported TTL, UI, request
  shaping, and cache-usage collection.
- [ ] Claude-compatible tool schemas, calls, native history, reasoning, usage,
  and cancellation map through existing application/core contracts.
- [ ] Provider configuration distinguishes direct Anthropic access,
  Anthropic-compatible endpoints, and OpenRouter access.
- [ ] Provider failures are sanitized, redacted, and emitted through the
  current generic request-error event; cancellation retains its existing typed
  outcome.

### Non-functional requirements

- [ ] Provider code does not embed OAuth login UI, credential acquisition,
  refresh, or persistence logic.
- [ ] Credential and authorization values are redacted from logs, errors, and
  diagnostics.
- [ ] Direct-provider failures never silently fall back to OpenRouter or
  another paid provider.
- [ ] The provider works for ordinary text requests without optional
  extensions or tools.
- [ ] Provider-specific feature configuration, UI, tags, enablement, and
  public metadata remain in extensions even when transport mechanics require a
  narrow provider hook.
- [ ] Provider request retry remains owned by `AnthropicProvider`.
- [ ] Unsupported compatible-endpoint features are omitted or fail explicitly
  according to a compatibility profile.
- [ ] Deterministic unit/contract coverage precedes local Ollama and selective
  hosted Anthropic tests.
- [ ] Batch processing and structured outputs are outside this task.
- [ ] Image attachments, model-price cost estimation, and the portable
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

## Execution plan

Status: Draft

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

- [ ] Create provider package, descriptor, metadata, and test configuration.
- [ ] Complete Stage 1 core provider, tools, reasoning, usage, and deterministic
  acceptance.
- [ ] Complete Stage 2 compatibility profiles, Ollama effort/usage coverage,
  duration/TPS interoperability, and unsupported-field acceptance.
- [ ] Complete Stage 3 official capability, interleaved/preserved thinking,
  automatic caching/TTL, and hosted acceptance.
- [ ] Add safe generic error messages and provider-owned retry behavior.
- [ ] Document delivered behavior and limitations.
- [ ] Update package and portable requirements with concrete evidence.

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