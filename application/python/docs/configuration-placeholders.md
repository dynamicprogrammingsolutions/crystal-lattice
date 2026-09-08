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

A missing variable is reported as `env_missing` and resolves to an empty
string. Missing credential variables do not prevent the CLI from starting,
although an API request still needs the real credential required by its
provider or tool.

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
- `BUILTIN_PLUGINS`: built-in plugin bundle directory for the install layout.

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