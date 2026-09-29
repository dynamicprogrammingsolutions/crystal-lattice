# Shared human-time telemetry

`@crystal-lattice/frontend-rn-components` owns the headless human-time
telemetry behavior shared by the mobile and macOS applications:

- desktop activity-burst tracking with a configurable inactivity deadline and
  earlier explicit close;
- durable per-connection span cache operations over an injected
  `KeyValueStore`;
- debounced, retry-safe application-action uploads;
- exact cache removal and rejected-span isolation;
- definitive action-failure classification and standard warning emission;
- pure diagnostic entry/status transformations.

The package does not choose an application's settings store, active connection,
surface routing, or diagnostics UI. Mobile supplies an AsyncStorage adapter and
a single-connection provider. Desktop supplies the same storage adapter plus a
multi-connection coordinator and separate-window diagnostics bridge.

## Public entry points

The package root exports:

- `HumanTimeSpanTracker`
- `HumanTimeSpanUploader`
- `appendHumanTimeSpan`, `loadHumanTimeSpans`,
  `removeFirstHumanTimeSpans`, and `removeHumanTimeSpans`
- `emitHumanTimeTelemetryWarning`
- diagnostic status and entry helpers

Cache and uploader consumers must inject a `KeyValueStore`. Keeping platform
storage outside the shared implementation avoids coupling the package to one
AsyncStorage runtime and makes deterministic tests straightforward. Mobile
uses its own foreground-session lifecycle collector and does not use the
activity tracker.

## Verification

The package test proves that one rejected span is retained while valid
neighbors are confirmed and removed. Mobile and desktop provider tests exercise
the shared behavior through their production adapters. Each application also
has a real-backend integration tier covering transport, server action, plugin,
SQLite store, retry deduplication, definitive failures, and rejected-span
isolation.

Run the shared package tests from the repository root:

```bash
npm --workspace @crystal-lattice/frontend-rn-components test
```