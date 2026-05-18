from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .export_utils import (
    PDF_ENGINE_AUTO,
    build_message_export_context,
    convert_markdown_to_epub,
    convert_markdown_to_pdf,
    ensure_suffix,
    normalize_pdf_engine,
    render_message_markdown,
    slugify_filename_stem,
    temp_output_path,
)
from .smtp import send_icloud_attachment

if TYPE_CHECKING:  # pragma: no cover
    from agent_app.application_future import AgentApplication


def _error(message: str) -> Dict[str, Any]:
    return {"status": "error", "message": message}


def _load_session_message(
    app: "AgentApplication",
    *,
    session_id: str,
    message_index: int,
) -> tuple[Any, Dict[str, Any], Any, Any]:
    loaded = app.load_session(session_id)
    if loaded is None:
        raise KeyError(f"Session {session_id!r} not found")
    _core, base_config, session = loaded
    messages = list(getattr(session, "messages", []) or [])
    if message_index < 0 or message_index >= len(messages):
        raise IndexError(
            f"Message index {message_index} is out of range for session {session_id!r}"
        )
    effective_config = app.resolve_effective_config(base_config, session)
    return session, effective_config, messages[message_index], base_config


def _kindle_config(effective_config: Dict[str, Any]) -> tuple[str, str, str, str]:
    smtp_user = str(effective_config.get("send_to_kindle_smtp_user") or "").strip()
    from_addr = str(
        effective_config.get("send_to_kindle_from_addr") or smtp_user
    ).strip()
    to_addr = str(effective_config.get("send_to_kindle_default_to") or "").strip()
    keychain_service = str(
        effective_config.get("send_to_kindle_keychain_service") or "kindle-smtp"
    ).strip()
    if not smtp_user:
        raise RuntimeError("Missing config: send_to_kindle_smtp_user")
    if not from_addr:
        raise RuntimeError("Missing config: send_to_kindle_from_addr")
    if not to_addr:
        raise RuntimeError("Missing config: send_to_kindle_default_to")
    if not keychain_service:
        raise RuntimeError("Missing config: send_to_kindle_keychain_service")
    return smtp_user, from_addr, to_addr, keychain_service


