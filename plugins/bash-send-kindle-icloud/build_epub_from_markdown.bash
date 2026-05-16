#!/usr/bin/env bash
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_LUA_FILTER="${SELF_DIR}/strip_local_file_references.lua"

require_command() {
  local name="$1"
  command -v "$name" >/dev/null 2>&1 || {
    echo "${name} is required but not found in PATH" >&2
    exit 2
  }
}

read_args_json() {
  cat
}

build_preview() {
  local args_json="$1"
  local title output_epub count

  require_command jq

  title="$(printf '%s' "$args_json" | jq -r '.title // "Untitled EPUB"')"
  output_epub="$(printf '%s' "$args_json" | jq -r '.output_epub // "<missing-output>"')"
  count="$(printf '%s' "$args_json" | jq -r '(.markdown_files // []) | length')"

  printf 'build_epub_from_markdown title=%s files=%s output=%s\n' \
    "$title" "$count" "$output_epub"
}

build_epub() {
  local args_json="$1"
  local output_epub title author language toc_depth lua_filter
  local -a markdown_files pandoc_args

  require_command jq
  require_command pandoc

  output_epub="$(printf '%s' "$args_json" | jq -r '.output_epub // empty')"
  title="$(printf '%s' "$args_json" | jq -r '.title // "Untitled EPUB"')"
  author="$(printf '%s' "$args_json" | jq -r '.author // empty')"
  language="$(printf '%s' "$args_json" | jq -r '.language // "en-US"')"
  toc_depth="$(printf '%s' "$args_json" | jq -r '.toc_depth // 2')"
  lua_filter="$(printf '%s' "$args_json" | jq -r '.lua_filter // empty')"

  if [[ -z "$output_epub" ]]; then
    echo "output_epub is required" >&2
    exit 2
  fi

  markdown_files=()
  while IFS= read -r line; do
    markdown_files+=("$line")
  done < <(printf '%s' "$args_json" | jq -r '.markdown_files[]?')

  if [[ "${#markdown_files[@]}" -eq 0 ]]; then
    echo "markdown_files must contain at least one file" >&2
    exit 2
  fi

  for f in "${markdown_files[@]}"; do
    if [[ ! -f "$f" ]]; then
      echo "markdown file not found: $f" >&2
      exit 2
    fi
  done

  if [[ -z "$lua_filter" ]]; then
    lua_filter="$DEFAULT_LUA_FILTER"
  fi
  if [[ ! -f "$lua_filter" ]]; then
    echo "lua_filter not found: $lua_filter" >&2
    exit 2
  fi

  mkdir -p "$(dirname "$output_epub")"

  metadata_file="$(mktemp -t build-epub-metadata.XXXXXX.yaml)"
  trap 'rm -f "$metadata_file"' EXIT

  if [[ -n "$author" ]]; then
    cat >"$metadata_file" <<EOF
---
title: "${title}"
author:
  - "${author}"
language: "${language}"
toc: true
toc-depth: ${toc_depth}
---
EOF
  else
    cat >"$metadata_file" <<EOF
---
title: "${title}"
language: "${language}"
toc: true
toc-depth: ${toc_depth}
---
EOF
  fi

  pandoc_args=(
    "$metadata_file"
    "${markdown_files[@]}"
    --lua-filter="$lua_filter"
    --toc
    --toc-depth="$toc_depth"
    -o "$output_epub"
  )

  pandoc "${pandoc_args[@]}"

  printf 'built_epub=%s files=%s title=%s\n' \
    "$output_epub" "${#markdown_files[@]}" "$title"
}

schema() {
  cat <<'JSON'
{
  "id": "build_epub_from_markdown",
  "version": "0.1.0",
  "args_mode": "json",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "build_epub_from_markdown",
        "description": "Build an EPUB file from an ordered list of markdown files using pandoc. Local file links are converted to plain text by default to keep EPUB output reader-friendly.",
        "parameters": {
          "type": "object",
          "properties": {
            "markdown_files": {
              "type": "array",
              "items": {"type": "string"},
              "description": "Ordered list of markdown files to include in the EPUB."
            },
            "output_epub": {
              "type": "string",
              "description": "Output path for the generated EPUB file."
            },
            "title": {
              "type": "string",
              "description": "Optional EPUB title. Defaults to 'Untitled EPUB'."
            },
            "author": {
              "type": "string",
              "description": "Optional EPUB author."
            },
            "language": {
              "type": "string",
              "description": "Optional EPUB language. Defaults to 'en-US'."
            },
            "toc_depth": {
              "type": "integer",
              "description": "Optional table-of-contents depth. Defaults to 2."
            },
            "lua_filter": {
              "type": "string",
              "description": "Optional pandoc Lua filter path. Defaults to the plugin's built-in local-link stripping filter."
            }
          },
          "required": ["markdown_files", "output_epub"]
        }
      }
    }
  ]
}
JSON
}

preview() {
  if [[ "${1:-}" == "--args-json" ]]; then
    local args_json
    args_json="$(read_args_json)"
    build_preview "$args_json"
    return
  fi
  echo "build_epub_from_markdown"
}

run() {
  if [[ "${1:-}" == "--args-json" ]]; then
    local args_json
    args_json="$(read_args_json)"
    build_epub "$args_json"
    return
  fi
  echo "build_epub_from_markdown requires --args-json input" >&2
  exit 2
}

error() {
  local exit_code="${1:-1}"
  if [[ "${AGENT_TOOL_TIMED_OUT:-}" == "1" ]]; then
    echo "build_epub_from_markdown timed out after ${AGENT_TOOL_TIMEOUT_SECONDS:-?}s (exit_code=${exit_code})"
    exit 0
  fi
  echo "build_epub_from_markdown failed (exit_code=${exit_code})"
}

sub="${1:-}"
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