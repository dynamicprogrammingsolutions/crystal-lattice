from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest


ROOT = Path(__file__).resolve().parents[3]
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
SRC = ROOT / "plugins/message-export-actions/src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from message_export_actions import (  # noqa: E402
    MessageShareAsPdfAppPlugin,
    MessageSendToKindleAppPlugin,
)
from message_export_actions import export_utils  # noqa: E402
import message_export_actions as plugin_module  # noqa: E402


def _config_path(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            {"path": str(ROOT / "plugins" / "message-export-actions")},
        ],
        "agents": {
            "default": {
                "provider": "echo",
                "send_to_kindle_smtp_user": "tester@icloud.com",
                "send_to_kindle_from_addr": "tester@icloud.com",
                "send_to_kindle_default_to": "reader@kindle.com",
                "send_to_kindle_keychain_service": "kindle-smtp",
                "message_export_pdf_engine": "xhtml2pdf",
            }
        },
        "application": {"session_title_metadata_key": "title"},
    }
    path = tmp_path / "config_message_export_actions.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    return AgentApplication(
        str(_config_path(tmp_path)),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )


def _seed_session_with_message(app: AgentApplication, *, content: str) -> tuple[str, int]:
    core, base_config, session = app.create_session("default")
    updated = core.add_message(
        session,
        "assistant",
        content,
        config=app.resolve_effective_config(base_config, session),
    )
    app.save_session(updated)
    return updated.session_id, len(updated.messages) - 1


def _seed_session_with_messages(app: AgentApplication) -> str:
    core, base_config, session = app.create_session("default")
    session = core.add_message(
        session,
        "system",
        "System content should not be exported.",
        config=app.resolve_effective_config(base_config, session),
    )
    session = core.add_message(
        session,
        "user",
        "# User heading\nUser body",
        config=app.resolve_effective_config(base_config, session),
    )
    session = core.add_message(
        session,
        "tool",
        "Tool content should not be exported.",
        config=app.resolve_effective_config(base_config, session),
    )
    session = core.add_message(
        session,
        "assistant",
        "## Assistant heading\nAssistant body",
        config=app.resolve_effective_config(base_config, session),
    )
    session = core.add_message(
        session,
        "assistant",
        "",
        config=app.resolve_effective_config(base_config, session),
    )
    metadata = dict(session.metadata or {})
    metadata["title"] = "Project planning"
    session = type(session)(
        session_id=session.session_id,
        messages=session.messages,
        metadata=metadata,
    )
    app.save_session(session)
    return session.session_id


