# Script-Driven Cloud Layout Setup
Move cloud runtime directory/layout setup details out of the Docker runner where practical, using explicit scripts and env vars.

## Requirements checklist

- [ ] Define a layout/setup script hook for container/runtime directory preparation.
- [ ] Pass all relevant mount/path values as explicit env vars.
- [ ] Keep Docker runner responsible for starting/stopping containers and mounts.
- [ ] Preserve existing runtime layout behavior.
- [ ] Add tests for script env vars and resulting directory structure.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/0124-dockerfile-container-profiles.md`

## Background

The Docker runner currently prepares instance directories directly in Elixir and passes fixed container paths. Longer term, container-related operations should be controlled by explicit scripts/config where possible, while the Elixir runner remains responsible for container lifecycle.

Do this incrementally. Do not move all responsibilities at once if that risks destabilizing the start/sync flow.

## Expected Env Vars

Exact names can be refined, but scripts should receive values such as:

```text
CLOUD_AGENT_INSTANCE_DIR
CLOUD_AGENT_WORKSPACE_DIR
CLOUD_AGENT_SESSIONS_DIR
CLOUD_AGENT_CONFIG_PATH
CONFIG_DIR
WORKING_DIR
CLOUD_WORKSPACE_DIR
TRANSFER_DIR
SESSION_DIR
SESSION_ID
CLOUD_AGENT_CACHE_DIR
```
