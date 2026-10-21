from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
from typing import Any

import pytest
import requests

from agent_app.config import build_agent_config, load_resolved_config
from agent_terminal_app.local_runtime import open_runtime
from agent_terminal_app.runtime_layout import load_runtime_layout


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_DIR = (
    ROOT / "application" / "python" / "agent_terminal_app" / "default_config"
)
BUILTIN_PLUGINS = ROOT / "plugins"
OLLAMA_BASE_URL = os.environ.get(
    "OLLAMA_OPENAI_BASE_URL",
    "http://localhost:11434/v1",
)
OLLAMA_MODEL = "glm-5.3-flash:cloud"
RUN_GATE = "RUN_CRYSTAL_LATTICE_OLLAMA_SUBAGENT_E2E"
EPHEMERAL_REVIEW_GATE = "RUN_CRYSTAL_LATTICE_OLLAMA_EPHEMERAL_REVIEW_E2E"
MARKER = "CRYSTAL_LATTICE_DELEGATION_MARKER_8F31C2"
STALE_ROADMAP_ID = "ROADMAP-ALPHA"


def _require_real_test(gate: str = RUN_GATE) -> None:
    if os.environ.get(gate) != "1":
        pytest.skip(f"{gate} != '1'")
    try:
        response = requests.get(
            f"{OLLAMA_BASE_URL.rstrip('/')}/models",
            timeout=5,
        )
    except Exception as exc:
        pytest.skip(f"Ollama OpenAI-compatible endpoint is unavailable: {exc}")
    if not response.ok:
        pytest.skip(
            "Ollama OpenAI-compatible endpoint returned " f"HTTP {response.status_code}"
        )


def _write_delegation_config(config_dir: Path, session_root: Path) -> Path:
    shutil.copytree(
        DEFAULT_CONFIG_DIR,
        config_dir,
        ignore=shutil.ignore_patterns(".plugin_cache", "auth", "__pycache__"),
    )
    config_path = config_dir / "config.json"
    layout = load_runtime_layout()
    resolution_env = layout.application_env_overrides(
        config_path=config_path,
        session_root=session_root,
        env_overrides={
            "CONFIG_DIR": str(config_dir),
            "BUILTIN_PLUGINS": str(BUILTIN_PLUGINS),
        },
    )
    resolved, errors, _environment = load_resolved_config(
        config_path,
        env_overrides=resolution_env,
    )
    assert not [error for error in errors if error.get("severity") != "warning"], errors

    base_agent = build_agent_config(resolved, "glm-ollama")
    base_agent["model"] = OLLAMA_MODEL
    base_agent["provider"] = "ollama"
    base_agent["reasoning_effort"] = "max"

    outer_agent = {
        **base_agent,
        "display": {
            "title": "Delegation orchestrator",
            "description": "Delegates bounded work through Crystal Lattice.",
        },
        "disabled_plugins": [
            "claude_compaction",
            "claude_read_tool",
            "claude_write_tool",
            "claude_edit_tool",
            "claude_glob_tool",
            "claude_grep_tool",
            "claude_web_fetch_tool",
            "claude_web_search_tool",
            "claude_task_stop_tool",
            "claude_mcp_tool",
        ],
    }
    worker_agent = {
        **base_agent,
        "display": {
            "title": "Read-only review worker",
            "description": "Inspects project files without modifying them.",
        },
        "disabled_plugins": [
            "claude_compaction",
            "claude_write_tool",
            "claude_edit_tool",
            "claude_web_fetch_tool",
            "claude_web_search_tool",
            "claude_task_stop_tool",
            "claude_mcp_tool",
        ],
    }

    config: dict[str, Any] = {
        "plugin_cache_dir": str(config_dir / ".plugin_cache" / "plugins"),
        "plugin_policy": {
            "allow_remote": False,
            "allow_dynamic_plugin_install": True,
            "allow_bash_tools": True,
            "allow_node_tools": False,
        },
        "providers": {
            "ollama": {
                "provider": "reference_openai_compatible",
                "base_url": OLLAMA_BASE_URL,
                "model": OLLAMA_MODEL,
                "timeout": 600,
                "reasoning_field": "reasoning",
            }
        },
        "plugins": [
            "path:${env:BUILTIN_PLUGINS}/reference-openai-compatible-provider",
            "path:${env:BUILTIN_PLUGINS}/feature-system-message",
            "path:${env:BUILTIN_PLUGINS}/claude-tools",
        ],
        "agents": {
            "delegation-orchestrator": outer_agent,
            "subagent-worker": worker_agent,
        },
    }
    config_path.write_text(
        json.dumps(config, indent=2) + "\n",
        encoding="utf-8",
    )
    return config_path


