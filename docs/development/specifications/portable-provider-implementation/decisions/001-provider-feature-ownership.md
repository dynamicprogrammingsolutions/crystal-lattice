# Decision: provider feature ownership

## Context

Some provider-specific features are mostly request shaping, while others also
need retries, alternate transport calls, stream parsing, or client lifecycle
inside the provider. Putting the entire feature in the provider makes config,
UI, enablement, tests, and public metadata inseparable from transport.

## Decision

A provider-specific extension owns:

- configuration;
- UI;
- capability gating and tags;
- normalized feature state;
- request shaping;
- public metadata;
- feature tests and documentation.

The provider may implement inseparable transport mechanics, but only through a
narrow state or hook produced by the enabled extension. The provider does not
independently activate or expose the feature.

## Consequences

- Features remain independently selectable and testable.
- Provider code can still own the active HTTP/SDK loop.
- Disabling an extension removes its user-facing and request behavior.
- Cross-provider reusable behavior can be extracted later without moving
  provider transport prematurely.