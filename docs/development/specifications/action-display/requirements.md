# Action-display requirements

| ID | Requirement | Implementation | Verification | Documentation |
|---|---|---|---|---|
| DSP-001 | Display payloads support text/markdown, semantic variants, and banner/inline/modal presentation. | Implemented | Automated | Documented |
| DSP-002 | Follow-up actions use the common action execution path and preserve owning context. | Implemented | Automated | Documented |
| DSP-003 | Explicit supported presentation is not suppressed because of action source. | Implemented | Automated | Documented |
| DSP-004 | Mobile and desktop may use documented platform fallbacks without changing notification lifecycle. | Implemented | Automated; human checkpoint pending | Documented |
| DSP-005 | Sensitive values are excluded from display payloads. | Implemented contract | Focused tests/manual review | Documented |