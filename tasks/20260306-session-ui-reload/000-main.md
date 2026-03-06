# Session UI Reload On Settings/Plugins Changes

Ensure that when per-session settings (config overrides) or session plugin enablement changes, any session-specific UI (derived from `/sessions/{session_id}/ui-schema`) automatically reloads.

Goals:
- General mechanism shared by both mobile and desktop frontends.
- Minimal frontend changes (prefer SDK-level changes).
- Avoid major SDK refactors; keep changes additive.

Subtasks:
1. `tasks/20260306-session-ui-reload/010-a1-sdk-local-invalidation.md`
2. `tasks/20260306-session-ui-reload/020-a2-server-events-cross-client.md`
3. `tasks/20260306-session-ui-reload/030-c-etag-versioning.md`
4. `tasks/20260306-session-ui-reload/040-settings-ui-use-shared-schema-controller.md`
5. `tasks/20260306-session-ui-reload/050-session-settings-controller.md`
