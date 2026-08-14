# Notifications

Status: Implementing — Stage D complete; Stage E pending

The notification specification defines application- and session-scoped
notification records, lifecycle, event delivery, persistence, and portable
frontend presentation.

- [Product behavior](product-spec.md)
- [Technical contract](technical-spec.md)
- [Portable frontend behavior](frontend-behavior.md)
- [Requirements and evidence](requirements.md)

The committed baseline documents the implementation delivered through
`tasks/20260729-staged-application-config-and-full-reload.md`. This working
revision proposes authoritative dismissal, retention, history/replay, and
interaction-ready contracts tracked by
`tasks/20260619-generic-session-notifications/045-stage-1-authoritative-dismissal-retention-history-and-interaction-readiness.md`.

Stage A implements the backend lifecycle, revision, authoritative snapshot, and
server dismissal foundation. Stage B integrates authoritative snapshot and
dismissal behavior into mobile. Stage B-1 makes application notification
history durable, Stage B-2 adds revision-scoped failed-dismissal caching, and
Stage C adds authoritative desktop snapshot hydration and server dismissal.

The UI-effect invalidation amendment records the behavior implemented by
commit `6601e48a` and tracked by
`tasks/20260814-notification-ui-effect-specification.md`.

The stable-key publication amendment proposes removing `expected_revision`
from the plugin-facing notification contract, making producer publication an
atomic upsert by stable key, and keeping dismissal revision-scoped. It is
tracked by `tasks/20260814-notification-stable-key-publication.md`.

Related contracts:

- [Action displays](../action-display/index.md)
- [Application runtime reload](../application-runtime-reload/index.md)