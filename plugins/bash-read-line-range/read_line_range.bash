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
        "description": "Read lines [start_line, end_line] from a file. Optionally prefix lines with line numbers.",
        "parameters": {
          "type": "object",
          "properties": {
            "path": {"type": "string", "description": "Path to the file to read."},
            "start_line": {"type": "integer", "description": "1-based start line (inclusive)."},
            "end_line": {"type": "integer", "description": "1-based end line (inclusive)."},
            "show_line_numbers": {"type": "boolean", "default": false, "description": "When true, prefix each line with its line number."}
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
  [[ "$start_line" -le "$end_line" ]] || { echo "start_line must be <= end_line" >&2; exit 2; }

  if [[ "$show_line_numbers" == "true" ]]; then
    nl -ba "$path" | sed -n "${start_line},${end_line}p"
  else
    sed -n "${start_line},${end_line}p" "$path"
  fi
}


error() {
  exit_code="${1-1}"
  shift || true

  if [[ "${AGENT_TOOL_TIMED_OUT:-}" == "1" ]]; then
    echo "read_line_range timed out after ${AGENT_TOOL_TIMEOUT_SECONDS:-?}s (exit_code=${exit_code})"
    exit 0
  fi

  echo "read_line_range failed (exit_code=${exit_code})"
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
