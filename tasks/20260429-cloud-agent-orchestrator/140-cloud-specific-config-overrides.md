# Cloud-Specific Config Overrides
Add deterministic cloud runtime config overrides for path policy and other settings that must differ between local and cloud.

## Requirements checklist

- [ ] Add profile/config-level cloud runtime overrides applied during portable config generation.
- [ ] Apply overrides after mixin resolution and profile selection.
- [ ] Keep override behavior plugin-agnostic and deterministic.
- [ ] Support path-related settings such as `working_directory` and `allowed_paths`.
- [ ] Add tests for override ordering and stable defaults.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/070-cloud-profile-config-no-behavior-change.md`

## Background

Changing cloud runtime cwd fixes the immediate wrong-directory bug, but some config values may still carry local path assumptions. For example:

```json
"allowed_paths": [".", "..", "${env:CONFIG_DIR}"]
```

The meaning of `..` in cloud may be broader or different than intended. Profiles/config should be able to specify cloud-specific overrides without hardcoded plugin-name filtering.

## Expected Behavior

Overrides can adjust settings such as:

```json
{
  "cloud_runtime_overrides": {
    "providers.openai.allowed_paths": [".", "${env:CONFIG_DIR}"],
    "providers.openai.working_directory": "."
  }
}
```

Exact syntax can be refined, but tests should lock down:

- merge/replace semantics
- ordering after mixin/profile resolution
- env placeholder behavior
- unchanged defaults when no overrides are present