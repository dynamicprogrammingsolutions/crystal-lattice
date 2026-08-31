# Portable provider implementation technical specification

## Scope and ownership

The portable contract coordinates:

- `agent_core` provider, extension, feature, and tool protocols;
- application request, tool-loop, cancellation, and event behavior;
- individual provider plugin packages;
- the public authoring standard under `plugins/docs`;
- standard deterministic and integration test boundaries.

Wire protocols, credentials, model capabilities, retry policy, and optional
features remain package-owned refinements.

## Provider bundle structure

A substantial provider integration normally contains:

```text
provider package
├── provider
├── provider extensions
├── descriptor metadata
├── deterministic tests
├── compatible/hosted integration tests
├── README and user documentation
└── development specification and implementation mapping when warranted
```

The provider must be usable for its minimal ordinary request contract without
optional extensions. A bundle may register extensions automatically, but tag
and capability resolution decides which extensions are active.

## Provider responsibilities

The provider owns:

- provider identity;
- transport and client lifecycle;
- credential consumption, not interactive acquisition;
- base request construction;
- core/native conversion;
- ordinary and streaming API calls;
- raw stream parsing;
- completed native history;
- request-ID cancellation;
- raw provider error normalization;
- model discovery where supported;
- narrow transport hooks required by active extensions.

Providers must not silently select a different provider or paid service after
a failure.

## Extension responsibilities

A provider-specific feature extension owns:

- tags and required tags;
- model/capability gating;
- provider-native feature accumulation/finalization;
- public metadata and displays;
- feature-specific tests and docs.

The extension also owns configuration, UI, normalized state, and request
shaping when the package defines a provider-specific user contract. When the
feature maps directly to versioned provider request keys, the generic
request-options feature may own injection and declarative UI while the
provider-specific extension retains response interpretation, native-history,
metadata, tests, and documentation.

The provider may execute mechanics that cannot be separated from transport,
including retrying a feature-specific request or parsing a shared event. Those
mechanics consume normalized extension state and do not independently define
config, UI, or enablement.

Generic cold-path behavior that is portable across providers may remain a
feature plugin. Multi-session, persistence, login, or background operation
behavior belongs in an application plugin.

## Configuration and credentials

Provider configuration is a resolved immutable-by-convention mapping shared
with extensions and features.

- Explicit resolved config is the primary credential source.
- Direct environment lookup is optional fallback behavior and never overrides
  explicit config.
- Interactive login and persistence remain outside provider code.
- Runtime-only credentials are not written to session history or public
  metadata.
- Config names should align across provider packages when the concepts are
  genuinely equivalent.

Providers using a typed SDK define how raw request options are partitioned
between supported SDK arguments and an SDK body escape hatch. Messages,
history-derived system content, and stream mode remain provider-owned. SDK
variant selection, beta feature arrays, and beta-header composition remain
provider transport configuration rather than frontend behavior.

## Model discovery and capabilities

Providers should implement model discovery when the endpoint exposes an
authoritative catalog.

Model descriptors:

- contain a non-empty `id`;
- retain a display name when available;
- retain provider-published capability data where useful;
- derive stable tags used by extension resolution;
- preserve conservative behavior when capabilities are absent.

Discovery failures return an empty list rather than preventing explicit model
configuration. Providers should not infer unstable capability sets from model
names when authoritative metadata or explicit compatibility config is
available.

## Compatibility profiles

A provider protocol may be implemented by official and compatible endpoints.
One provider may support them when:

- the native message/history contract is coherent;
- differences are represented through named profiles or explicit overrides;
- unsupported fields are omitted or rejected before transport;
- errors identify the actual endpoint/provider;
- tests cover each claimed profile.

Capability precedence:

1. explicit disable or override;
2. authoritative model/endpoint capability;
3. named profile;
4. conservative default.

Compatibility must not mean silent fallback to a different transport,
provider, or paid account.

## Native conversion and history

Providers return coherent full native history:

- append completed native messages;
- do not append raw chunks or scratch buffers;
- preserve opaque fields required for follow-up requests;
- preserve tool-call IDs and result relationships;
- preserve reasoning signatures or continuation state;
- use internal metadata only for reconstruction/display data not sent on wire;
- support conversion of a single newly added core message.

When conversion is lossy, provider-native history is canonical for continuation
and core messages are the user-visible projection.

## Streaming

Streaming partials are chunk-local. The accumulator contains the growing
provider-native final message. Extensions merge into shared state without
discarding unknown keys.

Custom stream reducers are preferred for indexed content blocks, multiple
event types, partial tool JSON, rewinds, or protocol-specific completion
requirements.

A completed stream produces the same final native/core contract as a
non-streaming request. Premature or malformed completion is an error, not a
partial final.

## Tools

Providers and extensions use the request-bound tool interop registry:

