# Cloud Agent Orchestrator Renumbering Map
This side document records the task-file renaming performed to clarify the execution order. Use it to trace old references to their current task files.

## Renaming map

| Old task file | New task file |
| --- | --- |
| `tasks/20260429-cloud-agent-orchestrator/010-remote-docker-orchestrator-mvp.md` | `tasks/20260429-cloud-agent-orchestrator/0100-remote-docker-orchestrator-mvp.md` |
| `tasks/20260429-cloud-agent-orchestrator/015-agentapplication-cloud-runtime.md` | `tasks/20260429-cloud-agent-orchestrator/0101-agentapplication-cloud-runtime.md` |
| `tasks/20260429-cloud-agent-orchestrator/018-explicit-transfer-script-contract.md` | `tasks/20260429-cloud-agent-orchestrator/0102-explicit-transfer-script-contract.md` |
| `tasks/20260429-cloud-agent-orchestrator/019-async-runtime-readiness-observability.md` | `tasks/20260429-cloud-agent-orchestrator/0103-async-runtime-readiness-observability.md` |
| `tasks/20260429-cloud-agent-orchestrator/055-cloud-runtime-startup-optimizations.md` | `tasks/20260429-cloud-agent-orchestrator/0104-cloud-runtime-startup-optimizations.md` |
| `tasks/20260429-cloud-agent-orchestrator/060-connection-scoped-cloud-routing.md` | `tasks/20260429-cloud-agent-orchestrator/0110-connection-scoped-cloud-routing.md` |
| `tasks/20260429-cloud-agent-orchestrator/062-clean-up-e2e-test-realism.md` | `tasks/20260429-cloud-agent-orchestrator/0111-clean-up-e2e-test-realism.md` |
| `tasks/20260429-cloud-agent-orchestrator/065-cloud-runtime-working-directory.md` | `tasks/20260429-cloud-agent-orchestrator/0112-cloud-runtime-working-directory.md` |
| `tasks/20260429-cloud-agent-orchestrator/066-connection-created-session-routing.md` | `tasks/20260429-cloud-agent-orchestrator/0113-connection-created-session-routing.md` |
| `tasks/20260429-cloud-agent-orchestrator/067-cloud-transfer-endpoint-configuration.md` | `tasks/20260429-cloud-agent-orchestrator/0114-cloud-transfer-endpoint-configuration.md` |
| `tasks/20260429-cloud-agent-orchestrator/068-real-tool-sync-back-e2e.md` | `tasks/20260429-cloud-agent-orchestrator/0115-real-tool-sync-back-e2e.md` |
| `tasks/20260429-cloud-agent-orchestrator/070-cloud-profile-config-no-behavior-change.md` | `tasks/20260429-cloud-agent-orchestrator/0120-cloud-profile-config-no-behavior-change.md` |
| `tasks/20260429-cloud-agent-orchestrator/080-default-cloud-profile-scripts.md` | `tasks/20260429-cloud-agent-orchestrator/0121-default-cloud-profile-scripts.md` |
| `tasks/20260429-cloud-agent-orchestrator/090-sync-profile-selection-ui.md` | `tasks/20260429-cloud-agent-orchestrator/0122-sync-profile-selection-ui.md` |
| `tasks/20260429-cloud-agent-orchestrator/100-cloud-profile-user-docs.md` | `tasks/20260429-cloud-agent-orchestrator/0123-cloud-profile-user-docs.md` |
| `tasks/20260429-cloud-agent-orchestrator/110-dockerfile-container-profiles.md` | `tasks/20260429-cloud-agent-orchestrator/0124-dockerfile-container-profiles.md` |
| `tasks/20260429-cloud-agent-orchestrator/120-explicit-ssh-transfer-adapter-script.md` | `tasks/20260429-cloud-agent-orchestrator/0125-explicit-ssh-transfer-adapter-script.md` |
| `tasks/20260429-cloud-agent-orchestrator/130-script-driven-cloud-layout.md` | `tasks/20260429-cloud-agent-orchestrator/0126-script-driven-cloud-layout.md` |
| `tasks/20260429-cloud-agent-orchestrator/140-cloud-specific-config-overrides.md` | `tasks/20260429-cloud-agent-orchestrator/0127-cloud-specific-config-overrides.md` |
| `tasks/20260429-cloud-agent-orchestrator/020-linked-readonly-session-ux.md` | `tasks/20260429-cloud-agent-orchestrator/0200-linked-readonly-session-ux.md` |
| `tasks/20260429-cloud-agent-orchestrator/030-native-cloud-connection-ux.md` | `tasks/20260429-cloud-agent-orchestrator/0300-native-cloud-connection-ux.md` |
| `tasks/20260429-cloud-agent-orchestrator/040-reuse-multi-session-and-sync-polish.md` | `tasks/20260429-cloud-agent-orchestrator/0400-reuse-multi-session-and-sync-polish.md` |
| `tasks/20260429-cloud-agent-orchestrator/050-provider-and-deployment-expansion.md` | `tasks/20260429-cloud-agent-orchestrator/0500-provider-and-deployment-expansion.md` |

## Numbering shape

- `0100` through `0199`: MVP and follow-up work before the next major phase.
- `0200`: linked readonly session UX.
- `0300`: native cloud connection UX.
- `0400`: reuse, multi-session transfer, and sync polish.
- `0500`: provider and deployment expansion.