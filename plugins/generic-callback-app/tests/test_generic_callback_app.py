from __future__ import annotations

import pytest

from generic_callback_app import GenericCallbackAppPlugin


def test_start_external_flow_returns_copy_link_display() -> None:
    plugin = GenericCallbackAppPlugin()

    result = plugin.execute_action(
        None,
        "start_external_flow",
        {
            "connection_id": "test-connection",
            "result": "approved",
            "nonce": "n-123",
        },
        {"session_id": "session-123"},
        {},
    )

    expected_url = (
        "crystal-lattice://action/test-connection/session-123/"
        "complete_external_flow?result=approved&nonce=n-123"
    )
    assert result["callback_url"] == expected_url
    display = result["display"]
    assert display["display_id"] == "generic-callback-flow"
    copy_action = display["actions"][0]
    assert copy_action == {
        "kind": "copy_text",
        "id": "copy-generic-callback-link",
        "label": "Copy link",
        "text": expected_url,
        "copied_label": "Copied",
    }


def test_start_external_flow_can_include_plugin_id() -> None:
    plugin = GenericCallbackAppPlugin()

    result = plugin.execute_action(
        None,
        "start_external_flow",
        {
            "connection_id": "test-connection",
            "include_plugin_id": True,
        },
        {"session_id": "session-123"},
        {},
    )

    assert result["callback_url"] == (
        "crystal-lattice://action/test-connection/session-123/"
        "generic_callback_app/complete_external_flow?result=approved&nonce=n-123"
    )


def test_start_external_flow_requires_connection_id() -> None:
    plugin = GenericCallbackAppPlugin()

    with pytest.raises(ValueError, match="connection_id"):
        plugin.execute_action(
            None,
            "start_external_flow",
            {},
            {"session_id": "session-123"},
            {},
        )


def test_complete_external_flow_echoes_inputs_and_session_context() -> None:
    plugin = GenericCallbackAppPlugin()

    result = plugin.execute_action(
        None,
        "complete_external_flow",
        {
            "result": "approved",
            "nonce": "n-123",
            "redirect_url": "crystal-lattice://action/test-connection/session-123/complete_external_flow?result=approved&nonce=n-123",
        },
        {"session_id": "session-123"},
        {},
    )

    assert result == {
        "message": "Generic action complete",
        "handled": True,
        "action": "complete_external_flow",
        "inputs": {
            "result": "approved",
            "nonce": "n-123",
            "redirect_url": "crystal-lattice://action/test-connection/session-123/complete_external_flow?result=approved&nonce=n-123",
        },
        "context": {"session_id": "session-123"},
    }
