# Agent evaluation framework requirements

These requirements track the live implementation, verification,
documentation, and evidence state relative to the target specification.

Feature prefix: `AEVAL`

Implementation values use `Not started`, `In progress`, `Implemented`,
`Deferred`, or `Removed`.

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| AEVAL-001 | A maintainer-owned Python package exposes the agent evaluation library under the `agent_eval` import without making it public product documentation. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md` |
| AEVAL-002 | `AgentEval.run(name, execute, *, adapter=None, continue_from=None, workspace=None, cache_key=None)` is the minimal stable execution contract. | Not started | Unverified | Pending | Subtask 015 |
| AEVAL-003 | The framework does not hardcode prompts, message roles, guidance files, agents, models, skills, tools, reviewers, score types, mutation policy, or assertions. | Not started | Unverified | Pending | Subtask 015 |
| AEVAL-004 | A single `RuntimeAdapter` strategy separates generic lifecycle/caching/artifacts from runtime-specific configuration, restoration, snapshots, and observations. | Not started | Unverified | Pending | Subtask 015 |
| AEVAL-005 | The Crystal Lattice adapter uses Core/Application, supports caller-owned configuration and plugins, provides high-level context conveniences, and preserves direct access to application/core/session/configuration. | Not started | Unverified | Pending | Subtask 015 |
| AEVAL-006 | An execution callback may perform arbitrary Python and multiple runtime requests and may return any Python value through `Run.value`. | Not started | Unverified | Pending | Subtask 015 |
| AEVAL-007 | `Run` exposes the callback value, reusable snapshot, adapter observation, workspace, changed paths, artifact location, error, and concise helper methods without assigning a framework-owned verdict. | Not started | Unverified | Pending | Subtask 015 |
| AEVAL-008 | A run can continue from an immutable hash-verified parent snapshot in a clean compatible workspace while preserving parent and rebase/rebuild provenance. | Not started | Unverified | Pending | Subtask 015 |
| AEVAL-009 | Explicit cache keys reuse compatible expensive runs using adapter, workspace, parent, and schema fingerprints and reject incompatible or partial cache entries. | Not started | Unverified | Pending | Subtask 015 |
| AEVAL-010 | Existing paths and arbitrary workspace factories are supported, and an optional Git helper provides pinned revisions, clean workspaces, status, changed paths, and diffs. | Not started | Unverified | Pending | Subtask 015 |
| AEVAL-011 | Every run writes compact deterministic canonical artifacts and separately retained raw runtime/workspace/failure evidence, including useful error-phase information. | Not started | Unverified | Pending | Subtask 015 |
| AEVAL-012 | Artifact handling excludes credentials/authentication state, uses ignored local output by default, and permits runtime-owned redaction or retention behavior. | Not started | Unverified | Pending | Subtask 015 |
| AEVAL-013 | Deterministic tests cover callback execution, arbitrary return values, adapter selection, continuation, cache validation, workspace handling, artifacts, and failure preservation. | Not started | Unverified | Pending | Subtask 015 |
| AEVAL-014 | Pytest is the initial suite runner; real-model tests are explicitly marked and excluded from normal default tests, hosted execution is gated, and skipped gated tests are not counted as verification. | Not started | Unverified | Pending | Subtask 015 |
| AEVAL-015 | The first consumer tests exercise all `DOCGEN-*` and `DOCREP-*` documentation-standard instruction requirements through cached repository context and clean continuations. | Not started | Unverified | Pending | Subtask 015; `DOCVAL-005` |
| AEVAL-016 | Real-model artifacts preserve exact instruction, prompt, model/configuration, parent seed, response, tool, error, and result provenance while AI scoring remains supporting evidence rather than human verification. | Not started | Unverified | Pending | Subtask 015 |
| AEVAL-017 | Maintainer documentation explains the public contract, pytest workflow, cache behavior, artifact layout, custom configuration/plugin usage, and how to add a test without introducing framework-specific evaluation abstractions. | Not started | Unverified | Pending | Subtask 015 |