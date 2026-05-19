# Cloud Profile User Documentation
Create comprehensive user-facing documentation for cloud agent profile configuration, scripts, and defaults.

## Requirements checklist

- [ ] Add a dedicated user-facing cloud profile documentation page.
- [ ] Link from orchestrator/deployment docs where relevant without making orchestrator docs the primary user guide.
- [ ] Document profile sections, compatibility rules, path/env expansion, script env vars, defaults, and examples.
- [ ] Include examples for repo-local install scripts and multiple sync profiles.
- [ ] Keep docs aligned with implemented schema and tests.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/0122-sync-profile-selection-ui.md`

## Documentation Location

Prefer a dedicated page such as:

```text
docs/cloud-agent-profiles.md
```

or an equivalent application docs location. Orchestrator docs can link to this page, but should not be the main user-facing explanation because profiles are configured by app/plugin users, not only orchestrator deployers.

## Content To Include

- transfer-up profiles
- install profiles
- sync-down profiles
- container profiles
- compatibility model
- `${env:...}` expansion
- repo-root-relative paths
- config-asset-relative paths via `${env:CONFIG_DIR}`
- all script env vars
- default profile scripts and their safety tradeoffs
- examples:
  - current worktree patch round trip
  - clean-head upload with branch import
  - plain directory snapshot
  - repo install hook
