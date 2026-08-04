#!/bin/zsh
# Sample script: build an EPUB from a set of Markdown task notes using pandoc.
#
# This is a reference sample showing how to use pandoc outside the agent tool
# loop to assemble an EPUB from ordered Markdown files. It mirrors what the
# plugin's `build_epub_from_markdown` tool does, but is intended to be run
# directly from a shell rather than invoked by an agent.
#
# The example task directory (`tasks/20260516-auth-notifications-staged-rollout`)
# is the one this script was originally written for. Adjust TASK_DIR for your
# own Markdown source set.
set -euo pipefail

ROOT_DIR="${0:A:h:h:h:h}"
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