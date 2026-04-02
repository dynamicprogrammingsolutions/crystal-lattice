# Kimi Agent Notes

These notes are for further research or future automation work, not for direct copy-paste into final system instructions.

## Key upstream files

- `../kimi-cli/src/kimi_cli/agents/default/system.md`
- `../kimi-cli/src/kimi_cli/agents/default/agent.yaml`
- `../kimi-cli/src/kimi_cli/soul/agent.py`
- `../kimi-cli/src/kimi_cli/soul/kimisoul.py`
- `../kimi-cli/src/kimi_cli/soul/dynamic_injections/plan_mode.py`
- `../kimi-cli/src/kimi_cli/skill/__init__.py`

## What upstream actually does

1. Loads a Jinja2 system prompt template from `agents/default/system.md` with `StrictUndefined`.
2. Supplies built-in variables for current datetime, working directory, working-directory listing, root `AGENTS.md`, discovered skills, and additional workspace directories.
3. Appends dynamic injections after the base prompt, most notably plan-mode reminders.
4. Treats skills as a layered discovery system spanning built-in, user, and project directories.

## Important fidelity gaps

1. This platform does not currently model Kimi's dynamic plan-mode reminders.
2. There is no equivalent skills system to populate `KIMI_SKILLS` at runtime.
3. Additional workspace directory rendering is not part of the current system-message helpers.
4. Kimi's approval, rejection, checkpoint, and revert flows are host-specific and should not be copied literally.

## Good source anchors for later work

- `BuiltinSystemPromptArgs` in `soul/agent.py`
- `_load_system_prompt(...)` in `soul/agent.py`
- plan-mode injection text builders in `soul/dynamic_injections/plan_mode.py`
- skill discovery and formatting in `skill/__init__.py`