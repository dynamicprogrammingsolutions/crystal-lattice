# Decision: compatibility and capability discovery

## Context

Official Anthropic model discovery publishes capabilities, while compatible
endpoints may return only IDs or diverge on caching, images, thinking, tools,
usage, and error behavior. Separate providers would duplicate the same
Messages protocol and make tool/history interoperability harder to maintain.

## Decision

Use one `anthropic` provider with:

- official capability-based model discovery;
- named compatibility profiles;
- explicit compatibility overrides;
- conservative defaults when capabilities are absent;
- one provider-native history contract.

Capability precedence is:

1. explicit override;
2. published model capability;
3. named profile;
4. conservative default.

Ollama is the required local compatible profile and integration target.

## Consequences

- Official model support does not depend on hardcoded name patterns.
- Compatible endpoints can share the baseline provider without claiming full
  Anthropic behavior.
- Unsupported request fields are omitted deterministically.
- Profile and override tests become part of the provider's acceptance boundary.