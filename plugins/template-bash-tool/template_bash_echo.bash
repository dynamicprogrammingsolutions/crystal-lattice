#!/usr/bin/env bash
set -euo pipefail

subcommand="${1:-}"
shift || true

case "$subcommand" in
  schema)
    cat <<'JSON'
{
  "id": "template_bash_echo",
  "version": "0.1.0",
  "args_mode": "positional",
  "positional": [
    {"name": "value", "required": true},
    {"name": "uppercase", "default": false}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "template_bash_echo",
        "description": "Echo a value (optionally uppercase it).",
        "parameters": {
          "type": "object",
          "properties": {
            "value": {"type": "string"},
            "uppercase": {"type": "boolean", "default": false}
          },
          "required": ["value", "uppercase"]
        }
      }
    }
  ]
}
JSON
    ;;

  preview)
    value="${1:-}"
    uppercase="${2:-false}"
    echo "template_bash_echo value=$(printf %q "$value") uppercase=$uppercase"
    ;;

  run)
    value="${1:-}"
    uppercase="${2:-false}"

    if [[ "$uppercase" == "true" ]]; then
      printf '%s' "$value" | tr '[:lower:]' '[:upper:]'
    else
      printf '%s' "$value"
    fi
    ;;

  error)
    exit_code="${1:-1}"
    echo "Error: template_bash_echo failed (exit_code=$exit_code)"
    exit 0
    ;;

  *)
    echo "Usage: $0 {schema|preview|run|error}" >&2
    exit 2
    ;;
esac
