# Portable Home, status, and reorder contracts

The shared React Native package owns portable pieces used by mobile and
desktop:

- Watchlist identity and normalization;
- session-ID note normalization and limits;
- `24h`, `3d`, and `1w` Recent Sessions derivation;
- measured reorder target, placeholder, stable-child, and settled translation
  helpers;
- request-status labels, semantic tones, and badge/inline/dot presentation.
- state-aware local Watchlist and note action definitions shared by mobile and
  desktop session-action hosts.

Applications continue to own storage keys, hydration, screen layout,
connection opening, pointer or touch responders, and navigation.
The local action definitions contain only stable keys, labels, icons, order,
and default pin state. Each application handles them against its own local
Watchlist/note provider; they never invoke server-side session pin actions.
Shared action rows expose a button role on every platform. Mobile also exposes
an explicit accessibility activation action; macOS uses the native button
activation path so one accessibility click cannot dispatch the action twice.

`SessionRequestStatusIndicator` always supplies a textual accessibility value.
Dot-only tab presentation therefore does not make status color-only.

Primary tests:

- `src/homeWorkspace.test.ts`
- `src/reorderGeometry.test.ts`
- `src/sessionRequestStatus.test.ts`
- `src/localSessionActions.test.ts`