class MessageSendToKindleAppPlugin:
    name = "message_send_to_kindle"
    version = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        _ = app_config
        return {}

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = state, config, tags, models
        return [
            {
                "ui_type": "message_action",
                "id": "message_send_to_kindle",
                "label": "Send to Kindle",
                "icon": "book-open",
                "action_id": "send_to_kindle",
                "param_map": {
                    "session_id": "$session.session_id",
                    "message_index": "$message.index",
                    "title": "$dialog.title",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Send to Kindle",
                    "message": "Choose a title for the exported EPUB.",
                    "inputs": [
                        {
                            "name": "title",
                            "type": "string",
                            "label": "Title",
                            "required": True,
                            "placeholder": "Export title",
                        }
                    ],
                },
            }
        ]

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "send_to_kindle",
                "label": "Send to Kindle",
                "description": "Export one message as EPUB and send it through the configured Kindle email path.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "message_index": {"type": "integer", "required": True},
                    "title": {"type": "string", "required": True},
                },
            }
        ]

    def execute_action(
        self,
        app: "AgentApplication",
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = context, state
        if action_id != "send_to_kindle":
            return _error(f"Unknown action_id {action_id!r}")

        session_id = str(params.get("session_id") or "")
        message_index = params.get("message_index")
        title = str(params.get("title") or "").strip()
        if not session_id or not isinstance(message_index, int) or not title:
            return _error("Missing required Kindle export parameters.")

        try:
            _session, effective_config, message, _base_config = _load_session_message(
                app,
                session_id=session_id,
                message_index=message_index,
            )
            export_context = build_message_export_context(
                session_id=session_id,
                message_index=message_index,
                message=message,
            )
            markdown_text = render_message_markdown(export_context, title=title)
            filename = f"{slugify_filename_stem(title, fallback=export_context.default_filename_stem)}.epub"
            output_path = temp_output_path(filename=filename)
            convert_markdown_to_epub(
                markdown_text=markdown_text,
                title=title,
                output_path=output_path,
            )
            smtp_user, from_addr, to_addr, keychain_service = _kindle_config(effective_config)
            send_icloud_attachment(
                smtp_user=smtp_user,
                from_addr=from_addr,
                to_addr=to_addr,
                subject=title,
                body=f"Exported from session {session_id}, message {message_index}.",
                attachment_path=output_path,
                keychain_service=keychain_service,
            )
        except Exception as exc:
            return _error(str(exc))
        finally:
            if "output_path" in locals():
                try:
                    output_path.unlink(missing_ok=True)
                    output_path.parent.rmdir()
                except Exception:
                    pass

        return {
            "status": "ok",
            "message": f"Sent {filename} to {to_addr}.",
            "display": {
                "format": "text",
                "title": "Sent to Kindle",
                "body": f"Sent {filename} to {to_addr}.",
                "variant": "success",
                "presentation": "banner",
                "dismissible": True,
            },
        }


class MessageShareAsPdfAppPlugin:
    name = "message_share_as_pdf"
    version = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        _ = app_config
        return {}

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = state, config, tags, models
        return [
            {
                "ui_type": "message_action",
                "id": "message_share_as_pdf",
                "label": "Share as PDF",
                "icon": "share-2",
                "action_id": "share_as_pdf",
                "param_map": {
                    "session_id": "$session.session_id",
                    "message_index": "$message.index",
                    "title": "$dialog.title",
                    "filename": "$dialog.filename",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Share as PDF",
                    "message": "Optionally customize the document title and filename.",
                    "inputs": [
                        {
                            "name": "title",
                            "type": "string",
                            "label": "Title",
                            "required": False,
                            "submit_empty": True,
                            "placeholder": "Optional document title",
                        },
                        {
                            "name": "filename",
                            "type": "string",
                            "label": "Filename",
                            "required": False,
                            "submit_empty": True,
                            "placeholder": "Optional filename",
                        },
                    ],
                },
            }
        ]

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "share_as_pdf",
                "label": "Share as PDF",
                "description": "Export one message as PDF and return a follow-up action for save/share.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "message_index": {"type": "integer", "required": True},
                    "title": {"type": "string", "required": False, "default": ""},
                    "filename": {"type": "string", "required": False, "default": ""},
                },
            },
            {
                "id": "download_attachment",
                "label": "Download generated PDF",
                "description": "Download a generated PDF stored as a session asset.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "asset_id": {"type": "string", "required": True},
                },
            },
        ]

    def execute_action(
        self,
        app: "AgentApplication",
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = context, state
        if action_id == "download_attachment":
            session_id = str(params.get("session_id") or "")
            asset_id = str(params.get("asset_id") or "")
            if not session_id or not asset_id:
                return _error("Missing required download parameters.")
            try:
                asset_store = app.get_session_asset_store()
                record = asset_store.load(session_id, asset_id)
                payload = asset_store.load_bytes(session_id, asset_id)
            except Exception as exc:
                return _error(str(exc))
            return {
                "status": "ok",
                "attachment_asset": record.public_descriptor(),
                "data_base64": base64.b64encode(payload).decode("ascii"),
                "message": f"Downloaded attachment {asset_id}",
            }
        if action_id != "share_as_pdf":
            return _error(f"Unknown action_id {action_id!r}")

        session_id = str(params.get("session_id") or "")
        message_index = params.get("message_index")
        raw_title = str(params.get("title") or "").strip()
        raw_filename = str(params.get("filename") or "").strip()
        if not session_id or not isinstance(message_index, int):
            return _error("Missing required PDF export parameters.")

        try:
            _session, effective_config, message, _base_config = _load_session_message(
                app,
                session_id=session_id,
                message_index=message_index,
            )
            export_context = build_message_export_context(
                session_id=session_id,
                message_index=message_index,
                message=message,
            )
            title = raw_title or export_context.default_title
            if raw_filename:
                filename = ensure_suffix(raw_filename, ".pdf")
            elif raw_title:
                filename = ensure_suffix(
                    slugify_filename_stem(
                        raw_title,
                        fallback=export_context.default_filename_stem,
                    ),
                    ".pdf",
                )
            else:
                filename = f"{export_context.default_filename_stem}.pdf"

            markdown_text = render_message_markdown(export_context, title=title)
            output_path = temp_output_path(filename=filename)
            engine_used = convert_markdown_to_pdf(
                markdown_text=markdown_text,
                title=title,
                output_path=output_path,
                engine_setting=normalize_pdf_engine(
                    effective_config.get("message_export_pdf_engine", PDF_ENGINE_AUTO)
                ),
            )
            record = app.get_session_asset_store().store_base64(
                session_id=session_id,
                attachment_type="pdf",
                filename=filename,
                mime_type="application/pdf",
                data_base64=base64.b64encode(output_path.read_bytes()).decode("ascii"),
                metadata={"generated_by": self.name, "message_index": message_index},
            )
        except Exception as exc:
            return _error(str(exc))
        finally:
            if "output_path" in locals():
                try:
                    output_path.unlink(missing_ok=True)
                    output_path.parent.rmdir()
                except Exception:
                    pass

        return {
            "status": "ok",
            "attachment_asset": record.public_descriptor(),
            "engine": engine_used,
            "display": {
                "format": "text",
                "title": "PDF ready",
                "body": f"Generated {filename} from message {message_index} using {engine_used}.",
                "variant": "success",
                "presentation": "modal",
                "dismissible": True,
                "actions": [
                    {
                        "kind": "download_attachment_asset",
                        "id": "open_generated_pdf",
                        "label": "Open PDF",
                        "session_id": session_id,
                        "asset_id": record.asset_id,
                        "filename": filename,
                        "mime_type": "application/pdf",
                        "plugin": self.name,
                        "action_owner": "application",
                        "behavior": "platform_default",
                    }
                ],
            },
        }


__all__ = [
    "MessageSendToKindleAppPlugin",
    "MessageShareAsPdfAppPlugin",
]