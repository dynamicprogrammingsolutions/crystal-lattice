#!/usr/bin/env bash
set -euo pipefail


parse_flags() {
  path=""
  start=""
  end=""
  number="true"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --path)
        path="${2-}"; shift 2 ;;
      --start)
        start="${2-}"; shift 2 ;;
      --end)
        end="${2-}"; shift 2 ;;

      --number)
        number="true"; shift ;;
      --no-number)
        number="false"; shift ;;

      --path=*)
        path="${1#*=}"; shift ;;
      --start=*)
        start="${1#*=}"; shift ;;
      --end=*)
        end="${1#*=}"; shift ;;

      --)
        shift; break ;;
      *)
        echo "unknown arg: $1" >&2
        return 2 ;;
    esac
  done
}


validate_flags() {
  [[ -n "$path" ]] || { echo "--path is required" >&2; return 2; }
  [[ -n "$start" && "$start" =~ ^[0-9]+$ ]] || { echo "--start must be int" >&2; return 2; }
  [[ -n "$end" && "$end" =~ ^[0-9]+$ ]] || { echo "--end must be int" >&2; return 2; }
  if [[ ! -f "$path" ]]; then
    echo "file not found: $path" >&2
    return 2
  fi
}


schema() {
  cat <<'JSON'
{
  "id": "sed_lines",
  "version": "0.1.0",
  "args_mode": "flags",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "sed_lines",
        "description": "Print [start,end] lines from a file (optionally numbered).",
        "parameters": {
          "type": "object",
          "properties": {
            "path": {"type": "string"},
            "start": {"type": "integer"},
            "end": {"type": "integer"},
            "number": {"type": "boolean", "default": true}
          },
          "required": ["path", "start", "end"]
        }
      }
    }
  ]
}
JSON
}


preview() {
  parse_flags "$@" || true
  echo "sed_lines path=$path start=$start end=$end number=$number"
}


run() {
  parse_flags "$@"
  validate_flags

  if [[ "$number" == "true" ]]; then
    awk -v start="$start" -v end="$end" 'NR>=start && NR<=end { printf "%d:%s\n", NR, $0 }' "$path"
  else
    awk -v start="$start" -v end="$end" 'NR>=start && NR<=end { print }' "$path"
  fi
}


error() {
  exit_code="${1-1}"
  shift || true
  parse_flags "$@" || true

  if [[ "${AGENT_TOOL_TIMED_OUT:-}" == "1" ]]; then
    echo "sed_lines timed out after ${AGENT_TOOL_TIMEOUT_SECONDS:-?}s (exit_code=${exit_code})"
    exit 0
  fi

  echo "sed_lines failed (exit_code=${exit_code}) path=$path start=$start end=$end"
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
