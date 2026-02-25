#!/usr/bin/env bash
set -euo pipefail


schema() {
  cat <<'JSON'
{
  "id": "json_example",
  "version": "0.1.0",
  "args_mode": "json",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "json_example",
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


preview() {
  require_args_json_flag "${1-}"
  args_json="$(cat)"
  count="$(jq -r '.items | length' <<<"$args_json")"
  uppercase="$(jq -r '.uppercase // false' <<<"$args_json")"
  echo "json_example items=$count uppercase=$uppercase"
}


run() {
  require_args_json_flag "${1-}"
  args_json="$(cat)"
  uppercase="$(jq -r '.uppercase // false' <<<"$args_json")"
  if [[ "$uppercase" == "true" ]]; then
    jq -r '.items[] | ascii_upcase' <<<"$args_json"
  else
    jq -r '.items[]' <<<"$args_json"
  fi
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
  *)
    echo "unknown subcommand: $sub" >&2
    exit 2 ;;
esac
