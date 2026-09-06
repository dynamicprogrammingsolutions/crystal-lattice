# Compatible endpoint configuration

## When to share a provider

One provider implementation may support an official API and compatible
endpoints when they share a coherent request, response, streaming, and native
history model.

Use separate providers when compatibility requires materially different:

- message/history semantics;
- tool-call identity;
- stream completion rules;
- credential or security boundaries;
- persisted native data.

## Baseline tags

Provider tags describe the protocol features extensions can rely on.

Features implemented by every supported endpoint in the provider's documented
baseline may remain unconditional tags. Do not require users to repeat those
features in endpoint configuration.

Every advertised baseline tag needs deterministic provider/extension coverage
and real-endpoint verification for each documented compatible setup.

## Non-baseline optional features

Features not supported by every compatible endpoint require explicit gating.
The owning package may use model metadata or a narrow boolean capability
setting to emit the tag required by the optional extension.

Keep optional capability settings minimal:

- add a key only with the extension that consumes it;
- use booleans when only enabled/disabled tag emission is required;
- false or omission emits no optional-feature tag;
- do not use capability config as a second endpoint-documentation language.

Capability or tag config should not select credentials, endpoints, models, or
headers unless those values are ordinary explicit provider configuration.

When a package uses model-name regex fallbacks for optional capability details,
publish equivalent copyable configuration variants. Users must be able to
override an outdated alias or future model mapping without patching plugin
code.

## Inspectable presets

Compatible endpoint convenience setups should be ordinary inspectable
configuration:

- application mixins;
- copied provider examples;
- package-owned default-config fragments.

A hidden named runtime profile is not required when the behavior can be
expressed through normal config.

## Request validation

Providers preserve their protocol invariants, including history-owned message
fields, stream mode, SDK method selection, and required transport headers.

Portable compatibility does not require a provider to pre-validate or remove
every request option that a compatible endpoint may reject. When a user
explicitly sends an incompatible native request option, the normal sanitized
provider error may remain the authoritative signal.

An optional extension whose required tag is absent must not automatically add
its feature request fields.

## Discovery

Normalize the official model catalog first. Compatible catalogs may provide
only IDs and names or another common response envelope.

If discovery fails:

- return an empty list;
- log a bounded redacted warning;
- permit explicit model entry;
- do not invent model capabilities.

## Authentication

Resolved config remains the primary credential source. Secret values stay out
of model data, capability config, logs, and public metadata. Failure never
changes to another provider automatically.

## Testing a compatibility claim

Every advertised feature needs:

- deterministic tag and extension behavior tests;
- positive request/response tests;
- at least one real endpoint test when practical;
- documented model and config prerequisites.

Tests need not duplicate endpoint validation for every explicitly incompatible
request option.

Do not label an endpoint fully compatible when only an ordinary text request
has been tested.