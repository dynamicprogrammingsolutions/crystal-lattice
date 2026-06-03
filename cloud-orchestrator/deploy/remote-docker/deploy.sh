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
  CLOUD_ORCHESTRATOR_RUNTIME_READY_TIMEOUT_MS
                                      Runtime readiness timeout in milliseconds (default: 1800000)
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
deploy_dir="${repo_root}/cloud-orchestrator/deploy"

# shellcheck source=deploy/lib/source_bundle.sh
source "${deploy_dir}/lib/source_bundle.sh"

require_env CLOUD_ORCHESTRATOR_REMOTE
require_env CLOUD_ORCHESTRATOR_PUBLIC_URL

remote="${CLOUD_ORCHESTRATOR_REMOTE}"
remote_dir="${CLOUD_ORCHESTRATOR_REMOTE_DIR:-cloud-orchestrator}"
token_secret="${CLOUD_ORCHESTRATOR_TOKEN_SECRET:-$(openssl rand -hex 32)}"
control_token="${CLOUD_ORCHESTRATOR_CONTROL_TOKEN:-}"
host_data_dir="${CLOUD_ORCHESTRATOR_HOST_DATA_DIR:-/var/lib/cloud-orchestrator}"
port="${CLOUD_ORCHESTRATOR_PORT:-4100}"
runner="${CLOUD_ORCHESTRATOR_RUNNER:-docker}"
docker_proxy_host="${CLOUD_ORCHESTRATOR_DOCKER_PROXY_HOST:-host.docker.internal}"
docker_bind_host="${CLOUD_ORCHESTRATOR_DOCKER_BIND_HOST:-172.17.0.1}"
runtime_ready_timeout_ms="${CLOUD_ORCHESTRATOR_RUNTIME_READY_TIMEOUT_MS:-1800000}"
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

bundle_path="$(mktemp -t cloud-orchestrator-source.XXXXXX.tar.gz)"
cleanup() {
  rm -f "${bundle_path}"
}
trap cleanup EXIT

create_cloud_orchestrator_source_bundle "${bundle_path}" "${repo_root}"

remote_cleanup_command="
# Temporary development cleanup: stop old runtime and transfer containers
# and remove previous images to free disk space before rebuilding.
# TODO: Replace this deploy-time cleanup with continuous cleanup and
# persistent storage. This is a temporary development workaround,
# not a final solution.
runtime_container_ids=\$(docker ps -aq --format '{{.ID}} {{.Names}}' 2>/dev/null | awk '\$2 ~ /^cloud-agent-/ || \$2 ~ /^cloud-transfer-/ { print \$1 }')
if [[ -n \"\${runtime_container_ids}\" ]]; then
  printf '%s\n' \"\${runtime_container_ids}\" | xargs -r docker rm -f >/dev/null 2>&1 || true
fi
docker rmi cloud-agent-runtime:latest cloud-agent-transfer-ssh:latest >/dev/null 2>&1 || true
docker image prune -f >/dev/null 2>&1 || true
"

ssh_setup_command="
set -euo pipefail
${remote_cleanup_command}
mkdir -p $(quote "${remote_dir}")/.deploy
"

if [[ ${#ssh_extra[@]} -gt 0 ]]; then
  ssh "${ssh_extra[@]}" "${remote}" "${ssh_setup_command}"
else
  ssh "${remote}" "${ssh_setup_command}"
fi

rsync_args=(-az)
if [[ ${#rsync_extra[@]} -gt 0 ]]; then
  rsync_args+=("${rsync_extra[@]}")
fi
rsync_args+=("${bundle_path}" "${remote}:${remote_dir}/.deploy/source.tar.gz")

rsync "${rsync_args[@]}"

remote_command="
set -euo pipefail
mkdir -p $(quote "${remote_dir}")
cd $(quote "${remote_dir}")
find . -mindepth 1 -maxdepth 1 ! -name .deploy -exec rm -rf {} +
tar -xzf .deploy/source.tar.gz -C .
mkdir -p $(quote "${host_data_dir}")

if docker compose version >/dev/null 2>&1; then
  compose_cmd='docker compose'
  compose_file='cloud-orchestrator/docker-compose.single-node.yml'
else
  compose_cmd='docker-compose'
  compose_file='cloud-orchestrator/docker-compose.single-node-v2.yml'
fi
docker build -t cloud-agent-runtime:latest -f cloud-orchestrator/runtime/python/Dockerfile .
docker build -t cloud-agent-transfer-ssh:latest cloud-orchestrator/transfer/managed-ssh
CLOUD_ORCHESTRATOR_PUBLIC_URL=$(quote "${CLOUD_ORCHESTRATOR_PUBLIC_URL}") \\
CLOUD_ORCHESTRATOR_TOKEN_SECRET=$(quote "${token_secret}") \\
CLOUD_ORCHESTRATOR_CONTROL_TOKEN=$(quote "${control_token}") \\
CLOUD_ORCHESTRATOR_HOST_DATA_DIR=$(quote "${host_data_dir}") \\
CLOUD_ORCHESTRATOR_RUNNER=$(quote "${runner}") \\
CLOUD_ORCHESTRATOR_DOCKER_PROXY_HOST=$(quote "${docker_proxy_host}") \\
CLOUD_ORCHESTRATOR_DOCKER_BIND_HOST=$(quote "${docker_bind_host}") \\
CLOUD_ORCHESTRATOR_RUNTIME_READY_TIMEOUT_MS=$(quote "${runtime_ready_timeout_ms}") \\
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
CLOUD_ORCHESTRATOR_RUNTIME_READY_TIMEOUT_MS=$(quote "${runtime_ready_timeout_ms}") \\
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