def test_ui_schema_exposes_message_and_session_actions(tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    session_id, _message_index = _seed_session_with_message(app, content="Hello export")

    loaded = app.load_session(session_id)
    assert loaded is not None
    _core, base_config, session = loaded
    effective_config = app.resolve_effective_config(base_config, session)

    elements = app.get_application_ui_schema(config=effective_config)
    message_actions = {
        (el["plugin"], el["action_id"])
        for el in elements
        if el.get("ui_type") == "message_action"
    }

    assert ("message_send_to_kindle", "send_to_kindle") in message_actions
    assert ("message_share_as_pdf", "share_as_pdf") in message_actions
    session_actions = {
        (el["plugin"], el["action_id"])
        for el in elements
        if el.get("ui_type") == "session_action"
    }
    assert ("message_send_to_kindle", "send_session_to_kindle") in session_actions
    assert ("message_share_as_pdf", "share_session_as_pdf") in session_actions


def test_send_to_kindle_uses_optional_title_default_and_bashlike_epub_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _build_app(tmp_path)
    session_id, message_index = _seed_session_with_message(app, content="Kindle export body")

    sent: Dict[str, Any] = {}

    def _fake_convert_markdown_to_epub(
        *,
        markdown_text: str,
        title: str,
        output_path: Path,
        author: str | None = None,
        language: str = "",
        toc_depth: int = 0,
        lua_filter: Path | None = None,
    ) -> None:
        sent["markdown_text"] = markdown_text
        sent["title"] = title
        sent["language"] = language
        sent["toc_depth"] = toc_depth
        sent["lua_filter"] = lua_filter
        sent["author"] = author
        output_path.write_bytes(b"dummy-epub")

    def _fake_send_icloud_attachment(**kwargs: Any) -> None:
        sent.update(kwargs)

    monkeypatch.setattr(plugin_module, "convert_markdown_to_epub", _fake_convert_markdown_to_epub)
    monkeypatch.setattr(plugin_module, "send_icloud_attachment", _fake_send_icloud_attachment)

    result = app.execute_action(
        "message_send_to_kindle",
        "send_to_kindle",
        {
            "session_id": session_id,
            "message_index": message_index,
            "title": "",
        },
        action_owner="application",
    )

    assert result["status"] == "ok"
    assert sent["subject"] == f"Session {session_id[:8]} Message {message_index}"
    assert sent["to_addr"] == "reader@kindle.com"
    assert sent["attachment_path"].name == f"session-{session_id[:8]}-message-{message_index}.epub"
    assert "Kindle export body" in sent["markdown_text"]
    assert sent["language"] == "en-US"
    assert sent["toc_depth"] == 2
    assert isinstance(sent["lua_filter"], Path)
    assert sent["lua_filter"].name == "strip_local_file_references.lua"
    assert sent["author"] is None


def test_send_to_kindle_allows_recipient_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _build_app(tmp_path)
    session_id, message_index = _seed_session_with_message(app, content="Kindle export body")

    sent: Dict[str, Any] = {}

    def _fake_convert_markdown_to_epub(**kwargs: Any) -> None:
        kwargs["output_path"].write_bytes(b"dummy-epub")

    monkeypatch.setattr(plugin_module, "convert_markdown_to_epub", _fake_convert_markdown_to_epub)
    monkeypatch.setattr(plugin_module, "send_icloud_attachment", lambda **kwargs: sent.update(kwargs))

    result = app.execute_action(
        "message_send_to_kindle",
        "send_to_kindle",
        {
            "session_id": session_id,
            "message_index": message_index,
            "title": "",
            "to": "override@example.com",
        },
        action_owner="application",
    )

    assert result["status"] == "ok"
    assert sent["to_addr"] == "override@example.com"
    assert "override@example.com" in result["message"]


def test_send_session_to_kindle_filters_roles_and_demotes_headings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _build_app(tmp_path)
    session_id = _seed_session_with_messages(app)

    sent: Dict[str, Any] = {}

    def _fake_convert_markdown_to_epub(**kwargs: Any) -> None:
        sent.update(kwargs)
        output_path = kwargs["output_path"]
        output_path.write_bytes(b"dummy-epub")

    monkeypatch.setattr(plugin_module, "convert_markdown_to_epub", _fake_convert_markdown_to_epub)
    monkeypatch.setattr(plugin_module, "send_icloud_attachment", lambda **kwargs: sent.update(kwargs))

    result = app.execute_action(
        "message_send_to_kindle",
        "send_session_to_kindle",
        {"session_id": session_id, "title": ""},
        action_owner="application",
    )

    assert result["status"] == "ok"
    markdown_text = sent["markdown_text"]
    assert markdown_text.startswith(f"# {session_id} - Project planning")
    assert "## User message 1" in markdown_text
    assert "## Assistant message 3" in markdown_text
    assert "System content should not be exported." not in markdown_text
    assert "Tool content should not be exported." not in markdown_text
    assert "### User heading" in markdown_text
    assert "#### Assistant heading" in markdown_text
    assert sent["attachment_path"].name == "project-planning.epub"


def test_share_as_pdf_returns_download_followup_and_downloads_asset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _build_app(tmp_path)
    session_id, message_index = _seed_session_with_message(app, content="PDF export body")

    def _fake_convert_markdown_to_pdf(
        *,
        markdown_text: str,
        title: str,
        output_path: Path,
        engine_setting: str,
    ) -> str:
        assert engine_setting == "xhtml2pdf"
        assert "PDF export body" in markdown_text
        assert title == "Session PDF"
        output_path.write_bytes(b"%PDF-1.4\nmock pdf\n")
        return "xhtml2pdf"

    monkeypatch.setattr(plugin_module, "convert_markdown_to_pdf", _fake_convert_markdown_to_pdf)

    result = app.execute_action(
        "message_share_as_pdf",
        "share_as_pdf",
        {
            "session_id": session_id,
            "message_index": message_index,
            "title": "Session PDF",
            "filename": "",
        },
        action_owner="application",
    )

    assert result["status"] == "ok"
    display = result["display"]
    followup = display["actions"][0]
    assert followup["kind"] == "download_attachment_asset"
    assert followup["plugin"] == "message_share_as_pdf"
    assert followup["filename"] == "session-pdf.pdf"

    attachment_asset = result["attachment_asset"]
    asset_id = attachment_asset["asset_ref"]["asset_id"]

    download = app.execute_action(
        "message_share_as_pdf",
        "download_attachment",
        {"session_id": session_id, "asset_id": asset_id},
        action_owner="application",
    )

    assert download["status"] == "ok"
    assert base64.b64decode(download["data_base64"]) == b"%PDF-1.4\nmock pdf\n"


def test_share_session_as_pdf_uses_session_title_and_default_filename(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _build_app(tmp_path)
    session_id = _seed_session_with_messages(app)

    seen: Dict[str, Any] = {}

    def _fake_convert_markdown_to_pdf(
        *,
        markdown_text: str,
        title: str,
        output_path: Path,
        engine_setting: str,
    ) -> str:
        seen["markdown_text"] = markdown_text
        seen["title"] = title
        seen["engine_setting"] = engine_setting
        output_path.write_bytes(b"%PDF-1.4\nmock pdf\n")
        return "xhtml2pdf"

    monkeypatch.setattr(plugin_module, "convert_markdown_to_pdf", _fake_convert_markdown_to_pdf)

    result = app.execute_action(
        "message_share_as_pdf",
        "share_session_as_pdf",
        {"session_id": session_id, "title": "", "filename": ""},
        action_owner="application",
    )

    assert result["status"] == "ok"
    assert seen["title"] == "Project planning"
    assert seen["engine_setting"] == "xhtml2pdf"
    assert seen["markdown_text"].startswith(f"# {session_id} - Project planning")
    followup = result["display"]["actions"][0]
    assert followup["filename"] == f"session-{session_id[:8]}.pdf"


def test_select_pdf_runtime_engine_prefers_xhtml2pdf_when_pandoc_pdf_path_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_which(name: str) -> str | None:
        if name == "pandoc":
            return "/usr/local/bin/pandoc"
        return None

    monkeypatch.setattr(export_utils.shutil, "which", _fake_which)

    runtime_engine, pandoc_engine = export_utils.select_pdf_runtime_engine("auto")

    assert runtime_engine == "xhtml2pdf"
    assert pandoc_engine is None


def test_plugin_classes_keep_expected_ids() -> None:
    assert MessageSendToKindleAppPlugin.name == "message_send_to_kindle"
    assert MessageShareAsPdfAppPlugin.name == "message_share_as_pdf"


def test_demote_markdown_headings_starts_message_headings_at_h3() -> None:
    rendered = export_utils.demote_markdown_headings("# One\n## Two\n### Three", base_level=3)
    assert rendered == "### One\n#### Two\n##### Three"