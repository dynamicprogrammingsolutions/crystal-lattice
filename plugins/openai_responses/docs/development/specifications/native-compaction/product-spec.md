# Native conversation compaction product specification

## Purpose

Long conversations accumulate provider-native messages, tool activity,
reasoning state, attachments, and opaque continuation data. Native compaction
reduces the active history while preserving enough provider state for a later
request to continue coherently.

OpenAI API-key requests and ChatGPT-authenticated Codex requests expose
different compaction protocols. The plugin presents one session action and
selects the correct upstream protocol from the effective compaction
authentication mode.

## Users

Package users need to:

- compact all visible history or a visible prefix;
- continue the conversation after compaction;
- use an OpenAI API key or a saved ChatGPT login;
- override the compaction model when needed;
- force API compaction from a ChatGPT session when an API key is available;
- cancel a background compaction before it commits;
- see clear success, cancellation, conflict, and provider-failure outcomes.

Application clients need one stable background action and do not need to know
which upstream compaction protocol was selected.

## Target behavior

### Protocol selection

The effective compaction authentication mode selects the protocol:

| Effective mode | Protocol | Upstream request |
|---|---|---|
| API | V1 dedicated compact API | Non-streaming `POST /v1/responses/compact` |
| ChatGPT | V2 remote compaction | Streaming `POST /backend-api/codex/responses` |

The setting `use_chatgpt_auth_for_compaction: false` changes a
ChatGPT-authenticated session's compaction mode to API. It therefore requires
an OpenAI API key and uses the V1 endpoint.

### API/V1 compaction

API mode preserves the established compact API contract:

- the selected native prefix is sent through the SDK compact operation;
- model, instructions, input, and timeout are supplied;
- the compact endpoint returns the replacement native output;
- the untouched suffix follows the replacement output;
- existing compact API output shapes remain accepted.

### ChatGPT/V2 compaction

ChatGPT mode follows the current Codex remote-compaction contract:

- the selected native prefix is sent through the normal streaming Responses
  endpoint;
- a transient `compaction_trigger` item is appended to the request;
- the request advertises `remote_compaction_v2`;
- applicable normal-request options are reused;
- the completed stream must contain exactly one encrypted compaction item;
- eligible messages from the request prefix are retained client-side before
  that compaction item;
- the trigger is not persisted;
- the untouched suffix follows the compacted prefix.

### Session and transcript behavior

Compaction may cover all visible messages or a contiguous prefix beginning at
the start of native history. The selected visible range must have a valid
mapping to native history.

Provider-native history is canonical. The visible transcript is rebuilt from
the resulting native history. Users may choose either expanded rebuilt
messages or a compact placeholder projection without changing canonical
native state.

Leading system or developer content rendered from templates is sent in its
effective request form and restored in its stored form where required.

### Background operation

The primary application action starts compaction in the background and returns
acceptance promptly. While it is running:

- progress is visible through a persistent notification;
- another conflicting session operation is not admitted;
- cancellation interrupts the active HTTP operation and revokes commit
  authority;
- a late provider result is not committed after cancellation;
- concurrent history changes are detected before persistence.

Successful completion persists the rebuilt session and requests that mounted
clients reload it. Failure and conflict outcomes remain visible and offer a
retry action.

## Compatibility

### Previous plugin behavior

Earlier plugin versions called `responses.compact()` for both API and ChatGPT
authentication. With the ChatGPT base URL, that produced:

```text
POST /backend-api/codex/responses/compact
```

The ChatGPT backend no longer exposes that legacy route consistently. Current
ChatGPT compaction therefore uses V2 over the normal Responses endpoint.

### Preserved behavior

- API-key mode continues to use the V1 compact endpoint.
- `compaction_model` continues to override the normal request model only for
  compaction.
- `use_chatgpt_auth_for_compaction: false` continues to force API credentials
  and the API endpoint.
- Existing `compaction` and `compaction_summary` native items remain valid
  follow-up input.
- The synchronous compatibility action and the primary background action share
  one compaction backend.

## Non-goals

- Replacing general local, prompt-based summarization in other providers.
- Making the V1 compact endpoint the ChatGPT fallback.
- Persisting `compaction_trigger` as conversation history.
- Exposing transport-version selection as a separate user setting.
- Guaranteeing that every model supports both upstream protocols.
- Defining the general session-operation, notification, or ChatGPT-login
  frameworks.