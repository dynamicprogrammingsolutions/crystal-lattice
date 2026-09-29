# Request cancellation requirements

| ID | Requirement | Implementation | Verification | Documentation | Primary evidence |
|---|---|---|---|---|---|
| RCL-001 | Existing request cancellation remains hard and backward compatible. | Implemented | Automated | Documented | Core application cancellation tests |
| RCL-002 | First-party foreground shell tools terminate their process tree on hard cancellation. | Implemented | Automated | Documented | Shared-engine, generic Bash, Codex, and vendor wrapper tests |
| RCL-003 | Soft cancellation lets an active tool finish, persists its result, and prevents later phases. | Implemented | Automated | Documented | `test_soft_cancel_waits_for_active_tool_and_persists_result` |
| RCL-004 | Hard cancellation promotes soft cancellation and wins registration races. | Implemented | Automated | Documented | Application cancellation race and escalation tests |
| RCL-005 | Request cancellation does not reclaim successfully handed-off background commands. | Implemented | Automated | Documented | Shared shell background handoff coverage |
| RCL-006 | HTTP, embedded runtime, terminal, SDK, mobile, and desktop expose soft cancellation while retaining hard cancellation. | Implemented | Automated | Documented | Server, SDK, type-check, and UI tests |
| RCL-007 | Cancellation events identify soft versus hard mode compatibly. | Implemented | Automated | Documented | Application event and frontend compatibility tests |

Task: `tasks/20260927-hard-and-soft-request-cancellation.md`