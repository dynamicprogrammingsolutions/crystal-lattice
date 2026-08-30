# Anthropic API and compatible-endpoint protocol

## Native request shape

The provider targets the Anthropic Messages protocol:

- system content is supplied separately from the alternating message list;
- user and assistant messages contain strings or ordered content blocks;
- tool results are user content blocks linked by `tool_use_id`;
- assistant tool calls are `tool_use` content blocks;
- thinking and redacted-thinking blocks remain assistant content;
- complete native history is retained for later requests.

Internal `_metadata` may preserve core-only display and reconstruction data but
must be removed before the wire request.

## Core-to-native conversion

### System messages

Leading core system content becomes the provider system field. Multiple
effective system fragments retain their order. Stored template/source
information remains core metadata rather than wire content.

### User messages

Plain text becomes a user string or text block. Image multipart conversion is
added by `AnthropicAttachmentsExtension` when subtask 017 is delivered and the
active profile supports the source type.

### Assistant messages

Assistant text, thinking, redacted thinking, and tool-use blocks retain their
provider-native order. Core `metadata["tool_calls"]` is not a replacement for
canonical native blocks; it is the generic tool-loop view derived by the tools
extension.

### Tool messages

Core tool messages become user messages containing one or more `tool_result`
blocks. The tool call ID is required. Provider-native structured result
payloads are preserved when compatible with the active profile. Plain text
results become text tool-result content.

Consecutive core tool messages may be coalesced into one provider user message
when required by the protocol, without losing core/native index mappings.

## Native-to-core conversion

One provider assistant message normally becomes one core assistant message:

- visible text is joined into `content`;
- tool-use blocks become `metadata["tool_calls"]`;
- thinking becomes `metadata["reasoning"]`;
- provider-native thinking details and signatures remain in native history and
  may be surfaced as bounded metadata;
- usage is attached by the usage extension;
- provider-native indices identify the canonical source.

Tool-result user blocks rebuild as core tool messages where the native-index
mapping permits an unambiguous reconstruction. Ordinary user text remains a
user message. Multimodal image tool-result behavior is refined by the
attachment subtask.

## Streaming event reduction

The reducer supports the provider event lifecycle:

- `message_start`;
- `content_block_start`;
- `content_block_delta`;
- `content_block_stop`;
- `message_delta`;
- `message_stop`;
- provider error events.

Content blocks are keyed by provider index.

### Text

Text deltas emit chunk-local assistant partials and append text to the matching
native block.

### Thinking

Thinking deltas emit chunk-local reasoning partials through the reasoning
extension and append to the matching thinking block. Signature deltas update
native state but are not rendered as user-visible text.

Redacted-thinking blocks are retained as opaque native content and surfaced
only through safe metadata/display conventions.

### Tool input

Tool-use start events create an indexed tool call. Partial JSON deltas append
to a scratch buffer and produce best-effort parsed arguments for streaming
display. Finalization repairs or sanitizes arguments through the active tool
interop registry and removes the scratch buffer before persistence.

### Usage

Initial and final usage fields are retained in private native metadata. Missing
fields do not erase earlier values. The usage extension calculates the public
view.

### Completion

A successful stream requires coherent completion. Raw chunks and scratch
buffers never enter native history. Finalization appends exactly one completed
assistant native message for the turn.

## Thinking continuity

Thinking and redacted-thinking blocks from the latest assistant turn are
preserved exactly and in order for follow-up requests. Tool rounds must not
strip, reorder, rewrite, or synthesize signatures.

When a compatible endpoint does not support thinking signatures, the selected
profile defines whether thinking is omitted, converted to text, or replayed
with an allowed empty signature.

## Stop reasons

Provider stop reasons map to stable core meanings for:

- normal end turn;
- tool use;
- maximum tokens;
- stop sequence;
- refusal;
- context-window limit where distinct;
- cancellation;
- provider error.

Unknown reasons remain available in bounded provider metadata and map to a
safe generic outcome.

## Ordinary requests

Non-streaming responses use the same native assistant block shape and
finalization rules as streaming. Tools, thinking, usage, and attachment
behavior from installed extensions must not differ solely because streaming is
disabled.

## Compatible-endpoint tolerance

The parser ignores unknown additive fields and non-message SSE events.
Malformed known events fail with a bounded protocol error. Missing optional
usage or capabilities degrade safely. The provider never guesses support for a
request field that the active profile has disabled.