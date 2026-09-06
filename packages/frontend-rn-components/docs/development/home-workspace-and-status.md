# Portable Home, status, and reorder contracts

The shared React Native package owns portable pieces used by mobile and
desktop:

- Watchlist identity and normalization;
- session-ID note normalization and limits;
- `24h`, `3d`, and `1w` Recent Sessions derivation;
- measured reorder target, placeholder, stable-child, and settled translation
  helpers;
- request-status labels, semantic tones, and badge/inline/dot presentation.

Applications continue to own storage keys, hydration, screen layout,
connection opening, pointer or touch responders, and navigation.

`SessionRequestStatusIndicator` always supplies a textual accessibility value.
Dot-only tab presentation therefore does not make status color-only.

Primary tests:

- `src/homeWorkspace.test.ts`
- `src/reorderGeometry.test.ts`
- `src/sessionRequestStatus.test.ts`