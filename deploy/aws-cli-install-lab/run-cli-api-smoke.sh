#!/usr/bin/env bash

set -euo pipefail

VERSION="${VERSION:-0.1.0}"
BASE_URL="${BASE_URL:-https://download.crystallattice.dev/crystal-lattice-cli}"
PORT="${PORT:-19000}"
COMMAND_NAME="${COMMAND_NAME:-crystal-lattice}"

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$SCRIPT_DIR"

ROOT="$PWD"
INSTALL_ROOT="${INSTALL_ROOT:-$ROOT/.install/opt/crystal-lattice-cli}"
BIN_DIR="${BIN_DIR:-$ROOT/.install/bin}"
LOG_DIR="${LOG_DIR:-$ROOT/logs}"

mkdir -p "$INSTALL_ROOT" "$BIN_DIR" "$LOG_DIR"

if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$ROOT/.env"
  set +a
fi

if [ -z "${OPENROUTER_API_KEY:-}" ] && [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "Set OPENROUTER_API_KEY or OPENAI_API_KEY in .env or the environment." >&2
  exit 1
fi

if [ -n "${AGENT_ID:-}" ]; then
  selected_agent="$AGENT_ID"
elif [ -n "${OPENROUTER_API_KEY:-}" ]; then
  selected_agent="codex-openrouter"
else
  selected_agent="codex-openai"
fi

json_extract_session_id() {
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import json,sys; print(json.load(sys.stdin)["session"]["session_id"])'
  elif command -v python >/dev/null 2>&1; then
    python -c 'import json,sys; print(json.load(sys.stdin)["session"]["session_id"])'
  elif command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -Command '$json = [Console]::In.ReadToEnd() | ConvertFrom-Json; $json.session.session_id'
  else
    echo "Need python3, python, or powershell.exe to parse JSON responses." >&2
    return 1
  fi
}

json_extract_active_request_id() {
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import json,sys; v=json.load(sys.stdin).get("active_request_id"); print(v or "")'
  elif command -v python >/dev/null 2>&1; then
    python -c 'import json,sys; v=json.load(sys.stdin).get("active_request_id"); print(v or "")'
  elif command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -Command '$json = [Console]::In.ReadToEnd() | ConvertFrom-Json; if ($json.active_request_id) { $json.active_request_id }'
  else
    echo "Need python3, python, or powershell.exe to parse JSON responses." >&2
    return 1
  fi
}

is_windows_bash() {
  case "$(uname -s 2>/dev/null || true)" in
    MINGW*|MSYS*|CYGWIN*) return 0 ;;
    *) return 1 ;;
  esac
}

stop_server() {
  if [ -n "${SERVER_PID:-}" ]; then
    if is_windows_bash && command -v taskkill.exe >/dev/null 2>&1; then
      taskkill.exe //PID "$SERVER_PID" //T //F >/dev/null 2>&1 || true
    else
      kill "$SERVER_PID" >/dev/null 2>&1 || true
    fi
  fi
}

curl -fsSL "$BASE_URL/install.sh" | \
  VERSION="$VERSION" \
  INSTALL_ROOT="$INSTALL_ROOT" \
  BIN_DIR="$BIN_DIR" \
  bash

CLI="$BIN_DIR/$COMMAND_NAME"
export PATH="$BIN_DIR:$PATH"

"$CLI" --help >/dev/null
"$CLI" --runtime-layout-json > "$LOG_DIR/runtime-layout.json"
grep -q '"layout": "python-runtime"' "$LOG_DIR/runtime-layout.json"

marker="manual-cli-tool-smoke-$(date +%s)"
printf '%s\n' "$marker" > "$ROOT/tool-target.txt"

"$CLI" --server --config-local --host 127.0.0.1 --port "$PORT" \
  > "$LOG_DIR/server.log" 2> "$LOG_DIR/server.err" &
SERVER_PID=$!
trap stop_server EXIT

for _ in $(seq 1 90); do
  if curl -fsS "http://127.0.0.1:$PORT/api/hello" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

curl -fsS "http://127.0.0.1:$PORT/api/hello" > "$LOG_DIR/hello.json"

session_response="$(
  curl -fsS -X POST "http://127.0.0.1:$PORT/sessions" \
    -H 'Content-Type: application/json' \
    -d "{
      \"agent_id\": \"$selected_agent\",
      \"system_message\": \"You are testing an installed Crystal Lattice CLI. When asked about file contents, use tools and do not guess.\"
    }"
)"
printf '%s\n' "$session_response" > "$LOG_DIR/session.json"
SESSION_ID="$(printf '%s\n' "$session_response" | json_extract_session_id | tr -d '\r')"

curl -fsS -X POST "http://127.0.0.1:$PORT/sessions/$SESSION_ID/send_message" \
  -H 'Content-Type: application/json' \
  -d '{
    "message": {
      "role": "user",
      "content": "Use the tools to read ./tool-target.txt and tell me its exact contents. Do not answer without using a tool."
    },
    "config_overrides": {
      "allowed_paths": ["."],
      "working_directory": "."
    }
  }' > "$LOG_DIR/send-response.json"

for _ in $(seq 1 120); do
  curl -fsS "http://127.0.0.1:$PORT/sessions/$SESSION_ID/messages" > "$LOG_DIR/messages.json"
  active_request_id="$(json_extract_active_request_id < "$LOG_DIR/messages.json" | tr -d '\r')"
  [ -z "$active_request_id" ] && break
  sleep 2
done

grep -q '"role"[[:space:]]*:[[:space:]]*"user"' "$LOG_DIR/messages.json"
grep -q '"role"[[:space:]]*:[[:space:]]*"tool"' "$LOG_DIR/messages.json"
grep -q '"role"[[:space:]]*:[[:space:]]*"assistant"' "$LOG_DIR/messages.json"
grep -q "$marker" "$LOG_DIR/messages.json"

echo "PASS: installed CLI made a real LLM request with a tool call."
echo "Agent: $selected_agent"
echo "Session: $SESSION_ID"
echo "Logs: $LOG_DIR"