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
    monkeypatch.delenv("MISSING", raising=False)
    raw = {"value": "aaa_${env:MISSING}_bbb"}
    resolved, errors = resolve_placeholders(raw)

    assert resolved["value"] == "aaa__bbb"
    assert errors == [
        {
            "path": "value",
            "type": "env_missing",
            "severity": "warning",
            "variable": "MISSING",
            "detail": "Environment variable 'MISSING' is not set",
        }
    ]


def test_raw_wrapper_preserves_literal_string(monkeypatch):
    raw = {
        "plugins": [
            {"$raw": "path:${env:BASE}/x/${env:NAME}"},
        ],
        "message": {"$raw": "${file:/tmp/does-not-matter.txt}"},
    }
    monkeypatch.setenv("BASE", "/tmp/base")
    monkeypatch.setenv("NAME", "pkg")
    resolved, errors = resolve_placeholders(raw)

    assert errors == []
    assert resolved["plugins"] == ["path:${env:BASE}/x/${env:NAME}"]
    assert resolved["message"] == "${file:/tmp/does-not-matter.txt}"
