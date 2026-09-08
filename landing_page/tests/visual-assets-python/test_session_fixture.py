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
        "agent_id": "codex-openai",
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
                    "tool_calls": [
                        {
                            "name": "shell",
                            "arguments": {"command": "rg GZipResponder starlette"},
                        }
                    ],
                    "response_id": "private",
                    "usage": {"input_tokens": 10},
                },
            },
            {
                "role": "tool",
                "content": f"{tmp_path}/starlette/starlette/middleware/gzip.py",
            },
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
    assert candidate["session"]["metadata"] == {"agent_id": "codex-openai"}
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


def test_candidate_requires_consecutive_reasoning_follow_up_without_tools(
    tmp_path: Path,
) -> None:
    follow_up_prompt = "Should the defaults share a constant?"
    raw = {
        "messages": [
            {"role": "user", "content": "Inspect the regression"},
            {
                "role": "assistant",
                "content": "",
                "metadata": {
                    "tool_calls": [
                        {
                            "name": "shell",
                            "arguments": {"command": "rg GZipResponder starlette"},
                        }
                    ]
                },
            },
            {"role": "tool", "content": "class GZipResponder: ..."},
            {"role": "assistant", "content": "The constructor lost its default."},
            {"role": "user", "content": follow_up_prompt},
            {
                "role": "assistant",
                "content": "Use a shared constant to prevent drift.",
                "metadata": {"reasoning": "Compare patch size with maintenance risk."},
            },
        ]
    }

    candidate, tool_activity = module.build_candidate(
        raw,
        manifest={
            "fixture_id": "coding-plan",
            "presentation": {
                "session_id": "session-id",
                "title": "Plan",
                "subtitle": "Coding session",
            },
        },
        prompt="Inspect the regression",
        follow_up_prompt=follow_up_prompt,
        workspace=tmp_path,
    )

    assert tool_activity >= 1
    assert [item["message"]["role"] for item in candidate["messages"][-2:]] == [
        "user",
        "assistant",
    ]
    assert candidate["messages"][-1]["message"]["metadata"]["reasoning"]


def test_candidate_rejects_follow_up_tool_activity(tmp_path: Path) -> None:
    follow_up_prompt = "Should the defaults share a constant?"
    raw = {
        "messages": [
            {"role": "user", "content": "Inspect the regression"},
            {
                "role": "assistant",
                "content": "",
                "metadata": {
                    "tool_calls": [
                        {
                            "name": "shell",
                            "arguments": {"command": "rg GZipResponder starlette"},
                        }
                    ]
                },
            },
            {"role": "tool", "content": "class GZipResponder: ..."},
            {"role": "assistant", "content": "The constructor lost its default."},
            {"role": "user", "content": follow_up_prompt},
            {
                "role": "assistant",
                "content": "",
                "metadata": {
                    "tool_calls": [
                        {
                            "name": "shell",
                            "arguments": {"command": "rg thread_minimum_size"},
                        }
                    ]
                },
            },
            {"role": "tool", "content": "more output"},
            {
                "role": "assistant",
                "content": "Use a shared constant.",
                "metadata": {"reasoning": "Avoid drift."},
            },
        ]
    }

    with pytest.raises(RuntimeError, match="no tool activity"):
        module.build_candidate(
            raw,
            manifest={
                "fixture_id": "coding-plan",
                "presentation": {
                    "session_id": "session-id",
                    "title": "Plan",
                    "subtitle": "Coding session",
                },
            },
            prompt="Inspect the regression",
            follow_up_prompt=follow_up_prompt,
            workspace=tmp_path,
        )


def test_candidate_preserves_reviewed_tool_call_carrier_when_runtime_collapses_it(
    tmp_path: Path,
) -> None:
    follow_up_prompt = "Should the defaults share a constant?"
    seed_messages = [
        {"index": 0, "message": {"role": "user", "content": "Inspect"}},
        {
            "index": 1,
            "message": {
                "role": "assistant",
                "content": "",
                "metadata": {
                    "tool_calls": [
                        {
                            "name": "shell",
                            "arguments": {"command": "rg GZipResponder"},
                        }
                    ]
                },
            },
        },
        {
            "index": 2,
            "message": {"role": "tool", "content": "class GZipResponder: ..."},
        },
        {
            "index": 3,
            "message": {
                "role": "assistant",
                "content": "The constructor lost its default.",
            },
        },
    ]
    raw = {
        "messages": [
            seed_messages[0]["message"],
            seed_messages[2]["message"],
            seed_messages[3]["message"],
            {"role": "user", "content": follow_up_prompt},
            {
                "role": "assistant",
                "content": "Use a shared private constant.",
                "metadata": {"reasoning": "Compare maintenance and review scope."},
            },
        ]
    }

    candidate, _tool_activity = module.build_candidate(
        raw,
        manifest={
            "fixture_id": "coding-plan",
            "presentation": {
                "session_id": "session-id",
                "title": "Plan",
                "subtitle": "Coding session",
            },
        },
        prompt="Inspect",
        follow_up_prompt=follow_up_prompt,
        seed_fixture={"messages": seed_messages},
        workspace=tmp_path,
    )

    assert candidate["messages"][:4] == seed_messages
    assert [item["index"] for item in candidate["messages"]] == list(range(6))
    assert [item["message"]["role"] for item in candidate["messages"][-2:]] == [
        "user",
        "assistant",
    ]


def test_application_request_uses_shared_request_path(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "auth").mkdir()
    (config_dir / "auth" / "chatgpt-auth.json").write_text("{}", encoding="utf-8")
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
                "plugins": ["plugins.echo_openai_like_provider.EchoOpenAILikeProvider"],
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
        follow_up_prompt="Should the defaults share a constant?",
    )
    roles = [message["role"] for message in session["messages"]]
    assert roles.count("user") == 2
    assert [
        message["content"]
        for message in session["messages"]
        if message["role"] == "user"
    ] == [
        "Inspect the regression and propose a plan.",
        "Should the defaults share a constant?",
    ]
