#!/bin/zsh
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <artifact-root>" >&2
  exit 1
fi

ARTIFACT_ROOT_INPUT="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
ARTIFACT_ROOT="$(python - <<'PY' "$ARTIFACT_ROOT_INPUT"
from pathlib import Path
import sys
print(Path(sys.argv[1]).expanduser().resolve())
PY
)"
WORKFLOW_CONFIG="$REPO_ROOT/evaluations/evaluations/repoqa/workflows/filter_limit200_repeat5_api_nano_codex_workflow.json"
LOG_DIR="$ARTIFACT_ROOT/logs"
STATE_DIR="$ARTIFACT_ROOT/state"
NANO_RUN_MANIFEST_FILE="$STATE_DIR/nano-run-manifest.txt"
NANO_SEED_SOURCE="$REPO_ROOT/evaluations/evaluations/repoqa/config/openai_api_reasoning_none_codex_balanced/artifacts/aligned-run1/results/nano-50/repoqa-prompted/20260512T075936Z"

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
value = payload.get(field_name)
if value is None and isinstance(payload.get("stdout"), str):
    nested_text = payload["stdout"]
    nested_start = nested_text.find("{")
    nested_end = nested_text.rfind("}")
    if nested_start >= 0 and nested_end >= nested_start:
        nested_payload = json.loads(nested_text[nested_start:nested_end + 1])
        value = nested_payload.get(field_name)
if value is None:
    raise SystemExit(f"Could not find field {field_name!r} in {log_path}")
output_path.write_text(str(value) + "\n", encoding="utf-8")
PY
}

latest_run_manifest_for_stage() {
  local stage_dir="$1"
  local root="$ARTIFACT_ROOT/results/$stage_dir/repoqa-prompted"
  if [[ ! -d "$root" ]]; then
    return 1
  fi
  find "$root" -maxdepth 2 -name run-manifest.json | sort | tail -n 1
}

python "$REPO_ROOT/evaluations/evaluations/repoqa/workflows/chained_workflow.py" \
  --workflow-config "$WORKFLOW_CONFIG" \
  prepare-base-manifest \
  > "$LOG_DIR/prepare-base-manifest.log" 2>&1

if [[ ! -f "$NANO_RUN_MANIFEST_FILE" ]]; then
  if MANIFEST="$(latest_run_manifest_for_stage nano-200 2>/dev/null)"; [[ -n "${MANIFEST:-}" ]]; then
    printf '%s\n' "$MANIFEST" > "$NANO_RUN_MANIFEST_FILE"
  else
    python "$REPO_ROOT/evaluations/evaluations/repoqa/workflows/chained_workflow.py" \
      --workflow-config "$WORKFLOW_CONFIG" \
      --artifact-root "$ARTIFACT_ROOT" \
      seed-run nano \
      --source-run-dir "$NANO_SEED_SOURCE" \
      > "$LOG_DIR/seed-nano.log" 2>&1
    extract_json_field_to_file "$LOG_DIR/seed-nano.log" "$NANO_RUN_MANIFEST_FILE" "run_manifest_path"
  fi
fi

NANO_RUN_MANIFEST="$(tr -d '\n' < "$NANO_RUN_MANIFEST_FILE")"
python "$REPO_ROOT/evaluations/evaluations/repoqa/workflows/chained_workflow.py" \
  --workflow-config "$WORKFLOW_CONFIG" \
  --artifact-root "$ARTIFACT_ROOT" \
  run-stage nano \
  --run-manifest "$NANO_RUN_MANIFEST" \
  > "$LOG_DIR/nano-stage.log" 2>&1

python "$REPO_ROOT/evaluations/evaluations/repoqa/workflows/chained_workflow.py" \
  --workflow-config "$WORKFLOW_CONFIG" \
  --artifact-root "$ARTIFACT_ROOT" \
  report \
  > "$LOG_DIR/report.log" 2>&1