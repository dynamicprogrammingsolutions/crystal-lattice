from __future__ import annotations

import pytest

from manual_mcp_oauth_flow import DEFAULT_SCENARIO, build_parser


pytestmark = [pytest.mark.integration, pytest.mark.manual_integration]


def test_manual_oauth_default_scenario_is_available() -> None:
    """Guard the convenient manual flow defaults without contacting a provider."""

    parser = build_parser()
    args = parser.parse_args(["start"])
    assert args.config == DEFAULT_SCENARIO
    assert args.config.exists()


def test_manual_oauth_script_accepts_convenient_commands() -> None:
    parser = build_parser()

    start = parser.parse_args(["start"])
    finish = parser.parse_args(["finish"])
    verify = parser.parse_args(["verify"])

    assert start.command == "start"
    assert finish.command == "finish"
    assert verify.command == "verify"