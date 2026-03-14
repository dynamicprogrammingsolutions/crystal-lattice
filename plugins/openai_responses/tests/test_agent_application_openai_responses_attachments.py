from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
OPENAI_RESPONSES_SRC = ROOT / "plugins/openai_responses/src"
if str(OPENAI_RESPONSES_SRC) not in sys.path:
    sys.path.insert(0, str(OPENAI_RESPONSES_SRC))

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from agent_core import Session  # noqa: E402


def _vision_model() -> str:
    return os.getenv("OPENAI_RESPONSES_VISION_MODEL") or "gpt-5-mini"


def _make_config(tmp_path: Path, api_key: str) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "openai_responses": {
                "provider": "openai_responses",
                "model": _vision_model(),
                "api_key": api_key,
                "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
                "timeout": 120,
                "attachment_upload_mode": "upload_before_send",
            }
        },
        "plugins": [
            "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider",
            "openai_responses_plugins.openai_responses_attachments_extension.OpenAIResponsesAttachmentsExtension",
        ],
        "agents": {"default": {"provider": "openai_responses"}},
    }
    path = tmp_path / "config_openai_responses_agent_application_attachments.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _generate_red_square_png(tmp_path: Path) -> Path:
    image_path = tmp_path / "app-asset-red-square.png"
    try:
        subprocess.run(
            [
                "magick",
                "-size",
                "96x96",
                "xc:red",
                str(image_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        pytest.skip("magick not available; skipping AgentApplication attachment test")
    except subprocess.CalledProcessError as exc:
        pytest.fail(f"failed to generate AgentApplication image fixture: {exc.stderr.strip()}")

    if not image_path.exists():
        pytest.fail("ImageMagick did not create the expected AgentApplication image fixture")
    return image_path


def _run_request(
    app: AgentApplication,
    core: Any,
    session: Session,
    base_config: Dict[str, Any],
) -> tuple[Session, List[Dict[str, Any]]]:
    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    assert checkpoints, "expected at least one session checkpoint"
    final_session = checkpoints[-1]["session"]
    assert isinstance(final_session, Session)
    return final_session, events


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI AgentApplication attachment tests")
    return api_key


@pytest.mark.integration
@pytest.mark.openai
def test_agent_application_store_attachment_then_send_asset_ref_real_api(
    tmp_path: Path,
    ensure_openai_api_key: str,
) -> None:
    config_path = _make_config(tmp_path, ensure_openai_api_key)
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )

    core, base_config, session = app.create_session("default")
    image_path = _generate_red_square_png(tmp_path)
    image_base64 = base64.b64encode(image_path.read_bytes()).decode("ascii")

    store_result = app.execute_session_action(
        "openai_responses_attachments",
        "store_attachment",
        {
            "session_id": session.session_id,
            "client_attachment_id": "draft_agent_app_image",
            "attachment_type": "image",
            "filename": image_path.name,
            "mime_type": "image/png",
            "data_base64": image_base64,
        },
    )

    asset = store_result["attachment_asset"]
    stored_record = app.get_session_asset_store().load(session.session_id, asset["asset_ref"]["asset_id"])
    assert stored_record.provider_refs["openai_responses"]["status"] == "not_uploaded"

    loaded = app.load_session(session.session_id)
    assert loaded is not None
    core, base_config, session = loaded

    effective_config = app.resolve_effective_config(base_config, session)
    session = core.add_message(
        session,
        "user",
        (
            "Reply with exactly AGENT_APP_ASSET_OK if the stored attachment is a solid red "
            "square image. Otherwise reply with exactly AGENT_APP_ASSET_FAIL."
        ),
        config=effective_config,
        multipart_content=[
            {
                "type": "image",
                "content": {
                    "asset_ref": asset["asset_ref"],
                    "filename": asset["filename"],
                    "mime_type": asset["mime_type"],
                },
                "metadata": {},
            }
        ],
    )
    app.save_session(session)

    final_session, events = _run_request(app, core, session, base_config)

    assistants = [message for message in final_session.messages if message.role == "assistant"]
    assert assistants
    assert "AGENT_APP_ASSET_OK" in assistants[-1].content
    assert any(ev.get("type") == "final" for ev in events)

    updated_record = app.get_session_asset_store().load(session.session_id, asset["asset_ref"]["asset_id"])
    assert isinstance(updated_record.provider_refs["openai_responses"]["file_id"], str)