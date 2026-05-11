# Clean Up Cloud E2E Test Realism
Remove integration/e2e test logic that hides real cloud orchestrator defects, even if that makes tests fail until follow-up product fixes land.

## Requirements checklist

- [x] Review `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts` for test-only shortcuts, direct runtime debug endpoints, and config overrides that bypass real product behavior.
- [x] Remove or isolate path overrides that mask the default-config cloud runtime working-directory issue.
- [x] Add assertions that expose cloud-created sessions missing from connection session lists.
- [x] Replace or clearly scope direct `/cloud-agent/workspace/files` writes so sync-back coverage includes a realistic tool-created file path.
- [x] Keep realistic failing tests in place when they expose product defects; do not weaken them for a green suite.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/0110-connection-scoped-cloud-routing.md`

## Context

Review found several places where cloud orchestrator e2e coverage avoids real product behavior:

- `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts:412-425` defines absolute `localOverrides` and `cloudOverrides`.
- `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts:474-493` sends the cloud default-config turn with `configOverrides: cloudOverrides`, masking the runtime cwd bug in `tasks/20260429-cloud-agent-orchestrator/0112-cloud-runtime-working-directory.md`.
- `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts:1009-1017` creates a new session through the cloud connection but does not assert that the session appears in `cloudBackend.listSessions()`.
- `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts:708-716` writes `from-cloud.txt` through `/cloud-agent/workspace/files`, bypassing normal tool execution.

The goal of this subtask is not to fix every exposed product defect. It is to make the e2e tests honest enough that follow-up subtasks can fix the product behavior one issue at a time.

## Execution plan

Added during completion after reviewing the current frontend SDK e2e file, integration harness, cloud runtime debug endpoints, connection registry session aggregation, and the dependent routing/working-directory task notes.

1. Add a real process working-directory option to the TypeScript integration backend harness so default-config local Codex turns can run from the temporary workspace without per-request absolute path overrides.
2. Remove the cloud/default-config `working_directory` and `allowed_paths` request overrides from the Codex local-cloud-local e2e flow, while keeping only non-path behavior overrides that do not mask the runtime cwd issue.
3. Add cloud-created-session visibility assertions after cloud-side session creation so the connection session list defect is exposed instead of silently bypassed.
4. Replace the ungated sync-back proof that currently writes through `POST /cloud-agent/workspace/files` with a public session/tool-loop path and assert the synced-back workspace file comes from runtime behavior rather than the debug write endpoint.
5. Run focused frontend SDK verification. If the cleaned-up e2e exposes product defects, keep the failing assertions and report them rather than weakening the tests.

## Completion Notes

Added during completion after implementation.

- Added `cwd` support to the TypeScript backend integration harness so local default-config e2e servers can be started from the temporary project workspace.
- Removed default-config Codex request-time `working_directory` and `allowed_paths` overrides from the local/cloud/local chain. The remaining request overrides are non-path behavior knobs.
- Replaced the ungated sync-back test's direct `POST /cloud-agent/workspace/files` write with a public session/tool-loop path: create a cloud-side session, append an assistant `write_file` tool call, run `/send`, verify the file through the read probe, and sync it back.
- Added assertions that cloud-created sessions appear in connection-scoped `cloudBackend.listSessions()` for both the ungated echo/runtime flow and the OpenRouter flow.
- Verification:
  - `cd packages/frontend-sdk && npm test -- cloud-orchestrator.e2e.integration.test.ts` passed with all e2e tests skipped, confirming the file compiles.
  - `cd packages/frontend-sdk && RUN_CLOUD_ORCHESTRATOR_E2E=1 npm test -- cloud-orchestrator.e2e.integration.test.ts` failed as intended on the new cloud-created-session assertion: `cloudBackend.listSessions()` does not include the session created through the cloud connection. The preceding tool-created file sync-back path completed before this assertion.

The exposed failure should be fixed by `tasks/20260429-cloud-agent-orchestrator/0113-connection-created-session-routing.md`.