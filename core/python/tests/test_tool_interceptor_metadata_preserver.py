"""Unit tests for :class:`plugins.tool_interceptor_metadata_preserver.ToolInterceptorMetadataPreserver`."""

from __future__ import annotations

from typing import Any, Dict, List

from plugins.echo_provider_metadata_preserver import EchoProviderMetadataPreserver
from plugins.tool_interceptor_metadata_preserver import ToolInterceptorMetadataPreserver


def _chain_to_native(
    core_messages: List[Dict[str, Any]], native_seed: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    echo = EchoProviderMetadataPreserver()
    intercept = ToolInterceptorMetadataPreserver()
    after_echo = echo.to_native_messages(core_messages, native_seed)
    return intercept.to_native_messages(core_messages, after_echo)


def _chain_from_native(
    native_messages: List[Dict[str, Any]], core_seed: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    echo = EchoProviderMetadataPreserver()
    intercept = ToolInterceptorMetadataPreserver()
    after_echo = echo.from_native_messages(native_messages, core_seed)
    return intercept.from_native_messages(native_messages, after_echo)


def test_interceptor_metadata_survives_after_echo_preserver_to_native() -> None:
    core_messages = [
        {
            "role": "assistant",
            "content": "",
            "metadata": {
                "tool_calls": [{"id": "call_1", "type": "function"}],
                "interception_current": {
                    "phase": "tool_call",
                    "tool_call_id": "call_1",
                    "pending_prompt": {"id": "prompt_1", "title": "Confirm"},
                },
                "interception_phases": [{"entry_type": "prompt_response"}],
            },
        }
    ]
    native_seed = [{"role": "assistant", "content": ""}]
    out = _chain_to_native(core_messages, native_seed)
    md = out[0].get("_metadata") or {}
    assert md.get("tool_calls") == core_messages[0]["metadata"]["tool_calls"]
    assert md.get("interception_current") == core_messages[0]["metadata"][
        "interception_current"
    ]
    assert md.get("interception_phases") == core_messages[0]["metadata"][
        "interception_phases"
    ]


def test_interceptor_metadata_restored_after_echo_from_native() -> None:
    native_messages = [
        {
            "role": "assistant",
            "content": "",
            "_metadata": {
                "tool_calls": [{"id": "c1", "type": "function"}],
                "interception_current": {
                    "phase": "tool_call",
                    "answer": {"button_id": "allow"},
                },
                "interception_phases": [{"entry_type": "plugin_response"}],
            },
        }
    ]
    core_seed = [
        {"role": "assistant", "content": "", "metadata": {}}
    ]
    final = _chain_from_native(native_messages, core_seed)
    meta = final[0].get("metadata") or {}
    assert meta.get("tool_calls") == native_messages[0]["_metadata"]["tool_calls"]
    assert meta.get("interception_current") == native_messages[0]["_metadata"][
        "interception_current"
    ]
    assert meta.get("interception_phases") == native_messages[0]["_metadata"][
        "interception_phases"
    ]


def test_feature_sorts_after_echo_for_agent_core_ordering() -> None:
    echo_pri = getattr(EchoProviderMetadataPreserver, "priority", 100)
    int_pri = getattr(ToolInterceptorMetadataPreserver, "priority", 100)
    assert int_pri > echo_pri
