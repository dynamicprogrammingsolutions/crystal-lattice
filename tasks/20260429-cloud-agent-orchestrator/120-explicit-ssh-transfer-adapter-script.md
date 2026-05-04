# Explicit SSH Transfer Adapter Script
Move the managed SSH rsync adapter into explicit default config assets instead of relying on a hidden plugin fallback.

## Requirements checklist

- [ ] Package the default managed SSH rsync adapter script under default config assets.
- [ ] Reference the adapter explicitly from default config using `${env:CONFIG_DIR}`.
- [ ] Preserve current managed SSH behavior.
- [ ] Ensure adapter script receives explicit env vars.
- [ ] Remove or reduce hidden `null` fallback behavior for important lifecycle scripts.
- [ ] Add tests for adapter path resolution and env var passing.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/070-cloud-profile-config-no-behavior-change.md`

## Background

Currently the plugin can fall back to a packaged `managed_ssh_rsync.sh` when the config does not specify an adapter script. The desired direction is to make defaults explicit and inspectable in config.

The default config should point to a script such as:

```json
{
  "managed_ssh": {
    "adapter_script": "${env:CONFIG_DIR}/cloud-agent/transfer/managed-ssh-rsync"
  }
}
```

Exact path can be refined during implementation.

## Script Environment

The adapter should continue receiving explicit env vars such as:

```text
TRANSFER_DIRECTION
TRANSFER_DIR
TRANSFER_ID
TRANSFER_SSH_HOST
TRANSFER_SSH_PORT
TRANSFER_SSH_USER
TRANSFER_SSH_KEY_PATH
TRANSFER_SSH_KNOWN_HOSTS
TRANSFER_REMOTE_PATH
SSH_PATH
RSYNC_PATH
RSYNC_EXTRA_ARGS
```
