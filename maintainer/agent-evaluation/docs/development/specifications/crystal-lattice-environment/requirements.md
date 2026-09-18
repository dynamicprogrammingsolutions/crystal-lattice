# Crystal Lattice evaluation environment requirements

These requirements define the optional Crystal Lattice environment supplied
with `agent_eval`.

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| AEVAL-005 | The first `CrystalLatticeEnvironment` uses Core/Application, supports caller-owned configuration and plugins, and exposes a context with direct access to application, core, session, configuration, workspace, and run services. | Implemented | Automated | Documented | Real `AgentApplication`/`AgentCore` construction, plugin-loading, request, streaming, tool-loop, cache, continuation, and cleanup tests; package docs |
| AEVAL-006 | Crystal Lattice request execution/tool-loop control, stopping, snapshotting, observation, evidence projection, evaluation, and presentation are replaceable at their point of use and are not requirements for alternate environments. | Implemented | Automated | Documented | Default/custom driver, observer, stop, mutation classifier, named snapshot, projection, evaluation, presentation, and alternate-environment tests |
