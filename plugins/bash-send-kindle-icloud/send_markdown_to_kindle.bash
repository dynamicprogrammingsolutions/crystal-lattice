#!/usr/bin/env bash
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MARKDOWN_FILES=()

config_env_name() {
  printf 'AGENT_TOOL_CONFIG_%s\n' "$(printf '%s' "$1" | tr '[:lower:]' '[:upper:]' | tr -c 'A-Z0-9' '_')"
}

config_value() {
  local env_name
  env_name="$(config_env_name "$1")"
  printf '%s' "${!env_name-}"
}

defaulted_config() {
  local key="$1"
  local fallback="${2-}"
  local value
  value="$(config_value "$key")"
  if [[ -n "$value" ]]; then
    printf '%s' "$value"
    return
  fi
  printf '%s' "$fallback"
}

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

load_markdown_files() {
  local args_json="$1"
  local line

  MARKDOWN_FILES=()
  while IFS= read -r line; do
    MARKDOWN_FILES+=("$line")
  done < <(printf '%s' "$args_json" | jq -r '.markdown_files[]?')
}

derive_title_from_markdown() {
  if [[ "$#" -eq 0 ]]; then
    return 0
  fi

  awk '
    function trim(s) {
      sub(/^[[:space:]]+/, "", s)
      sub(/[[:space:]]+$/, "", s)
      return s
    }

    {
      line = $0

      if (line ~ /^[[:space:]]*#+[[:space:]]+/) {
        sub(/^[[:space:]]*#+[[:space:]]+/, "", line)
        sub(/[[:space:]]*#+[[:space:]]*$/, "", line)
        line = trim(line)
        if (line != "") {
          print line
          exit
        }
      }

      if (prev_line != "" && line ~ /^[[:space:]]*=+[[:space:]]*$/) {
        print prev_line
        exit
      }
      if (prev_line != "" && line ~ /^[[:space:]]*-+[[:space:]]*$/) {
        print prev_line
        exit
      }

      trimmed = trim($0)
      if (trimmed != "") {
        prev_line = trimmed
      } else {
        prev_line = ""
      }
    }
  ' "$@"
}

resolve_effective_title() {
  local args_json="$1"
  local title

  title="$(printf '%s' "$args_json" | jq -r '.title // empty')"
  if [[ -n "$title" ]]; then
    printf '%s' "$title"
    return
  fi

  title="$(derive_title_from_markdown "${MARKDOWN_FILES[@]}")"
  if [[ -n "$title" ]]; then
    printf '%s' "$title"
    return
  fi

  printf 'Untitled EPUB'
}

sanitize_filename_stem() {
  local value="$1"

  value="$(printf '%s' "$value" | tr '[:upper:]' '[:lower:]')"
  value="$(printf '%s' "$value" | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')"
  if [[ -z "$value" ]]; then
    value="untitled-epub"
  fi
  printf '%s' "$value"
}

normalize_output_filename() {
  local filename="$1"

  filename="$(basename "$filename")"
  if [[ -z "$filename" || "$filename" == "." ]]; then
    return 1
  fi

  case "$filename" in
    *.epub) ;;
    *) filename="${filename}.epub" ;;
  esac

  printf '%s' "$filename"
}

generated_output_filename() {
  local effective_title="$1"
  local stem timestamp

  stem="$(sanitize_filename_stem "$effective_title")"
  timestamp="$(date '+%Y%m%d-%H%M%S')"
  printf '%s-%s.epub' "$stem" "$timestamp"
}

resolve_output_filename() {
  local args_json="$1"
  local effective_title="$2"
  local output_filename

  output_filename="$(printf '%s' "$args_json" | jq -r '.output_filename // empty')"
  if [[ -n "$output_filename" ]]; then
    normalize_output_filename "$output_filename" && return
  fi

  generated_output_filename "$effective_title"
}

build_preview() {
  local args_json="$1"
  local title count recipient output_filename

  require_command jq
  load_markdown_files "$args_json"

  title="$(resolve_effective_title "$args_json")"
  count="$(printf '%s' "$args_json" | jq -r '(.markdown_files // []) | length')"
  recipient="$(printf '%s' "$args_json" | jq -r '.to // empty')"
  output_filename="$(resolve_output_filename "$args_json" "$title")"
  if [[ -z "$recipient" ]]; then
    recipient="$(defaulted_config send_to_kindle_default_to "<default-recipient>")"
  fi

  printf 'send_markdown_to_kindle title=%s files=%s to=%s output_filename=%s\n' \
    "$title" "$count" "$recipient" "$output_filename"
}

