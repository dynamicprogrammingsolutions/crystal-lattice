# Runtime reload requirements

| ID | Requirement | Implementation | Verification | Documentation |
|---|---|---|---|---|
| RLD-001 | Reload reconstructs `AgentApplication` without restarting the owning process. | Implemented | Automated | Documented |
| RLD-002 | New operations are rejected while admitted operations drain. | Implemented | Automated | Documented |
| RLD-003 | Candidate failure preserves the active application. | Implemented | Automated | Documented |
| RLD-004 | Old runtime resources, including MCP servers, close before completion. | Implemented | Automated | Documented |
| RLD-005 | Reload state is communicated through application notifications. | Implemented | Automated | Documented |
| RLD-006 | Native desktop and human UI behavior remains separately verified. | Implemented | Native execution/human pending | Documented |