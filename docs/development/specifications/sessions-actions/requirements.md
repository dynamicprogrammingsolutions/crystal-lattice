# Sessions-action requirements

| ID | Requirement | Implementation | Verification | Documentation |
|---|---|---|---|---|
| FSA-001 | Built-in and plugin actions share one reusable Sessions action model. | Implemented | Automated | Documented |
| FSA-002 | Pinned and complete-menu entries retain stable action identity. | Implemented | Automated | Documented |
| FSA-003 | Pin state is connection-scoped frontend state. | Implemented | Automated | Documented |
| FSA-004 | Platform-specific menus preserve accessible action behavior. | Implemented | Mobile automated; desktop native/human pending | Documented |
| FSA-005 | Relevant top action surfaces expose a stable, pinnable Notifications history action. | Proposed | Unverified | Draft |
| FSA-006 | Session actions may explicitly declare non-mutating execution; those actions can return transient displays without rebuilding, persisting, or reporting an updated session, while omitted declarations retain the existing mutating default. | Implemented | Automated | Documented |