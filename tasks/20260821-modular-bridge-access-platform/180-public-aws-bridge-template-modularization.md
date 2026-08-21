# Public AWS Bridge Template Modularization

Improve the public AWS bridge deployment components so operators can select
security profiles, attach replaceable services, manage secrets safely, and use
either EC2- or Fargate-compatible bridge images without hosted-service
assumptions.

## Requirements checklist

- [ ] Public templates parameterize access profile, pairing policy, E2EE policy,
  provider endpoints/JWKS, metrics, and quota/usage integration.
- [ ] Secrets are referenced from AWS secret storage rather than exposed as
  ordinary template parameters or command output.
- [ ] Bridge tasks can run behind secure HTTPS/WSS edges with required headers,
  no caching, and credential-log protections.
- [ ] Public components remain usable for community static-token and demo
  deployments without production services.
- [ ] EC2 and Fargate remain replaceable runtime choices at component
  boundaries.
- [ ] Multi-node clustering, health, graceful shutdown, and metrics hooks are
  represented consistently.
- [ ] Templates and scripts are idempotent, guarded, testable, and clean up
  safely.
- [ ] Existing public deployment profiles retain documented migration paths.
- [ ] Public AWS documentation covers cost-bearing resources and cleanup.

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
