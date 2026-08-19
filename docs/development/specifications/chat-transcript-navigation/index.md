# Chat transcript navigation

Status: Baseline documented; viewport-preservation correction pending

This cross-package specification defines portable navigation through a chat
transcript in the mobile and desktop applications. It coordinates the
application HTTP message-range contract, shared frontend range planning, and
the independently implemented mobile and desktop transcript viewports.

The specification owns shared behavior, not one native scroll implementation.
Mobile may retain its inverted React Native list and desktop may retain its
macOS scroll coordinator as long as both conform to the portable behavior.

Specification documents:

- [Product behavior](product-spec.md)
- [Portable frontend behavior](frontend-behavior.md)
- [Technical contract](technical-spec.md)
- [Requirements and evidence](requirements.md)

Current implementation owners:

- `application/python/agent_terminal_app`: session-message HTTP ranges and
  snapshot context;
- `packages/frontend-sdk`: message types, chat controller, and shared range
  planning;
- `mobile/crystal-lattice-control-rn`: mobile transcript controls and inverted
  viewport;
- `desktop/crystal-lattice-control-desktop-rn`: desktop transcript controls,
  viewport anchors, and scroll coordination.

The baseline records existing intended behavior and its current evidence. In
particular, preserving a user's place across overlapping range loads is an
existing requirement, but it is not reliably implemented or validated.
Previous/next user-message navigation, direct navigation to an arbitrary
message index, and a lightweight session-wide message outline are future
extensions and are not claimed as baseline behavior.