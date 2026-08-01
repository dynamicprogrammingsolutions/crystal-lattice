# Notifications

Status: Implementing — B-1 automated verification complete; manual pending

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
desktop keeps local dismissal until Stage C.

Related contracts:

- [Action displays](../action-display/index.md)
- [Application runtime reload](../application-runtime-reload/index.md)