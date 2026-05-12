#!/bin/zsh
set -euo pipefail

REPO_ROOT="/Users/ferenci84/Dev/Mine/ai-agent-platform"
CONFIG_DIR="$REPO_ROOT/evaluations/benchmarks/repoqa_prompted/config/openai_chatgpt_reasoning_none_balanced"
PROFILE="repoqa-prompted-gpt54mini-balanced-sample-chatgpt-docker"
MANIFEST_PATH="$CONFIG_DIR/manifests/repoqa-prompted-balanced-all-limit20-seed1.json"
LOG_DIR="$CONFIG_DIR/launcher-logs"
STATUS_LOG="$LOG_DIR/auth-status.log"
RUN_LOG="$LOG_DIR/run.log"
RESULTS_ROOT="$CONFIG_DIR/results/mini-sample-chatgpt/repoqa-prompted"

mkdir -p "$LOG_DIR"

extract_json_payload() {
  python - <<'PY' "$1"
from pathlib import Path
import sys

text = Path(sys.argv[1]).read_text(encoding="utf-8")
start = text.find("{")
end = text.rfind("}")
if start < 0 or end < start:
    raise SystemExit(1)
print(text[start:end + 1])
PY
}

while true; do
  agent-evaluations auth status \
    --config-dir "$CONFIG_DIR" \
    > "$STATUS_LOG" 2>&1 || true
  AUTH_STATE="$(
    python - <<'PY' "$STATUS_LOG"
from pathlib import Path
import json
import sys

text = Path(sys.argv[1]).read_text(encoding="utf-8")
start = text.find("{")
end = text.rfind("}")
if start < 0 or end < start:
    print("unknown")
    raise SystemExit(0)
payload = json.loads(text[start:end + 1])
status = payload.get("auth_status") if isinstance(payload, dict) else None
print(status.get("state") if isinstance(status, dict) else "unknown")
PY
  )"
  if [[ "$AUTH_STATE" == "authenticated" ]]; then
    break
  fi
  sleep 15
done

RUN_MANIFEST_PATH=""
if [[ -d "$RESULTS_ROOT" ]]; then
  RUN_MANIFEST_PATH="$(find "$RESULTS_ROOT" -maxdepth 2 -name run-manifest.json 2>/dev/null | sort | tail -n 1)"
fi
if [[ -n "$RUN_MANIFEST_PATH" ]]; then
  agent-evaluations run repoqa-prompted \
    --config-dir "$CONFIG_DIR" \
    --profile "$PROFILE" \
    --manifest-path "$MANIFEST_PATH" \
    --run-manifest "$RUN_MANIFEST_PATH" \
    > "$RUN_LOG" 2>&1
else
  agent-evaluations run repoqa-prompted \
    --config-dir "$CONFIG_DIR" \
    --profile "$PROFILE" \
    --manifest-path "$MANIFEST_PATH" \
    > "$RUN_LOG" 2>&1
fi