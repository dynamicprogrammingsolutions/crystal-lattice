from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import pytest

from agent_app.config import build_agent_config, load_resolved_config
from agent_terminal_app.runtime_layout import load_runtime_layout


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_DIR = (
    ROOT / "application" / "python" / "agent_terminal_app" / "default_config"
)
FIXTURES = Path(__file__).parent / "fixtures"
RUN_GATE = "RUN_CRYSTAL_LATTICE_OPENAI_EPHEMERAL_REVIEW_E2E"
MODEL_DISCOVERY_GATE = "RUN_CRYSTAL_LATTICE_OPENAI_MODEL_DISCOVERY_E2E"
PARENT_MODEL = "gpt-5.6-luna"
CHILD_MODEL = "gpt-6-luna"
PROMPT = (
    "Ask a subagent using gpt-6-luna to check whether the statuses in index.csv "
    "agree with the documents under notes/. Don't persist the subagent session. "
    "Report any discrepancies without changing the files."
)


def _require_credentials(gate: str = RUN_GATE) -> Path:
    if os.environ.get(gate) != "1":
        pytest.skip(f"{gate} != '1'")
    credentials = (
        Path(
            os.environ.get("CHATGPT_CREDENTIALS")
            or str(Path.home() / ".crystal" / "auth" / "chatgpt-auth.json")
        )
        .expanduser()
        .resolve()
    )
    # Once explicitly enabled, missing prerequisites are failures, not passing skips.
    assert credentials.is_file(), f"Saved ChatGPT login missing: {credentials}"
    return credentials


def _write_config(config_dir: Path, session_root: Path, credentials: Path) -> Path:
    shutil.copytree(
        DEFAULT_CONFIG_DIR,
        config_dir,
        ignore=shutil.ignore_patterns(".plugin_cache", "auth", "__pycache__"),
    )
    config_path = config_dir / "config.json"
    environment = load_runtime_layout().application_env_overrides(
        config_path=config_path, session_root=session_root
    )
    resolved, errors, _ = load_resolved_config(config_path, env_overrides=environment)
    assert not [error for error in errors if error.get("severity") != "warning"], errors

    agent = build_agent_config(resolved, "codex-openai")
    agent.update(
        {
            "model": PARENT_MODEL,
            "auth_mode": "chatgpt",
            "chatgpt_credentials_path": str(credentials),
            "reasoning_effort": "low",
            "include_tasks": False,
            "include_crystal_lattice_access": False,
            "timeout": 180,
            "enable_flex_processing": False,
            "enable_prompt_cache_retention_24h": False,
            "chatgpt_rate_limits_path": str(config_dir / "rate-limits.json"),
            "chatgpt_usage_journal_path": str(config_dir / "usage.ndjson"),
        }
    )
    config = {
        "plugin_cache_dir": str(config_dir / ".plugin_cache" / "plugins"),
        "plugin_policy": {
            "allow_remote": False,
            "allow_dynamic_plugin_install": True,
            "allow_bash_tools": True,
            "allow_node_tools": False,
        },
        "plugins": [
            "plugins.tool_gating_feature.ToolGatingFeature",
            f"path:{ROOT / 'plugins' / 'feature-request-options'}",
            f"path:{ROOT / 'plugins' / 'feature-system-message'}",
            f"path:{ROOT / 'plugins' / 'openai_responses'}",
            f"path:{ROOT / 'plugins' / 'codex-tools'}",
            "model_delegation_observer.DelegationEvidenceAppPlugin",
        ],
        "providers": {"openai": resolved["providers"]["openai"]},
        # Both calls use this agent; the child must override its parent-model default.
        "agents": {"codex-openai": agent},
    }
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return config_path


