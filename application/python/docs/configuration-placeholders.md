# Configuration placeholders

Configuration strings can load environment variables and files before mixins
and variants are resolved.

## Environment variables

`${env:NAME}` is supported anywhere inside a string:

```json
{
  "api_key": "${env:OPENROUTER_API_KEY}",
  "plugin_cache_dir": "${env:CONFIG_DIR}/.plugin_cache/plugins"
}
```

A missing variable is reported as an `env_missing` warning with its variable
name and config path, then resolves to an empty string. The warning is not
itself fatal, but the empty result may cause an independent validation failure
when the field is structurally required, such as in a plugin path. Optional
credential placeholders in the generated default config do not prevent the
CLI from starting; API-backed functionality still needs the credentials
defined by its provider or tool.

Embedding applications can provide:

- `env_overrides`: values that override process environment values and are
  also installed into the runtime environment overlay;
- `config_env`: config-resolution-only values that are available to
  placeholders but are not installed into the process environment.

## `.env` files

Users do not need to export provider keys in their shell for normal CLI use.
The command collects `.env` values for config resolution in this order:

1. `.env` beside the active config file.
2. `./.crystal/.env` in the working directory.
3. `~/.crystal/.env`.
4. The standard `.env` discovered from the working directory or a parent.

Existing process environment values take precedence. Among `.env` files, the
first discovered value for a key wins. The loaded values are passed to config
placeholder resolution and are not copied into `os.environ`.

For `crystal-lattice --config-local`, place provider keys beside the generated
config:

```bash
# .crystal/.env
OPENAI_API_KEY=...
OPENROUTER_API_KEY=...
ANTHROPIC_API_KEY=...
```

Configuring a key enables requests that use the corresponding credentialed
API. It is not a prerequisite for starting the CLI or using unrelated local
functionality.

## Built-in path variables

The application supplies:

- `CONFIG_DIR`: absolute directory containing the active config file;
- `WORKING_DIR`: absolute current working directory;
- `BUILTIN_PLUGINS`: built-in plugin bundle directory for the install layout;
- `CRYSTAL_DATA_DIR`: user-level Crystal data directory, defaulting to
  `~/.crystal`. This is the home for user-owned data such as usage journals
  and cost tracking stores. It defaults to the same directory as `CONFIG_DIR`
  on a normal install, but it follows the user rather than the active config
  file location, so data does not move when a different config file (or a
  copied config asset tree, as in the cloud runtime) is active.
- `CRYSTAL_LATTICE_SYSTEM_MESSAGES`: runtime-owned system-message resources.
- `CRYSTAL_LATTICE_CLI_ARGV_JSON`: authoritative CLI argument vector for the
  active config and session root.
- `CRYSTAL_LATTICE_CLI_COMMAND`: platform-shell-rendered form of the
  authoritative CLI invocation.
- `CRYSTAL_LATTICE_CONFIG`: absolute active config path.
- `CRYSTAL_LATTICE_SESSIONS`: absolute active session root.
- `CRYSTAL_LATTICE_PYTHON`: general runtime Python interpreter when available.
- `CRYSTAL_LATTICE_PYTHON_API_MODULE`: supported Python import module when
  available.
- `CRYSTAL_LATTICE_DOCS`: local application docs when packaged.
- `CRYSTAL_LATTICE_DOCS_URL`: stable public application docs URL.

Example:

```json
{
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/openrouter",
    "path:${env:BUILTIN_PLUGINS}/feature-system-message"
  ],
  "agents": {
    "default": {
      "working_directory": "${env:WORKING_DIR}"
    }
  }
}
```

## File placeholders

`${file:...}` loads a complete UTF-8 text file. It must occupy the complete
string value:

```json
{
  "system_message": {
    "template": "${file:${env:CONFIG_DIR}/system-message.md}"
  }
}
```

A missing file is reported as `file_missing` and resolves to an empty string.

## Literal values

Wrap a value in `$raw` to bypass placeholder expansion:

```json
{
  "example": {
    "$raw": "literal ${env:NAME} text"
  }
}
```

The resulting value is:

```text
literal ${env:NAME} text
```

`$raw` is the placeholder-resolution escape. Other configuration controls,
including `$variants` and `$merge`, are documented separately.

## Portable example

```json
{
  "plugin_cache_dir": "${env:CONFIG_DIR}/.plugin_cache/plugins",
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/feature-system-message"
  ],
  "agents": {
    "default": {
      "system_message": {
        "template": "{{AGENTS}}",
        "variables": {
          "AGENTS": {
            "text": "${file:${env:WORKING_DIR}/AGENTS.md}"
          }
        }
      }
    }
  }
}
```
