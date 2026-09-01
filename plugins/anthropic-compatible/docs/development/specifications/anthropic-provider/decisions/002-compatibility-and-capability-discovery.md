# Decision: compatibility and capability discovery

## Context

Official Anthropic model discovery publishes capabilities, while compatible
endpoints may return only IDs or diverge on caching, images, thinking, tools,
usage, and error behavior. Separate providers would duplicate the same
Messages protocol and make tool/history interoperability harder to maintain.

## Decision

Use one `anthropic` provider with:

- official capability-based model discovery;
- baseline streaming, tools, reasoning, and usage tags;
- explicit boolean capability configuration only for non-baseline optional
  extension tags;
- reusable ordinary application mixins/presets for compatible endpoints;
- one provider-native history contract.

Capability keys are added with their owning optional extension. False or
omitted capabilities emit no optional feature tag. Capability config does not
filter requests or replace endpoint validation.

Ollama is the required local compatible configuration and integration target.

## Consequences

- Official model support does not depend on hardcoded name patterns.
- Compatible endpoints can share the baseline provider without claiming full
  Anthropic behavior.
- Compatible presets remain inspectable configuration.
- Capability/tag and real-endpoint tests become part of the provider's
  acceptance boundary.