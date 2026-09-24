# Crystal Lattice evaluation environment requirements

These requirements define the optional Crystal Lattice environment supplied
with `agent_eval`.

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| AEVAL-005 | The first `CrystalLatticeEnvironment` uses Core/Application, supports caller-owned configuration and plugins, and exposes a context with direct access to application, core, session, configuration, workspace, and run services. | Implemented | Automated | Documented | Real `AgentApplication`/`AgentCore` construction, plugin-loading, request, streaming, tool-loop, cache, continuation, and cleanup tests; package docs |
| AEVAL-006 | Crystal Lattice request execution/tool-loop control, stopping, snapshotting, observation, evidence projection, evaluation, and presentation are replaceable at their point of use and are not requirements for alternate environments. | Implemented | Automated | Documented | Default/custom driver, observer, stop, mutation classifier, named snapshot, projection, evaluation, presentation, and alternate-environment tests |
| CLEVAL-001 | Crystal Lattice evaluation consumers can obtain an accurate review representation of delivered instructions, effective configuration, visible conversation, tool activity, execution failures, and available provider usage. | Implemented | Automated against real saved GLM and GPT sessions; exercised end to end by the task-guidance packages | Documented | `agent_eval.crystal_lattice.review` (`project_session_review`, `project_effective_config_view`); task 095 |
| CLEVAL-002 | Crystal Lattice review representations are lean, human-readable, safe to retain, and sufficiently detailed to diagnose relevant model or execution behavior. | Implemented | Automated; 12–20x size reduction on sampled sessions; secret scan over committed packages found no credential values | Documented | Lean session projection (no full tool results, no encrypted reasoning); `render_session_markdown`; task 095 |
| CLEVAL-003 | The Crystal Lattice review representation is reusable by multiple evaluation suites and contains no task-guidance, documentation-guidance, or other suite-specific semantics. | Implemented | Automated; imports and semantics checked | Documented | Suite-agnostic projection consumed by the task-guidance adapter; kernel remains free of session semantics; task 095 |
| CLEVAL-004 | Crystal Lattice review data distinguishes information captured directly from information reconstructed or unavailable after the run. | Implemented | Automated; captured/reconstructed/inherited/unavailable states covered | Documented | Availability classification on instructions, usage, inherited continuation prefixes; task 095 |

`CLEVAL-*` requirements refine the environment-owned provenance previously
included in the removed generic `AEVAL-017` requirement.
