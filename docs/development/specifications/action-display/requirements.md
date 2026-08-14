# Action-display requirements

| ID | Requirement | Implementation | Verification | Documentation |
|---|---|---|---|---|
| DSP-001 | Display payloads support text/markdown, semantic variants, and banner/inline/modal presentation. | Implemented | Automated | Documented |
| DSP-002 | Follow-up actions use the common action execution path and preserve owning context. | Implemented | Automated | Documented |
| DSP-003 | Explicit supported presentation is not suppressed because of action source. | Implemented | Automated | Documented |
| DSP-004 | Mobile and desktop may use documented platform fallbacks without changing notification lifecycle. | Implemented | Automated; human checkpoint pending | Documented |
| DSP-005 | Sensitive values are excluded from display payloads. | Implemented contract | Focused tests/manual review | Documented |
| DSP-006 | Notification dismiss delegates to server lifecycle while direct-display close remains frontend-local. | Implemented mobile/desktop | Automated mobile/desktop; desktop human postponed | Documented |
| DSP-007 | All hosts preserve embedded form values and parameter mappings for follow-up actions. | Proposed | Unverified | Draft |
| DSP-008 | Historical replay disables mutating actions unless explicitly valid and server-validated. | Proposed | Unverified | Draft |
| DSP-009 | A notification display may optimistically cache dismissal only for the exact displayed revision; direct and historical display close never enters that cache. | Implemented mobile | Automated SDK/component; mobile confirmed | Documented |
| DSP-010 | Persistent operation-progress notifications are dismissible by default; nondismissible presentation requires an explicit product reason and must not be used as a substitute for operation ownership or update coordination. | Proposed | Unverified | Draft |
