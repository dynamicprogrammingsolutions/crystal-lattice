# Cloud Orchestrator Guidelines

Cloud orchestrator tests must preserve realistic local-app -> orchestrator -> runtime -> sync-back behavior. Do not make e2e tests green by bypassing the public flow with direct runtime debug endpoints, absolute path overrides, harness-only transfer hosts, or fallback routing that hides a product bug. A realistic failing e2e is useful evidence; fix the code or record the exposed issue.

Related tests and harnesses:

- `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts`
- `packages/frontend-sdk/src/integration/harness.ts`
- `cloud-orchestrator/test/cloud_orchestrator/router_test.exs`
- `cloud-orchestrator/test/cloud_orchestrator/registry_test.exs`
- `cloud-orchestrator/test/cloud_orchestrator/docker_runner_test.exs`
- `cloud-orchestrator/test/cloud_orchestrator/token_test.exs`
- `cloud-orchestrator/deploy/aws-ec2/tests/smoke_secure.sh`
- `plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py`
