# Task-guidance evaluation suite requirements

Implementation values use `Not started`, `In progress`, `Implemented`,
`Deferred`, or `Removed`.

| ID | Requirement | Implementation | Verification | Documentation | Primary evidence |
|---|---|---|---|---|---|
| TGEVAL-001 | Existing task-guidance execution, assertion, review, provenance, imported-session, and bundle behavior migrates from `test/task_guidance/` into a package-owned suite without losing readable historical evidence. | Not started | Unverified | Target documented | Suite specification; task 090 |
| TGEVAL-002 | Six reviewed contracts cover three bounded handoff cases and three substantial decomposition cases. Each complex case has approximately four coherent deliverables, acceptable alternative partitions, real crossings and dependencies, and enough surface to expose excessive phase- or layer-based fragmentation. | Not started | Human review pending | Target documented | `scenarios/`; task 090 |
| TGEVAL-003 | Independent stage matrices use one canonical reviewed input per stage and record exact workspace, conversation-prefix, guidance, prompt, model, effort, and stage-input identity. | Not started | Unverified | Target documented | Suite specification; testing strategy |
| TGEVAL-004 | Fresh-agent continuation verifies that task files preserve enough facts, decisions, questions, pointers, scope, and evidence boundaries to prepare a correct plan without the original conversation or broad rediscovery. | Not started | Unverified | Target documented | Fresh-agent scenario assertions; task 090 |
| TGEVAL-005 | Same-agent continuation verifies reuse of prior investigation and compares normalized investigation effort with fresh-agent and initial-investigation stages after semantic quality passes. | Not started | Unverified | Target documented | Continuity evidence; testing strategy |
| TGEVAL-006 | Retain-plan and omit-plan variants distinguish semantic plan preservation from factual handoff preservation and reject hidden plan content or lost constraints. | Not started | Unverified | Target documented | Scenario contracts; semantic assessment |
| TGEVAL-007 | Task topology evidence maps actual children to reviewed coherent deliverables, identifies mergeable fragments, overpacked and unmatched work, parent-outcome mappings, real acyclic dependencies, valid versus automatic technical-layer boundaries, and ownership of important behavior crossings. | Not started | Unverified | Target documented | Complex decomposition scenarios; task 090 |
| TGEVAL-008 | Efficiency evidence records normalized investigation calls, unique reads, broad searches, repeated reads, diagnostics, and mutations; thresholds are calibrated from B0 and cannot override plan-quality failures. | Not started | Unverified | Target documented | Testing strategy; negative-control design |
| TGEVAL-009 | B0, B1, and placement candidates preserve paired provenance and use the same semantic targets; focused comparisons precede any justified full model/effort matrix. | Not started | Unverified | Target documented | Task 090; running and calibration target |
| TGEVAL-010 | Deterministic validity, semantic quality, pairwise review, empirical efficiency, and human acceptance remain separate, and only complete structurally valid upstream records feed dependent stages. | Not started | Unverified | Target documented | Suite specification; testing strategy |

Shared implementation and delivery references will be recorded below this table
after execution. Requirement rows will not be expanded with repeated run IDs.