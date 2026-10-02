# Provider-native context maintenance

Provider-native compaction and context editing are optional protocol features.
They are different from provider-independent prompt summarization:

- generic summarization creates ordinary text through portable application
  behavior;
- native compaction returns provider-defined continuation state that must be
  preserved and replayed;
- native context editing changes the provider's active context according to
  provider-defined policy and may not return a replacement client transcript.

## Ownership

Use provider extensions for native compaction and context-editing controls.
The extension owns:

- capability/model gating;
- config and UI;
- request shaping;
- response interpretation;
- public non-sensitive metadata;
- feature tests and user documentation.

The provider owns inseparable transport mechanics:

- SDK resource selection;
- beta/version header composition;
- raw content-block or stream-event reduction shared with other extensions;
- request cancellation and raw errors.

Use an application plugin only when the upstream protocol exposes a genuinely
separate long-running operation that needs background progress, conflict
handling, or persistence reconciliation. Do not copy another provider's
background compaction lifecycle onto an ordinary request-time protocol.

## Native history

Provider-returned compaction and continuation blocks are canonical native
history:

- preserve all required opaque fields;
- remove only runtime parser scratch data;
- survive persistence and reload;
- return unchanged on the next request;
- never reconstruct encrypted or signed data from visible text.

The visible transcript may show a placeholder or status, but that projection
must not replace native continuation data.

Server-side context editing does not authorize local transcript deletion. Only
rewrite local/native history when the provider returns a replacement history
and the package specification defines its application.

## Capability matrix

Model the upstream features separately:

| Capability | Provider extension behavior |
|---|---|
| Automatic compaction | Adds the provider's ordinary-request threshold/policy and preserves returned continuation state |
| Reasoning retention | Controls whether earlier provider reasoning is available to later sampling |
| Selective tool-use clearing | Removes old tool interactions through an explicit provider policy |
| Manual compaction | Runs a distinct provider operation over full history or a selected prefix |

Do not implement a synthetic setting merely so two provider packages have the
same number of controls. General truncation is not selective tool-use
clearing, and a plain text summary is not opaque native compaction. Document
unsupported rows explicitly.

Anthropic exposes automatic compaction, thinking retention, and selective
tool-use clearing. OpenAI Responses exposes automatic compaction, reasoning
retention, and a separate manual compaction operation, but no independent
tool-use-clearing strategy.

## Capabilities and compatible endpoints

Native context maintenance is normally an optional feature tag. Authoritative
model descriptors are preferred. Explicit boolean capabilities can opt a
compatible endpoint in.

When support is absent:

- the extension contributes no automatic request fields;
- feature UI is omitted;
- baseline provider behavior remains available.

Explicit raw request options may still reach the endpoint. The provider need
not pre-filter every unsupported option.

## Usage

Some providers report compaction as separate internal iterations whose tokens
are absent from top-level request usage. In that case:

- use the complete iteration breakdown as authoritative;
- include each billable iteration exactly once in normalized totals;
- retain separate compaction token classes for display and cost estimation;
- keep raw provider usage for forward compatibility;
- verify duration/TPS semantics against the normalized total.

## Standard tests

Deterministic tests cover:

- each claimed capability independently, including explicit absence of nearby
  but unsupported capabilities;
- support tags and unsupported omission;
- config/UI and request shaping;
- version/beta composition;
- complete ordinary and streaming continuation blocks;
- malformed or incomplete completion;
- cancellation without partial-history commit;
- applied-edit metadata without unintended local deletion;
- iteration usage without double counting;
- coexistence with tools, reasoning, attachments, and prompt caching where
  applicable.

Persistence coverage reloads the session through a new Core/application
instance and verifies that the next request receives the original opaque
continuation block.

Use a hosted test when a local compatible endpoint cannot produce real native
compaction. Prefer one focused model and the smallest supported trigger.