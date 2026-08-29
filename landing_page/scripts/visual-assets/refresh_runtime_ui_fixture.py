from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

DROP_CONFIG_KEYS = {
    "api_key",
    "chatgpt_account_id",
    "chatgpt_credentials_path",
    "credentials",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--session-fixture", required=True)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--candidate", required=True)
    return parser.parse_args()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prepare_imports(repository_root: Path) -> None:
    source_roots = [
        repository_root / "core/python",
        repository_root / "plugins/feature-request-options/src",
        repository_root / "plugins/session-actions-app/src",
        repository_root / "plugins/session-title-app/src",
        repository_root / "plugins/generate-title-app/src",
        repository_root / "plugins/summarize-range-app/src",
        repository_root / "plugins/openai_responses/src",
    ]
    for source_root in reversed(source_roots):
        value = str(source_root)
        if value not in sys.path:
            sys.path.insert(0, value)


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _sanitize(item)
            for key, item in value.items()
            if key.lower() not in DROP_CONFIG_KEYS
        }
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value


def build_runtime_ui_fixture(
    *,
    repository_root: Path,
    config_path: Path,
    session_fixture_path: Path,
    agent_id: str,
) -> dict[str, Any]:
    _prepare_imports(repository_root)

    from agent_app.application_future import AgentApplication
    from agent_app.config import resolve_request_config
    from agent_core import Message, Session
    from openai_responses_plugins.openai_responses_provider import (
        OpenAIResponsesProvider,
    )

    config = json.loads(config_path.read_text(encoding="utf-8"))
    visual_fixture = config.get("visual_fixture")
    if not isinstance(visual_fixture, dict):
        raise RuntimeError("visual_fixture config must be a mapping")
    model_catalog = visual_fixture.get("model_catalog")
    if not isinstance(model_catalog, list) or not model_catalog:
        raise RuntimeError("visual_fixture.model_catalog must be a non-empty list")
    session_overrides = visual_fixture.get("session_overrides")
    if not isinstance(session_overrides, dict):
        session_overrides = {}
    snapshots = visual_fixture.get("snapshots")
    if not isinstance(snapshots, list):
        raise RuntimeError("visual_fixture.snapshots must be a list")
    settings_keys = visual_fixture.get("settings_keys")
    if not isinstance(settings_keys, list) or not all(
        isinstance(key, str) and key for key in settings_keys
    ):
        raise RuntimeError(
            "visual_fixture.settings_keys must be a non-empty string list"
        )

    OpenAIResponsesProvider.get_models = lambda self, provider_config: list(
        model_catalog
    )

    reviewed = json.loads(session_fixture_path.read_text(encoding="utf-8"))
    raw_messages = reviewed.get("messages")
    if not isinstance(raw_messages, list) or not raw_messages:
        raise RuntimeError("reviewed session fixture must contain messages")
    assistant_messages = [
        item
        for item in raw_messages
        if isinstance(item, dict)
        and isinstance(item.get("message"), dict)
        and item["message"].get("role") == "assistant"
        and isinstance(item["message"].get("content"), str)
        and item["message"]["content"].strip()
    ]
    if not assistant_messages:
        raise RuntimeError(
            "reviewed session fixture must contain a completed assistant message"
        )
    user_messages = [
        item
        for item in raw_messages
        if isinstance(item, dict)
        and isinstance(item.get("message"), dict)
        and item["message"].get("role") == "user"
        and isinstance(item["message"].get("content"), str)
        and item["message"]["content"].strip()
    ]
    if not user_messages:
        raise RuntimeError("reviewed session fixture must contain a user request")
    usage_source = assistant_messages[-1]
    usage_message = {
        "index": usage_source.get("index"),
        "message": {
            **usage_source["message"],
            "content": "\n".join(
                usage_source["message"]["content"].splitlines()[:8]
            ).strip(),
        },
    }
    focused_fix_start = "### Focused backwards-compatible fix"
    focused_fix_end = "Keep it keyword-only."
    focused_fix_content = usage_source["message"]["content"]
    focused_fix_start_index = focused_fix_content.find(focused_fix_start)
    focused_fix_end_index = focused_fix_content.find(
        focused_fix_end,
        focused_fix_start_index,
    )
    if focused_fix_start_index < 0 or focused_fix_end_index < 0:
        raise RuntimeError(
            "reviewed assistant response is missing the expected focused-fix section"
        )
    mobile_hero_messages = [
        user_messages[0],
        {
            "index": usage_source.get("index"),
            "message": {
                **usage_source["message"],
                "metadata": {
                    key: value
                    for key, value in usage_source["message"]
                    .get(
                        "metadata",
                        {},
                    )
                    .items()
                    if key not in {"reasoning", "openai_responses_reasoning"}
                },
                "content": focused_fix_content[
                    focused_fix_start_index:focused_fix_end_index
                ].strip(),
            },
        },
    ]

    with tempfile.TemporaryDirectory(prefix="crystal-runtime-ui-") as raw_temp:
        runtime_root = Path(raw_temp)
        app = AgentApplication(
            str(config_path),
            str(runtime_root / "sessions"),
            env_overrides={
                "OPENAI_API_KEY": "website-runtime-fixture-not-used",
                "SESSION_RUNTIME_DIR": str(runtime_root),
                "CRYSTAL_PLUGIN_PYTHON": sys.executable,
            },
        )
        try:
            core, base_config, created = app.create_session(agent_id)
            messages = [
                Message.from_dict(item["message"])
                for item in raw_messages
                if isinstance(item, dict) and isinstance(item.get("message"), dict)
            ]
            session = Session(
                session_id=created.session_id,
                messages=messages,
                metadata={
                    **created.metadata,
                    "overrides": session_overrides,
                },
            )
            app.save_session(session)
            effective_config = resolve_request_config(
                base_config,
                session_overrides,
            )
            full_session_ui_schema = core.get_ui_schema(config=effective_config)
            session_application_ui_schema = app.get_session_application_ui_schema(
                session.session_id
            )
            session_config_schema = core.get_config_schema()
        finally:
            app.close()

    ui_by_key = {
        element.get("key"): element
        for element in full_session_ui_schema
        if isinstance(element, dict) and isinstance(element.get("key"), str)
    }
    message_footer_elements = [
        element
        for element in full_session_ui_schema
        if isinstance(element, dict) and element.get("ui_type") == "message_footer"
    ]
    schema_by_key = {
        element.get("key"): element
        for element in session_config_schema
        if isinstance(element, dict) and isinstance(element.get("key"), str)
    }
    missing_ui_keys = [key for key in settings_keys if key not in ui_by_key]
    if missing_ui_keys:
        raise RuntimeError(
            "Configured visual settings are missing from the runtime UI schema: "
            + ", ".join(missing_ui_keys)
        )
    session_ui_schema = [ui_by_key[key] for key in settings_keys]
    session_config_schema = [
        schema_by_key[key] for key in settings_keys if key in schema_by_key
    ]

    return {
        "schema_version": 1,
        "fixture_id": "mobile-workbench",
        "source": {
            "config_sha256": _sha256(config_path),
            "session_fixture_sha256": _sha256(session_fixture_path),
        },
        "session_ui_schema": _sanitize(session_ui_schema),
        "message_footer_elements": _sanitize(message_footer_elements),
        "mobile_hero_messages": _sanitize(mobile_hero_messages),
        "provider_usage_message": _sanitize(usage_message),
        "session_application_ui_schema": _sanitize(session_application_ui_schema),
        "session_config_schema": _sanitize(session_config_schema),
        "session_base_config": _sanitize(base_config),
        "session_overrides": _sanitize(session_overrides),
        "snapshots": _sanitize(snapshots),
    }


def main() -> int:
    args = _parse_args()
    repository_root = Path(args.repository_root).resolve()
    config_path = Path(args.config).resolve()
    session_fixture_path = Path(args.session_fixture).resolve()
    candidate_path = Path(args.candidate).resolve()
    candidate = build_runtime_ui_fixture(
        repository_root=repository_root,
        config_path=config_path,
        session_fixture_path=session_fixture_path,
        agent_id=args.agent,
    )
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(
        json.dumps(candidate, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
