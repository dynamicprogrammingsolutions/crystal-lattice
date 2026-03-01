#!/usr/bin/env bash
set -euo pipefail


schema() {
  cat <<'JSON'
{
  "id": "read_line_range",
  "version": "0.1.0",
  "args_mode": "positional",
  "positional": [
    {"name": "path", "required": true},
    {"name": "start_line", "required": true},
    {"name": "end_line", "required": true},
    {"name": "show_line_numbers", "required": false, "default": false}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "read_line_range",
        "description": "Read lines [start_line, end_line] from a file.",
        "parameters": {
          "type": "object",
          "properties": {
            "path": {"type": "string"},
            "start_line": {"type": "integer"},
            "end_line": {"type": "integer"},
            "show_line_numbers": {"type": "boolean", "default": false}
          },
          "required": ["path", "start_line", "end_line"]
        }
      }
    }
  ]
}
JSON
}


preview() {
  path="${1-}"
  start_line="${2-}"
  end_line="${3-}"
  show_line_numbers="${4-false}"
  echo "read_line_range path=$path start_line=$start_line end_line=$end_line show_line_numbers=$show_line_numbers"
}


run() {
  path="${1-}"
  start_line="${2-}"
  end_line="${3-}"
  show_line_numbers="${4-false}"

  [[ -n "$path" ]] || { echo "path is required" >&2; exit 2; }
  [[ -f "$path" ]] || { echo "file not found: $path" >&2; exit 2; }
  [[ "$start_line" =~ ^[0-9]+$ ]] || { echo "start_line must be an int" >&2; exit 2; }
  [[ "$end_line" =~ ^[0-9]+$ ]] || { echo "end_line must be an int" >&2; exit 2; }

  if [[ "$show_line_numbers" == "true" ]]; then
    nl -ba "$path" | sed -n "${start_line},${end_line}p"
  else
    sed -n "${start_line},${end_line}p" "$path"
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
