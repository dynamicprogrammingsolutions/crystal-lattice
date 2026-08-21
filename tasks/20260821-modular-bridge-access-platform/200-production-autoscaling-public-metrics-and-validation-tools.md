# Production Autoscaling Public Metrics And Validation Tools

Provide production-capable public metrics, draining hooks, load generators, and
validation tools without selecting private capacity thresholds or an EC2 versus
Fargate production runtime.

## Requirements checklist

- [ ] Bridge connection, session, transfer, throughput, saturation, reconnect,
  and error metrics have stable documented semantics.
- [ ] Bridge processes support graceful drain and shutdown for long-lived
  WebSocket and HTTP transfer work.
- [ ] Load tools exercise scale-out, new-connection distribution, scale-in,
  task loss, reconnect/resume, and cluster churn.
- [ ] Validation can target Docker, external URLs, public AWS EC2, and public
  AWS Fargate profiles.
- [ ] Tests distinguish local simulation, AWS infrastructure smoke, and full
  public backend/client E2E boundaries.
- [ ] Generic scaling-policy inputs are replaceable and do not publish
  commercial thresholds.
- [ ] Cost-bearing tests require explicit guards and reliable cleanup.
- [ ] Public documentation explains supported evidence and remaining runtime
  decisions.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On:

- `tasks/20260821-modular-bridge-access-platform/050-demo-connection-autoscaling-and-load-harness.md`
- `tasks/20260821-modular-bridge-access-platform/180-public-aws-bridge-template-modularization.md`

## Required reading

- Existing bridge AWS smoke tests and frontend SDK integration harness
- Bridge clustering and registry/session lifecycle code
- AWS ALB/ECS/EC2 connection draining and autoscaling documentation

## Execution plan

Status: Draft

Promote the demo metrics/load seams into stable public operational contracts,
add graceful drain behavior, and build repeatable provider-independent load and
failure scenarios. Leave capacity targets and production stack composition to
the operator.

### Implementation decisions and open questions

- Existing connections do not migrate on scale-out; new connections and
  reconnect behavior are measured explicitly.
- Production runtime selection remains open.
- No AWS test counts as passing if cleanup, collection, or teardown fails.

### Documentation

- Document metrics, drain lifecycle, load profiles, commands, guards, evidence
  boundaries, diagnosis, and cleanup.

### Task checklist

- [ ] Stabilize metric names and exporters.
- [ ] Implement graceful drain/shutdown hooks.
- [ ] Extend load generator and cluster-churn scenarios.
- [ ] Add Docker/external/AWS provider selection.
- [ ] Add guarded EC2/Fargate exercises.
- [ ] Add failure cleanup and diagnostic output.
- [ ] Add tests and documentation.

### Requirement verification

- Exercise controlled scale-out/in and task loss with active clients.
- Verify new connections distribute after scale-out.
- Verify drain completes or forces documented reconnect after timeout.
- Verify all test-created AWS resources are cleaned up.
