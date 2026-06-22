# Mobile Component And Backend-Integrated Testing

Create a standardized React Native mobile testing approach that covers both fast unit-like component behavior and e2e-like component integration against a real FastAPI backend.

## Task checklist

- [x] `tasks/20260615-mobile-component-integration-tests/010-audit-and-test-tier-design.md`
- [x] `tasks/20260615-mobile-component-integration-tests/020-react-native-testing-library-setup.md`
- [x] `tasks/20260615-mobile-component-integration-tests/030-generic-component-behavior-tests.md`
- [x] `tasks/20260615-mobile-component-integration-tests/040-real-backend-component-integration-harness.md`
- [x] `tasks/20260615-mobile-component-integration-tests/050-session-settings-real-backend-example.md`
- [x] `tasks/20260615-mobile-component-integration-tests/060-ci-and-runbook.md`

## Context

The goal is to avoid copying plugin-produced UI schema into frontend tests when verifying feature-specific behavior. For feature/plugin scenarios, tests should be able to start a real FastAPI backend, load the actual plugin/config, connect through the frontend SDK (`FetchTransport` + `RestAgentBackend`), create/select a real session, then render only the mobile component under test.

At the same time, the test suite still needs fast unit-like component tests for generic frontend behaviors such as:

- rendering `checkbox`, `select`, `dropdown`, `text`, `multiline`, and `readonly` settings controls;
- pressing a chip and seeing callback/patch behavior;
- fallback rendering for unknown component types;
- basic validation/error states;
- mobile-only UI rendering details that should not require backend startup.

The motivating real-backend example is a lightweight plugin from the terminal app's default config:

- `path:${env:BUILTIN_PLUGINS}/feature-request-options`

That plugin is already listed in `application/python/agent_terminal_app/config_openrouter_app_layer.json` and has no runtime dependencies. The real-backend component integration example should verify actual backend-provided request-options settings appear in the mobile settings window and can patch real backend overrides, while avoiding heavier path plugins with large optional dependency trees.

Relevant existing code seams:

- `packages/frontend-sdk/src/integration/harness.ts`
  - Starts a real FastAPI backend for TypeScript integration tests.
- `packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts`
  - Uses real backend + `FetchTransport` + `RestAgentBackend`.
- `packages/frontend-sdk/src/sessionSettings/sessionSettingsController.ts`
  - Loads session UI schema, overrides, config schema, and base config.
- `packages/frontend-sdk-react/src/useSessionSettingsController.ts`
  - React hook used by mobile settings UI.
- `packages/frontend-sdk-react/src/sessionSettings/logic.ts`
  - Filters `ui_type: "config"` and builds setting items.
- `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx`
  - Mobile settings UI and renderers for settings component types.

## Design Intent

Define two test tiers:

1. Fast component tests.
   These use React Native Testing Library and mocked/fake local data. They test generic UI behavior and component rendering without a backend.

2. Real-backend component integration tests.
   These use React Native Testing Library plus the real FastAPI backend harness. They test the real backend/plugin/SDK/frontend contract while rendering only one component or screen slice.

Do not make the real-backend tier the default for every component. Use it when the value is verifying the real source of data, such as plugin UI schema, config schema, session overrides, app actions, or transport/controller behavior.

## Reference Findings

The previous discussion identified a useful prior session:

- `.crystal/sessions/ff01f5c0-3d65-43cb-9ef4-9643d9c40b7c.json`
  - Discusses "true component tests" such as "if button X pressed, text Y appears."
  - Recommends `@testing-library/react-native`, a `renderWithTheme` helper, and care around global mocks.

Current mobile app state from prior audit:

- Existing tests use `react-test-renderer`.
- `@testing-library/react-native` is not installed in `mobile/crystal-lattice-control-rn`.
- Current Jest setup has native-module mocks, but app-level tests can fail on missing native module registration such as `RNGestureHandlerModule` unless setup is corrected.

## Branch And Overlap Notes

Added during completion on 2026-06-15.

- Implementation branch/worktree:
  - Branch: `task/20260615-mobile-component-integration-tests`
  - Worktree: `/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260615-mobile-component-integration-tests`
- Branch history cleanup:
  - The implementation branch was rebased so it no longer contains the temporary PDF example cherry-pick or its revert.
  - This avoids a future merge accidentally reverting the separate message-export/PDF work.
- Checked related branch/worktree:
  - Branch: `task/20260611-action-deeplinks-dialog-select`
  - Worktree: `/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260611-action-deeplinks-dialog-select`
- Overlap finding:
  - The deeplink branch adds `mobile/crystal-lattice-control-rn/__tests__/ApplicationActionDialog.test.tsx` and `mobile/crystal-lattice-control-rn/src/components/applicationActionDialogRenderers.tsx`, but it does not touch mobile `package.json`, `package-lock.json`, `jest.config.js`, `jest.setup.js`, `tsconfig.json`, `README.md`, `SessionSettingsModal`, or the new settings tests.
  - The deeplink branch test still uses `react-test-renderer`, so there was no existing React Native Testing Library setup to cherry-pick.
  - The full deeplink commit was not cherry-picked because it is a broad feature commit touching backend/app routing, mobile app linking, shared RN components, and SDK action helpers. Pulling it into this testing branch would create unnecessary coupling.
  - The new centralized native mocks and Jest aliases should be compatible with that branch when it merges later.

## Execution plan

Added during completion on 2026-06-15.

Approach: staged implementation with verification after each tier.

1. Update task context to use the lightweight default-config path plugin `feature-request-options` as the real-backend example.
2. Audit the current mobile Jest setup, frontend SDK integration harness, and settings modal/component seams.
3. Add React Native Testing Library to the mobile app, centralize native-module mocks, and add a small `renderWithMobileProviders` helper.
4. Add fast generic component tests for settings controls using mocked controller/data rather than plugin-specific fixtures.
5. Add a real-backend component integration harness that wraps the existing frontend SDK backend server harness and returns a usable `RestAgentBackend`.
6. Add a real-backend `SessionSettingsModal` example that loads `path:${env:BUILTIN_PLUGINS}/feature-request-options`, creates a real session, verifies request-options settings appear, and patches real overrides.
7. Add or update package scripts and docs so the fast tier and real-backend tier are easy to run separately.
8. Run focused verification commands, update checklists and completion notes, and report any remaining blockers.

## Completion Notes

Added during completion on 2026-06-15.

- Added fast React Native Testing Library support and generic settings component tests.
- Added explicit real-backend component integration support and a real `SessionSettingsModal` example using the lightweight default-config path plugin `feature-request-options`.
- Updated `SessionSettingsController` so settings include `ui_type: "config"` elements from session application UI schema as well as session UI schema.
- Added mobile docs for the two test tiers.
- Verification passed for mobile Jest, mobile real-backend component integration, and the SDK settings-controller unit test.
- Mobile `npm run tsc` still fails on the pre-existing `AnimatedSplashScreen` `AppLogo` prop mismatch: `type` is not part of `AppLogoProps`.
