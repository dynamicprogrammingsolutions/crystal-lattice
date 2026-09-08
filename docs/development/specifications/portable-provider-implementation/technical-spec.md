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

A provider may split generic interpretation from provider-specific controls:

- a baseline extension interprets and preserves response/native-history data
  shared by compatible endpoints;
- a capability-gated controls extension enriches model descriptors, owns exact
  provider-specific settings and UI, and maps those settings into request
  fields;
- raw request options execute later as the final protocol escape hatch.

Authoritative model descriptors win over package fallbacks. Packages that use
regex fallbacks for known models document equivalent copyable configuration
variants so users can override or repair the mapping without changing plugin
code.

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

Feature-owning extensions may enrich descriptors with normalized capability
subtrees used by their own UI and request shaping. Explicit capability details
may override discovered or fallback values.

Discovery failures return an empty list rather than preventing explicit model
configuration. Providers should not infer unstable capability sets from model
names when authoritative metadata or explicit compatibility config is
available.

## Portable model-selection UI

A provider with a selectable string model exposes one ordinary
`ui_type: "config"` element bound to `key: "model"`.

- The element uses `type: "dropdown"` and string value/label options, including
  an empty option list when discovery fails.
- Nested `custom_value` settings keep explicit model IDs usable through the
  same searchable field when the authoritative catalog is incomplete or
  unavailable.
- Provider model selection writes the ordinary session `model` override. It
  does not define a provider-specific UI type or application action.

The same config element may include a self-contained compact presentation:

```json
{
  "ui_type": "config",
  "type": "dropdown",
  "key": "model",
  "label": "Model",
  "icon": "cpu",
  "options": [
    {"value": "provider/model-a", "label": "Model A"}
  ],
  "placeholder": "Search models or enter a model ID",
  "custom_value": {
    "enabled": true,
    "pattern": "^[^\\s]+$",
    "option_label": "Use '{value}' as a custom model ID"
  },
  "rich_ui": {
    "kind": "dropdown",
    "label": "Model",
    "show_label": false,
    "options": [
      {"value": "provider/model-a", "label": "Model A"}
    ],
    "placeholder": "Search models or enter a model ID",
    "custom_value": {
      "enabled": true,
      "pattern": "^[^\\s]+$",
      "option_label": "Use '{value}' as a custom model ID"
    },
    "placements": ["composer"],
    "default_pinned": true
  }
}
```

The containing config element owns setting identity, effective-value
resolution, mutation, defaults, disabled state, reset behavior, and the
ordinary/fallback label and icon. `rich_ui` owns compact presentation and
repeats its compact label, options, searchable custom entry, placement, and
pinning fields. Normal action menus and frontends without rich-UI support use
the outer label and icon without interpreting `rich_ui`.

The one dropdown input filters declared labels/values and offers a synthetic
custom option when the trimmed query fully matches `custom_value.pattern`.
Option entries may carry semantic `tone` and `icon` fields. A selected option
icon overrides the outer icon only for compact presentation; otherwise the
compact control uses the outer icon. `rich_ui.show_icon: false` suppresses the
icon in compact presentation while retaining the ordinary fallback icon.
Compact controls may hide their visual label and apply host-specific visual
truncation while retaining the full accessibility value.

Boolean settings may use `rich_ui.kind: "toggle"` with exactly one `false` and
one `true` option. False defaults to the primary tone, true to success, and a
disabled control to muted. A provider or feature adopts this presentation only
within its own approved contract; portable UI support does not imply migrating
unrelated plugins or request-option schemas.

`plugins/dummy-rich-config-ui` is the reference manual-test consumer for
semantic option icons and tones. It is disabled by default, can be enabled for
an ordinary agent, and exercises dropdown, toggle, placement, pinning, and
disabled-state rendering without affecting provider requests.

Initial chat placements are `session_header` and `composer`. Placement is
additive: the complete setting remains available in Session Settings.
Unknown rich kinds remain transportable and fall back to the ordinary setting.

Ordinary `session_action` elements may use their existing rich toggle/list
contract at the same chat placements. The ordinary action and dialog remain
the execution and fallback path.

Composer hosts may explicitly enable a two-row pinned-action layout. The
default remains one row. A two-row host declares whether the leftover row is
above or below the primary row; both rows align from the right and excess
controls remain available through the ordinary menu.

## Compatible endpoint capabilities and presets

A provider protocol may be implemented by official and compatible endpoints.
One provider may support them when:

- the native message/history contract is coherent;
- non-baseline optional plugin features are gated by explicit provider tags;
- reusable endpoint setups remain ordinary inspectable configuration or
  mixins;
- explicit request options retain their provider-native meaning;
- errors identify the actual endpoint/provider;
- tests cover each claimed capability.

Baseline protocol tags shared by all supported endpoints remain
provider-defined and need not be repeated in capability config.

When a provider uses explicit capability configuration for non-baseline
optional plugin gating:

- values are booleans;
- true emits the documented optional-feature tag;
- false or omission emits no tag;
- capabilities do not double as request validation or endpoint documentation.

An optional extension whose required tag is absent does not automatically add
its request fields. If a user explicitly supplies an incompatible native
request option, the endpoint/provider error may report the incompatibility.
Portable conformance does not require providers to pre-validate or filter every
compatible-endpoint difference.

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
- compatible-endpoint capability/tag configuration.
- normalized usage and formatting when usage is supported;
- turn/session cumulative usage and duration/TPS compatibility;
- cost-estimation provenance and pricing-catalog behavior when cost estimation
  is supported.

### Application integration

At least one test uses the public application/core flow for ordinary and
tool-enabled requests and verifies persistence/reload when native history is
material.

### Local compatible endpoint

Protocols with a practical local implementation should provide explicit local
configuration or a reusable preset and run enabled integration tests for every
advertised capability. Tests need not duplicate endpoint validation for every
explicit incompatible request option.

### Hosted provider

Selective hosted tests verify official behavior that deterministic or local
compatible endpoints cannot prove. Hosted tests are marked for credentials,
cost, latency, and provider selection.

Skipped gated tests are reported as not run unless the gate was explicitly
enabled and the skip is expected.

### Reasoning and tools

Every provider configuration claiming both reasoning and tools runs the
canonical bank-file reasoning continuity test in streaming and non-streaming
modes. Configurations claiming preservation across an inserted user request
also run the interrupted-user variant and verify that follow-up reasoning is
absent or materially shorter than the initial reasoning while the result
remains `Clock`.

Configurations intentionally retaining insufficient reasoning history use a
strict expected failure or documented negative assertion. Provider-native
reasoning state and tool relationships remain structurally valid regardless of
the server-side retention policy.

## Documentation

Each substantial provider package documents:

- installation/loading;
- first successful request;
- configuration and credential sources;
- model discovery;
- supported extensions;
- compatible endpoint configuration, capabilities, and presets;
- tools and native-history limitations;
- errors, retries, and cancellation;
- deterministic and hosted test commands;
- provider-specific limitations.

Development documentation maps implementation entry points to the package
specification without redefining the contract.