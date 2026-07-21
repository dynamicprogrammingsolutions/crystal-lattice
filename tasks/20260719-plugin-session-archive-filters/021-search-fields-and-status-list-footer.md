# Search fields and status session-list footer

Add focused title/subtitle and first-message filters to the search plugin, and
show the current workflow status at the end of each session row's metadata
footer with a server-scoped visibility override.

## Requirements checklist

- [x] The main-search plugin keeps the existing main search and adds separate
  title/subtitle and complete first-user-message filters with case-insensitive
  matching.
  - Automated verification:
    [plugins/session-main-search-app/tests/test_session_main_search_app.py](../../plugins/session-main-search-app/tests/test_session_main_search_app.py)
- [x] The first-message filter searches the complete first non-empty user
  message rather than the abbreviated list preview, while sessions without a
  user message remain valid list entries.
  - Automated verification:
    [plugins/session-main-search-app/tests/test_session_main_search_app.py](../../plugins/session-main-search-app/tests/test_session_main_search_app.py)
- [x] The status plugin contributes a human-readable status field to
  `presentation.meta`, treats missing status as `To do`, honors the configured
  metadata key, and places status after the existing built-in metadata fields.
  - Automated verification:
    [plugins/session-status-app/tests/test_session_status_app.py](../../plugins/session-status-app/tests/test_session_status_app.py)
- [x] Status-footer visibility defaults from
  `application.session_status_show_in_session_list_footer`, can be overridden
  by the server setting with the same key, and returns to the configured
  default when that override is deleted.
  - Automated verification:
    [plugins/session-status-app/tests/test_session_status_app.py](../../plugins/session-status-app/tests/test_session_status_app.py)
    and
    [core/python/tests/test_application_layer_app_plugins_basic.py](../../core/python/tests/test_application_layer_app_plugins_basic.py)
- [x] Server-setting changes made through a frontend backend refresh both the
  application session-list declarations and the loaded session summaries
  without clearing active filter state.
  - Automated verification:
    [packages/frontend-sdk/src/plugins/pluginsRegistry.test.ts](../../packages/frontend-sdk/src/plugins/pluginsRegistry.test.ts),
    [packages/frontend-sdk/src/sessions/sessionsController.test.ts](../../packages/frontend-sdk/src/sessions/sessionsController.test.ts),
    [mobile/crystal-lattice-control-rn/__tests__/SessionsScreen.test.tsx](../../mobile/crystal-lattice-control-rn/__tests__/SessionsScreen.test.tsx),
    and
    [desktop/crystal-lattice-control-desktop-rn/__tests__/SessionsPanel.test.tsx](../../desktop/crystal-lattice-control-desktop-rn/__tests__/SessionsPanel.test.tsx)
- [x] Mobile and desktop expose both additional filters through the existing
  shared filter UI and render the server-provided status text at the end of the
  session-row metadata footer.
  - Automated verification:
    [mobile/crystal-lattice-control-rn/__tests__/SessionsScreen.test.tsx](../../mobile/crystal-lattice-control-rn/__tests__/SessionsScreen.test.tsx)
    and
    [desktop/crystal-lattice-control-desktop-rn/__tests__/SessionsPanel.test.tsx](../../desktop/crystal-lattice-control-desktop-rn/__tests__/SessionsPanel.test.tsx)
  - Manual verification: confirm filter labels, footer placement, and the live
    visibility switch in the mobile and macOS session lists using a personal
    configuration under `~/.crystal`.
- [x] Plugin documentation and maintained default configuration accurately
  describe the new filters, status footer, application default, and live server
  override.
  - Automated verification:
    [application/python/tests/test_default_config_effective_agent_configs.py](../../application/python/tests/test_default_config_effective_agent_configs.py)
  - Manual verification: review the rendered/default-config documentation and
    both affected plugin READMEs for user-facing accuracy.

Parent Task: `tasks/20260719-plugin-session-archive-filters/000-main.md`

Depends On: `tasks/20260719-plugin-session-archive-filters/020-plugin-driven-filters-and-search.md`

## Execution plan

Approved during completion on July 21, 2026.

1. Extend `session-main-search-app` with two ordinary non-main text filters:
   title/subtitle over the displayed presentation fields and first message over
   a complete `first_user_message` summary field. Add a `session_list` trigger
   action that derives the first non-empty user message, and include that field
   in the existing broad main search without removing the frontend fallback
   search used when no valid main-search plugin is loaded.
2. Extend `session-status-app` with a `session_list` trigger that maps the
   effective stored status to its existing human-readable option label. Expose
   that label through a `session_list_field` with `role: "meta"` and an order
   after Updated, Created, and message count.
3. Add `application.session_status_show_in_session_list_footer` as the status
   plugin's configured default and expose the same key as a server-scoped
   checkbox. Use a persisted server value when present and fall back to the
   application default when absent or deleted.
4. Supply current server settings in ordinary application UI-schema context so
   the status plugin can include or omit its session-list field without keeping
   a second authoritative settings copy. Keep the existing settings storage,
   HTTP routes, and payload formats unchanged.
5. Refresh the shared application-plugin registry and active sessions list
   after frontend server-setting invalidation, preserving the existing
   connection-scoped filter controller and its values.
6. Update the affected plugin READMEs, `plugins/docs` contracts, bundled default
   configuration, and generated/default-config reference.
7. Add or extend contract-level plugin, application, shared frontend, mobile,
   and desktop tests, then run focused package suites, lint/type checks,
   documentation validation, and `git diff --check`.

## Completion Notes

Added during completion on July 21, 2026.

- Added `session_title_search` and `session_first_message_search` while keeping
  `session_search` as the only main search and preserving the existing
  no-plugin frontend fallback.
- Added the complete normalized first non-empty user message as the
  `first_user_message` session-summary field.
- Added `session_status_label` derivation and the ordered
  `session_status_meta` field, producing row metadata such as
  `2 messages · Status: In progress`.
- Added the application default and server-scoped override
  `session_status_show_in_session_list_footer`.
- Made current server settings available to ordinary application UI-schema
  generation and made shared frontend plugin/session controllers refresh after
  server-setting invalidation.
- Updated plugin READMEs, `plugins/docs`, bundled configuration, and the default
  configuration reference.
- Automated plugin, application, HTTP/terminal, shared frontend, mobile, and
  desktop tests pass. Mobile TypeScript, Python Ruff/Black checks, JSON
  validation, compile checks, and `git diff --check` pass.
- The broad default-config integration test remains blocked before its feature
  assertions by unrelated local `attr.Converter` import errors in MCP/Codex
  plugins. A focused default-config test verifies the new application default.
- Broad desktop TypeScript checking still reports the repository's existing
  Feather declaration, `ChatPane` optional-string, and theme `shadow` errors;
  the focused desktop component test and changed test-file lint pass.
- Manual verification with a personal `~/.crystal` configuration was completed
  for the visual filter labels, status footer placement, and live
  server-setting toggle.