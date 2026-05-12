#!/bin/zsh
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <artifact-root>" >&2
  exit 1
fi

ARTIFACT_ROOT_INPUT="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
ARTIFACT_ROOT="$(python - <<'PY' "$ARTIFACT_ROOT_INPUT"
from pathlib import Path
import sys
print(Path(sys.argv[1]).expanduser().resolve())
PY
)"
WORKFLOW_CONFIG="$REPO_ROOT/evaluations/benchmarks/repoqa_prompted/chained_limit50_repeat5_workflow.json"
LOG_DIR="$ARTIFACT_ROOT/logs"
STATE_DIR="$ARTIFACT_ROOT/state"
NANO_RUN_MANIFEST_FILE="$STATE_DIR/nano-run-manifest.txt"
MINI_RUN_MANIFEST_FILE="$STATE_DIR/mini-run-manifest.txt"
FULL_RUN_MANIFEST_FILE="$STATE_DIR/full-run-manifest.txt"
NANO_SEED_SOURCE="$REPO_ROOT/evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced/results/nano-sample/repoqa-prompted/20260511T101417Z"
MINI_SEED_SOURCE="$REPO_ROOT/evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced/results/mini-sample/repoqa-prompted/20260511T101841Z"
FULL_SEED_SOURCE="$REPO_ROOT/evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced/results/full-sample/repoqa-prompted/20260511T105035Z"

mkdir -p "$LOG_DIR" "$STATE_DIR"

extract_json_field_to_file() {
  local log_path="$1"
  local output_path="$2"
  local field_name="$3"
  python - <<'PY' "$log_path" "$output_path" "$field_name"
import json
import sys
from pathlib import Path

log_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
field_name = sys.argv[3]
text = log_path.read_text(encoding="utf-8")
start = text.find("{")
end = text.rfind("}")
if start < 0 or end < start:
    raise SystemExit(f"Could not find JSON payload in {log_path}")
payload = json.loads(text[start:end + 1])
output_path.write_text(str(payload[field_name]) + "\n", encoding="utf-8")
PY
}

python "$REPO_ROOT/evaluations/benchmarks/repoqa_prompted/chained_workflow.py" \
  --workflow-config "$WORKFLOW_CONFIG" \
  prepare-base-manifest \
  > "$LOG_DIR/prepare-base-manifest.log" 2>&1

if [[ ! -f "$NANO_RUN_MANIFEST_FILE" ]]; then
  python "$REPO_ROOT/evaluations/benchmarks/repoqa_prompted/chained_workflow.py" \
    --workflow-config "$WORKFLOW_CONFIG" \
    --artifact-root "$ARTIFACT_ROOT" \
    seed-run nano \
    --source-run-dir "$NANO_SEED_SOURCE" \
    > "$LOG_DIR/seed-nano.log" 2>&1
  extract_json_field_to_file "$LOG_DIR/seed-nano.log" "$NANO_RUN_MANIFEST_FILE" "run_manifest_path"
fi

NANO_RUN_MANIFEST="$(tr -d '\n' < "$NANO_RUN_MANIFEST_FILE")"
python "$REPO_ROOT/evaluations/benchmarks/repoqa_prompted/chained_workflow.py" \
  --workflow-config "$WORKFLOW_CONFIG" \
  --artifact-root "$ARTIFACT_ROOT" \
  run-stage nano \
  --run-manifest "$NANO_RUN_MANIFEST" \
  > "$LOG_DIR/nano-stage.log" 2>&1

python "$REPO_ROOT/evaluations/benchmarks/repoqa_prompted/chained_workflow.py" \
  --workflow-config "$WORKFLOW_CONFIG" \
  --artifact-root "$ARTIFACT_ROOT" \
  refilter-next nano \
  > "$LOG_DIR/refilter-nano.log" 2>&1

if [[ ! -f "$MINI_RUN_MANIFEST_FILE" ]]; then
  python "$REPO_ROOT/evaluations/benchmarks/repoqa_prompted/chained_workflow.py" \
    --workflow-config "$WORKFLOW_CONFIG" \
    --artifact-root "$ARTIFACT_ROOT" \
    seed-run mini \
    --source-run-dir "$MINI_SEED_SOURCE" \
    > "$LOG_DIR/seed-mini.log" 2>&1
  extract_json_field_to_file "$LOG_DIR/seed-mini.log" "$MINI_RUN_MANIFEST_FILE" "run_manifest_path"
fi

MINI_RUN_MANIFEST="$(tr -d '\n' < "$MINI_RUN_MANIFEST_FILE")"
python "$REPO_ROOT/evaluations/benchmarks/repoqa_prompted/chained_workflow.py" \
  --workflow-config "$WORKFLOW_CONFIG" \
  --artifact-root "$ARTIFACT_ROOT" \
  run-stage mini \
  --run-manifest "$MINI_RUN_MANIFEST" \
  > "$LOG_DIR/mini-stage.log" 2>&1

python "$REPO_ROOT/evaluations/benchmarks/repoqa_prompted/chained_workflow.py" \
  --workflow-config "$WORKFLOW_CONFIG" \
  --artifact-root "$ARTIFACT_ROOT" \
  refilter-next mini \
  > "$LOG_DIR/refilter-mini.log" 2>&1

if [[ ! -f "$FULL_RUN_MANIFEST_FILE" ]]; then
  python "$REPO_ROOT/evaluations/benchmarks/repoqa_prompted/chained_workflow.py" \
    --workflow-config "$WORKFLOW_CONFIG" \
    --artifact-root "$ARTIFACT_ROOT" \
    seed-run full \
    --source-run-dir "$FULL_SEED_SOURCE" \
    > "$LOG_DIR/seed-full.log" 2>&1
  extract_json_field_to_file "$LOG_DIR/seed-full.log" "$FULL_RUN_MANIFEST_FILE" "run_manifest_path"
fi

FULL_RUN_MANIFEST="$(tr -d '\n' < "$FULL_RUN_MANIFEST_FILE")"
python "$REPO_ROOT/evaluations/benchmarks/repoqa_prompted/chained_workflow.py" \
  --workflow-config "$WORKFLOW_CONFIG" \
  --artifact-root "$ARTIFACT_ROOT" \
  run-stage full \
  --run-manifest "$FULL_RUN_MANIFEST" \
  > "$LOG_DIR/full-stage.log" 2>&1

python "$REPO_ROOT/evaluations/benchmarks/repoqa_prompted/chained_workflow.py" \
  --workflow-config "$WORKFLOW_CONFIG" \
  --artifact-root "$ARTIFACT_ROOT" \
  report \
  > "$LOG_DIR/report.log" 2>&1