#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Deploy Cloud Orchestrator to an explicit remote Docker host, then run the
frontend SDK cloud-orchestrator E2E in external mode against that deployment.

Required environment:
  RUN_CLOUD_ORCHESTRATOR_REMOTE_DOCKER_E2E=1
  CLOUD_ORCHESTRATOR_REMOTE       SSH target, for example user@example-host
  CLOUD_ORCHESTRATOR_PUBLIC_URL   Public URL, for example https://cloud.example.com

Optional environment is forwarded to deploy/remote-docker/deploy.sh, including:
  CLOUD_ORCHESTRATOR_REMOTE_DIR
  CLOUD_ORCHESTRATOR_CONTROL_TOKEN
  CLOUD_ORCHESTRATOR_TOKEN_SECRET
  CLOUD_ORCHESTRATOR_HOST_DATA_DIR
  CLOUD_ORCHESTRATOR_PORT
  SSH_OPTS
  RSYNC_OPTS

Extra arguments are forwarded to Vitest after the test file path.

This smoke leaves the remote deployment running.
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

if [[ "${RUN_CLOUD_ORCHESTRATOR_REMOTE_DOCKER_E2E:-}" != "1" ]]; then
  echo "Set RUN_CLOUD_ORCHESTRATOR_REMOTE_DOCKER_E2E=1 to run this remote deploy smoke." >&2
  exit 2
fi

require_env CLOUD_ORCHESTRATOR_REMOTE
require_env CLOUD_ORCHESTRATOR_PUBLIC_URL

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../../../.." && pwd)"

"${repo_root}/cloud-orchestrator/deploy/remote-docker/deploy.sh"

export RUN_CLOUD_ORCHESTRATOR_E2E=1
export CLOUD_ORCHESTRATOR_E2E_MODE=external
export CLOUD_ORCHESTRATOR_E2E_URL="${CLOUD_ORCHESTRATOR_PUBLIC_URL}"
if [[ -n "${CLOUD_ORCHESTRATOR_CONTROL_TOKEN:-}" ]]; then
  export CLOUD_ORCHESTRATOR_E2E_CONTROL_TOKEN="${CLOUD_ORCHESTRATOR_CONTROL_TOKEN}"
fi

npm test --prefix "${repo_root}/packages/frontend-sdk" -- \
  src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts \
  "$@"