def _message_texts(session: Any) -> list[str]:
    return [
        message.content
        for message in session.messages
        if isinstance(message.content, str)
    ]


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.ollama
@pytest.mark.timeout(900)
def test_glm_ollama_uses_access_guidance_to_run_real_subagent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_real_test()
    workspace = tmp_path / "external-project"
    workspace.mkdir()
    (workspace / ".project-marker").write_text(MARKER + "\n", encoding="utf-8")
    session_root = tmp_path / "shared-sessions"
    config_path = _write_delegation_config(
        tmp_path / "crystal-config",
        session_root,
    )

    monkeypatch.chdir(workspace)
    monkeypatch.setenv(
        "PYTHONPATH",
        os.pathsep.join(
            [
                str(ROOT / "core" / "python"),
                str(ROOT / "application" / "python"),
                os.environ.get("PYTHONPATH", ""),
            ]
        ),
    )

    with open_runtime(
        config_path=config_path,
        session_root=session_root,
    ) as runtime:
        result = runtime.run(
            "Ask a subagent for the project marker and report its answer.",
            agent_id="delegation-orchestrator",
            overrides={"include_crystal_lattice_access": True},
            timeout=720,
        )
        summaries = runtime.application.list_session_summaries()
        sessions = [
            runtime.application.load_session_record(summary["session_id"])
            for summary in summaries
        ]

    assert result.status == "succeeded", result.to_dict()
    worker_sessions = [
        session
        for session in sessions
        if session is not None
        and session.session_id != result.session_id
        and session.metadata.get("agent_id") == "subagent-worker"
    ]
    assert worker_sessions, (
        "The outer model did not create a separately persisted subagent-worker "
        f"session. Outer result: {result.to_dict()}"
    )

    worker = worker_sessions[-1]
    worker_text = "\n".join(_message_texts(worker))
    assert MARKER in worker_text
    assert worker.messages[-1].role == "assistant"

    outer = next(
        session
        for session in sessions
        if session is not None and session.session_id == result.session_id
    )
    outer_text = "\n".join(_message_texts(outer))
    outer_metadata = "\n".join(
        json.dumps(message.metadata or {}, sort_keys=True, default=str)
        for message in outer.messages
    )
    assert MARKER in result.output_text
    assert MARKER in outer_text
    assert "agent_terminal_app" in outer_metadata
    assert "subagent-worker" in outer_metadata
    assert str(config_path.resolve()) in outer_metadata
    assert str(session_root.resolve()) in outer_metadata


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.ollama
@pytest.mark.timeout(900)
def test_glm_ollama_constructs_ephemeral_self_contained_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_real_test(EPHEMERAL_REVIEW_GATE)
    workspace = tmp_path / "external-project"
    (workspace / "roadmaps").mkdir(parents=True)
    (workspace / "tasks").mkdir()
    (workspace / "roadmaps" / "release.md").write_text(
        "| ID | Status |\n"
        "|---|---|\n"
        f"| {STALE_ROADMAP_ID} | pending |\n"
        "| ROADMAP-BETA | pending |\n",
        encoding="utf-8",
    )
    (workspace / "tasks" / "alpha.md").write_text(
        "# Alpha\n\n"
        "## Requirements checklist\n\n"
        "- [x] Alpha is complete.\n\n"
        "## Completion Notes\n\n"
        "- Completed and verified.\n",
        encoding="utf-8",
    )
    (workspace / "tasks" / "beta.md").write_text(
        "# Beta\n\n" "## Requirements checklist\n\n" "- [ ] Beta remains open.\n",
        encoding="utf-8",
    )
    session_root = tmp_path / "shared-sessions"
    config_path = _write_delegation_config(
        tmp_path / "crystal-config",
        session_root,
    )

    monkeypatch.chdir(workspace)
    monkeypatch.setenv(
        "PYTHONPATH",
        os.pathsep.join(
            [
                str(ROOT / "core" / "python"),
                str(ROOT / "application" / "python"),
                os.environ.get("PYTHONPATH", ""),
            ]
        ),
    )

    with open_runtime(
        config_path=config_path,
        session_root=session_root,
    ) as runtime:
        result = runtime.run(
            "Use an ephemeral subagent to review roadmaps/release.md against "
            "the task files under tasks/ and tell me which roadmap entries "
            "have stale status. Do not inspect the files yourself.",
            agent_id="delegation-orchestrator",
            overrides={"include_crystal_lattice_access": True},
            timeout=720,
        )
        summaries = runtime.application.list_session_summaries()
        outer = runtime.application.load_session_record(result.session_id)

    assert result.status == "succeeded", result.to_dict()
    assert STALE_ROADMAP_ID in result.output_text
    assert [summary["session_id"] for summary in summaries] == [result.session_id]
    assert outer is not None
    outer_metadata = "\n".join(
        json.dumps(message.metadata or {}, sort_keys=True, default=str)
        for message in outer.messages
    )
    assert "--ephemeral" in outer_metadata or (
        "persistence" in outer_metadata and "ephemeral" in outer_metadata
    )
    assert "subagent-worker" in outer_metadata
    assert "roadmaps/release.md" in outer_metadata
    assert "tasks/" in outer_metadata
