# Notification requirements

| ID | Requirement | Implementation | Verification | Documentation |
|---|---|---|---|---|
| NTF-001 | Session notifications are persisted with the session and hidden from model history. | Implemented | Automated | Documented |
| NTF-002 | Application notifications remain available across `AgentApplication` replacement while the owner lives. | Implemented | Automated | Documented |
| NTF-003 | Producer publication by stable key atomically updates the current active occurrence or creates a new occurrence when none is active. | Implemented | Automated | Documented |
| NTF-004 | Notification failures do not abort tool or request execution. | Implemented | Automated | Documented |
| NTF-005 | Session notification mutations use session-safe read-modify-write persistence. | Implemented | Automated | Documented |
| NTF-006 | Notification lifecycle events preserve application/session scope. | Implemented | Automated | Documented |
| FNT-001 | Mobile application notifications render only on Sessions. | Implemented | Automated; human checkpoint pending | Documented |
| FNT-002 | Mobile session notifications render only on the matching Chat. | Implemented | Automated; human checkpoint pending | Documented |
| FNT-003 | Desktop connection notifications aggregate in the message/detail area and retain connection identity. | Implemented | Component/integration/native automated; desktop confirmed | Documented |
| FNT-004 | Desktop session notifications render for the active session at the common message/detail location. | Implemented | Component/integration/native automated; desktop confirmed | Documented |
| NTF-007 | Notification dismissal is persisted by the same server-side authority as the notification record. | Implemented backend/mobile/desktop | Automated backend/API/mobile/desktop; desktop human postponed | Documented |
| NTF-008 | Notification records have monotonic revisions and reject stale update/resolution/dismiss mutations. Producer publication does not require a producer-supplied revision. | Implemented | Automated | Documented |
| NTF-009 | Retention supports explicit, presentation-TTL, request-completion, and server-lifetime policies. | Implemented | Automated backend/SDK/mobile integration; mobile confirmed | Documented |
| NTF-010 | Active records are never silently pruned and terminal history is independently bounded. | Implemented | Automated session/SQLite store; mobile retention confirmed | Documented |
| NTF-011 | Application notifications expose an authoritative current-state snapshot for new or reconnected frontends. | Implemented backend/mobile/desktop | Automated HTTP/SDK/mobile/desktop; desktop human postponed | Documented |
| NTF-012 | The record model represents notification and interaction lifecycles without destructive normalization. | Proposed | Unverified | Draft |
| NTF-013 | Application notification active and terminal records persist across owner and server-process restart in a configurable durable store. | Implemented | Automated public HTTP/store restart; mobile confirmed | Documented |
| NTF-014 | Application notification lifecycle mutations are atomic and terminal records remain available to later history queries until retention removes them. | Implemented | Automated store/API lifecycle tests | Documented |
| NTF-015 | Notification UI effects are revision-scoped commands: only a pending revision that explicitly supplies an effect requests execution, and lifecycle-only or terminal revisions do not inherit or repeat it. | Implemented | Automated core/SDK/iOS simulator | Documented |
| NTF-017 | Producer-facing notification publication by stable key does not accept caller-supplied `expected_revision`; the notification service owns revision assignment and increment, and a stale terminal or older occurrence does not suppress a later key-scoped producer publication. | Proposed | Unverified | Draft |
| NTF-018 | Dismissal remains revision-scoped for user/client mutations and does not prevent a later producer publication for the same key. | Proposed | Unverified | Draft |
| NTF-016 | Notifications and application-action responses share explicit refresh field meanings, while notification effects exclude action-only navigation and mutation-derived behavior. | Implemented | Automated SDK/action/notification tests | Documented |
| FNT-005 | The dismissing frontend updates immediately, while other open devices may reconcile later and newly hydrated devices honor server dismissal. | Implemented mobile/desktop | Automated mobile/desktop; desktop human postponed | Documented |
| FNT-006 | Relevant top action bars expose a reusable Notifications history action. | Proposed | Unverified | Draft |
| FNT-007 | Historical rich displays can be shown again locally without reactivating lifecycle state. | Proposed | Unverified | Draft |
| FNT-008 | Active interactions are nondismissible and discoverable through a compact waiting-for-input indicator. | Proposed | Unverified | Draft |
| FNT-009 | A failed frontend dismissal can remain locally persisted and hidden for the exact notification revision, with retry when that same revision is observed again. | Implemented mobile | Automated SDK/component/real-backend; mobile confirmed | Documented |
| FNT-010 | A cached dismissal is never promoted to a newer revision; an authoritative newer pending revision removes the obsolete cache and is presented. A dismissal of one revision or occurrence never suppresses a later pending publication for the same stable key. | Implemented mobile | Automated SDK/component/real-backend; mobile confirmed | Documented |
| FNT-011 | A notification refresh effect invalidates data only on its owning connection and remains observable until an appropriate frontend consumer successfully reloads authoritative state. | Implemented mobile/desktop | Automated SDK/mobile/desktop; iOS simulator confirmed | Documented |
| FNT-012 | Active, inactive, cached, and later-mounted consumers converge on authoritative state without notification-driven navigation. | Implemented mobile/desktop | Automated SDK/mobile; desktop implementation inspection | Documented |
| FNT-013 | Frontend delivery prevents duplicate concurrent reloads for one invalidation, retains failed or deferred invalidations for retry, and does not let acknowledgment of an older invalidation clear a newer one. | Implemented | Automated SDK and iOS simulator regression | Documented |
| FNT-014 | Frontend dismissal targets the displayed notification ID and optional expected revision; a stale dismissal cannot hide a newer revision or later stable-key occurrence. | Proposed | Unverified | Draft |

Primary task evidence:

- `tasks/20260729-staged-application-config-and-full-reload.md`
- `tasks/20260619-generic-session-notifications/000-main.md`
- `tasks/20260619-generic-session-notifications/045-stage-1-authoritative-dismissal-retention-history-and-interaction-readiness.md`
- `tasks/20260802-openai-responses-background-compaction.md`
- `tasks/20260814-notification-ui-effect-specification.md`
- `tasks/20260814-notification-stable-key-publication.md`
- commit `6601e48a` (`Make notification refresh invalidations durable`)
