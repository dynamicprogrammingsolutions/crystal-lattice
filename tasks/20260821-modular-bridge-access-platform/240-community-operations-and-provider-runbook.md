# Community Operations And Provider Runbook

Document and verify how community operators deploy, secure, monitor, replace
providers, back up state, rotate keys, diagnose failures, and upgrade the public
bridge platform.

## Requirements checklist

- [ ] Operators can deploy local-open, static-token, and demo profiles with
  explicit security warnings and expected results.
- [ ] Provider implementers can attach identity, entitlement, quota, usage, and
  grant services through the public contracts.
- [ ] Runbooks cover token/key rotation, E2EE reset, backups, restore, upgrades,
  compatibility, metrics, draining, and cleanup.
- [ ] Troubleshooting distinguishes transport, authentication, pairing,
  entitlement, limits, E2EE, provider, and local-backend failures.
- [ ] Public operational examples contain no private hosted topology,
  credentials, thresholds, or customer-support procedures.
- [ ] Commands and expected outputs are validated by tests or smoke scripts.
- [ ] AWS and non-AWS community paths remain documented.
- [ ] Security and data-retention responsibilities are explicit.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On:

- `tasks/20260821-modular-bridge-access-platform/180-public-aws-bridge-template-modularization.md`
- `tasks/20260821-modular-bridge-access-platform/200-production-autoscaling-public-metrics-and-validation-tools.md`

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