- declare accepted schema formats;
- declare emitted call formats;
- adapt schemas during request initialization;
- preserve provider-native call shapes where supported;
- sanitize calls before native-history persistence;
- convert tool-result messages through provider/native conversion.

Tool-result display and structured payload metadata must survive tool execution
and session reload.

## Usage and performance metadata

Substantial generative providers implement usage through a provider extension
when the upstream response exposes token counts.

The extension owns:

- usage config and UI;
- provider-native usage normalization;
- formatted per-message fields;
- turn-cumulative input/output usage;
- session-cumulative usage;
- raw provider usage;
- persistence/rebuild;
- compatibility with duration/TPS calculation.

At minimum, normalized metadata distinguishes input, output, total, reasoning,
cache-read, and cache-write tokens when the provider reports them.

Turn-cumulative usage is retained in stable internal metadata so
`DurationExtension` and equivalent performance features can calculate turn TPS
without understanding provider-native usage.

## Cost estimation

Locally calculated monetary values are cost estimates.

Portable precedence:

1. provider-reported request cost when present;
2. provider-reported token classes with maintained/configured model rates;
3. estimated cache/token classes with maintained/configured model rates;
4. no cost value when rates or required usage are incomplete.

Metadata distinguishes reported and estimated values. Estimated cache counts
remain separate from raw provider usage and never masquerade as provider
reported values.

Maintained model-pricing catalogs:

- are checked-in runtime inputs;
- record their source and refresh time;
- resolve documented model aliases;
- support input, cached-input, cache-write where applicable, and output rates;
- are refreshed through explicit maintainer tooling rather than live request
  traffic;
- produce no estimate for unknown or incomplete entries.

Generic formatting, cumulative calculations, cached-token estimation, and
cost-estimation helpers should be shared across providers. Native usage mapping
and provider-specific rate classes remain provider-extension concerns.

## Cancellation

Providers register active transports by request ID and close/cancel the
matching operation when requested. Cancellation:

- emits the portable cancellation outcome;
- prevents retries and completed-history append;
- is idempotent;
- cleans up active runtime state.

## Errors and redaction

The target application-facing provider error includes:

- stable category;
- safe message;
- provider and request ID;
- HTTP status when present;
- retryability;
- bounded redacted details.

The shared application layer preserves structured provider errors rather than
collapsing them to untyped text. Provider packages map native error types into
the shared categories and may retain a safe provider-native subtype.

Provider request retries remain provider-owned. The portable error event
communicates what happened and whether a retry may be meaningful; it does not
execute retries.

Authentication acquisition, refresh, login status, and logout remain
application-plugin responsibilities. Frontends render error state and invoke
plugin actions but do not own credential lifecycle.

Authorization values, credentials, full sensitive payloads, and raw user
content are excluded from ordinary logs and errors.

## Verification profiles

### Deterministic

Every provider package covers:

- config and credential precedence;
- request construction and redaction;
- core/native conversion;
- ordinary and streaming finalization;
- tool mappings where supported;
- native history;
- cancellation;
- error normalization;
- extension enablement/disablement;
- compatibility overrides.
- normalized usage and formatting when usage is supported;
- turn/session cumulative usage and duration/TPS compatibility;
- cost-estimation provenance and pricing-catalog behavior when cost estimation
  is supported.

### Application integration

At least one test uses the public application/core flow for ordinary and
tool-enabled requests and verifies persistence/reload when native history is
material.

### Local compatible endpoint

Protocols with a practical local implementation should define a local
compatibility profile and run enabled integration tests for the supported
subset. Unsupported capabilities require negative/omission tests.

### Hosted provider

Selective hosted tests verify official behavior that deterministic or local
compatible endpoints cannot prove. Hosted tests are marked for credentials,
cost, latency, and provider selection.

Skipped gated tests are reported as not run unless the gate was explicitly
enabled and the skip is expected.

### Reasoning and tools

Every provider/profile claiming both reasoning and tools runs the canonical
bank-file reasoning continuity test in streaming and non-streaming modes.
Profiles claiming preservation across an inserted user request also run the
interrupted-user variant and verify that follow-up reasoning is absent or
materially shorter than the initial reasoning while the result remains
`Clock`.

Profiles intentionally retaining insufficient reasoning history use a strict
expected failure or documented negative assertion. Provider-native reasoning
state and tool relationships remain structurally valid regardless of the
server-side retention policy.

## Documentation

Each substantial provider package documents:

- installation/loading;
- first successful request;
- configuration and credential sources;
- model discovery;
- supported extensions;
- compatibility profiles;
- tools and native-history limitations;
- errors, retries, and cancellation;
- deterministic and hosted test commands;
- provider-specific limitations.

Development documentation maps implementation entry points to the package
specification without redefining the contract.