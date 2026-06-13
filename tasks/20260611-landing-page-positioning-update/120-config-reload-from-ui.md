# Reload Config From UI

Add a user-facing way to reload Crystal Lattice configuration after changing
plugins, agents, or settings, without restarting the whole app flow.

## Requirements checklist

- [ ] Decide whether config reload is a global application action, terminal slash command, desktop/mobile action, or a combination.
- [ ] Reload plugin configuration safely and report validation errors clearly.
- [ ] Preserve active sessions where possible and document any limits.
- [ ] Add UI feedback for successful reload and failed reload.
- [ ] Add tests for config reload behavior and error reporting.

Parent Task: `tasks/20260611-landing-page-positioning-update/000-main.md`

## Context

The landing page emphasizes replacing plugins through config. That workflow is
much easier to believe if users can reload config from the UI after adding or
changing a plugin, instead of restarting and reconnecting manually.