run_tool() {
  local tool_file="$1"
  local payload="$2"

  printf '%s' "$payload" | bash "$tool_file" run --args-json
}

build_payload() {
  local args_json="$1"
  local output_epub="$2"
  local effective_title="$3"

  printf '%s' "$args_json" | jq -c --arg output_epub "$output_epub" --arg title "$effective_title" '
    {
      markdown_files: (.markdown_files // []),
      output_epub: $output_epub,
      title: $title
    }
    + (if .author != null then {author: .author} else {} end)
    + (if .language != null then {language: .language} else {} end)
    + (if .toc_depth != null then {toc_depth: .toc_depth} else {} end)
    + (if .lua_filter != null then {lua_filter: .lua_filter} else {} end)
  '
}

send_payload() {
  local args_json="$1"
  local attachment="$2"
  local effective_title="$3"

  printf '%s' "$args_json" | jq -c --arg attachment "$attachment" --arg title "$effective_title" '
    {
      attachment: $attachment
    }
    + (if .to != null then {to: .to} else {} end)
    + (
        if .subject != null then {subject: .subject}
        elif $title != "" then {subject: $title}
        else {}
        end
      )
    + (if .body != null then {body: .body} else {} end)
  '
}

run_combined() {
  local args_json="$1"
  local tmp_dir tmp_epub build_json send_json cleanup_cmd effective_title output_filename

  require_command jq
  load_markdown_files "$args_json"
  effective_title="$(resolve_effective_title "$args_json")"
  output_filename="$(resolve_output_filename "$args_json" "$effective_title")"

  tmp_dir="$(mktemp -d -t send-markdown-to-kindle.XXXXXX)"
  tmp_epub="${tmp_dir}/${output_filename}"
  cleanup_cmd="$(printf "rm -rf %q" "$tmp_dir")"
  trap "$cleanup_cmd" EXIT

  build_json="$(build_payload "$args_json" "$tmp_epub" "$effective_title")"
  run_tool "${SELF_DIR}/build_epub_from_markdown.bash" "$build_json"

  send_json="$(send_payload "$args_json" "$tmp_epub" "$effective_title")"
  run_tool "${SELF_DIR}/send_to_kindle.bash" "$send_json"
}

schema() {
  cat <<'JSON'
{
  "id": "send_markdown_to_kindle",
  "version": "0.1.0",
  "args_mode": "json",
  "config_keys": [
    "send_to_kindle_smtp_user",
    "send_to_kindle_from_addr",
    "send_to_kindle_default_to",
    "send_to_kindle_keychain_service"
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "send_markdown_to_kindle",
        "description": "Build an EPUB from an ordered list of markdown files and send it through iCloud SMTP without keeping the generated EPUB on disk.",
        "parameters": {
          "type": "object",
          "properties": {
            "markdown_files": {
              "type": "array",
              "items": {"type": "string"},
              "description": "Ordered list of markdown files to include in the EPUB."
            },
            "title": {
              "type": "string",
              "description": "Optional EPUB title. When omitted, the first Markdown heading found across markdown_files is used. Also used as the default email subject when subject is omitted."
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
            },
            "output_filename": {
              "type": "string",
              "description": "Optional attachment filename for the generated EPUB. When omitted, the tool generates one from the effective title by lowercasing it, replacing non-alphanumeric runs with '-', and appending a local timestamp in YYYYMMDD-HHMMSS format plus '.epub'."
            },
            "to": {
              "type": "string",
              "description": "Optional override recipient email address. When omitted, uses the send_to_kindle_default_to config key."
            },
            "subject": {
              "type": "string",
              "description": "Optional email subject. Defaults to title when provided."
            },
            "body": {
              "type": "string",
              "description": "Optional email body."
            }
          },
          "required": ["markdown_files"]
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
  echo "send_markdown_to_kindle"
}

run() {
  if [[ "${1:-}" == "--args-json" ]]; then
    local args_json
    args_json="$(read_args_json)"
    run_combined "$args_json"
    return
  fi
  echo "send_markdown_to_kindle requires --args-json input" >&2
  exit 2
}

error() {
  local exit_code="${1:-1}"
  if [[ "${AGENT_TOOL_TIMED_OUT:-}" == "1" ]]; then
    echo "send_markdown_to_kindle timed out after ${AGENT_TOOL_TIMEOUT_SECONDS:-?}s (exit_code=${exit_code})"
    exit 0
  fi
  echo "send_markdown_to_kindle failed (exit_code=${exit_code})"
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