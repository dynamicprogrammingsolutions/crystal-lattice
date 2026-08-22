# Community Operations And Provider Runbook

Document and verify how community operators deploy, secure, monitor, replace
providers, back up state, rotate keys, diagnose failures, and upgrade the public
bridge platform.

## Requirements checklist

### Functional requirements

- [ ] **P1** — Community operators can deploy supported profiles and attach
  replacement identity, entitlement, quota, usage, and access-grant services
  through the public contracts.
- [ ] **P2** — Runbooks cover token/key rotation, E2EE reset, backups, restore,
  upgrades, compatibility, metrics, draining, cleanup, and troubleshooting
  across transport, authentication, pairing, entitlement, quota, E2EE,
  provider, and local-backend failures.
- [ ] **P3** — Validated commands and expected results cover supported AWS and
  non-AWS community deployments.

### Non-functional requirements

- [ ] **P1** — Public operations guidance excludes private hosted topology,
  credentials, commercial thresholds, and customer-support procedures and
  clearly assigns security and data-retention responsibilities.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On:

- `tasks/20260821-modular-bridge-access-platform/180-public-aws-bridge-template-modularization.md`
- `tasks/20260821-modular-bridge-access-platform/200-production-autoscaling-public-metrics-and-validation-tools.md`

## Specifications and requirements

- `docs/development/specifications/bridge-access-control/index.md`:
  `BAC-004` through `BAC-017`
- `docs/development/specifications/bridge-connectivity/index.md`:
  `BRG-019`, `BRG-020`
- `docs/development/specifications/bridge-e2ee/index.md`:
  `BEE-008` through `BEE-010`

## Required reading

- Bridge quickstart, protocol, deployment, and production-deployment docs
- Public provider, E2EE, quota, metrics, and AWS contracts
- Current community CLI/mobile connection guides

## Execution plan

Status: Draft

Consolidate public operational guidance around delivered profiles and provider
contracts, source command examples from tested scripts, and add focused
recovery/rotation/upgrade smoke coverage where documentation alone would be
unreliable.

### Implementation decisions and open questions

- This is a public self-hosting runbook, not customer-support or hosted-service
  operations.
- Provider-specific examples use demo/fake services or community-supplied
  values.

### Documentation

This task primarily updates current package user and development docs. New
claims land with the implementation/test scripts that make them true.

### Task checklist

- [ ] Consolidate profile deployment and provider attachment.
- [ ] Add rotation, backup/restore, upgrade, drain, and E2EE reset procedures.
- [ ] Add metrics/diagnosis and error taxonomy.
- [ ] Add AWS and non-AWS cleanup/recovery.
- [ ] Validate commands and expected results.
- [ ] Update documentation indexes and site preparation.

### Requirement verification

- Execute first-success flows for each public profile.
- Exercise at least one token rotation, provider replacement, backup/restore,
  and failed-upgrade recovery.
- Validate all linked commands and documentation builds.
