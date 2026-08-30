# Anthropic provider requirements

These requirements track the live implementation of the
[Anthropic-compatible provider specification](index.md).

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| ANTH-001 | The package exposes provider ID `anthropic`, class `AnthropicProvider`, and the approved separate baseline extensions from `plugins/anthropic-compatible`. | Not started | Unverified | Pending | `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md` |
| ANTH-002 | API-key mode uses resolved `config["api_key"]` first, may use `ANTHROPIC_API_KEY` only as fallback, and never persists or exposes the credential. | Not started | Unverified | Pending | subtask 010 |
| ANTH-003 | Official `/v1/models` discovery retains model capability metadata and derives model UI and capability tags without hardcoded official model-name rules. | Not started | Unverified | Pending | subtask 010 |
| ANTH-004 | The provider supports ordinary and streaming Anthropic Messages requests with coherent full native history and request-ID cancellation. | Not started | Unverified | Pending | subtask 010 |
| ANTH-005 | Core/native conversion preserves ordered text, thinking, redacted-thinking, tool-use, and tool-result content required for multi-turn continuation. | Not started | Unverified | Pending | subtask 010 |
| ANTH-006 | `AnthropicToolsExtension` owns tool configuration, schema injection, streamed call reconstruction, result mapping, interop declarations, and public tool metadata. | Not started | Unverified | Pending | subtask 010 |
| ANTH-007 | `AnthropicReasoningExtension` owns thinking configuration/UI, capability gating, effort, streamed reasoning, redacted thinking, and signature continuity. | Not started | Unverified | Pending | subtask 010 |
| ANTH-008 | `AnthropicUsageExtension` owns public input, output, cache-read, cache-creation, turn/session cumulative, formatted, and duration/TPS-compatible usage metadata. | Not started | Unverified | Pending | subtask 010 |
| ANTH-009 | `AnthropicPromptCachingExtension` ships in the baseline, supports automatic caching with a selectable supported TTL, and omits cache fields on unsupported profiles. | Not started | Unverified | Pending | subtask 010 |
| ANTH-010 | `AnthropicAttachmentsExtension` owns image policy/UI/actions while preserving image inputs and multimodal tool results through official and compatible profiles. | Not started | Unverified | Pending | subtask 017 |
| ANTH-011 | Portable structured provider errors preserve stable categories, retryability, statuses, request IDs, and redacted detail through lifecycle hooks and clients without moving provider retries or auth lifecycle ownership. | Not started | Unverified | Pending | subtask 019; portable provider requirements |
| ANTH-012 | The official, Ollama, and custom compatibility profiles use conservative capability precedence and never silently enable unsupported request fields. | Not started | Unverified | Pending | subtask 010 |
| ANTH-013 | Deterministic contract and application tests cover the provider and every baseline extension. | Not started | Unverified | Pending | subtask 010 |
| ANTH-014 | Enabled local Ollama tests prove the documented compatible-local messages, tools, thinking, usage, effort, duration/TPS, model-discovery, and omission contracts. | Not started | Unverified | Pending | subtask 010 |
| ANTH-015 | Selective hosted Anthropic tests prove official model discovery, API-key auth, streaming, tools, thinking continuity, caching, usage, safe errors, provider-owned retry, and cancellation. | Not started | Unverified | Pending | subtask 010 |
| ANTH-016 | Anthropic cost estimation uses a maintained public model-pricing catalog, reported token classes, cache-read/cache-write rates, explicit estimation provenance, and portable cumulative metadata without the Admin Cost API. | Not started | Unverified | Pending | subtask 018 |

## Deferred provider features

Server web tools, fast mode/service tiers, native compaction/context editing,
Files/PDFs/document citations, token counting, and advanced server tools are
owned by subtasks 011 through 016. Image attachments, cost estimation, and
portable provider request errors are owned by subtasks 017 through 019. Their
implementation must add or refine stable requirement IDs before execution.

Message Batches and structured outputs are not planned by this task group.