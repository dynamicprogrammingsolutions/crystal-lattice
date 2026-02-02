from __future__ import annotations

from agent_app.config import resolve_placeholders


def test_embedded_env_substitution_multiple(monkeypatch):
    raw = {
        "plugins": [
            "path:${env:BASE}/x/${env:NAME}",
        ]
    }
    monkeypatch.setenv("BASE", "/tmp/base")
    monkeypatch.setenv("NAME", "pkg")
    resolved, errors = resolve_placeholders(raw)
    assert errors == []
    items = resolved["plugins"]
    assert isinstance(items, list)
    assert items[0] == "path:/tmp/base/x/pkg"


def test_embedded_env_substitution_missing(monkeypatch):
    raw = {"value": "aaa_${env:MISSING}_bbb"}
    resolved, errors = resolve_placeholders(raw)
    assert resolved["value"] == "aaa__bbb"
    assert any(e.get("type") == "env_missing" for e in errors)
