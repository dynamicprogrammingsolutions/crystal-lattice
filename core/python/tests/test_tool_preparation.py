from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from agent_app.application_future import AgentApplication
from agent_core import AgentCore


class PreparedCatalogTool:
    name = "prepared_catalog_tool"
    version = "1.0.0"

    prepare_calls = 0

    @classmethod
    def reset(cls) -> None:
        cls.prepare_calls = 0

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def prepare(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        type(self).prepare_calls += 1
        return {
            "runtime_key": "sync-runtime",
            "preview": "prepared preview",
            "schemas": [
                {
                    "type": "function",
                    "function": {
                        "name": "prepared_echo",
                        "description": "Echo prepared runtime metadata",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                        },
                    },
                }
            ],
        }

    def get_tool_schemas(
        self,
        state: Dict[str, Any],
        *,
        prepared: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        return list((prepared or {}).get("schemas") or [])

    def format_tool_call_preview(
        self,
        tool_name: str | None,
        payload: Any,
        state: Dict[str, Any],
        *,
        prepared: Dict[str, Any] | None = None,
        **_kwargs: Any,
    ) -> str:
        return str((prepared or {}).get("preview") or "")

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: Dict[str, Any],
        *,
        context: Dict[str, Any] | None = None,
        prepared: Dict[str, Any] | None = None,
        **_kwargs: Any,
    ) -> Dict[str, Any]:
        runtime_key = str((prepared or {}).get("runtime_key") or "missing")
        trigger_source = str((context or {}).get("trigger_source") or "unknown")
        return {"success": True, "result": f"{runtime_key}:{trigger_source}"}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return f"Result: {result.get('result')}"


class AsyncPreparedCatalogTool:
    name = "async_prepared_catalog_tool"
    version = "1.0.0"

    prepare_async_calls = 0

    @classmethod
    def reset(cls) -> None:
        cls.prepare_async_calls = 0

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    async def prepare_async(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        type(self).prepare_async_calls += 1
        return {
            "schemas": [
                {
                    "type": "function",
                    "function": {
                        "name": "async_prepared_echo",
                        "description": "Schema discovered asynchronously",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                        },
                    },
                }
            ]
        }

    def get_tool_schemas(
        self,
        state: Dict[str, Any],
        *,
        prepared: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        return list((prepared or {}).get("schemas") or [])


class ApplicationPreparedTool:
    name = "application_prepared_tool"
    version = "1.0.0"

    prepare_calls = 0
    last_context: Dict[str, Any] | None = None

    @classmethod
    def reset(cls) -> None:
        cls.prepare_calls = 0
        cls.last_context = None

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def prepare(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        type(self).prepare_calls += 1
        type(self).last_context = dict(context or {})
        return {
            "schemas": [
                {
                    "type": "function",
                    "function": {
                        "name": "application_prepared_echo",
                        "description": "Prepared in application request flow",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                        },
                    },
                }
            ]
        }

    def get_tool_schemas(
        self,
        state: Dict[str, Any],
        *,
        prepared: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        return list((prepared or {}).get("schemas") or [])

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: Dict[str, Any],
        **_kwargs: Any,
    ) -> Dict[str, Any]:
        return {"success": True, "result": tool_name}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return str(result.get("result") or "")


def _tool_call(name: str) -> Dict[str, Any]:
    return {
        "id": "call-1",
        "type": "function",
        "function": {
            "name": name,
            "arguments": {},
        },
    }


def _write_config(tmp_path: Path, config: Dict[str, Any], name: str) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def test_prepare_tools_populates_sync_discovery_and_execution() -> None:
    PreparedCatalogTool.reset()
    core = AgentCore()
    core.register_tool(PreparedCatalogTool)

    assert core.get_available_tools({}) == []
    assert core.format_tool_call_preview(_tool_call("prepared_echo"), {}) == {
        "id": "call-1",
        "preview": "",
    }

    core.prepare_tools({})

    descriptors = core.get_available_tools({})
    assert [descriptor.tool_name for descriptor in descriptors] == ["prepared_echo"]
    assert PreparedCatalogTool.prepare_calls == 1
    assert core.format_tool_call_preview(_tool_call("prepared_echo"), {}) == {
        "id": "call-1",
        "preview": "prepared preview",
    }

    results = core.execute_tool_calls([_tool_call("prepared_echo")], {})
    assert results == [
        {
            "role": "tool",
            "content": "Result: sync-runtime:core",
            "metadata": {
                "tool_call_id": "call-1",
                "tool_name": "prepared_echo",
                "tool_schema": descriptors[0].schema,
                "tool_plugin": "prepared_catalog_tool",
                "display": {"type": "text", "content": "Result: sync-runtime:core"},
            },
            "toolResult": {"type": "tool_result", "text": "Result: sync-runtime:core"},
        }
    ]


def test_get_available_tools_does_not_trigger_prepare_implicitly() -> None:
    PreparedCatalogTool.reset()
    core = AgentCore()
    core.register_tool(PreparedCatalogTool)

    assert core.get_tool_schemas({}) == []
    assert PreparedCatalogTool.prepare_calls == 0


def test_prepare_tools_blocks_on_async_prepare_hook() -> None:
    AsyncPreparedCatalogTool.reset()
    core = AgentCore()
    core.register_tool(AsyncPreparedCatalogTool)

    core.prepare_tools({})

    descriptors = core.get_available_tools({})
    assert [descriptor.tool_name for descriptor in descriptors] == ["async_prepared_echo"]
    assert AsyncPreparedCatalogTool.prepare_async_calls == 1


def test_application_send_request_prepares_tools_with_application_context(
    tmp_path: Path,
) -> None:
    ApplicationPreparedTool.reset()
    config = {
        "plugin_cache_dir": str(tmp_path / ".plugin-cache"),
        "providers": {
            "primary": {
                "provider": "dummy_provider",
                "model": "test-model",
            }
        },
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.test_tool_preparation.ApplicationPreparedTool",
        ],
        "agents": {
            "alpha": {
                "provider": "primary",
            }
        },
    }
    config_path = _write_config(tmp_path, config, "config_tool_prepare.json")
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
    )

    core, base_config, session = app.create_session("alpha")
    session = core.add_message(session, "user", "hello")
    app.save_session(session)

    events = list(app.send_request(core, session, base_config, stream=False))

    assert events
    assert ApplicationPreparedTool.prepare_calls == 1
    assert isinstance(ApplicationPreparedTool.last_context, dict)
    assert ApplicationPreparedTool.last_context["trigger_source"] == "application"
    assert ApplicationPreparedTool.last_context["runtime_store"] is app.get_runtime_store()
    assert ApplicationPreparedTool.last_context["tool_runtime"] is app.get_tool_runtime()
    assert ApplicationPreparedTool.last_context["session"]["session_id"] == session.session_id
    assert isinstance(ApplicationPreparedTool.last_context["request_id"], str)