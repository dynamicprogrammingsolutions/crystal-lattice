from __future__ import annotations

import json

import pytest

from manual_mcp_oauth_flow import DEFAULT_SCENARIO, build_parser


pytestmark = [pytest.mark.integration, pytest.mark.manual_integration]


def test_manual_oauth_default_scenario_is_available() -> None:
    """Guard the convenient manual flow defaults without contacting a provider."""

    parser = build_parser()
    args = parser.parse_args(["start"])
    assert args.config == DEFAULT_SCENARIO
    assert args.config.exists()

    scenario = json.loads(args.config.read_text(encoding="utf-8"))
    assert "mcp_oauth_manual" not in scenario
    assert "figma" in scenario["mcp_servers"]
    assert scenario["mcp_servers"]["figma"]["oauth"]["token_exchange"] == {
        "include_client_secret": True,
        "include_resource": True,
    }


def test_manual_oauth_script_accepts_convenient_commands() -> None:
    parser = build_parser()

    start = parser.parse_args(["start"])
    finish = parser.parse_args(["finish"])
    verify = parser.parse_args(["verify"])

    assert start.command == "start"
    assert finish.command == "finish"
    assert verify.command == "verify"


def test_manual_oauth_script_accepts_wrapper_only_inputs() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "finish",
            "--server",
            "figma",
            "--callback-port",
            "41793",
            "--callback-url",
            "http://localhost:41793/oauth/callback?code=a&state=b",
        ]
    )

    assert args.server == "figma"
    assert args.callback_port == 41793
    assert args.callback_url.endswith("code=a&state=b")