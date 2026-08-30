# Provider implementation standard

Use this standard when creating or materially expanding a provider plugin
bundle.

It complements the detailed provider, extension, tool-interop, packaging, and
testing guides by defining the minimum portable boundaries expected from a
substantial provider implementation.

## Documents

- [Runtime contract](runtime-contract.md): provider lifecycle, conversion,
  streaming, native history, cancellation, errors, and redaction.
- [Feature ownership](feature-ownership.md): provider versus extension,
  feature, tool, and application responsibilities.
- [Compatibility profiles](compatibility-profiles.md): official and compatible
  endpoints, model capabilities, overrides, and fallback rules.
- [Conformance testing](conformance-testing.md): deterministic, application,
  local-compatible, and hosted verification.
- [Package and documentation](package-and-documentation.md): package layout,
  descriptors, README/docs, tests, and delivery checklist.

## Minimum implementation checklist

A substantial provider bundle should provide:

- an explicit provider ID and package;
- ordinary and streaming request support where the API supports streaming;
- core/native conversion and coherent complete native history;
- request-ID cancellation;
- redacted deterministic errors;
- model discovery or an explicit manual-model fallback;
- separate provider extensions for optional provider-specific features;
- request-bound tool interop;
- deterministic provider and extension tests;
- application integration;
- local-compatible or hosted verification appropriate to the protocol;
- current package documentation.

Optional provider features are not universal requirements. When implemented,
they follow the ownership and verification rules in this standard.