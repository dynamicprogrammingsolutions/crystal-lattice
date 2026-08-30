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
  formatting, and usage UI.
- [ ] `AnthropicPromptCachingExtension` is included in the baseline and owns
  automatic/explicit caching configuration, UI, request shaping, and retention
  controls.
- [ ] `AnthropicAttachmentsExtension` owns image attachment policy, session
  asset actions, UI, and compatibility gating.
- [ ] Claude-compatible tool schemas, calls, multimodal results, native
  history, reasoning, usage, and cancellation map through existing
  application/core contracts.
- [ ] Provider configuration distinguishes direct Anthropic access,
  Anthropic-compatible endpoints, and OpenRouter access.
- [ ] Authentication, billing, permission, not-found, conflict,
  request-too-large, rate-limit, timeout, overload, provider, transport,
  validation, and cancellation failures map to stable application-facing
  outcomes.

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
- [ ] Unsupported compatible-endpoint features are omitted or fail explicitly
  according to a compatibility profile.
- [ ] Deterministic unit/contract coverage precedes local Ollama and selective
  hosted Anthropic tests.
- [ ] Batch processing and structured outputs are outside this task.

Parent Task:
`tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`

Specification:

- `plugins/anthropic-compatible/docs/development/specifications/anthropic-provider/index.md`
- `docs/development/specifications/portable-provider-implementation/index.md`

Primary requirement IDs:

- `ANTH-001` through `ANTH-015`
- `PPI-001` through `PPI-010`

## Scope

The baseline package directory is `plugins/anthropic-compatible`. Runtime names
use the shorter Anthropic form:

- provider ID: `anthropic`
- provider class: `AnthropicProvider`
- Python module: `anthropic_plugins`
- extension classes: `AnthropicToolsExtension`,
  `AnthropicReasoningExtension`, `AnthropicUsageExtension`,
  `AnthropicPromptCachingExtension`, and
  `AnthropicAttachmentsExtension`

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
  controls.
- The local `../pi` Anthropic provider demonstrates indexed SSE content-block
  reduction, partial tool JSON, thinking signatures, cache compatibility
  controls, and multiple Anthropic-compatible endpoints.

## Execution plan

Status: Draft

Create the first-party package under `plugins/anthropic-compatible` using the
current provider-plugin package conventions and the approved package
specification. Implement the transport-focused provider first, then add the
five required provider extensions as independently tested components.

Use official `/v1/models` capability data for official Anthropic model tags and
UI. Support conservative compatible-endpoint profiles with explicit overrides
when capability metadata is absent. Exercise the baseline through deterministic
fixtures, local Ollama, and selective hosted Anthropic tests.

Run the existing Claude tool package through the provider and fix only
provider-boundary incompatibilities demonstrated by realistic tests. Do not
move provider-specific server features from subtasks 011 through 016 into this
baseline.

### Implementation decisions and open questions

- Decision: API-key authentication is the only credential mode implemented by
  010.
- Decision: resolved config is the primary API-key source; direct
  `ANTHROPIC_API_KEY` lookup is fallback-only.
- Decision: official Anthropic and Anthropic-compatible endpoints use one
  provider with explicit compatibility profiles rather than separate provider
  classes.
- Decision: provider transport and native mapping remain usable without
  extensions.
- Decision: tools, reasoning, usage, prompt caching, and attachments are
  separate provider extensions.
- Decision: automatic prompt caching is enabled by default for the official
  Anthropic profile and disabled unless declared supported for compatible
  endpoints.
- Decision: usage remains separate from prompt caching; cache-read/write
  counts are surfaced by the usage extension.
- Decision: image wire mapping required by tool results is baseline behavior;
  PDF and Files API support belongs to subtask 014.
- Decision: server web search and web fetch belong to subtask 011.
- Open: select the HTTP/SDK transport after comparing cancellation, raw SSE
  visibility, compatible-endpoint behavior, dependency weight, and test seams.
- Open: finalize the generic typed provider-error contract needed to preserve
  stable error categories through the application event layer.

### Documentation

- Implement against the package-owned specification and update its requirements
  throughout delivery.
- Add the package README and current user docs for installation,
  configuration, API keys, model discovery, compatibility profiles, tools,
  reasoning, usage, caching, images, errors, and hosted tests when those
  behaviors are delivered.
- Add package development documentation mapping implementation entry points to
  the specification without redefining the contract.
- Update the public portable provider standard only for behavior that is
  actually delivered and reusable.

### Task checklist

- [ ] Finalize transport and generic provider-error decisions.
- [ ] Create provider package, descriptor, metadata, and test configuration.
- [ ] Implement API-key configuration and redacted request construction.
- [ ] Implement official and compatible model discovery.
- [ ] Implement core/native message conversion and native-history retention.
- [ ] Implement ordinary request, streaming reduction, finalization, and
  cancellation.
- [ ] Implement `AnthropicToolsExtension`.
- [ ] Implement `AnthropicReasoningExtension`.
- [ ] Implement `AnthropicUsageExtension`.
- [ ] Implement `AnthropicPromptCachingExtension`.
- [ ] Implement `AnthropicAttachmentsExtension` for images.
- [ ] Add stable error normalization and retryability metadata.
- [ ] Add deterministic provider, extension, and application tests.
- [ ] Run enabled local Ollama compatibility tests.
- [ ] Run selective hosted Anthropic ordinary, streaming, tool, reasoning,
  caching, image, model-discovery, error, and cancellation smokes.
- [ ] Document delivered behavior and limitations.
- [ ] Update package and portable requirements with concrete evidence.

### Requirement verification

- Provider contract tests prove request construction, native conversion,
  content-block streaming, finalization, cancellation, and error redaction.
- Extension contract tests prove feature ownership, enablement, request
  shaping, metadata, and operation without unrelated extensions.
- Application integration proves ordinary and tool-enabled requests.
- Ollama integration proves the `messages-basic`, `messages-agent`, and
  `compatible-local` profiles for supported capabilities.
- Hosted Anthropic tests prove capability discovery, caching, thinking
  continuity, and official authentication/error behavior.
- Cancellation and classified provider failures produce the expected
  application events without secret disclosure.

### Additional implementation verification

- Multi-turn native history survives application persistence/reload.
- Thinking and redacted-thinking blocks remain ordered and signatures survive
  tool rounds.
- Tool-result payloads do not lose image, display, or provider-native metadata.
- Usage degrades safely when compatible providers omit cache or partial-stream
  fields.
- Prompt-cache settings are omitted for Ollama and other profiles that do not
  declare support.
- Unknown model capability fields are preserved or ignored safely without
  weakening conservative defaults.