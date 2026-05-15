# Real Tool Sync-Back E2E
Verify sync-back using files created by normal cloud tool execution rather than direct runtime debug file endpoints.

## Requirements checklist

- [x] Keep any direct `/cloud-agent/workspace/files` checks narrowly scoped to runtime debug/file API coverage.
- [x] Add cloud sync-back e2e coverage where a file is created or modified by shell/apply-patch or file writer tool execution.
- [x] Assert the tool-created cloud file syncs back to the local workspace through `cloud.sync_down` or `cloud.close_session`.
- [x] Avoid request-time path overrides unless the test is explicitly about documented override behavior.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/0111-clean-up-e2e-test-realism.md`
Depends On: `tasks/20260429-cloud-agent-orchestrator/0112-cloud-runtime-working-directory.md`

## Context

`packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts:708-716` currently writes `from-cloud.txt` through `/cloud-agent/workspace/files` before testing sync-down. That validates transfer mechanics, but bypasses the user-facing path where tools create workspace changes according to provider/tool cwd and path policy.

This task should add or convert coverage so sync-back proves the real cloud agent workflow: model/tool execution creates the file in the cloud workspace, then the cloud plugin exports and applies those changes locally.

## Execution plan

Added during completion after investigating the current e2e test state and approved by the user.

1. Tighten the ungated cloud sync-back e2e so the tool-created file proof goes through normal tool-loop/session history plus local sync-back, not a direct runtime debug file read.
2. Keep direct `/cloud-agent/workspace/files` GETs scoped to transfer/runtime debug coverage for transferred local files and config assets.
3. Preserve the deterministic assistant `write_file` tool call in the ungated echo-provider e2e because that still exercises the public `/send` tool-loop path without relying on model behavior.
4. Preserve or tighten the OpenRouter e2e as the model-prompted version, waiting on tool-result session history before asserting the synced-back local file.
5. Run focused frontend SDK verification, then gated local cloud e2e, then the OpenRouter-gated e2e if credentials are available through the backend application's normal dotenv/config lookup.

## Completion Notes

Added during completion after implementation and verification.

- Added a `hasToolResult(...)` test helper so cloud tool execution can be verified through session history.
- Updated the ungated cloud sync-back e2e to wait for the `write_file` tool result in the cloud-created session instead of reading the tool-created file through `/cloud-agent/workspace/files`.
- Updated the OpenRouter e2e to wait for the model-prompted `write_file` tool result instead of probing the tool-created file through the runtime debug file endpoint.
- Kept direct `/cloud-agent/workspace/files` GETs for transferred local files and config assets, where they are runtime transfer/debug API coverage rather than the sync-back proof.
- Verified that the tool-created files sync back locally through `cloud.sync_down`.

Verification:

```bash
cd packages/frontend-sdk && npm test -- cloud-orchestrator.e2e.integration.test.ts
cd packages/frontend-sdk && RUN_CLOUD_ORCHESTRATOR_E2E=1 npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "opens a cloud session through CloudTransport and syncs workspace files back down"
cd packages/frontend-sdk && RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_CLOUD_ORCHESTRATOR_OPENROUTER_E2E=1 npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "runs local and cloud OpenRouter tool calls"
cd packages/frontend-sdk && RUN_CLOUD_ORCHESTRATOR_E2E=1 npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts
```