# Provider compatibility profiles

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

## Profile contents

A named profile may define:

- base endpoint paths;
- authentication header style;
- version and feature headers;
- model-discovery shape;
- stream event support;
- tool schema/call/result differences;
- reasoning fields and continuation rules;
- prompt-cache support;
- attachment source types;
- usage timing and fields;
- error envelopes;
- unsupported request options.

Profiles are immutable-by-convention data and should be directly testable.

## Capability precedence

Resolve capability support in this order:

1. explicit configuration override;
2. authoritative model or endpoint capability;
3. named profile;
4. conservative default.

An explicit disable wins. An endpoint incompatibility can restrict a
model-advertised capability.

## Unsupported features

When a feature is unsupported:

- do not send its request fields;
- do not show misleading config UI;
- do not synthesize success metadata;
- report an explicit unsupported result when directly invoked;
- leave unrelated provider behavior unchanged.

Ignoring a field successfully is not evidence that the endpoint implements the
feature.

## Discovery

Normalize the official model catalog first. Compatible catalogs may provide
only IDs and names.

If discovery fails:

- return an empty list;
- log a bounded redacted warning;
- permit explicit model entry;
- retain conservative feature defaults.

## Authentication

Credential source and header behavior may vary by profile, but:

- resolved config remains primary;
- secret values stay out of profile/model data;
- diagnostics name the actual endpoint/profile;
- failure never changes to another provider automatically.

## Testing a compatibility claim

Every claimed profile needs:

- deterministic request/response fixtures;
- positive tests for supported features;
- negative or omission tests for unsupported fields;
- at least one real endpoint test when practical;
- documented model/config prerequisites.

Do not label an endpoint fully compatible when only an ordinary text request
has been tested.