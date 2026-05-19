#!/bin/zsh
set -euo pipefail

ROOT_DIR="${0:A:h:h}"
TASK_DIR="${ROOT_DIR}/tasks/20260516-auth-notifications-staged-rollout"
OUTPUT_PATH="${TASK_DIR}/20260516-auth-notifications-staged-rollout.epub"

pandoc \
  --toc \
  --metadata title="Auth And Notifications Staged Rollout" \
  --metadata lang="en-US" \
  -o "${OUTPUT_PATH}" \
  "${TASK_DIR}/000-main.md" \
  "${TASK_DIR}/docs/local-notifications-background-refresh.md" \
  "${TASK_DIR}/010-local-notification-polling.md" \
  "${TASK_DIR}/docs/push-notifications-fcm-apns.md" \
  "${TASK_DIR}/020-bridge-push-delivery.md" \
  "${TASK_DIR}/docs/authentik-auth-concepts.md" \
  "${TASK_DIR}/030-authentik-auth-integration.md"

print "${OUTPUT_PATH}"