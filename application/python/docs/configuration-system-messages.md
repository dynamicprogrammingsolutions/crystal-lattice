# System-message configuration

Multi-vendor configurations can keep large system messages readable by
combining Markdown files with `feature-system-message`.

## Recommended pattern

- Put large static sections in Markdown files.
- Load the template with `${file:...}`.
- Define reusable runtime helpers with `system_message.runtime_code`.
- Load static sections with `files`.
- Use `condition` for optional sections.
- Use `inline_code` for short runtime values.
- Use file-backed `code` helpers for moderately complex dynamic sections.

```json
{
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/openrouter",
    "path:${env:BUILTIN_PLUGINS}/feature-system-message"
  ],
  "agents": {
    "default": {
      "provider": "openrouter_gemini_tools",
      "system_message": {
        "template": "{{BASE}}\n\n{{GIT_SECTION}}\n\n{{WORKING_DIRECTORY_LINE}}",
        "runtime_code": "${env:CONFIG_DIR}/system_messages/helpers/runtime.py",
        "variables": {
          "BASE": {
            "files": [
              "${env:CONFIG_DIR}/system_messages/gemini/preamble.md",
              "${env:CONFIG_DIR}/system_messages/gemini/core-mandates.md"
            ]
          },
          "GIT_SECTION": {
            "files": [
              "${env:CONFIG_DIR}/system_messages/gemini/git-section.md"
            ],
            "condition": {
              "inline_code": "is_git_repo()"
            }
          },
          "WORKING_DIRECTORY_LINE": {
            "inline_code": "f'Current working directory: {cwd}'"
          }
        }
      }
    }
  }
}
```

## Inline and file-backed code

`inline_code` supports:

- expression form: the expression result is rendered;
- block form: the block sets `VALUE`.

`runtime_code` executes once per request and exports non-underscore globals to
the namespace used by `inline_code`, file-backed `code`, and their conditions.

The namespace always includes:

- `CONFIG`: effective resolved request config.

During UI-schema queries it also includes:

- `TAGS`;
- `MODELS`.

If runtime code exports a zero-argument `get_ui_elements()` function, the
feature merges its returned items into the normal UI schema.

Typical runtime exports include:

- `cwd`;
- `is_git_repo()`;
- `git_root()`;
- `Path`;
- `os`.

Without `runtime_code`, snippets see Python builtins unless they import what
they need.

Configuration-owned runtime helpers can inspect `CONFIG`, including values
selected by mixins and variants.

## Complete examples

- [Bundled default configuration](../agent_terminal_app/default_config/config.json)
- [feature-system-message](../../../plugins/feature-system-message/README.md)

## Optional Crystal Lattice access guidance

The bundled default config defines one shared `crystal_lattice_access` mixin.
Maintained vendor templates end with:

```text
{{CRYSTAL_LATTICE_ACCESS}}

{{CRYSTAL_LATTICE_CLI_ACCESS}}
```

The mixin contains both complete access values and a separate parent-only
`CRYSTAL_LATTICE_DELEGATION_GUIDANCE` value under `text`, followed by small
named variables that read only the corresponding runtime access values. The
full section uses `include_crystal_lattice_access()`; the CLI-only section uses
`include_crystal_lattice_cli_access()`. Those access conditions are mutually
exclusive. The delegation section accompanies either valid mode.

The helper contributes the `include_crystal_lattice_access` checkbox,
defaulting to false, and validates availability. It contains no command, SDK,
history, documentation, or delegation instruction prose.

When full values are available, the UI and compiled message identify CLI and
Python SDK access. When only CLI values are available, the UI explicitly says
**CLI only** and only that section compiles. When CLI values are unavailable,
the element remains visible with `disabled: true` and a description naming
the problem.

The CLI invocation includes the active `--config` and `--sessions-dir`, which
is important when the agent is working in another project's directory.

The parent-only section distinguishes three things explicitly: instructions
given to the parent, the selected child's normal configured system/developer
message, and the self-contained child user prompt constructed by the parent.

See [Local headless agent runs](headless-agent-runs.md#let-a-configured-agent-delegate-from-another-project)
for the rendered behavior, runtime-layout differences, and existing-config
adoption.