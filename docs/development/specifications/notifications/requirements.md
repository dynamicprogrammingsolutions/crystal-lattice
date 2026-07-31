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
| FNT-005 | Current dismissal is frontend-local and revision-scoped. | Implemented | Automated | Documented |

Primary task evidence:

- `tasks/20260729-staged-application-config-and-full-reload.md`
- `tasks/20260619-generic-session-notifications/000-main.md`