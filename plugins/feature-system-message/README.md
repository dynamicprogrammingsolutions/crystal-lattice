# feature-system-message

Feature plugin providing configurable system-message templating for request-time prompt composition.

## Overview

This plugin lets application config define a default system-message template plus named variables.
The template is rendered for each request without mutating the stored core session history.

Supported variable sources:

- string: direct replacement text
- `{"text": "..."}`: explicit inline text
- `{"files": ["path1.md", "path2.md"]}`: concatenated file contents
- `{"code": "path/to/helper.py"}`: execute a Python helper file
- `{"inline_code": "...python..."}`: evaluate or execute inline Python

Any object-form variable may also include:

- `{"condition": {"code": "path/to/check.py"}}`
- `{"condition": {"inline_code": "is_git_repo()"}}`

When a condition is falsey, the variable resolves to an empty string and the main value is not read or executed.

Optionally, the `system_message` object may also include:

- `"runtime_code": "path/to/runtime.py"`

That file is executed once per request, and all exported non-underscore globals from it become the runtime namespace for `inline_code`, file-backed `code`, and their condition variants.

## Example

```json
{
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/feature-system-message"
  ],
  "agents": {
    "gemini": {
      "provider": "openrouter_gemini_tools",
      "system_message": {
        "template": "${file:${env:CONFIG_DIR}/system_messages/gemini/template.md}",
        "runtime_code": "${env:CONFIG_DIR}/system_messages/helpers/runtime.py",
        "variables": {
          "PREAMBLE": {
            "files": [
              "${env:CONFIG_DIR}/system_messages/gemini/preamble.md"
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

## `inline_code`

`inline_code` supports two lightweight forms:

- Single expression: the result is used directly.
- Block execution: the plugin executes the code and reads `VALUE` from the resulting namespace.

Examples:

```json
{
  "WORKING_DIRECTORY_LINE": {
    "inline_code": "f'Current working directory: {cwd}'"
  }
}
```

```json
{
  "GIT_SECTION": {
    "inline_code": "if is_git_repo():\n    VALUE = '# Git Repository\\n\\n- Review changes with git status before committing.'\nelse:\n    VALUE = ''"
  }
}
```

If an inline block does not set `VALUE`, the rendered value becomes an empty string.

`inline_code` only sees builtins by default. If you want convenience names such as `cwd` or `is_git_repo()`, define them in `runtime_code`.

## File-Backed `code`

The existing `code` behavior is preserved.

The plugin executes the referenced Python file with `runpy.run_path(...)` and then looks for:

- `SYSTEM_MESSAGE_VALUE`
- or a callable `get_value()`

If neither produces a value, the rendered result becomes an empty string.

Example helper file:

```python
import os
from pathlib import Path


def get_value() -> str:
    agents = Path(os.getcwd()) / "AGENTS.md"
    if not agents.is_file():
        return ""
    return "# Contextual Instructions\n\n" + agents.read_text(encoding="utf-8")
```

## `runtime_code`

Use `runtime_code` when you want a reusable, config-defined namespace for dynamic sections.

Example runtime file:

```python
import subprocess
from pathlib import Path


cwd = str(Path.cwd().resolve())


def git_root(path: str | None = None) -> str | None:
    target = Path(path or cwd)
    proc = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def is_git_repo(path: str | None = None) -> bool:
    return git_root(path) is not None
```

All exported non-underscore globals become available to dynamic code.

That means `inline_code` or `condition.inline_code` can use names such as:

- `cwd`: current working directory as an absolute string
- `is_git_repo(path: str | None = None) -> bool`
- `git_root(path: str | None = None) -> str | None`

but those names now come from your config-defined runtime file rather than from the feature plugin itself.

## Recommended Pattern

- Keep large static instruction text in markdown files.
- Use `files` or `${file:...}` to load those files into the template.
- Put reusable imports, helpers, and convenience values in `runtime_code`.
- Use `condition` for whole-section inclusion.
- Use `inline_code` for short dynamic strings.
- Use `code` for moderately complex dynamic sections such as optional local-instructions blocks.

See [application/python/agent_terminal_app/config_v2_multi_family_tools_simplified.json](application/python/agent_terminal_app/config_v2_multi_family_tools_simplified.json) for a multi-vendor example that follows this pattern.