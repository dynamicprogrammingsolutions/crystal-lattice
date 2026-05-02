# Real Tool Sync-Back E2E
Verify sync-back using files created by normal cloud tool execution rather than direct runtime debug file endpoints.

## Requirements checklist

- [ ] Keep any direct `/cloud-agent/workspace/files` checks narrowly scoped to runtime debug/file API coverage.
- [ ] Add cloud sync-back e2e coverage where a file is created or modified by shell/apply-patch or file writer tool execution.
- [ ] Assert the tool-created cloud file syncs back to the local workspace through `cloud.sync_down` or `cloud.close_session`.
- [ ] Avoid request-time path overrides unless the test is explicitly about documented override behavior.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/062-clean-up-e2e-test-realism.md`
Depends On: `tasks/20260429-cloud-agent-orchestrator/065-cloud-runtime-working-directory.md`

## Context

`packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts:708-716` currently writes `from-cloud.txt` through `/cloud-agent/workspace/files` before testing sync-down. That validates transfer mechanics, but bypasses the user-facing path where tools create workspace changes according to provider/tool cwd and path policy.

This task should add or convert coverage so sync-back proves the real cloud agent workflow: model/tool execution creates the file in the cloud workspace, then the cloud plugin exports and applies those changes locally.