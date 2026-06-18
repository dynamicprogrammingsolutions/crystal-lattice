# Audit And Test Tier Design

Define the exact test tiers, file locations, naming conventions, and shared helper boundaries before adding new testing infrastructure.

## Requirements checklist

- [x] Audit current mobile Jest setup, mocks, and component test patterns.
- [x] Audit the existing frontend SDK real-backend integration harness.
- [x] Decide where shared test helpers should live.
- [x] Define naming/placement for fast component tests versus real-backend component integration tests.
- [x] Define which tests should run in default mobile `npm test` versus explicit integration commands.
- [x] Document the intended test tier boundaries.

Parent Task: tasks/20260615-mobile-component-integration-tests/000-main.md

## Known Starting Points

Mobile test setup:

- `mobile/crystal-lattice-control-rn/jest.config.js`
- `mobile/crystal-lattice-control-rn/jest.setup.js`
- `mobile/crystal-lattice-control-rn/__tests__/`
- `mobile/crystal-lattice-control-rn/package.json`

Existing frontend SDK integration setup:

- `packages/frontend-sdk/src/integration/harness.ts`
- `packages/frontend-sdk/src/integration/__tests__/README.md`
- `packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts`

Settings components and logic:

- `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx`
- `packages/frontend-sdk-react/src/useSessionSettingsController.ts`
- `packages/frontend-sdk-react/src/sessionSettings/SessionSettingsHost.tsx`
- `packages/frontend-sdk-react/src/sessionSettings/logic.ts`
- `packages/frontend-sdk-react/src/sessionSettings/logic.test.ts`

## Design Questions

Answer these before implementation:

- Should real-backend component integration tests live under the mobile app, e.g. `mobile/crystal-lattice-control-rn/__integration__/`, or under `packages/frontend-sdk/src/integration` with mobile test dependencies?
- Should backend-start helpers be imported from `packages/frontend-sdk/src/integration/harness.ts`, extracted into a reusable test-support package, or wrapped by mobile-local helpers?
- Should the mobile default `npm test` exclude real-backend tests by pattern?
- What package script should run the real-backend tests? Example: `npm run test:integration:components`.
- How should tests load repo-root `.env` or intentionally avoid hosted provider credentials?

## Acceptance Criteria

- The design identifies exact file locations and commands.
- The design explains which tier should be used for plugin-specific UI schema validation versus generic component rendering.
- The design avoids creating duplicate backend harness code when the frontend SDK integration harness can be reused or wrapped.

## Audit Findings

Added during completion on 2026-06-15.

Mobile app package and test runner:

- `mobile/crystal-lattice-control-rn` is not listed in the repo-root npm workspaces, so mobile test commands should remain local to the mobile package.
- `mobile/crystal-lattice-control-rn/package.json` currently has `test: jest`, `tsc: tsc --noEmit`, and no separate integration test script.
- Existing mobile tests live under `mobile/crystal-lattice-control-rn/__tests__/` and use `react-test-renderer`.
- `@testing-library/react-native` is not currently installed.
- `npm view @testing-library/react-native` showed version `14.0.0`, with peers compatible with the app's React `19.1.1`, React Native `0.82.1`, and Jest `29.x`.

Current mobile Jest setup:

- `mobile/crystal-lattice-control-rn/jest.config.js` uses the `react-native` preset and `jest.setup.js`.
- The current `transformIgnorePatterns` already transforms the local frontend SDK packages and `react-native-url-polyfill`.
- `jest.setup.js` centralizes several native mocks, but `react-native-gesture-handler` is only mocked in one existing test file. App-level tests can still fail on `RNGestureHandlerModule`; this should move into shared setup.
- Existing tests also locally mock `Modal` in at least one file. React Native Testing Library tests will likely need a shared modal mock or a documented per-test choice.

Frontend SDK backend integration harness:

- `packages/frontend-sdk/src/integration/harness.ts` already starts a real FastAPI backend through `scripts/run_backend_server_for_ts_integration_tests.py`.
- The harness creates a temporary config/session root, finds a free port, sets `REPO_ROOT`/`BUILTIN_PLUGINS`, waits on `/api/hello`, and returns `baseUrl`, `port`, `configPath`, `sessionsRoot`, `stdout`, and `stop`.
- `packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts` already demonstrates `FetchTransport` + `RestAgentBackend` against the real backend.
- The mobile real-backend component tier should wrap this harness rather than duplicate Python process startup.

Settings component seams:

- `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx` currently owns both controller wiring and mobile renderers for `checkbox`, `select`, `dropdown`, `text`, `multiline`, `readonly`, and fallback text-like rendering.
- `packages/frontend-sdk-react/src/sessionSettings/SessionSettingsHost.tsx` is generic and renderer-driven, which is a good seam for fast generic rendering tests.
- `packages/frontend-sdk-react/src/useSessionSettingsController.ts` and `packages/frontend-sdk/src/sessionSettings/sessionSettingsController.ts` are the real data-loading path for integration tests.
- Backend-provided UI schema expectations for lightweight default-config path plugins should live in the real-backend component integration example. Prefer path plugins already listed in the app default config and avoid path plugins with heavy install dependencies.

## Design Decisions

Added during completion on 2026-06-15.

Fast component tests:

- Location: `mobile/crystal-lattice-control-rn/__tests__/`.
- Naming: `*.test.tsx`.
- Command: existing `npm test`.
- Dependencies: React Native Testing Library, shared mobile render helper, shared native mocks.
- Scope: generic component behavior only, using in-memory items/controllers/callbacks. Do not load real plugins or start FastAPI.

Real-backend component integration tests:

- Location: `mobile/crystal-lattice-control-rn/__integration__/`.
- Naming: `*.integration.test.tsx`.
- Command: add an explicit mobile script such as `npm run test:components:integration`.
- Jest config: add a separate integration Jest config that reuses the mobile setup but matches only `__integration__/**/*.integration.test.tsx`.
- Backend startup: add a mobile-local wrapper that imports `packages/frontend-sdk/src/integration/harness.ts`, starts the backend, creates `FetchTransport` + `RestAgentBackend`, and exposes cleanup.
- Scope: real backend/plugin/SDK/component contracts, especially plugin-provided UI schema, session overrides, and application-action UI flows.

Shared helper placement:

- Put React Native render helpers under `mobile/crystal-lattice-control-rn/src/testUtils/`.
- Put real-backend integration helpers under `mobile/crystal-lattice-control-rn/__integration__/support/`.
- Keep the backend process startup logic in the SDK harness. The mobile helper should be a thin adapter.

Tier boundary:

- Use fast component tests for generic rendering behavior such as "a select item renders chips and pressing one calls `selectOption`."
- Use real-backend component integration tests for behavior where the source of truth is backend/plugin code, such as "request-options settings from `path:${env:BUILTIN_PLUGINS}/feature-request-options` appear in `SessionSettingsModal` and patch session overrides."
- Do not use either tier as a substitute for simulator/device E2E when testing native permissions, OS-level layout, keyboard behavior, or real deep-link handling.

## Completion Notes

Added during completion on 2026-06-15.

Completed the audit and settled the first implementation shape. The next task should add React Native Testing Library, move common native mocks into shared setup, and create the first fast component smoke test.
