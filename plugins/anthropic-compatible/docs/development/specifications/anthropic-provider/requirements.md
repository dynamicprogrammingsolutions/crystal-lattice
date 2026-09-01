# Anthropic provider requirements

These requirements track the live implementation of the
[Anthropic-compatible provider specification](index.md).

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| ANTH-001 | The package exposes provider ID `anthropic`, class `AnthropicProvider`, and the approved separate baseline extensions from `plugins/anthropic-compatible`. | In progress | Automated | Documented | provider, tools, reasoning, and usage classes; Stage 3 caching remains |
| ANTH-002 | API-key mode uses resolved `config["api_key"]` first, may use `ANTHROPIC_API_KEY` only as fallback, and never persists or exposes the credential. | Implemented | Automated | Documented | `tests/test_provider_unit.py`; package README |
| ANTH-003 | Official `/v1/models` discovery retains model capability metadata and derives model UI and capability tags without hardcoded official model-name rules. | In progress | Automated | Documented | discovery/raw capability tests pass; capability-derived tags remain Stage 3 |
| ANTH-004 | The provider supports ordinary and streaming Anthropic Messages requests with coherent full native history and request-ID cancellation. | Implemented | Automated | Documented | provider/stack/Ollama tests; package README |
| ANTH-005 | Core/native conversion preserves ordered text, thinking, redacted-thinking, tool-use, and tool-result content required for multi-turn continuation. | Implemented | Automated | Documented | reducer, stack reload, and Ollama tool tests |
| ANTH-006 | `AnthropicToolsExtension` owns tool configuration, schema injection, streamed call reconstruction, result mapping, interop declarations, and public tool metadata. | Implemented | Automated | Documented | `tests/test_extensions_unit.py`; Ollama tool round |
| ANTH-007 | `AnthropicReasoningExtension` owns streamed reasoning, redacted thinking, public metadata, native-history reconstruction, and signature continuity while raw request options own request-body reasoning fields. | Implemented | Automated | Documented | extension isolation/round-trip tests; manual/adaptive request options and hosted continuity tests |
| ANTH-008 | `AnthropicUsageExtension` owns public input, output, cache-read, cache-creation, turn/session cumulative, formatted, and duration/TPS-compatible usage metadata. | In progress | Automated | Documented | usage unit/stack/Ollama tests; duration/TPS acceptance remains Stage 2 |
| ANTH-009 | `AnthropicPromptCachingExtension` ships in the baseline, supports automatic caching with a selectable supported TTL, and runs only when its required capability tag is present. | Not started | Unverified | Pending | subtask 010 |
| ANTH-010 | `AnthropicAttachmentsExtension` owns image policy/UI/actions while preserving image inputs and multimodal tool results through official and compatible profiles. | Not started | Unverified | Pending | subtask 017 |
| ANTH-011 | Portable structured provider errors preserve stable categories, retryability, statuses, request IDs, and redacted detail through lifecycle hooks and clients without moving provider retries or auth lifecycle ownership. | Not started | Unverified | Pending | subtask 019; portable provider requirements |
| ANTH-012 | Streaming, tools, reasoning, and usage remain baseline provider tags, while explicit boolean capabilities are reserved for non-baseline optional extension tags; compatible endpoint presets remain ordinary inspectable configuration and do not filter explicit request options. | Not started | Unverified | Pending | subtask 010 |
| ANTH-013 | Deterministic contract and application tests cover the provider and every baseline extension. | In progress | Automated | Documented | 29 fast provider tests cover provider/tools/reasoning/usage and beta transport; caching remains |
| ANTH-014 | Enabled local Ollama tests prove the documented compatible-local messages, tools, thinking, usage, effort passthrough, duration/TPS, and model-discovery contracts. | In progress | Automated | Documented | 4 local `qwen3:0.6b` tests pass; full effort/TPS/discovery matrix remains Stage 2 |
| ANTH-015 | Selective hosted Anthropic tests prove official model discovery, API-key auth, streaming, tools, thinking continuity, caching, usage, safe errors, provider-owned retry, and cancellation. | In progress | Automated | Documented | 2 baseline hosted tests, Haiku ordinary/streaming bank continuity, Sonnet keep-all/clearing profiles, and the default-config Read-tool smoke pass; caching and later hosted matrix remain |
| ANTH-016 | Anthropic cost estimation uses a maintained public model-pricing catalog, reported token classes, cache-read/cache-write rates, explicit estimation provenance, and portable cumulative metadata without the Admin Cost API. | Not started | Unverified | Pending | subtask 018 |
| ANTH-017 | Reasoning-and-tools profiles pass the canonical bank-file continuity contract in ordinary and streaming modes, and cross-request preservation profiles satisfy the interrupted-user reasoning-size contract or record an explicit negative profile. | Implemented | Automated | Documented | direct Haiku ordinary/streaming and Sonnet keep-all pass; latest-turn-only reports server-cleared reasoning while native client history remains intact |

## Deferred provider features

Server web tools, fast mode/service tiers, native compaction/context editing,
Files/PDFs/document citations, token counting, and advanced server tools are
owned by subtasks 011 through 016. Image attachments, cost estimation, and
portable provider request errors are owned by subtasks 017 through 019. Their
implementation must add or refine stable requirement IDs before execution.

Message Batches and structured outputs are not planned by this task group.