# Cross-Package Notification and Action-Display Contracts

Create the authoritative root specifications for notification records,
lifecycle events, plugin/tool behavior, and action-display payloads.

## Requirements checklist

- [x] A root notification specification defines application and session
  notification records, lifecycle, persistence classes, event contracts,
  plugin/tool APIs, failure behavior, security, and compatibility.
- [x] A separate root action-display specification defines display payloads,
  follow-up actions, presentation semantics, defaults, replacement behavior,
  and compatibility.
- [x] Stable `NTF-*` and `DSP-*` requirements record implementation,
  verification, documentation, task, and delivery evidence.
- [ ] Material cross-package decisions are captured as root-level decision
  records.
- [x] The contracts are implementation-neutral and do not assign authority to
  current Python, TypeScript, or React Native types.
- [x] Existing event/action/plugin pages link to the contracts or are recorded
  for compatibility handling without becoming competing sources of truth.

Parent Task:
`tasks/20260730-runtime-notification-specification-documentation/000-main.md`

## Approved artifacts

```text
docs/development/specifications/notifications/
├── index.md
├── product-spec.md
├── technical-spec.md
├── frontend-behavior.md
└── requirements.md

docs/development/specifications/action-display/
├── index.md
├── technical-spec.md
└── requirements.md
```

Use decision records only for material choices whose rationale cannot be
captured concisely in the specification. Preserve separate `NTF-*`, `FNT-*`,
and `DSP-*` requirement namespaces.

## Notification contract content

Normalize and verify:

- application-global versus persistent session scope;
- ID, stable deduplication key, kind, status, severity, title/body, timestamps,
  request ID, source provenance, display, resolution, and model visibility;
- pending/resolved Stage 1 lifecycle and future-compatible extension rules;
- create/update/resolve/list behavior;
- same-key pending update semantics;
- application notification events without `session_id`;
- session notification create/update/resolve events with `session_id`;
- session metadata as reconnect authority;
- durable application-store lifetime and process-restart behavior;
- checkpoint/event ordering and event publication being best effort;
- session lock/read-modify-write expectations and pending-preserving pruning;
- direct application-plugin APIs versus failure-contained tool sink;
- hidden model visibility;
- requirements not to expose credentials or sensitive config in records,
  events, or displays.
- authoritative server-side dismissal stored with the notification record,
  while preserving the committed local-dismissal behavior as implementation
  history rather than the target contract;
- explicit revisions, stale mutation behavior, retention, history, historical
  replay, and interaction-compatible extension rules;

Primary code/evidence references:

- `core/python/agent_app/notifications.py`
- `core/python/agent_app/application_owner.py`
- `core/python/agent_app/application_future.py`
- `core/python/agent_app/app_context.py`
- `core/python/tests/test_session_notifications.py`
- `core/python/tests/test_application_owner.py`
- `application/python/tests/test_notification_demo_plugins_http.py`
- `packages/frontend-sdk/src/types/notifications.ts`
- `packages/frontend-sdk/src/types/applicationNotifications.ts`
- `docs/api/events.md`

## Action-display contract content

Normalize and verify:

- display ID, format, title, body, variant, presentation, dismissibility, form,
  and actions;
- `run_action`, `open_url`, `copy_text`,
  `download_attachment_asset`, and `dismiss`;
- fixed parameters, parameter mapping, form values, and action ownership;
- `banner`, `inline`, and `modal` semantic meanings without prescribing a
  current UI toolkit;
- explicit presentation taking precedence on application, session,
  session-list, and message action surfaces;
- source defaults: application notification → banner, session notification →
  inline, direct action response → modal;
- stable display upsert/replacement behavior;
- unknown/missing value compatibility;
- URL, clipboard, download, form, and sensitive-value safety boundaries.

Primary code/evidence references:

- `packages/frontend-sdk/src/types/plugins.ts`
- `packages/frontend-sdk/src/plugins/actionDisplayPolicy.ts`
- `packages/frontend-sdk/src/plugins/displayPresentation.ts`
- `packages/frontend-sdk/src/plugins/actionRunner.ts`
- `plugins/docs/actions.md`
- the three dummy notification/display plugin packages.

## Candidate cross-package decisions

- Persist session notifications in session metadata and application
  notifications in the runtime-injected durable application notification
  store.
- Reuse action-display payloads for notifications.
- Keep notification event delivery and tool sinks best effort.
- Keep Stage 1 notification model visibility hidden.
- Use stable-key update semantics for pending notifications.
- Honor explicit presentation independently of producer/action surface.
- Store dismissal with the same server-side authority as the notification.
- Do not require immediate dismissal reconciliation on other already-open
  devices; require authoritative hydration for newly opened devices.
- Keep direct action displays transient unless explicitly recorded as
  notifications.

## Existing documentation treatment

`docs/api/events.md` currently mixes general event-stream mechanics with the
new notification contract. Do not move all notification authority under Core
Python. Preserve or split:

- package-owned event transport mechanics;
- root cross-package notification event shape/lifecycle;
- portable frontend consumption behavior owned by subtask 020.

`plugins/docs/actions.md` and `plugins/docs/application-plugins.md` should
eventually become authoring-oriented consumers of these contracts.

Do not create hand-maintained `docs/reference/contracts/*` pages in the first
baseline. Add them later only as generated references or concise lookup tables
with no competing lifecycle narrative.

## Status audit — August 3, 2026

The approved root artifacts exist and the `NTF-*` and `DSP-*` matrices are in
place.

Explicit scope decision:

- determine whether the unchecked decision-record requirement accepts material
  rationale recorded directly in the root technical specifications, consistent
  with the approved “create a decision record only when needed” rule, or
  requires standalone decision files. No additional contract content is
  currently known to be missing.
