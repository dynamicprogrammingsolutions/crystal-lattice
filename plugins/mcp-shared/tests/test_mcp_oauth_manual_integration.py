from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest

from mcp_shared import build_mcp_oauth_login_request, render_oauth_redirect_uri


pytestmark = [pytest.mark.integration, pytest.mark.manual_integration]


def _load_scenario() -> dict[str, Any]:
    scenario_path = os.environ.get("MCP_OAUTH_MANUAL_SCENARIO")
    if not scenario_path:
        pytest.skip("MCP_OAUTH_MANUAL_SCENARIO is not set")
    path = Path(scenario_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return json.loads(path.read_text(encoding="utf-8"))


def _selected_variants(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    variants = scenario.get("redirect_matrix")
    if not isinstance(variants, list) or not variants:
        raise AssertionError("scenario redirect_matrix must be a non-empty list")
    selected = os.environ.get("MCP_OAUTH_MANUAL_VARIANT")
    if not selected:
        return [variant for variant in variants if isinstance(variant, dict)]
    return [
        variant
        for variant in variants
        if isinstance(variant, dict) and variant.get("id") == selected
    ]


def _merge_server_config(
    scenario: dict[str, Any],
    variant: dict[str, Any],
) -> dict[str, Any]:
    server = scenario.get("server")
    if not isinstance(server, dict):
        raise AssertionError("scenario server must be an object")
    config = deepcopy(server.get("config"))
    if not isinstance(config, dict):
        raise AssertionError("scenario server.config must be an object")
    oauth = dict(config.get("oauth") if isinstance(config.get("oauth"), dict) else {})
    variant_oauth = variant.get("oauth")
    if isinstance(variant_oauth, dict):
        oauth.update(variant_oauth)
    config["oauth"] = oauth
    return config


def _render_redirect_uri(
    scenario: dict[str, Any],
    variant: dict[str, Any],
    server_name: str,
) -> str:
    defaults = scenario.get("defaults") if isinstance(scenario.get("defaults"), dict) else {}
    config = _merge_server_config(scenario, variant)
    oauth = config["oauth"]
    template = oauth.get("redirect_uri")
    if not isinstance(template, str) or not template:
        raise AssertionError("variant oauth.redirect_uri must be a non-empty string")

    rendered = template.replace(
        "{port}",
        str(
            os.environ.get("MCP_OAUTH_MANUAL_CALLBACK_PORT")
            or defaults.get("callback_port")
            or 41793
        ),
    )
    return render_oauth_redirect_uri(
        rendered,
        connection_id=str(defaults.get("connection_id") or "manual-connection"),
        session_id=str(defaults.get("session_id") or "manual-session"),
        plugin_id=str(defaults.get("plugin_id") or "mcp_runtime_app"),
        action_id=str(defaults.get("action_id") or "mcp_complete_login"),
        server_name=server_name,
    )


def _expected_outcomes(
    scenario: dict[str, Any],
    variant: dict[str, Any],
) -> set[str]:
    values = variant.get("expected_start_outcomes")
    if not isinstance(values, list):
        defaults = scenario.get("defaults")
        values = (
            defaults.get("expected_start_outcomes")
            if isinstance(defaults, dict)
            else None
        )
    if not isinstance(values, list) or not values:
        return {"authorization_url"}
    return {str(value) for value in values}


def _state_dir(scenario: dict[str, Any]) -> Path:
    configured = os.environ.get("MCP_OAUTH_MANUAL_STATE_DIR")
    if configured:
        root = Path(configured).expanduser()
    else:
        root = Path(__file__).resolve().parents[1] / ".manual-state"
    scenario_id = str(scenario.get("id") or "manual")
    path = root / scenario_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[redacted]" if key == "client_secret" else _redact(child)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


@pytest.mark.asyncio
async def test_mcp_oauth_manual_start_matrix() -> None:
    scenario = _load_scenario()
    server = scenario.get("server")
    if not isinstance(server, dict):
        raise AssertionError("scenario server must be an object")
    server_name = server.get("name")
    if not isinstance(server_name, str) or not server_name:
        raise AssertionError("scenario server.name must be a non-empty string")

    state_dir = _state_dir(scenario)
    results: list[dict[str, Any]] = []
    for variant in _selected_variants(scenario):
        variant_id = str(variant.get("id") or "unnamed")
        config = _merge_server_config(scenario, variant)
        server_url = config.get("url")
        if not isinstance(server_url, str) or not server_url:
            raise AssertionError("scenario server.config.url must be a non-empty string")
        redirect_uri = _render_redirect_uri(scenario, variant, server_name)

        try:
            login = await build_mcp_oauth_login_request(
                server_url=server_url,
                raw_spec=config,
                redirect_uri=redirect_uri,
            )
        except Exception as exc:
            outcome = "start_error"
            result = {
                "variant_id": variant_id,
                "outcome": outcome,
                "redirect_uri": redirect_uri,
                "error": str(exc) or type(exc).__name__,
            }
        else:
            parsed = urlparse(login["authorization_url"])
            query = parse_qs(parsed.query)
            assert query["redirect_uri"] == [redirect_uri]
            assert query["state"] == [login["state"]]
            assert query["code_challenge_method"] == ["S256"]
            outcome = "authorization_url"
            result = {
                "variant_id": variant_id,
                "outcome": outcome,
                "redirect_uri": redirect_uri,
                "authorization_url": login["authorization_url"],
                "token_endpoint": login["token_endpoint"],
                "state": login["state"],
                "client_info": login["client_info"],
                "resource": login.get("resource"),
                "code_verifier": login["code_verifier"],
            }

        assert outcome in _expected_outcomes(scenario, variant)
        results.append(result)
        (state_dir / f"{variant_id}.json").write_text(
            json.dumps(result, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    assert results
    print(json.dumps(_redact(results), indent=2, sort_keys=True))