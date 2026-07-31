# Application runtime reload

Status: Implemented Stage 1 baseline

Application runtime reload replaces `AgentApplication` while the owning
process, listeners, event store, and frontend connections remain alive.

- [Product behavior](product-spec.md)
- [Technical contract](technical-spec.md)
- [Requirements](requirements.md)