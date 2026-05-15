from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
CODEX_TOOLS_SRC = ROOT / "plugins/codex-tools/src"
if str(CODEX_TOOLS_SRC) not in sys.path:
    sys.path.insert(0, str(CODEX_TOOLS_SRC))

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from agent_core.tool_result_payloads import TOOL_RESULT_FIELD  # noqa: E402
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider  # noqa: F401,E402


PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB"
    "/6X7bAAAAABJRU5ErkJggg=="
)


def _write_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "working_directory": str(tmp_path),
        "allowed_paths": [str(tmp_path)],
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "echo-model"},
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "codex_tools.view_image_tool.ViewImageTool",
        ],
        "agents": {
            "default": {
                "provider": "echo",
                "working_directory": str(tmp_path),
                "allowed_paths": [str(tmp_path)],
            }
        },
    }
    path = tmp_path / "config_tool_image_assets.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def test_tool_loop_persists_asset_backed_view_image_message(tmp_path: Path) -> None:
    image = tmp_path / "tiny.png"
    image.write_bytes(base64.b64decode(PNG_BASE64))
    app = AgentApplication(
        str(_write_config(tmp_path)),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    core, base_config, session = app.create_session("default")
    pending_call = {
        "id": "call_view",
        "type": "function",
        "function": {"name": "view_image", "arguments": json.dumps({"path": "tiny.png"})},
    }
    session = core.add_message(
        session,
        "assistant",
        "Opening image.",
        metadata={"tool_calls": [pending_call]},
    )
    app.save_session(session, acquire_lock=True)

    events = list(app.send_request(core, session, base_config, stream=False))

    tool_events = [event for event in events if event.get("type") == "tool_results"]
    assert tool_events
    tool_message = tool_events[0]["messages"][0]
    assert isinstance(tool_message["content"], str)
    assert isinstance(tool_message[TOOL_RESULT_FIELD], dict)
    display = (tool_message.get("metadata") or {}).get("display") or {}
    assert display["type"] == "image"
    assert display["metadata"]["download_plugin_id"] == "session_asset_attachments"

    stored = app.load_session_record(session.session_id)
    assert stored is not None
    persisted_tool = next(msg for msg in stored.messages if msg.role == "tool")
    persisted_dict = persisted_tool.to_dict()
    assert isinstance(persisted_dict["content"], str)
    tool_result = persisted_dict[TOOL_RESULT_FIELD]
    assert tool_result["type"] == "provider_native_tool_result"
    part = persisted_dict["metadata"]["display"]["content"]
    assert part["asset_ref"]["kind"] == "session_asset"
    assert part["filename"] == "tiny.png"
    assert part["preview_data_base64"] == PNG_BASE64
    assert app.get_session_asset_store().load_bytes(
        session.session_id,
        part["asset_ref"]["asset_id"],
    ) == image.read_bytes()