def _records(path: Path) -> list[dict[str, Any]]:
    assert path.is_file(), "The real provider/session observers did not start"
    return [json.loads(line) for line in path.read_text().splitlines()]


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openai
@pytest.mark.timeout(420)
def test_luna_parent_discovers_models_from_access_guidance(tmp_path: Path) -> None:
    credentials = _require_credentials(MODEL_DISCOVERY_GATE)
    workspace = tmp_path / "external-project"
    workspace.mkdir()
    session_root = tmp_path / "shared-sessions"
    config_path = _write_config(tmp_path / "crystal-config", session_root, credentials)
    trace_path = tmp_path / "model-discovery-evidence.ndjson"
    log_path = tmp_path / "parent-stderr.log"
    prompt = (
        "Discover the models available to the configured coding agent and "
        "tell me which are Luna models."
    )
    environment = {
        **os.environ,
        "CRYSTAL_DELEGATION_TEST_TRACE": str(trace_path),
        "PYTHONPATH": os.pathsep.join(
            [
                str(FIXTURES),
                str(ROOT / "application" / "python"),
                str(ROOT / "core" / "python"),
                str(ROOT / "plugins" / "openai_responses" / "src"),
                os.environ.get("PYTHONPATH", ""),
            ]
        ),
    }
    command = [
        sys.executable,
        "-m",
        "agent_terminal_app",
        "--config",
        str(config_path),
        "--sessions-dir",
        str(session_root),
        "run",
        "--agent",
        "codex-openai",
        "--set",
        "include_crystal_lattice_access=true",
        "--prompt",
        prompt,
        "--timeout",
        "300",
        "--format",
        "json",
    ]
    with log_path.open("w", encoding="utf-8") as stderr:
        completed = subprocess.run(
            command,
            cwd=workspace,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=stderr,
            text=True,
            timeout=360,
            check=False,
        )
    assert completed.returncode == 0, f"Inspect {log_path}: {completed.stdout}"
    result = json.loads(completed.stdout)
    assert result["status"] == "succeeded" and result["error"] is None, result
    records = _records(trace_path)
    requests = [row for row in records if row["kind"] == "provider_request"]
    first_request = requests[0]
    assert first_request["model"] == PARENT_MODEL
    assert first_request["user_prompts"] == [prompt]
    assert first_request["has_model_discovery_guidance"]
    discoveries = [row for row in records if row["kind"] == "model_discovery"]
    assert discoveries, "The parent did not use production CLI/SDK model discovery"
    assert all(row["agent_id"] == "codex-openai" for row in discoveries)
    luna_ids = {
        model["id"]
        for row in discoveries
        for model in row["models"]
        if "luna" in (model["id"] + " " + model.get("name", "")).lower()
    }
    assert {"gpt-5.6-luna", "gpt-6-luna"}.issubset(luna_ids), discoveries
    assert all(model_id in result["output_text"] for model_id in luna_ids), result
    assert {path.stem for path in session_root.glob("*.json")} == {result["session_id"]}
    print(f"\nParent answer:\n{result['output_text']}\n")
    print(f"Real model-discovery evidence: {trace_path}")


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openai
@pytest.mark.timeout(420)
def test_luna_parent_delegates_ephemeral_self_contained_review(tmp_path: Path) -> None:
    credentials = _require_credentials()
    workspace = tmp_path / "external-project"
    notes = workspace / "notes"
    notes.mkdir(parents=True)
    index = workspace / "index.csv"
    index.write_text(
        "document,status\n" "alpha.md,draft\n" "beta.md,draft\n" "gamma.md,approved\n",
        encoding="utf-8",
    )
    for name, status in [
        ("alpha.md", "approved"),
        ("beta.md", "draft"),
        ("gamma.md", "approved"),
    ]:
        (notes / name).write_text(f"# {name}\n\nStatus: {status}\n", encoding="utf-8")
    original_files = {
        path: path.read_bytes() for path in [index, *sorted(notes.glob("*.md"))]
    }
    session_root = tmp_path / "shared-sessions"
    config_path = _write_config(tmp_path / "crystal-config", session_root, credentials)
    trace_path = tmp_path / "delegation-evidence.ndjson"
    log_path = tmp_path / "parent-stderr.log"
    environment = {
        **os.environ,
        "CRYSTAL_DELEGATION_TEST_TRACE": str(trace_path),
        "PYTHONPATH": os.pathsep.join(
            [
                str(FIXTURES),
                str(ROOT / "application" / "python"),
                str(ROOT / "core" / "python"),
                str(ROOT / "plugins" / "openai_responses" / "src"),
                os.environ.get("PYTHONPATH", ""),
            ]
        ),
    }
    command = [
        sys.executable,
        "-m",
        "agent_terminal_app",
        "--config",
        str(config_path),
        "--sessions-dir",
        str(session_root),
        "run",
        "--agent",
        "codex-openai",
        "--set",
        "include_crystal_lattice_access=true",
        "--prompt",
        PROMPT,
        "--timeout",
        "300",
        "--format",
        "json",
    ]
    with log_path.open("w", encoding="utf-8") as stderr:
        completed = subprocess.run(
            command,
            cwd=workspace,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=stderr,
            text=True,
            timeout=360,
            check=False,
        )
    assert (
        completed.returncode == 0
    ), f"Real parent failed; inspect {log_path}. stdout: {completed.stdout}"
    result = json.loads(completed.stdout)
    assert result["status"] == "succeeded", result
    assert result["persistence"] == "persisted", result
    assert result["error"] is None, result
    for term in ("alpha", "draft", "approved"):
        assert term in result["output_text"].lower(), result["output_text"]

    records = _records(trace_path)
    requests = [row for row in records if row["kind"] == "provider_request"]
    parent_request = next(row for row in requests if row["model"] == PARENT_MODEL)
    assert parent_request["user_prompts"] == [PROMPT]
    assert parent_request["has_parent_guidance"], parent_request
    assert "agent based on GPT-5" in parent_request["instructions_start"]
    child_requests = [row for row in requests if row["model"] == CHILD_MODEL]
    assert child_requests, "No actual gpt-6-luna provider request"
    first_child = child_requests[0]
    assert first_child["input_roles"] == ["user"], first_child
    assert len(first_child["user_prompts"]) == 1, first_child
    assert not first_child["has_parent_guidance"], first_child
    assert "agent based on GPT-6" in first_child["instructions_start"]
    assert (
        first_child["instructions_sha256"] != parent_request["instructions_sha256"]
    ), "The child must receive its own configured instructions"
    child_prompt = first_child["user_prompts"][0]
    assert len(child_prompt) < 4000, child_prompt
    assert "index.csv" in child_prompt and "notes/" in child_prompt, child_prompt
    assert any(
        word in child_prompt.lower() for word in ("status", "statuses")
    ), child_prompt
    assert any(
        word in child_prompt.lower()
        for word in (
            "read-only",
            "read only",
            "don't change",
            "do not change",
            "without changing",
            "do not modify",
            "don't modify",
        )
    ), child_prompt
    assert any(
        word in child_prompt.lower()
        for word in ("report", "return", "discrepanc", "mismatch")
    ), child_prompt
    assert "These instructions are for you, the parent agent" not in child_prompt

    child_completions = [
        row
        for row in records
        if row["kind"] == "provider_completed"
        and row["configured_model"] == CHILD_MODEL
    ]
    assert child_completions, "The real child did not complete"
    child_answer = child_completions[-1]
    assert child_answer["status"] == "completed", child_answer
    assert str(child_answer["response_model"]).startswith(CHILD_MODEL), child_answer
    for term in ("alpha", "draft", "approved"):
        assert term in child_answer["output_text"].lower(), child_answer
    child_session_ids = {row["session_id"] for row in child_completions}
    assert result["session_id"] not in child_session_ids
    saves = [
        row for row in records if row["kind"] in ("session_save", "session_snapshot")
    ]
    assert saves, "Session-write observer did not exercise the parent store"
    assert not child_session_ids.intersection(row["session_id"] for row in saves)
    assert {path.stem for path in session_root.glob("*.json")} == {result["session_id"]}
    for path, original in original_files.items():
        assert path.read_bytes() == original, f"The read-only review changed {path}"

    outer = json.loads((session_root / f"{result['session_id']}.json").read_text())
    tool_calls = "\n".join(
        json.dumps(message.get("metadata") or {}, default=str)
        for message in outer["messages"]
        if message.get("role") == "assistant"
    )
    assert "agent_terminal_app" in tool_calls, "No production tool-call delegation"
    assert CHILD_MODEL in tool_calls
    assert "--ephemeral" in tool_calls or (
        "persistence" in tool_calls and "ephemeral" in tool_calls
    )
    print(f"\nChild prompt:\n{child_prompt}\n")
    print(f"Child answer:\n{child_answer['output_text']}\n")
    print(f"Parent answer:\n{result['output_text']}\n")
    print(f"Real delegation evidence: {trace_path}")
