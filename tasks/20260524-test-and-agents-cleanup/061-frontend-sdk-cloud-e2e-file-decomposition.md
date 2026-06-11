# Frontend SDK Cloud E2E File Decomposition

Split or otherwise reorganize the frontend SDK cloud orchestrator e2e coverage so cloud subcategories are selected by explicit files/scripts instead of internal category env gates. This is a direct follow-up to task `060`, which made exact-file selection the standard model but intentionally avoided decomposing the large mixed cloud e2e file in the same pass.

## Requirements checklist

- [ ] Audit `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts` and identify separable cloud e2e categories.
- [ ] Replace remaining `RUN_CLOUD_ORCHESTRATOR_*` category gates with file/script selection where practical.
- [ ] Keep env vars for credentials, modes, and AWS danger interlocks.
- [ ] Preserve existing coverage for base cloud e2e, OpenRouter cloud e2e, local Codex/default-config e2e, and AWS Codex/default-config e2e.
- [ ] Update `packages/frontend-sdk/package.json` scripts and integration README guidance to match the new file layout.
- [ ] Verify with safe collection or targeted runs, avoiding hosted API, Docker, cloud, and AWS execution unless explicitly requested.

Parent Task: `tasks/20260524-test-and-agents-cleanup/000-main.md`

Depends On: `tasks/20260524-test-and-agents-cleanup/060-sdk-test-guidance-and-command-alignment.md`

## Why this follow-up exists

Task `060` moved the frontend SDK toward a safer command model:

- default `npm test` excludes `src/integration/**`
- integration scripts select exact files through `vitest.integration.config.ts`
- old broad category gates such as `RUN_BACKEND_INTEGRATION`, `RUN_BRIDGE_E2E_INTEGRATION`, and `RUN_CLOUD_ORCHESTRATOR_E2E` were removed where file selection was enough

However, `cloud-orchestrator.e2e.integration.test.ts` still contains multiple materially different categories in one file:

- base local/AWS cloud orchestrator e2e
- OpenRouter cloud tool-call e2e
- local Codex/default-config e2e
- AWS Codex/default-config e2e

Because those categories still share one file, task `060` kept these internal gates:

- `RUN_CLOUD_ORCHESTRATOR_OPENROUTER_E2E`
- `RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_E2E`
- `RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_EC2_E2E`

This follow-up should remove that remaining category-gate pattern by splitting or restructuring the file, while preserving the AWS danger interlocks such as `RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1`.

## Likely files to inspect

- `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts`
- `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.profiles.e2e.integration.test.ts`
- `packages/frontend-sdk/src/integration/harness.ts`
- `packages/frontend-sdk/package.json`
- `packages/frontend-sdk/src/integration/__tests__/README.md`