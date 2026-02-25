#!/usr/bin/env bash
set -euo pipefail


schema() {
  cat <<'JSON'
{
  "id": "complex_example",
  "version": "0.1.0",
  "args_mode": "json",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "complex_example",
        "description": "Demonstrate args_mode=json with jq parsing.",
        "parameters": {
          "type": "object",
          "properties": {
            "items": {"type": "array", "items": {"type": "string"}},
            "uppercase": {"type": "boolean", "default": false}
          },
          "required": ["items"]
        }
      }
    }
  ]
}
JSON
}


require_args_json_flag() {
  if [[ "${1-}" != "--args-json" ]]; then
    echo "expected --args-json" >&2
    return 2
  fi
}


read_args_json() {
  cat
}


preview() {
  require_args_json_flag "${1-}"
  args_json="$(read_args_json)"
  count="$(jq -r '.items | length' <<<"$args_json")"
  uppercase="$(jq -r '.uppercase // false' <<<"$args_json")"
  echo "complex_example items=$count uppercase=$uppercase"
}


run() {
  require_args_json_flag "${1-}"
  args_json="$(read_args_json)"

  uppercase="$(jq -r '.uppercase // false' <<<"$args_json")"
  if [[ "$uppercase" == "true" ]]; then
    jq -r '.items[] | ascii_upcase' <<<"$args_json"
  else
    jq -r '.items[]' <<<"$args_json"
  fi
}


error() {
  exit_code="${1-1}"
  shift || true

  if [[ "${AGENT_TOOL_TIMED_OUT:-}" == "1" ]]; then
    echo "complex_example timed out after ${AGENT_TOOL_TIMEOUT_SECONDS:-?}s (exit_code=${exit_code})"
    exit 0
  fi

  echo "complex_example failed (exit_code=${exit_code})"
}


sub="${1-}"
shift || true

case "$sub" in
  schema)
    schema ;;
  preview)
    preview "$@" ;;
  run)
    run "$@" ;;
  error)
    error "$@" ;;
  *)
    echo "unknown subcommand: $sub" >&2
    exit 2 ;;
esac
