#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Deploy Cloud Orchestrator to a remote Docker host.

Required environment:
  CLOUD_ORCHESTRATOR_REMOTE       SSH target, for example user@example-host
  CLOUD_ORCHESTRATOR_PUBLIC_URL   Public URL, for example https://cloud.example.com

Optional environment:
  CLOUD_ORCHESTRATOR_REMOTE_DIR        Remote directory (default: cloud-orchestrator in the SSH user's home)
  CLOUD_ORCHESTRATOR_TOKEN_SECRET      Runtime token secret (default: generated)
  CLOUD_ORCHESTRATOR_CONTROL_TOKEN     Optional control-plane bearer token
  CLOUD_ORCHESTRATOR_HOST_DATA_DIR     Host data directory (default: /var/lib/cloud-orchestrator)
  CLOUD_ORCHESTRATOR_PORT              Published HTTP port (default: 4100)
  CLOUD_ORCHESTRATOR_DOCKER_PROXY_HOST Hostname the orchestrator uses to reach runtime ports
  CLOUD_ORCHESTRATOR_DOCKER_BIND_HOST  Host IP for runtime port binding (default: 172.17.0.1)
  SSH_OPTS                             Extra ssh options
  RSYNC_OPTS                           Extra rsync options

Example:
  CLOUD_ORCHESTRATOR_REMOTE=user@example-host \
  CLOUD_ORCHESTRATOR_PUBLIC_URL=https://cloud.example.com \
  ./deploy/remote-docker/deploy.sh
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

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source_dir="${repo_root}/cloud-orchestrator"

require_env CLOUD_ORCHESTRATOR_REMOTE
require_env CLOUD_ORCHESTRATOR_PUBLIC_URL

remote="${CLOUD_ORCHESTRATOR_REMOTE}"
remote_dir="${CLOUD_ORCHESTRATOR_REMOTE_DIR:-cloud-orchestrator}"
token_secret="${CLOUD_ORCHESTRATOR_TOKEN_SECRET:-$(openssl rand -hex 32)}"
control_token="${CLOUD_ORCHESTRATOR_CONTROL_TOKEN:-}"
host_data_dir="${CLOUD_ORCHESTRATOR_HOST_DATA_DIR:-/var/lib/cloud-orchestrator}"
port="${CLOUD_ORCHESTRATOR_PORT:-4100}"
runner="${CLOUD_ORCHESTRATOR_RUNNER:-docker}"
cloud_workspace_dir="${CLOUD_WORKSPACE_DIR:-/workspace}"
docker_proxy_host="${CLOUD_ORCHESTRATOR_DOCKER_PROXY_HOST:-host.docker.internal}"
docker_bind_host="${CLOUD_ORCHESTRATOR_DOCKER_BIND_HOST:-172.17.0.1}"
secret_key_base="${SECRET_KEY_BASE:-$(openssl rand -hex 64)}"
transfer_port_start="${TRANSFER_PORT_START:-22000}"
transfer_port_end="${TRANSFER_PORT_END:-22099}"

rsync_extra=()
if [[ -n "${RSYNC_OPTS:-}" ]]; then
  # shellcheck disable=SC2206
  rsync_extra=(${RSYNC_OPTS})
fi

ssh_extra=()
if [[ -n "${SSH_OPTS:-}" ]]; then
  # shellcheck disable=SC2206
  ssh_extra=(${SSH_OPTS})
fi

rsync_args=(
  -az
  --delete
  --exclude '_build'
  --exclude 'deps'
  --exclude '.data'
  --exclude '.elixir_ls'
)
if [[ ${#rsync_extra[@]} -gt 0 ]]; then
  rsync_args+=("${rsync_extra[@]}")
fi
rsync_args+=("${source_dir}/" "${remote}:${remote_dir}/")

rsync "${rsync_args[@]}"

remote_command="
set -euo pipefail
cd ${remote_dir}
mkdir -p $(quote "${host_data_dir}")
if docker compose version >/dev/null 2>&1; then
  compose_cmd='docker compose'
  compose_file='docker-compose.single-node.yml'
else
  compose_cmd='docker-compose'
  compose_file='docker-compose.single-node-v2.yml'
fi
docker build -t cloud-agent-runtime:latest runtime/python
CLOUD_ORCHESTRATOR_PUBLIC_URL=$(quote "${CLOUD_ORCHESTRATOR_PUBLIC_URL}") \\
CLOUD_ORCHESTRATOR_TOKEN_SECRET=$(quote "${token_secret}") \\
CLOUD_ORCHESTRATOR_CONTROL_TOKEN=$(quote "${control_token}") \\
CLOUD_ORCHESTRATOR_HOST_DATA_DIR=$(quote "${host_data_dir}") \\
CLOUD_ORCHESTRATOR_RUNNER=$(quote "${runner}") \\
CLOUD_ORCHESTRATOR_DOCKER_PROXY_HOST=$(quote "${docker_proxy_host}") \\
CLOUD_ORCHESTRATOR_DOCKER_BIND_HOST=$(quote "${docker_bind_host}") \\
CLOUD_WORKSPACE_DIR=$(quote "${cloud_workspace_dir}") \\
SECRET_KEY_BASE=$(quote "${secret_key_base}") \\
TRANSFER_PORT_START=$(quote "${transfer_port_start}") \\
TRANSFER_PORT_END=$(quote "${transfer_port_end}") \\
PORT=$(quote "${port}") \\
CLOUD_ORCHESTRATOR_PORT=$(quote "${port}") \\
\${compose_cmd} -f \"\${compose_file}\" build
CLOUD_ORCHESTRATOR_PUBLIC_URL=$(quote "${CLOUD_ORCHESTRATOR_PUBLIC_URL}") \\
CLOUD_ORCHESTRATOR_TOKEN_SECRET=$(quote "${token_secret}") \\
CLOUD_ORCHESTRATOR_CONTROL_TOKEN=$(quote "${control_token}") \\
CLOUD_ORCHESTRATOR_HOST_DATA_DIR=$(quote "${host_data_dir}") \\
CLOUD_ORCHESTRATOR_RUNNER=$(quote "${runner}") \\
CLOUD_ORCHESTRATOR_DOCKER_PROXY_HOST=$(quote "${docker_proxy_host}") \\
CLOUD_ORCHESTRATOR_DOCKER_BIND_HOST=$(quote "${docker_bind_host}") \\
CLOUD_WORKSPACE_DIR=$(quote "${cloud_workspace_dir}") \\
SECRET_KEY_BASE=$(quote "${secret_key_base}") \\
TRANSFER_PORT_START=$(quote "${transfer_port_start}") \\
TRANSFER_PORT_END=$(quote "${transfer_port_end}") \\
PORT=$(quote "${port}") \\
CLOUD_ORCHESTRATOR_PORT=$(quote "${port}") \\
\${compose_cmd} -f \"\${compose_file}\" up -d
"

if [[ ${#ssh_extra[@]} -gt 0 ]]; then
  ssh "${ssh_extra[@]}" "${remote}" "${remote_command}"
else
  ssh "${remote}" "${remote_command}"
fi

echo "Cloud Orchestrator deployed to ${CLOUD_ORCHESTRATOR_PUBLIC_URL}"
echo "Health check: curl -fsS ${CLOUD_ORCHESTRATOR_PUBLIC_URL%/}/health"