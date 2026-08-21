# Demo Connection Autoscaling And Load Harness

Publish bridge workload metrics and a deterministic non-production scaling
policy so connection-driven scale behavior can be tested before choosing the
production AWS runtime or scaling policy.

## Requirements checklist

- [ ] Bridge nodes publish active app connections, active server connections,
  active sessions, pending requests/transfers, throughput, and relevant
  saturation metrics.
- [ ] A replaceable demo scaling policy computes desired capacity from
  configurable connection thresholds, minimum, and maximum capacity.
- [ ] A local simulator and load harness can exercise scale-out, steady-state,
  scale-in, reconnect, and task-loss scenarios without production providers.
- [ ] Demo scaling decisions are observable and deterministic under an
  injected clock.
- [ ] The policy is explicitly non-production and does not hardcode EC2 or
  Fargate.
- [ ] Public AWS tests can optionally consume the metrics and demo policy.
- [ ] Tests verify metric cleanup and no negative/leaked counts after failures.
- [ ] Documentation explains the metric semantics and policy replacement
  boundary.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On: `tasks/20260821-modular-bridge-access-platform/040-demo-entitlement-limits-and-client-integration.md`

## Required reading

- `bridge-elixir/lib/bridge/server_registry.ex`
- `bridge-elixir/lib/bridge/session_manager.ex`
- Bridge HTTP transfer coordinator on the mixed-transport branch
- `bridge-elixir/deploy/aws-fargate/secure-origin.yaml`
- `bridge-elixir/deploy/aws-fargate/tests/`
- AWS ECS service autoscaling documentation

## Supporting details

A useful default demo rule is:

```text
desired =
  clamp(
    min_tasks,
    ceil(active_connections / configured_connections_per_task),
    max_tasks
  )
```

The implementation should also report CPU/memory and transfer pressure, but
the simple rule exists to prove metric and policy replacement. It does not
establish production capacity values.

## Execution plan

Status: Draft

Add a stable bridge metrics surface, deterministic scaling-policy interface,
local simulator, and repeatable connection/load generator. Optionally wire the
demo metric into guarded AWS tests, while leaving EC2/Fargate and production
threshold selection to later work.

### Implementation decisions and open questions

- Metrics are public operational contracts; production thresholds are not.
- Scaling decisions must not be required for bridge correctness.
- Long-lived connections do not migrate on scale-out; the harness must measure
  distribution of new connections and reconnect behavior.
- Scale-in behavior is simulated first and tested against AWS only under an
  explicit cost guard.

### Documentation

- Document metric names, units, aggregation, reset/cleanup, simulator commands,
  load profiles, and explicit non-production status.

### Task checklist

- [ ] Define bridge metrics and exporter boundary.
- [ ] Instrument app/server connections, sessions, requests, transfers, and
  throughput.
- [ ] Implement demo scaling policy and injected clock.
- [ ] Add load generator and local simulator.
- [ ] Add task-loss, reconnect, and cleanup scenarios.
- [ ] Add optional guarded AWS exercise.
- [ ] Add dashboards/output suitable for test diagnosis.
- [ ] Add tests and documentation.

### Requirement verification

- Produce deterministic desired-capacity decisions for controlled connection
  counts.
- Exercise scale-out/in simulations and abrupt node loss.
- Assert registries, leases, and metrics return to zero after cleanup.
- Verify the bridge remains functional if the scaling-policy component is
  unavailable.
- Run a guarded AWS smoke when authorized and report it separately from local
  evidence.
