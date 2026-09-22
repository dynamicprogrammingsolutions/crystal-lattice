Parent Task: tasks/20260922-duration-and-human-time-tracking/000-main.md

Depends On:
- tasks/20260922-duration-and-human-time-tracking/010-session-duration-store.md

# Human Time Telemetry

Track human time (review + composition) from frontend-reported activity events recorded into the duration store, with ingestion via a plugin-defined action and computation from event rows. Human time surfaces through the report action only — it uses the store and report features from 010 and does not stamp messages (user decision, 2026-09-22).

## Requirements checklist

- [ ] An application-plugin action accepts frontend-reported per-session activity events in batches via the existing `executeAction` path; no new SDK method or HTTP endpoint is added.
- [ ] A server-settings UI-schema entry names the telemetry plugin id so frontends can discover where to send events.
- [ ] Event types cover at least session viewing, scroll activity, and message composition (v1: `session_viewed`, `scroll`, `compose_typing`, `message_composed`; the set is extensible).
- [ ] Events are recorded as rows in the same duration store keyed by `(working_directory, session_id)`, idempotent per event id (repeated events do not double-count).
- [ ] Human time is split into review time and composition time, computed from event rows with a configurable max-idle threshold (gaps longer than the threshold do not count).
- [ ] Human time surfaces through the report action only, computed live from event rows (review, composition, combined per session); no message stamping and no status-bar elements in v1.
- [ ] Per-message composition data is retained in the store keyed by the composed event; rewriting user messages is out of scope.
- [ ] Frontends own their collection and batching implementation; the ingestion contract (action shape, event types, batching, event ids) is documented.
- [ ] Ingestion and computation are best-effort: telemetry failures never break requests, saves, or the report.

## Supporting details

### Facts

- Frontends already call `executeAction({pluginId, actionId, inputs})` through the `AgentBackend` interface (`packages/frontend-sdk/src/backend/backend.ts`); the cost report/reset actions already flow through this path including bridge/mobile usage. No SDK change is needed for the action transport.
- Server settings live at `runtime/server_settings.json` and are exposed via `GET /server/settings` and `GET /server/settings/ui-schema`; a server-scoped config element is the discovery surface for the telemetry plugin id (precedent: `plugins/session-status-app` server-scoped elements).
- The duration-tracking app plugin (from 010) is the natural host for the ingestion action, or a sibling app plugin in the same package; the store resolution is shared.
- Surfacing is report-only in v1 (user decision, 2026-09-22): the report action computes live human-time totals from event rows; the request-finalize stamping surface and status-bar elements are not used for human time. Stamping human time onto messages can be revisited later if wanted.
- The transport decision is approved: plugin-defined action with server-setting discovery. The generic telemetry endpoint with plugin-defined hooks that are also actions was reviewed and recorded as a possible future framework generalization, not v1 scope (see parent task).

### Design points to pin in this subtask's plan

- Event id assignment: frontend-provided ids accepted, plugin-assigned monotonic ids when absent; uniqueness enforced by the store (record-once pattern).
- Event schema: `{type, timestamp (ISO UTC), event_id?, details?}` with `session_id` at the batch level; `message_composed` carries a correlation id for per-message composition data.
- Max-idle threshold: config key with a default (proposal: 60 seconds).
- Review/composition classification: `session_viewed`/`scroll` → review spans; `compose_typing` → composition spans ending at `message_composed`; idle gaps above the threshold excluded.
- Report columns: human review, composition, combined per session (live computation); top sessions/projects can include human time.
- Frontend collector scope: the contract plus backend tests are this subtask's scope; the RN app collectors (mobile/desktop) are follow-up work consuming the documented contract, and the terminal may emit a minimal collector if cheap.

## Task relations

- Takes over `tasks/20260801-duration-and-stats-tracking/040-human-time-telemetry-plugin.md` and `050-human-time-tracking-plugin.md` (superseded; their JSONL buffer, read pointer, and two-plugin split are replaced by store rows and queries).