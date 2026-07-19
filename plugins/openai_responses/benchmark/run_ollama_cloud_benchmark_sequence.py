from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BENCHMARK_DIR = Path(__file__).resolve().parent
STATE_PATH = Path("/tmp/ollama_cloud_benchmark_sequence_state.json")
LOG_DIR = Path("/tmp/ollama_cloud_benchmark_logs")


def _jobs() -> list[dict[str, str]]:
    models = ["kimi-k2.6:cloud", "glm-5.1:cloud", "glm-5:cloud"]
    out: list[dict[str, str]] = []
    for model in models:
        out.append(
            {
                "profile": "ollama-cloud-standard-3k-500",
                "model": model,
                "desired_input_tokens": "3000",
                "desired_output_tokens": "500",
            }
        )
    for model in models:
        out.append(
            {
                "profile": "ollama-cloud-large-context-32k-500",
                "model": model,
                "desired_input_tokens": "32000",
                "desired_output_tokens": "500",
            }
        )
    return out


def _write_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    jobs = _jobs()
    state = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "current_index": None,
        "current_job": None,
        "jobs": [],
    }
    _write_state(state)

    for index, job in enumerate(jobs):
        log_name = (
            f"{index + 1:02d}_"
            f"{job['profile'].replace(':', '_')}_"
            f"{job['model'].replace(':', '_')}.log"
        )
        log_path = LOG_DIR / log_name
        state["current_index"] = index
        state["current_job"] = {**job, "log_path": str(log_path)}
        state["jobs"].append(
            {
                **job,
                "status": "running",
                "log_path": str(log_path),
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        _write_state(state)

        cmd = [
            sys.executable,
            str(BENCHMARK_DIR / "run_openai_responses_tier_matrix.py"),
            "--agent-config-json",
            str(BENCHMARK_DIR / "kimi_ollama_benchmark_agent.json"),
            "--model",
            job["model"],
            "--repeat",
            "5",
            "--execution-mode",
            "parallel",
            "--max-workers",
            "2",
            "--desired-input-tokens",
            job["desired_input_tokens"],
            "--desired-output-tokens",
            job["desired_output_tokens"],
            "--profile",
            job["profile"],
        ]

        with log_path.open("w", encoding="utf-8") as handle:
            proc = subprocess.run(
                cmd,
                cwd=REPO_ROOT,
                stdout=handle,
                stderr=subprocess.STDOUT,
                text=True,
            )

        completed = state["jobs"][-1]
        completed["finished_at"] = datetime.now(timezone.utc).isoformat()
        if proc.returncode == 0:
            completed["status"] = "done"
        else:
            completed["status"] = "error"
            completed["returncode"] = proc.returncode
        state["current_index"] = None
        state["current_job"] = None
        _write_state(state)

        if proc.returncode != 0:
            state["status"] = "error"
            _write_state(state)
            return proc.returncode

    state["status"] = "done"
    state["finished_at"] = datetime.now(timezone.utc).isoformat()
    _write_state(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())