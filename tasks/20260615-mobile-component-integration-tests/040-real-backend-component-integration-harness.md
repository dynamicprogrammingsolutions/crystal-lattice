# Real-Backend Component Integration Harness

Create a reusable test harness that starts a real FastAPI backend and renders selected mobile components against a real frontend SDK backend.

## Requirements checklist

- [x] Reuse or wrap `packages/frontend-sdk/src/integration/harness.ts` instead of duplicating backend process startup logic.
- [x] Provide a helper to start a backend from a test config and return `RestAgentBackend`, `FetchTransport`, `baseUrl`, and `stop`.
- [x] Provide helpers to create/select sessions for component tests.
- [x] Provide cleanup that always stops backend processes and removes temporary directories.
- [x] Add a package script for this heavier test tier.
- [x] Keep the harness deterministic and local by default, with no hosted-provider keys required.

Parent Task: tasks/20260615-mobile-component-integration-tests/000-main.md
Depends On: tasks/20260615-mobile-component-integration-tests/020-react-native-testing-library-setup.md

## Desired Test Shape

The intended test shape is:

```ts
const started = await startMobileComponentBackend({
  config: {
    providers: {
      test_provider: {
        provider: 'deterministic_stream',
        model: 'test-model',
        timeout: 60,
      },
    },
    plugins: [
      'plugins.deterministic_stream_provider.DeterministicStreamProvider',
      'path:${env:BUILTIN_PLUGINS}/feature-request-options',
    ],
    agents: {
      default: {
        provider: 'test_provider',
        request_options: { temperature: '0.5' },
        request_options_ui: {
          temperature: ['0.0', '0.5', '1.0'],
        },
      },
    },
  },
});

try {
  const created = await started.backend.createSession({ agentId: 'default' });
  renderWithMobileProviders(
    <SessionSettingsModal
      backend={started.backend}
      sessionId={created.session.session_id}
      visible
      onRequestClose={jest.fn()}
    />,
  );
} finally {
  await started.stop();
}
```

The exact config shape should follow the existing backend integration harness conventions, not this sketch if the harness requires different fields.

## Notes

This tier is not a full simulator/device E2E test. It runs in Node/Jest/React Native Testing Library, but uses a real backend process and real HTTP SDK transport. It can validate backend/plugin/SDK/component contracts without opening the full app or a simulator.

Use this tier for:

- real plugin UI schema appearing in a component;
- real session override patching through the SDK;
- action dialog behavior against real application actions;
- controller/transport behavior that cannot be honestly represented by static mock data.

Do not use this tier for:

- native permission behavior;
- actual iOS/Android keyboard/layout behavior;
- OS-specific navigation/deep-link handling;
- visual screenshots.

Those belong to a later Detox/Maestro/Appium-style simulator/device E2E layer.

## Acceptance Criteria

- A shared helper can start and stop a real FastAPI backend from a mobile component test.
- The helper returns a usable `RestAgentBackend`.
- A minimal proof test can create a session through the real backend and render a simple component with the backend passed in.
- The new command is documented and not part of the fastest default unit test run unless explicitly approved.

## Completion Notes

Added during completion on 2026-06-15.

- Added `mobile/crystal-lattice-control-rn/jest.integration.config.js`.
- Added `mobile/crystal-lattice-control-rn/__integration__/support/mobileComponentBackend.ts`.
- Added `npm run test:components:integration`.
- The helper wraps `packages/frontend-sdk/src/integration/harness.ts`, creates `FetchTransport`, creates `RestAgentBackend`, and exposes `createMobileComponentSession`.
- Default `npm test` excludes `__integration__/`, keeping the real-backend tier explicit.
- `mobile/crystal-lattice-control-rn/tsconfig.json` excludes `__integration__/` because the backend harness is Node-only and should not be part of app TypeScript compilation.
