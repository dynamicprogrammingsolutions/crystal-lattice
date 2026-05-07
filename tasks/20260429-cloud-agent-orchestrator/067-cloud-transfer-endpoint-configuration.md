# Cloud Transfer Endpoint Configuration
Make cloud transfer endpoints real deployment configuration instead of harness-only knowledge.

## Requirements checklist

- [x] Define how deployed orchestrators advertise or document the managed SSH transfer public host separately from the HTTP orchestrator URL.
- [x] Update local app/cloud plugin configuration flow so AWS CloudFront deployments do not require e2e-only `transfer_public_host` injection.
- [x] Revert the e2e-only `transfer_public_host` harness injection so the AWS transfer configuration gap remains visible until product configuration is fixed.
- [x] Keep CloudFront as the orchestrator HTTP endpoint and use the EC2 origin host only for managed SSH transfers.
- [x] Update AWS/local e2e coverage to use the same configuration path a real deployment or copied connection setup would use.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/062-clean-up-e2e-test-realism.md`
Depends On: `tasks/20260429-cloud-agent-orchestrator/060-connection-scoped-cloud-routing.md`

## Context

During gated AWS e2e, upload/download transfers failed when the plugin used the CloudFront host for managed SSH ports. A previous test workaround parsed the EC2 origin host from deployment output in `packages/frontend-sdk/src/integration/harness.ts`, stored it as `transferPublicHost`, and injected it into test config in `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts`. That workaround has been reverted because it was harness-only knowledge rather than a real user/deployment configuration path.

A normal local app configured with only the CloudFront orchestrator URL still does not know where to connect for managed SSH transfer slots. This task should turn that into real deployment/application configuration rather than a test-only workaround.

## Execution plan

Added during completion after investigating the current managed SSH transfer flow, AWS EC2 deployment scripts, local app plugin config, and current task status for `tasks/20260429-cloud-agent-orchestrator/065-cloud-runtime-working-directory.md` and `tasks/20260429-cloud-agent-orchestrator/066-connection-created-session-routing.md`.

1. Add first-class orchestrator deployment configuration for the managed SSH transfer public host.

   - Add `transfer_public_host` to cloud orchestrator config, sourced from `CLOUD_ORCHESTRATOR_TRANSFER_PUBLIC_HOST`.
   - Update managed SSH endpoint selection to use request `public_host`, then configured `transfer_public_host`, then the current `public_url` host fallback.
   - Preserve request-level `public_host` as a manual/compatibility override.

2. Wire AWS EC2 CloudFront deployment to set and advertise the transfer host.

   - Pass the EC2 public DNS into the orchestrator container as `CLOUD_ORCHESTRATOR_TRANSFER_PUBLIC_HOST`.
   - Extend AWS deploy output/status JSON and text with `CloudOrchestratorTransferPublicHost`/`transferPublicHost`.
   - Keep `CLOUD_ORCHESTRATOR_PUBLIC_URL` as the CloudFront URL for HTTP control-plane traffic.

3. Keep local app configuration simple and real-user shaped.

   - Avoid requiring `application.cloud_agent.transfer_public_host` for AWS CloudFront deploys.
   - Keep the plugin compatible with optional `transfer_public_host`, but omit the field from transfer-create payloads when unset so the orchestrator owns the normal endpoint choice.
   - Update docs/default examples to describe the advanced override separately from the happy path.

4. Update tests and e2e harness expectations without reintroducing harness-only injection.

   - Add focused Elixir coverage for configured transfer host fallback and request override precedence.
   - Add/update Python plugin coverage proving transfer creation does not require `transfer_public_host` in app config.
   - Update frontend SDK AWS deploy-output parsing only to expose/document the transfer host, not inject it into cloud app config.
   - Check tasks 065 and 066 before gated e2e. Defer broader e2e failures when they depend on their remaining/open issues rather than weakening this task's tests.

5. Verification target.

   - `cd cloud-orchestrator && mix test`
   - `PYTHONPATH=plugins/cloud-agent-app/src pytest plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py -q`
   - `cd packages/frontend-sdk && npm test -- cloud-orchestrator.e2e.integration.test.ts`
   - Run AWS-gated e2e only if the environment is available and failures are not attributable to still-open/deferred work from tasks 065/066.

## Completion Notes

Added during completion after implementation and verification.

- Added orchestrator config `transfer_public_host`, sourced from `CLOUD_ORCHESTRATOR_TRANSFER_PUBLIC_HOST`.
- Updated managed SSH endpoint host selection to prefer request `public_host`, then configured `transfer_public_host`, then the host from `CLOUD_ORCHESTRATOR_PUBLIC_URL`.
- Updated AWS EC2 CloudFront deploy to set `CLOUD_ORCHESTRATOR_TRANSFER_PUBLIC_HOST` to the EC2 public DNS while keeping `CLOUD_ORCHESTRATOR_PUBLIC_URL` as the CloudFront URL.
- Added deploy/status output fields `CloudOrchestratorTransferPublicHost` and `transferPublicHost` so the split endpoint model is visible without requiring local app config injection.
- Updated the cloud app plugin to omit `public_host` from transfer-create payloads unless `application.cloud_agent.transfer_public_host` is explicitly set as an advanced/manual override.
- Updated docs to describe the normal flow: local apps configure only the orchestrator HTTP URL/token and use the transfer endpoint returned by the orchestrator.
- Updated frontend SDK deploy-output parsing to expose `transferPublicHost` for visibility, without injecting it into cloud app config.
- Checked dependent task status before gated e2e: `tasks/20260429-cloud-agent-orchestrator/065-cloud-runtime-working-directory.md` is complete; `tasks/20260429-cloud-agent-orchestrator/066-connection-created-session-routing.md` still has its gated-e2e dependency check open. AWS-gated e2e was deferred for this task.

Verification:

```bash
cd cloud-orchestrator && mix format && mix test
PYTHONPATH=plugins/cloud-agent-app/src pytest plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py -q
cd packages/frontend-sdk && npm test -- cloud-orchestrator.e2e.integration.test.ts
```