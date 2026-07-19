from __future__ import annotations

import json
import re
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESULTS_JSON_PATH = REPO_ROOT / "artifacts" / "openai_responses_tier_runs.json"


def requested_tier_from_case(case_name: str) -> str:
    if case_name.endswith("priority"):
        return "priority"
    if case_name.endswith("flex"):
        return "flex"
    return "default"


def load_results_store(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"version": 1, "runs": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"results store at {path} is not a JSON object")
    runs = payload.get("runs")
    if not isinstance(runs, list):
        raise RuntimeError(f"results store at {path} is missing a runs list")
    return payload


def append_results_store(path: Path, records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    payload = load_results_store(path)
    payload.setdefault("version", 1)
    payload.setdefault("runs", [])
    payload["runs"].extend(records)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def _safe_float(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def aggregate_records(
    records: Sequence[Dict[str, Any]],
    *,
    profiles: Optional[set[str]] = None,
    models: Optional[set[str]] = None,
    case_names: Optional[set[str]] = None,
) -> List[Dict[str, Any]]:
    grouped: Dict[tuple[str, str, str], List[Dict[str, Any]]] = {}

    for record in records:
        profile = record.get("profile")
        model = record.get("model")
        case_name = record.get("case_name")
        if not isinstance(profile, str) or not isinstance(model, str) or not isinstance(case_name, str):
            continue
        if profiles is not None and profile not in profiles:
            continue
        if models is not None and model not in models:
            continue
        if case_names is not None and case_name not in case_names:
            continue
        grouped.setdefault((profile, model, case_name), []).append(record)

    summaries: List[Dict[str, Any]] = []
    for (profile, model, case_name), items in sorted(grouped.items()):
        successes = [item for item in items if item.get("status") == "ok"]
        tps_values = [
            value
            for value in (_safe_float(item.get("turn_tps")) for item in successes)
            if isinstance(value, float)
        ]
        duration_values = [
            value
            for value in (_safe_float(item.get("duration_seconds")) for item in successes)
            if isinstance(value, float)
        ]
        summaries.append(
            {
                "profile": profile,
                "model": model,
                "case_name": case_name,
                "requested_tier": requested_tier_from_case(case_name),
                "auth_mode": items[0].get("auth_mode"),
                "runs": len(items),
                "successes": len(successes),
                "errors": len(items) - len(successes),
                "mean_tps": mean(tps_values) if tps_values else None,
                "min_tps": min(tps_values) if tps_values else None,
                "max_tps": max(tps_values) if tps_values else None,
                "mean_duration_seconds": mean(duration_values) if duration_values else None,
                "min_duration_seconds": min(duration_values) if duration_values else None,
                "max_duration_seconds": max(duration_values) if duration_values else None,
            }
        )
    return summaries


def render_summary_lines(summaries: Sequence[Dict[str, Any]]) -> Iterable[str]:
    yield "profile\tmodel\tcase_name\truns\tsuccesses\terrors\tmean_tps\tmin_tps\tmax_tps\tmean_duration_s\tmin_duration_s\tmax_duration_s"
    for item in summaries:
        yield (
            f"{item['profile']}\t{item['model']}\t{item['case_name']}\t"
            f"{item['runs']}\t{item['successes']}\t{item['errors']}\t"
            f"{item['mean_tps']}\t{item['min_tps']}\t{item['max_tps']}\t"
            f"{item['mean_duration_seconds']}\t{item['min_duration_seconds']}\t{item['max_duration_seconds']}"
        )


def parse_text_artifact(path: Path, *, profile: str) -> List[Dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    top: Dict[str, str] = {}
    current: Optional[Dict[str, Any]] = None
    records: List[Dict[str, Any]] = []

    header_re = re.compile(r"^\[model=(.+?) case=(.+?) repeat=(\d+)\]$")
    in_summary = False

    for line in lines:
        if line == "[summary]":
            in_summary = True
            current = None
            continue
        if in_summary:
            continue
        match = header_re.match(line)
        if match:
            model, case_name, repeat_index = match.groups()
            current = {
                "profile": profile,
                "model": model,
                "case_name": case_name,
                "repeat_index": int(repeat_index),
                "requested_tier": requested_tier_from_case(case_name),
                "artifact_path": str(path),
                "batch_started_at": top.get("started_at"),
            }
            records.append(current)
            continue
        if current is None:
            if "=" in line:
                key, value = line.split("=", 1)
                top[key] = value
            continue
        if not line.strip():
            current = None
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        current[key] = value

    normalized: List[Dict[str, Any]] = []
    for raw in records:
        metrics: Dict[str, Any] = {}
        for key in (
            "input_tokens",
            "output_tokens",
            "duration_seconds",
            "tps",
            "output_chars",
            "approx_input_tokens_target",
            "approx_output_tokens_target",
            "approx_context_tokens",
        ):
            value = raw.get(key)
            if value is None:
                continue
            try:
                if key in {"input_tokens", "output_tokens", "output_chars", "approx_input_tokens_target", "approx_output_tokens_target", "approx_context_tokens"}:
                    metrics[key] = int(value)
                else:
                    metrics[key] = float(value)
            except Exception:
                pass

        normalized.append(
            {
                "profile": raw["profile"],
                "model": raw["model"],
                "case_name": raw["case_name"],
                "auth_mode": raw.get("auth_mode"),
                "requested_tier": raw["requested_tier"],
                "repeat_index": raw["repeat_index"],
                "execution_mode": top.get("execution_mode"),
                "max_workers": int(top["max_workers"]) if top.get("max_workers") else None,
                "run_scope": top.get("run_scope"),
                "desired_input_tokens": int(top["desired_input_tokens"]) if top.get("desired_input_tokens") else None,
                "desired_output_tokens": int(top["desired_output_tokens"]) if top.get("desired_output_tokens") else None,
                "status": raw.get("status"),
                "error": raw.get("error"),
                "artifact_path": raw.get("artifact_path"),
                "batch_started_at": raw.get("batch_started_at"),
                "reported_service_tier": raw.get("reported_service_tier"),
                "effective_auth_mode": raw.get("effective_auth_mode"),
                "input_tokens": metrics.get("input_tokens"),
                "output_tokens": metrics.get("output_tokens"),
                "duration_seconds": metrics.get("duration_seconds"),
                "turn_tps": metrics.get("tps"),
                "output_chars": metrics.get("output_chars"),
                "approx_input_tokens_target": metrics.get("approx_input_tokens_target"),
                "approx_output_tokens_target": metrics.get("approx_output_tokens_target"),
                "approx_context_tokens": metrics.get("approx_context_tokens"),
            }
        )

    return normalized