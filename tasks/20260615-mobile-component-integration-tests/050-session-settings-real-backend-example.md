# Session Settings Real-Backend Example

Add a concrete real-backend component integration test for `SessionSettingsModal`, using the lightweight default-config path plugin `feature-request-options` as the example.

## Requirements checklist

- [x] Start a real FastAPI backend with `path:${env:BUILTIN_PLUGINS}/feature-request-options` loaded.
- [x] Create a real session through `RestAgentBackend`.
- [x] Render `SessionSettingsModal` against the real backend and session.
- [x] Assert the actual backend-provided request-options config settings appear in the settings modal.
- [x] Change request-options settings and verify the real backend receives/stores the session overrides.
- [x] Keep plugin-specific assertions in this real-backend test, not in generic component tests.

Parent Task: tasks/20260615-mobile-component-integration-tests/000-main.md
Depends On: tasks/20260615-mobile-component-integration-tests/040-real-backend-component-integration-harness.md

## Motivating Config

The motivating lightweight path plugin is:

- `path:${env:BUILTIN_PLUGINS}/feature-request-options`

Known backend-side expectations:

- `feature-request-options` is listed in `application/python/agent_terminal_app/config_openrouter_app_layer.json`.
- The plugin has no runtime dependencies.
- When `request_options_ui` is configured, it generates settings with flat keys such as:
  - `request_options__temperature`
  - `request_options__max_tokens`
  - `request_options__thinking__clear_thinking`

This subtask should add the mobile UI contract test for the real backend/settings path while staying fast enough for repeated local runs.

## Example Assertions

Useful assertions:

- `screen.findByText('Temperature')`
- `screen.getByText('0.0')`
- `screen.getByText('0.5')`
- `screen.getByText('1.0')`
- `screen.getByText('Max Tokens')`
- `screen.getByText('Thinking Clear Thinking')`
- After pressing `1.0`, `backend.getSessionOverrides(sessionId)` eventually returns `{ request_options__temperature: '1.0' }`.
- After pressing `1024`, `backend.getSessionOverrides(sessionId)` eventually returns `{ request_options__max_tokens: '1024' }`.

## Acceptance Criteria

- The test uses the real backend as the source of UI schema.
- The test does not copy the full UI schema into the frontend fixture.
- The test verifies both rendering and at least one real settings mutation.
- The example is clear enough for future plugin-specific UI tests to copy.

## Completion Notes

Added during completion on 2026-06-15.

- Added `mobile/crystal-lattice-control-rn/__integration__/SessionSettingsModal.realBackend.integration.test.tsx`.
- The test starts FastAPI with:
  - `plugins.deterministic_stream_provider.DeterministicStreamProvider`
  - `path:${env:BUILTIN_PLUGINS}/feature-request-options`
- The test creates a real session through `RestAgentBackend`, renders `SessionSettingsModal`, waits for request-options settings, presses select chips, and verifies stored flat-key overrides.
- The earlier message-export/PDF example was replaced to avoid installing heavy path plugin dependencies during this test tier while still using `path:...` syntax for a plugin that appears in the app default config.
- While building the earlier version, the first run exposed a real product gap: application-plugin `ui_type: "config"` elements were not included in session settings. The controller fix remains, with generic SDK regression coverage, but the default real-backend example no longer depends on that heavier plugin path.
- Added SDK regression coverage in `packages/frontend-sdk/src/sessionSettings/sessionSettingsController.test.ts`.
- Verification passed:

```bash
cd mobile/crystal-lattice-control-rn
npm run test:components:integration
```
