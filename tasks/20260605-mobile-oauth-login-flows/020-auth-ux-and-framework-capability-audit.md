# Auth UX And Framework Capability Audit
Define the desired login-type selection UX and determine whether the existing framework can already express it or needs extension work.

## Requirements checklist

- [ ] Audit whether existing `session_action.dialog` primitives can support chip-style login-type selection with a single confirm button.
- [ ] Audit whether the mobile/frontend layer already supports the required dialog rendering behavior.
- [ ] Define how login-type preference should work in settings versus action-time selection when no preference is set.
- [ ] Document the fallback plan if the framework only supports the current multi-button action chaining UX.

Parent Task: `tasks/20260605-mobile-oauth-login-flows/000-main.md`
Depends On: `tasks/20260605-mobile-oauth-login-flows/010-codex-mobile-redirect-poc.md`

## Product intent

Desired UX from the request:

- User can select login type in settings.
- If no login type is selected, the action itself should present the available options.
- Prefer one dialog with chip-style selection and a single primary action button.
- Avoid the current UX shape where multiple buttons each trigger a new action hop.

## Current repo references

- `plugins/chatgpt-auth-app/src/chatgpt_auth_app/__init__.py`
  - Current ChatGPT auth session actions are exposed as separate `session_action` items with `dialog: {"kind": "none"}`.
- `plugins/chatgpt-auth-app/src/chatgpt_auth_app/__init__.py`
  - The pending login display currently returns inline markdown plus `open_url`, `copy_text`, and `run_action` buttons.
- `plugins/docs/ui-elements.md`
  - Documents current `session_action` dialog support and existing `dialog.kind == "form"` patterns.
- `core/python/agent_app/app_plugins.py`
  - Confirms that application plugins can expose actions and commands, with commands remaining frontend bindings to actions.

## Questions to answer

- Does the framework already have a dialog/input type that can be rendered as chips or a segmented selector?
- If not, can the frontend render a conventional single-select control from an existing dialog schema without core changes?
- Should login type live in:
  - provider config
  - session overrides
  - application-plugin state
  - frontend-only preference that gets passed into the start action
- How should the action behave when settings are unset:
  - action returns a dialog
  - action returns a display payload with follow-up action buttons
  - action first launches a selection step, then executes the chosen path

## Expected output

- Recommended UX contract for login-type selection.
- Decision on whether this can be built with current framework primitives.
- If framework changes are required, a concrete list of missing capabilities and the smallest extension that would unlock the target UX.