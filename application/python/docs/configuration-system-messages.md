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

The bundled default config defines a `CRYSTAL_LATTICE_ACCESS` variable at the
end of each maintained vendor template. It uses a variable-level runtime
helper and condition, following the same pattern as optional task guidance:

```json
{
  "system_message": {
    "template": "{{BASE}}\n\n{{CRYSTAL_LATTICE_ACCESS}}",
    "variables": {
      "CRYSTAL_LATTICE_ACCESS": {
        "code": "${env:CRYSTAL_LATTICE_SYSTEM_MESSAGES}/helpers/crystal_lattice_access.py",
        "runtime_code": "${env:CRYSTAL_LATTICE_SYSTEM_MESSAGES}/helpers/crystal_lattice_access.py",
        "condition": {
          "inline_code": "include_crystal_lattice_access()"
        }
      }
    }
  }
}
```

The helper contributes an `include_crystal_lattice_access` checkbox, defaulting
to false. When enabled, it renders only the named runtime-owned CLI, config,
session, interpreter/API, and documentation values. It does not enumerate the
environment or expose credentials.

The CLI invocation includes the active `--config` and `--sessions-dir`, which
is important when the agent is working in another project's directory.

See [Local headless agent runs](headless-agent-runs.md#let-a-configured-agent-delegate-from-another-project)
for the rendered behavior, runtime-layout differences, and existing-config
adoption.