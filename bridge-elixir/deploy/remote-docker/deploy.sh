#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Deploy the Bridge service to a remote single-node Docker host.

Required environment:
  BRIDGE_REMOTE             SSH target, for example user@example-host
  BRIDGE_PUBLIC_URL         Public HTTP origin, for example https://bridge.example.com
  BRIDGE_TOKEN_SECRET       Stable pairing-token signing secret

Optional environment:
  BRIDGE_REMOTE_DIR                    Remote directory (default: bridge-elixir)
  BRIDGE_COMPOSE_PROJECT               Compose project (default: bridgeelixir)
  BRIDGE_PORT                          Published origin port (default: 4000)
  BRIDGE_BIND_HOST                     Published bind host (default: 0.0.0.0)
  BRIDGE_CLUSTER_STRATEGY              Cluster strategy (default: none)
  BRIDGE_TOKEN_SALT                    Pairing-token salt (default: pairing-token-v1)
  BRIDGE_HTTP_TRANSFER_TOKEN_SALT      Transfer-token salt (default: http-transfer-token-v1)
  BRIDGE_HTTP_TIMEOUT_MS               Transfer timeout (default: 120000)
  BRIDGE_HTTP_MAX_BODY_BYTES           Transfer body limit (default: 104857600)
  BRIDGE_MAX_PENDING_HTTP_TRANSFERS    Active transfer limit (default: 128)
  BRIDGE_HTTP_COMPRESS_THRESHOLD_BYTES Gzip threshold (default: 1024)
  BRIDGE_VERIFY_LARGE_BODY             Probe a 1.2 MB public request (default: 0)
  BRIDGE_RUN_EXTERNAL_E2E              Run frontend SDK external E2E (default: 0)
  BRIDGE_WEBSOCKET_URL                 E2E WebSocket URL; derived from public URL
  SSH_OPTS                             Extra ssh options
  RSYNC_OPTS                           Extra rsync options

Example:
  BRIDGE_REMOTE=user@example-host \
  BRIDGE_PUBLIC_URL=https://bridge.example.com \
  BRIDGE_TOKEN_SECRET=replace-with-a-stable-secret \
  ./bridge-elixir/deploy/remote-docker/deploy.sh
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: ${name}" >&2
    usage >&2
    exit 2
  fi
}

quote() {
  printf "%q" "$1"
}

