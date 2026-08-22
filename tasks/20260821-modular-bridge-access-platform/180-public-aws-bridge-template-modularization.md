# Public AWS Bridge Template Modularization

Improve the public AWS bridge deployment components so operators can select
security profiles, attach replaceable services, manage secrets safely, and use
either EC2- or Fargate-compatible bridge images without hosted-service
assumptions.

## Requirements checklist

### Functional requirements

- [ ] **P1** — Public AWS components support configurable access, pairing,
  E2EE, providers/JWKS, metrics, quotas, usage, and community profiles without
  coupling to one hosted service or runtime.
- [ ] **P1** — Bridge deployments run behind secure HTTPS/WSS edges with the
  headers, cache policy, health, clustering, graceful-shutdown, and metrics
  hooks required by the public bridge contracts.
- [ ] **P2** — EC2 and Fargate remain replaceable runtime choices at public
  component boundaries.

### Non-functional requirements

- [ ] **P1** — Secrets are referenced from AWS secret storage and are not
  exposed as ordinary template parameters, command output, or logs.
- [ ] **P1** — Templates and scripts are idempotent, explicitly guarded, and
  clean up safely.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On:

- `tasks/20260821-modular-bridge-access-platform/020-configurable-bridge-access-and-pairing-profiles.md`
- `tasks/20260821-modular-bridge-access-platform/050-demo-connection-autoscaling-and-load-harness.md`
- `tasks/20260821-modular-bridge-access-platform/170-mixed-transport-access-e2ee-and-metering-alignment.md`

## Required reading

- `bridge-elixir/deploy/aws-fargate/`
- `bridge-elixir/deploy/aws-ec2/`
- Completed AWS Fargate task
- AWS ECS/EC2, Secrets Manager, CloudFormation, ALB, CloudFront, and CloudWatch
  documentation

## Execution plan

Status: Draft

Refactor the public templates into reusable edge, bridge-service, metrics, and
configuration components. Move secrets to managed references, expose provider
contracts without embedding a particular hosted service, and preserve guarded
real-AWS smoke tests.

Existing public deployment profiles retain documented migration paths, and the
public AWS documentation identifies cost-bearing resources and cleanup.

### Implementation decisions and open questions

- This task does not choose the production hosted runtime.
- Public templates may provide reference composition; production account,
  domain, database, and alert configuration remain external.
- Existing cheap/test profiles remain clearly labeled.

### Documentation

- Update AWS prerequisites, profiles, parameters, secrets, costs, validation,
  smoke tests, stop/start/down behavior, and provider attachment.

### Task checklist

- [ ] Extract reusable template/component boundaries.
- [ ] Add profile/provider/E2EE/quota parameters and validation.
- [ ] Integrate AWS secret references.
- [ ] Preserve EC2 and Fargate image/runtime compatibility.
- [ ] Add metrics and graceful lifecycle configuration.
- [ ] Update scripts, outputs, static validation, and guarded smoke tests.
- [ ] Add migration and documentation.

### Requirement verification

- Validate every CloudFormation template.
- Deploy static-token and demo profiles through guarded AWS smoke tests.
- Verify secrets are absent from stack outputs, command logs, and task
  descriptions where avoidable.
- Exercise multi-node health and one controlled task replacement.
