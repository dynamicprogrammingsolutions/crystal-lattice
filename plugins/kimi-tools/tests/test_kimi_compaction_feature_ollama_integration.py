# Copyright 2026 Dynamic Programming Solutions Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Ollama OpenAI-compatible integration test for Kimi compaction context forwarding."""

from __future__ import annotations

# ruff: noqa: E402

import base64
import json
import os
import sys
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parents[3]
for rel in (
    "core/python",
    "plugins/kimi-tools/src",
    "plugins/reference-openai-compatible-provider/src",
):
    path = ROOT / rel
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from agent_core.tool_result_payloads import (  # noqa: E402
    FORMAT_OPENAI_CHAT_COMPLETIONS,
    make_provider_native_tool_result,
)

import importlib  # noqa: E402

_kcf = importlib.import_module("kimi_tools.kimi_compaction_feature")
KimiCompactionFeature = _kcf.KimiCompactionFeature

MODEL = os.getenv("OLLAMA_OPENAI_MODEL", "qwen3:0.6b")
BASE_URL = os.getenv("OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1")
TIMEOUT = float(os.getenv("OLLAMA_OPENAI_TIMEOUT", "60"))


def _ollama_available(base_url: str) -> bool:
    try:
        r = requests.get(f"{base_url.rstrip('/')}/models", timeout=2)
        return bool(r.ok)
    except Exception:
        return False


@pytest.mark.integration
@pytest.mark.ollama
def test_compact_conversation_with_asset_ref_requires_context_ollama(
    tmp_path: Path,
) -> None:
    """Regression test: kimi_compaction_feature must pass context to send_request_stream
    so that providers can resolve session asset references in tool messages."""
    if not _ollama_available(BASE_URL):
        pytest.skip("Ollama OpenAI-compatible endpoint not reachable")

    try:
        importlib.import_module("reference_openai_compatible_provider.provider")
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"Ollama compaction test dependencies not installed: {exc}")

    full_cfg = {
        "providers": {
            "ollama": {
                "provider": "reference_openai_compatible",
                "model": MODEL,
                "base_url": BASE_URL,
                "timeout": TIMEOUT,
            },
        },
        "plugins": [
            "reference_openai_compatible_provider.provider.OpenAICompatibleProvider",
            "kimi_tools.kimi_compaction_feature.KimiCompactionFeature",
        ],
        "agents": {
            "default": {
                "provider": "ollama",
                "compaction": {
                    "enabled": True,
                    "type": "kimi",
                },
            },
        },
    }
    config_path = tmp_path / "config_ollama.json"
    config_path.write_text(json.dumps(full_cfg), encoding="utf-8")

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    asset_store = app.get_session_asset_store()

    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    # Store a fake image asset
    record = asset_store.store_base64(
        session_id=session_id,
        attachment_type="image",
        filename="test.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"fake-image").decode("ascii"),
    )
    asset_id = record.asset_id

    # Add a user message
    session = core.add_message(
        session, "user", "Hello", metadata=None, config=base_config
    )
    session = core.add_message(
        session, "assistant", "Hi there", metadata=None, config=base_config
    )
    session = core.add_message(
        session, "user", "How are you?", metadata=None, config=base_config
    )

    # Add a tool message with an asset_ref in the tool result
    tool_result = make_provider_native_tool_result(
        format=FORMAT_OPENAI_CHAT_COMPLETIONS,
        content=[
            {"type": "text", "text": "Tool result with image"},
            {
                "type": "image_url",
                "image_url": {
                    "asset_ref": {
                        "kind": "session_asset",
                        "session_id": session_id,
                        "asset_id": asset_id,
                        "attachment_type": "image",
                    }
                },
            },
        ],
    )
    session = core.add_message(
        session,
        "tool",
        "",
        metadata={"tool_call_id": "tc1"},
        config=base_config,
        tool_result=tool_result,
    )

    app.save_session(session)

    try:
        result = app.execute_session_action(
            "kimi_compaction",
            "compact_conversation",
            {"session_id": session_id, "start": 0, "end": 4},
        )
    except RuntimeError as exc:
        error_msg = str(exc)
        assert (
            "session asset attachment requires session_asset_store in context"
            in error_msg
        )
        pytest.fail(
            f"Regression detected: kimi_compaction_feature did not forward context to "
            f"send_request_stream. Error: {error_msg}"
        )

    # With the fix, it succeeds and returns a mutation.
    assert result.get("message") == "Compacted conversation."
