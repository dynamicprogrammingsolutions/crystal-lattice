# Cloud Transfer Endpoint Configuration
Make cloud transfer endpoints real deployment configuration instead of harness-only knowledge.

## Requirements checklist

- [ ] Define how deployed orchestrators advertise or document the managed SSH transfer public host separately from the HTTP orchestrator URL.
- [ ] Update local app/cloud plugin configuration flow so AWS CloudFront deployments do not require e2e-only `transfer_public_host` injection.
- [x] Revert the e2e-only `transfer_public_host` harness injection so the AWS transfer configuration gap remains visible until product configuration is fixed.
- [ ] Keep CloudFront as the orchestrator HTTP endpoint and use the EC2 origin host only for managed SSH transfers.
- [ ] Update AWS/local e2e coverage to use the same configuration path a real deployment or copied connection setup would use.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/062-clean-up-e2e-test-realism.md`
Depends On: `tasks/20260429-cloud-agent-orchestrator/060-connection-scoped-cloud-routing.md`

## Context

During gated AWS e2e, upload/download transfers failed when the plugin used the CloudFront host for managed SSH ports. A previous test workaround parsed the EC2 origin host from deployment output in `packages/frontend-sdk/src/integration/harness.ts`, stored it as `transferPublicHost`, and injected it into test config in `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts`. That workaround has been reverted because it was harness-only knowledge rather than a real user/deployment configuration path.

A normal local app configured with only the CloudFront orchestrator URL still does not know where to connect for managed SSH transfer slots. This task should turn that into real deployment/application configuration rather than a test-only workaround.