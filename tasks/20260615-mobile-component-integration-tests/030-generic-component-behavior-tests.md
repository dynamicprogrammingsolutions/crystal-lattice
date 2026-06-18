# Generic Component Behavior Tests

Add fast unit-like tests for generic mobile component behavior without starting a backend.

## Requirements checklist

- [x] Add tests for generic settings control rendering behavior.
- [x] Cover at least `checkbox`, `select`, `dropdown`, `text` or `multiline`, and fallback behavior where practical.
- [x] Verify user-style interactions with `fireEvent`, such as pressing a select chip and invoking the expected callback.
- [x] Keep tests generic and not tied to a specific plugin such as message export/PDF.
- [x] Prefer visible labels/text and accessibility labels over fragile implementation queries.

Parent Task: tasks/20260615-mobile-component-integration-tests/000-main.md
Depends On: tasks/20260615-mobile-component-integration-tests/020-react-native-testing-library-setup.md

## Scope

These tests should prove generic rendering behavior. They may use small in-memory objects and callbacks. They should not start FastAPI, load real plugins, or call real SDK transports.

Good targets include:

- `SessionSettingsHost` with mobile renderers, if renderers are extractable.
- `SessionSettingsModal` with a mocked controller/hook, if this stays maintainable.
- A newly extracted mobile settings renderer component if the current modal is too monolithic to test generically without backend state.

If implementation reveals that `SessionSettingsModal` renderers are too embedded for clean tests, consider extracting the settings body/renderers into a small mobile-local component. Keep that extraction scoped to testing and maintainability, not a broad redesign.

## Example Behaviors

- A generic `select` setting renders option labels and marks/uses the selected value.
- Pressing a select chip calls `selectOption(key, value)`.
- A generic `checkbox` setting renders the label and calls `toggleCheckbox(key, next)`.
- A text setting calls save with the relevant key.
- Unknown or text-like types use fallback rendering.

## Acceptance Criteria

- Tests are fast and run as part of the normal mobile Jest suite.
- Tests do not duplicate plugin-specific UI schema from real plugins.
- The tests provide a clear template for future generic component behavior tests.

## Completion Notes

Added during completion on 2026-06-15.

- Added `mobile/crystal-lattice-control-rn/__tests__/SessionSettingsModal.test.tsx`.
- The test renders `SessionSettingsModal` with a mocked `useSessionSettingsController`, so it exercises the actual mobile settings renderers while keeping data generic and in-memory.
- Covered generic `select`, `checkbox`, `dropdown`, `text`, `readonly`, and fallback rendering.
- Verified `fireEvent.press` on a select chip calls `patchOverride` with the generic key/value.
- Verified text editing and save calls `patchOverride` with the updated generic value.
- Plugin-specific/default-config settings remain reserved for the real-backend integration example.
