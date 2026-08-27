from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


LANDING_ROOT = Path(__file__).resolve().parents[2]
ROOT = LANDING_ROOT.parent
MODULE_PATH = LANDING_ROOT / "scripts" / "visual-assets" / "refresh_session_fixture.py"
SPEC = importlib.util.spec_from_file_location("refresh_session_fixture", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_candidate_sanitizes_paths_and_private_metadata(tmp_path: Path) -> None:
    manifest = {
        "fixture_id": "coding-plan",
        "presentation": {
            "session_id": "website-coding-plan",
            "title": "Plan a Starlette compatibility fix",
            "subtitle": "Coding session",
        },
    }
    raw = {
        "messages": [
            {"role": "system", "content": "hidden"},
            {"role": "user", "content": f"Inspect {tmp_path}/starlette"},
            {
                "role": "assistant",
                "content": "Planning",
                "metadata": {
                    "tool_calls": [{"name": "shell", "arguments": {"command": "rg GZipResponder starlette"}}],
                    "response_id": "private",
                    "usage": {"input_tokens": 10},
                },
            },
            {"role": "tool", "content": f"{tmp_path}/starlette/starlette/middleware/gzip.py"},
        ]
    }
    candidate, tool_activity = module.build_candidate(
        raw,
        manifest=manifest,
        prompt="Inspect the regression",
        workspace=tmp_path / "starlette",
    )
    encoded = json.dumps(candidate)
    assert "private" not in encoded
    assert str(tmp_path) not in encoded
    assert "/workspace/starlette" in encoded
    assert tool_activity >= 1


def test_candidate_rejects_install_or_source_write(tmp_path: Path) -> None:
    manifest = {
        "fixture_id": "coding-plan",
        "presentation": {
            "session_id": "website-coding-plan",
            "title": "Plan",
            "subtitle": "Coding session",
        },
    }
    raw = {
        "messages": [
            {"role": "user", "content": "Plan"},
            {
                "role": "assistant",
                "content": "Inspecting",
                "metadata": {
                    "tool_calls": [
                        {"name": "shell", "arguments": {"command": "yarn install"}}
                    ]
                },
            },
        ]
    }
    with pytest.raises(RuntimeError, match="Forbidden tool activity"):
        module.build_candidate(
            raw,
            manifest=manifest,
            prompt="Plan",
            workspace=tmp_path,
        )


def test_application_request_uses_shared_request_path(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "auth").mkdir()
    (config_dir / "auth" / "chatgpt-auth.json").write_text(
        "{}", encoding="utf-8"
    )
    config_path = config_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "plugin_cache_dir": str(tmp_path / "plugin-cache"),
                "providers": {
                    "echo": {
                        "provider": "echo_openai_like",
                        "model": "test-model",
                    }
                },
                "plugins": [
                    "plugins.echo_openai_like_provider.EchoOpenAILikeProvider"
                ],
                "agents": {"default": {"provider": "echo"}},
                "application": {},
            }
        ),
        encoding="utf-8",
    )
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    session = module.run_application_session(
        repository_root=ROOT,
        config_path=config_path,
        config_dir=config_dir,
        session_root=tmp_path / "sessions",
        workspace=workspace,
        agent_id="default",
        prompt="Inspect the regression and propose a plan.",
    )
    roles = [message["role"] for message in session["messages"]]
    assert roles == ["user", "assistant"]
    assert "Inspect the regression" in session["messages"][-1]["content"]