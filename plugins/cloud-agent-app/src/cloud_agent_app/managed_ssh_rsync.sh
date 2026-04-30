#!/usr/bin/env bash
set -euo pipefail

: "${TRANSFER_DIRECTION:?TRANSFER_DIRECTION is required}"
: "${TRANSFER_DIR:?TRANSFER_DIR is required}"
: "${TRANSFER_SSH_HOST:?TRANSFER_SSH_HOST is required}"
: "${TRANSFER_SSH_PORT:?TRANSFER_SSH_PORT is required}"
: "${TRANSFER_SSH_USER:?TRANSFER_SSH_USER is required}"
: "${TRANSFER_SSH_KEY_PATH:?TRANSFER_SSH_KEY_PATH is required}"
: "${TRANSFER_SSH_KNOWN_HOSTS:?TRANSFER_SSH_KNOWN_HOSTS is required}"

ssh_path="${SSH_PATH:-ssh}"
rsync_path="${RSYNC_PATH:-rsync}"
remote_path="${TRANSFER_REMOTE_PATH:-.}"

ssh_args=(
  -i "${TRANSFER_SSH_KEY_PATH}"
  -p "${TRANSFER_SSH_PORT}"
  -o "BatchMode=yes"
  -o "IdentitiesOnly=yes"
  -o "StrictHostKeyChecking=yes"
  -o "UserKnownHostsFile=${TRANSFER_SSH_KNOWN_HOSTS}"
)

rsync_args=(-az --delete)
if [[ -n "${RSYNC_EXTRA_ARGS:-}" ]]; then
  # shellcheck disable=SC2206
  extra_args=(${RSYNC_EXTRA_ARGS})
  rsync_args+=("${extra_args[@]}")
fi

remote="${TRANSFER_SSH_USER}@${TRANSFER_SSH_HOST}:${remote_path}"
ssh_command="${ssh_path}"
for arg in "${ssh_args[@]}"; do
  printf -v quoted '%q' "${arg}"
  ssh_command+=" ${quoted}"
done

case "${TRANSFER_DIRECTION}" in
  upload)
    "${rsync_path}" "${rsync_args[@]}" -e "${ssh_command}" "${TRANSFER_DIR}/" "${remote}/"
    ;;
  download)
    mkdir -p "${TRANSFER_DIR}"
    "${rsync_path}" "${rsync_args[@]}" -e "${ssh_command}" "${remote}/" "${TRANSFER_DIR}/"
    ;;
  *)
    echo "Unsupported TRANSFER_DIRECTION=${TRANSFER_DIRECTION}" >&2
    exit 2
    ;;
esac