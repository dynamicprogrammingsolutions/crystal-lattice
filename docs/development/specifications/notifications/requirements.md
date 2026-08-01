# Notification requirements

| ID | Requirement | Implementation | Verification | Documentation |
|---|---|---|---|---|
| NTF-001 | Session notifications are persisted with the session and hidden from model history. | Implemented | Automated | Documented |
| NTF-002 | Application notifications remain available across `AgentApplication` replacement while the owner lives. | Implemented | Automated | Documented |
| NTF-003 | Stable-key creation updates an existing pending lifecycle item. | Implemented | Automated | Documented |
| NTF-004 | Notification failures do not abort tool or request execution. | Implemented | Automated | Documented |
| NTF-005 | Session notification mutations use session-safe read-modify-write persistence. | Implemented | Automated | Documented |
| NTF-006 | Notification lifecycle events preserve application/session scope. | Implemented | Automated | Documented |
| FNT-001 | Mobile application notifications render only on Sessions. | Implemented | Automated; human checkpoint pending | Documented |
| FNT-002 | Mobile session notifications render only on the matching Chat. | Implemented | Automated; human checkpoint pending | Documented |
| FNT-003 | Desktop connection notifications aggregate in the message/detail area and retain connection identity. | Implemented | Component/integration automated; native/human pending | Documented |
| FNT-004 | Desktop session notifications render for the active session at the common message/detail location. | Implemented | Component/integration automated; native/human pending | Documented |
| NTF-007 | Notification dismissal is persisted by the same server-side authority as the notification record. | Proposed | Unverified | Draft |
| NTF-008 | Notification records have monotonic revisions and reject stale mutations. | Proposed | Unverified | Draft |
| NTF-009 | Retention supports explicit, TTL, request-completion, and server-lifetime policies. | Proposed | Unverified | Draft |
| NTF-010 | Active and terminal/history limits are separate and active interactions are never silently pruned. | Proposed | Unverified | Draft |
| NTF-011 | Application notifications expose an authoritative current-state snapshot for new or reconnected frontends. | Proposed | Unverified | Draft |
| NTF-012 | The record model represents notification and interaction lifecycles without destructive normalization. | Proposed | Unverified | Draft |
| FNT-005 | The dismissing frontend updates immediately, while other open devices may reconcile later and newly hydrated devices honor server dismissal. | Proposed | Unverified | Draft |
| FNT-006 | Relevant top action bars expose a reusable Notifications history action. | Proposed | Unverified | Draft |
| FNT-007 | Historical rich displays can be shown again locally without reactivating lifecycle state. | Proposed | Unverified | Draft |
| FNT-008 | Active interactions are nondismissible and discoverable through a compact waiting-for-input indicator. | Proposed | Unverified | Draft |

Primary task evidence:

- `tasks/20260729-staged-application-config-and-full-reload.md`
- `tasks/20260619-generic-session-notifications/000-main.md`
- `tasks/20260619-generic-session-notifications/045-stage-1-authoritative-dismissal-retention-history-and-interaction-readiness.md`