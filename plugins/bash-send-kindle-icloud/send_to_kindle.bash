#!/usr/bin/env bash
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELPER="${SELF_DIR}/send_icloud_email.py"

resolve_python() {
  if [[ -n "${SEND_TO_KINDLE_PYTHON:-}" ]] && [[ -x "${SEND_TO_KINDLE_PYTHON}" ]]; then
    printf '%s\n' "${SEND_TO_KINDLE_PYTHON}"
    return
  fi
  if [[ -n "${AGENT_TOOL_PYTHON:-}" ]] && [[ -x "${AGENT_TOOL_PYTHON}" ]]; then
    printf '%s\n' "${AGENT_TOOL_PYTHON}"
    return
  fi
  if [[ -n "${PYTHON:-}" ]] && [[ -x "${PYTHON}" ]]; then
    printf '%s\n' "${PYTHON}"
    return
  fi
  if [[ -n "${VIRTUAL_ENV:-}" ]] && [[ -x "${VIRTUAL_ENV}/bin/python3" ]]; then
    printf '%s\n' "${VIRTUAL_ENV}/bin/python3"
    return
  fi
  command -v python3
}

PYTHON_BIN="$(resolve_python)"

config_env_name() {
  printf 'AGENT_TOOL_CONFIG_%s\n' "$(printf '%s' "$1" | tr '[:lower:]' '[:upper:]' | tr -c 'A-Z0-9' '_')"
}

config_value() {
  local env_name
  env_name="$(config_env_name "$1")"
  printf '%s' "${!env_name-}"
}

required_config() {
  local key="$1"
  local value
  value="$(config_value "$key")"
  if [[ -z "$value" ]]; then
    echo "missing agent config key: $key" >&2
    exit 1
  fi
  printf '%s' "$value"
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

resolve_attachment() {
  local attachment="$1"
  if [[ -z "$attachment" ]]; then
    echo "attachment is required" >&2
    exit 1
  fi
  if [[ "$attachment" == ~* ]]; then
    attachment="${HOME}${attachment#"~"}"
  fi
  if [[ ! -f "$attachment" ]]; then
    echo "attachment not found: $attachment" >&2
    exit 1
  fi
  printf '%s' "$attachment"
}

json_field() {
  local field="$1"
  printf '%s' "${ARGS_JSON}" | "$PYTHON_BIN" -c '
import json, sys
field = sys.argv[1]
raw = sys.stdin.read()
obj = {} if not raw.strip() else json.loads(raw)
if not isinstance(obj, dict):
    raise SystemExit("arguments must be a JSON object")
value = obj.get(field, "")
if value is None:
    value = ""
if not isinstance(value, str):
    raise SystemExit(f"{field} must be a string")
sys.stdout.write(value)
' "$field"
}

load_args_json() {
  ARGS_JSON="$(cat)"
  ATTACHMENT="$(resolve_attachment "$(json_field attachment)")"
  SUBJECT="$(json_field subject)"
  BODY="$(json_field body)"
  TO_OVERRIDE="$(json_field to)"
}

schema() {
  cat <<'JSON'
{
  "id": "send_to_kindle",
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
        "name": "send_to_kindle",
        "description": "Send a local file, typically an EPUB, through iCloud SMTP. Defaults such as destination address and Keychain service are resolved from agent config keys.",
        "parameters": {
          "type": "object",
          "properties": {
            "attachment": {
              "type": "string",
              "description": "Path to the local file to send."
            },
            "subject": {
              "type": "string",
              "description": "Optional email subject. Defaults to the EPUB filename."
            },
            "body": {
              "type": "string",
              "description": "Optional email body."
            },
            "to": {
              "type": "string",
              "description": "Optional override recipient email address. When omitted, uses the send_to_kindle_default_to config key."
            }
          },
          "required": ["attachment"]
        }
      }
    }
  ]
}
JSON
}


preview() {
  if [[ "${1:-}" == "--args-json" ]]; then
    load_args_json
    local recipient subject
    recipient="${TO_OVERRIDE:-$(defaulted_config send_to_kindle_default_to "")}"
    if [[ -z "$recipient" ]]; then
      recipient="<missing-default-to>"
    fi
    subject="${SUBJECT:-$(basename "$ATTACHMENT")}"
    printf "send_to_kindle attachment=%s to=%s subject=%s\n" "$ATTACHMENT" "$recipient" "$subject"
    return
  fi
  echo "send_to_kindle"
}


run() {
  if [[ "${1:-}" == "--args-json" ]]; then
    load_args_json

    local smtp_user from_addr recipient subject body keychain_service password
    smtp_user="$(required_config send_to_kindle_smtp_user)"
    from_addr="$(defaulted_config send_to_kindle_from_addr "$smtp_user")"
    recipient="${TO_OVERRIDE:-$(defaulted_config send_to_kindle_default_to "")}"
    if [[ -z "$recipient" ]]; then
      echo "missing recipient email; provide 'to' or set send_to_kindle_default_to" >&2
      exit 1
    fi
    subject="${SUBJECT:-$(basename "$ATTACHMENT")}"
    body="${BODY:-}"
    keychain_service="$(defaulted_config send_to_kindle_keychain_service "kindle-smtp")"

    if [[ "${SEND_TO_KINDLE_DRY_RUN:-}" == "1" ]]; then
      printf "dry_run=true attachment=%s to=%s from=%s smtp_user=%s keychain_service=%s\n" \
        "$ATTACHMENT" "$recipient" "$from_addr" "$smtp_user" "$keychain_service"
      return
    fi

    password="$(security find-generic-password -s "$keychain_service" -a "$smtp_user" -w)"
    printf '%s' "$password" | \
      "${PYTHON_BIN}" "${HELPER}" \
        --smtp-host "smtp.mail.me.com" \
        --smtp-port 587 \
        --smtp-user "$smtp_user" \
        --from "$from_addr" \
        --to "$recipient" \
        --subject "$subject" \
        --body "$body" \
        --attachment "$ATTACHMENT" \
        --password-stdin
    printf "sent attachment=%s to=%s subject=%s\n" "$ATTACHMENT" "$recipient" "$subject"
    return
  fi
  echo "send_to_kindle requires --args-json input" >&2
  exit 2
}


error() {
  exit_code="${1:-1}"
  if [[ "${AGENT_TOOL_TIMED_OUT:-}" == "1" ]]; then
    echo "send_to_kindle timed out after ${AGENT_TOOL_TIMEOUT_SECONDS:-?}s (exit_code=${exit_code})"
    exit 0
  fi
  echo "send_to_kindle failed (exit_code=${exit_code})"
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