write_dotenv() {
  local name="$1"
  local value="$2"
  if [[ "$value" == *$'\n'* || "$value" == *$'\r'* || "$value" == *"'"* ]]; then
    echo "${name} must not contain newlines or single quotes" >&2
    exit 2
  fi
  printf "%s='%s'\n" "$name" "$value"
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
bridge_dir="${repo_root}/bridge-elixir"

require_env BRIDGE_REMOTE
require_env BRIDGE_PUBLIC_URL
require_env BRIDGE_TOKEN_SECRET

if [[ ! -s "${bridge_dir}/mix.lock" ]]; then
  echo "bridge-elixir/mix.lock is required for a reproducible Docker build" >&2
  exit 2
fi

remote="${BRIDGE_REMOTE}"
remote_dir="${BRIDGE_REMOTE_DIR:-bridge-elixir}"
public_url="${BRIDGE_PUBLIC_URL%/}"
compose_project="${BRIDGE_COMPOSE_PROJECT:-bridgeelixir}"
bridge_port="${BRIDGE_PORT:-4000}"
bind_host="${BRIDGE_BIND_HOST:-0.0.0.0}"
cluster_strategy="${BRIDGE_CLUSTER_STRATEGY:-none}"
token_salt="${BRIDGE_TOKEN_SALT:-pairing-token-v1}"
transfer_token_salt="${BRIDGE_HTTP_TRANSFER_TOKEN_SALT:-http-transfer-token-v1}"
http_timeout_ms="${BRIDGE_HTTP_TIMEOUT_MS:-120000}"
http_max_body_bytes="${BRIDGE_HTTP_MAX_BODY_BYTES:-104857600}"
max_pending_transfers="${BRIDGE_MAX_PENDING_HTTP_TRANSFERS:-128}"
compress_threshold="${BRIDGE_HTTP_COMPRESS_THRESHOLD_BYTES:-1024}"
restart_policy="${BRIDGE_RESTART_POLICY:-unless-stopped}"
verify_large_body="${BRIDGE_VERIFY_LARGE_BODY:-0}"
run_external_e2e="${BRIDGE_RUN_EXTERNAL_E2E:-0}"

websocket_url="${BRIDGE_WEBSOCKET_URL:-}"
if [[ -z "$websocket_url" ]]; then
  websocket_url="${public_url/http:/ws:}/ws/websocket"
  websocket_url="${websocket_url/https:/wss:}"
fi

ssh_extra=()
if [[ -n "${SSH_OPTS:-}" ]]; then
  # shellcheck disable=SC2206
  ssh_extra=(${SSH_OPTS})
fi

rsync_extra=()
if [[ -n "${RSYNC_OPTS:-}" ]]; then
  # shellcheck disable=SC2206
  rsync_extra=(${RSYNC_OPTS})
fi

bundle_path="$(mktemp -t bridge-source.XXXXXX.tar.gz)"
runtime_env_path="$(mktemp -t bridge-runtime.XXXXXX.env)"
large_body_path="$(mktemp -t bridge-large-body.XXXXXX.bin)"
cleanup() {
  rm -f "$bundle_path" "$runtime_env_path" "$large_body_path"
}
trap cleanup EXIT

COPYFILE_DISABLE=1 tar \
  --exclude '.git' \
  --exclude '.DS_Store' \
  --exclude '.env' \
  --exclude '.envrc' \
  --exclude '_build' \
  --exclude 'deps' \
  --exclude '.elixir_ls' \
  --exclude 'cover' \
  --exclude 'test/tmp' \
  -czf "$bundle_path" \
  -C "$bridge_dir" \
  .

umask 077
{
  write_dotenv BRIDGE_TOKEN_SECRET "${BRIDGE_TOKEN_SECRET}"
  write_dotenv BRIDGE_TOKEN_SALT "$token_salt"
  write_dotenv BRIDGE_HTTP_TRANSFER_TOKEN_SALT "$transfer_token_salt"
  write_dotenv BRIDGE_CLUSTER_STRATEGY "$cluster_strategy"
  write_dotenv BRIDGE_HTTP_TIMEOUT_MS "$http_timeout_ms"
  write_dotenv BRIDGE_HTTP_MAX_BODY_BYTES "$http_max_body_bytes"
  write_dotenv BRIDGE_MAX_PENDING_HTTP_TRANSFERS "$max_pending_transfers"
  write_dotenv BRIDGE_HTTP_COMPRESS_THRESHOLD_BYTES "$compress_threshold"
  write_dotenv BRIDGE_BIND_HOST "$bind_host"
  write_dotenv BRIDGE_PORT "$bridge_port"
  write_dotenv BRIDGE_RESTART_POLICY "$restart_policy"
} >"$runtime_env_path"

# The quoted remote path is intentionally expanded before ssh.
# shellcheck disable=SC2029
ssh "${ssh_extra[@]}" "$remote" \
  "set -eu; mkdir -p $(quote "${remote_dir}")/.deploy; chmod 700 $(quote "${remote_dir}")/.deploy"

rsync_args=(-az)
if [[ -n "${SSH_OPTS:-}" ]]; then
  rsync_args+=(-e "ssh ${SSH_OPTS}")
fi
if [[ ${#rsync_extra[@]} -gt 0 ]]; then
  rsync_args+=("${rsync_extra[@]}")
fi
rsync "${rsync_args[@]}" "$bundle_path" "$remote:${remote_dir}/.deploy/source.tar.gz"
rsync "${rsync_args[@]}" "$runtime_env_path" "$remote:${remote_dir}/.deploy/runtime.env"

remote_command="
set -euo pipefail
cd $(quote "${remote_dir}")
chmod 600 .deploy/runtime.env
find . -mindepth 1 -maxdepth 1 ! -name .deploy -exec rm -rf {} +
tar -xzf .deploy/source.tar.gz -C .
set -a
. .deploy/runtime.env
set +a

if docker compose version >/dev/null 2>&1; then
  compose_cmd='docker compose'
  compose_file='docker-compose.single-node.yml'
elif docker-compose version >/dev/null 2>&1; then
  compose_cmd='docker-compose'
  compose_file='docker-compose.single-node-v2.yml'
else
  echo 'Neither docker compose nor docker-compose is available' >&2
  exit 1
fi

\${compose_cmd} -p $(quote "${compose_project}") -f \"\${compose_file}\" build
\${compose_cmd} -p $(quote "${compose_project}") -f \"\${compose_file}\" up -d --remove-orphans

healthy=0
for _attempt in \$(seq 1 60); do
  if curl -fsS http://127.0.0.1:$(quote "${bridge_port}")/health >/dev/null; then
    healthy=1
    break
  fi
  sleep 1
done

if [[ \"\${healthy}\" != '1' ]]; then
  echo 'Bridge origin health check failed' >&2
  \${compose_cmd} -p $(quote "${compose_project}") -f \"\${compose_file}\" ps >&2 || true
  \${compose_cmd} -p $(quote "${compose_project}") -f \"\${compose_file}\" logs --tail=120 bridge >&2 || true
  exit 1
fi

capabilities=\$(curl -fsS http://127.0.0.1:$(quote "${bridge_port}")/bridge/v1/capabilities)
if ! grep -q '\"protocol_version\":1' <<<\"\${capabilities}\"; then
  echo 'Bridge origin does not advertise HTTP protocol version 1' >&2
  printf '%s\n' \"\${capabilities}\" >&2
  exit 1
fi

\${compose_cmd} -p $(quote "${compose_project}") -f \"\${compose_file}\" ps
"

# The assembled command contains only values quoted by quote().
# shellcheck disable=SC2029
ssh "${ssh_extra[@]}" "$remote" "$remote_command"

curl -fsS "${public_url}/health" >/dev/null
public_capabilities="$(curl -fsS "${public_url}/bridge/v1/capabilities")"
if ! grep -q '"protocol_version":1' <<<"$public_capabilities"; then
  echo "Public bridge does not advertise HTTP protocol version 1" >&2
  printf '%s\n' "$public_capabilities" >&2
  exit 1
fi

if [[ "$verify_large_body" == "1" ]]; then
  head -c 1200000 /dev/zero >"$large_body_path"
  large_status="$(
    curl -sS -o /dev/null -w '%{http_code}' \
      -X POST \
      -H 'Content-Type: application/octet-stream' \
      --data-binary "@${large_body_path}" \
      "${public_url}/__bridge_large_body_probe__"
  )"
  if [[ "$large_status" != "404" ]]; then
    echo "Public 1.2 MB body probe expected an upstream 404, received ${large_status}" >&2
    exit 1
  fi
fi

if [[ "$run_external_e2e" == "1" ]]; then
  (
    cd "$repo_root"
    BRIDGE_E2E_MODE=external \
      BRIDGE_E2E_URL="$websocket_url" \
      npm --workspace @crystal-lattice/frontend-sdk run integration:bridge
  )
fi

echo "Bridge deployed to ${public_url}"
echo "Health: ${public_url}/health"
echo "Capabilities: ${public_url}/bridge/v1/capabilities"