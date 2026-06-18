# Grok Agent Notes

These notes are for further research or future automation work, not for direct copy-paste into final system instructions.

## Key upstream files

- `grok-cli/src/agent/grok-agent.ts`
- `grok-cli/src/grok/tools.ts`

## What upstream actually does

1. Constructs one compact system message inside the Grok agent constructor.
2. Injects a custom-instructions block before the main default guidance when custom instructions exist.
3. Hardcodes the visible tool list and conditionally mentions `edit_file` when Morph support is configured.
4. Appends a current-working-directory line using `process.cwd()`.

## Important fidelity gaps

1. The real-time web and X claim should not be copied unless the host truly has that capability.
2. Confirmation wording is host-specific.
3. The tool inventory must be regenerated from the actual configured Grok-compatible surface.

## Good source anchors for later work

- custom instruction injection near the constructor setup
- tool inventory block in the default system message string
- current working directory interpolation
- `GROK_TOOLS` and related schema definitions in `grok-cli/src/grok/tools.ts`