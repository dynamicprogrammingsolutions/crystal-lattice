from __future__ import annotations

from typing import Any


from reference_openai_compatible_provider.provider import OpenAICompatibleProvider


class _Resp:
    def __init__(
        self, *, ok: bool, payload: Any = None, status_code: int = 200, text: str = ""
    ):
        self.ok = ok
        self._payload = payload
        self.status_code = status_code
        self.text = text

    def json(self) -> Any:
        return self._payload


def test_get_models_success(monkeypatch):
    def fake_get(url: str, headers: dict[str, str], timeout: float):
        assert url == "http://example.com/v1/models"
        assert timeout == 10.0
        assert headers == {"Authorization": "Bearer secret"}
        return _Resp(
            ok=True,
            payload={
                "data": [
                    {"id": "m1", "name": "Model One"},
                    {"id": "m2"},
                    {"id": ""},
                    "bad",
                ]
            },
        )

    monkeypatch.setattr("requests.get", fake_get)

    provider = OpenAICompatibleProvider()
    models = provider.get_models(
        {"base_url": "http://example.com/v1", "timeout": 12, "api_key": "secret"}
    )
    assert models == [{"id": "m1", "name": "Model One"}, {"id": "m2"}]


def test_get_models_failure_returns_empty(monkeypatch):
    def fake_get(url: str, headers: dict[str, str], timeout: float):
        return _Resp(ok=False, status_code=401, text="nope")

    monkeypatch.setattr("requests.get", fake_get)

    provider = OpenAICompatibleProvider()
    assert (
        provider.get_models({"base_url": "http://example.com/v1", "timeout": 1}) == []
    )


def test_get_models_exception_returns_empty(monkeypatch):
    def fake_get(url: str, headers: dict[str, str], timeout: float):
        raise TimeoutError("slow")

    monkeypatch.setattr("requests.get", fake_get)

    provider = OpenAICompatibleProvider()
    assert (
        provider.get_models({"base_url": "http://example.com/v1", "timeout": 1}) == []
    )


def test_get_models_uses_configured_tls_ca_bundle(monkeypatch):
    def fake_get(
        url: str,
        headers: dict[str, str],
        timeout: float,
        verify: str,
    ):
        assert url == "https://example.com/v1/models"
        assert headers == {}
        assert timeout == 10.0
        assert verify == "/app/reviewer-ca.pem"
        return _Resp(ok=True, payload={"data": [{"id": "reviewer-model"}]})

    monkeypatch.setattr("requests.get", fake_get)

    provider = OpenAICompatibleProvider()
    assert provider.get_models(
        {
            "base_url": "https://example.com/v1",
            "timeout": 12,
            "tls_ca_bundle": "/app/reviewer-ca.pem",
        }
    ) == [{"id": "reviewer-model"}]


def test_get_ui_elements_keeps_rich_dropdown_when_no_models():
    provider = OpenAICompatibleProvider()
    elements = provider.get_ui_elements({}, [], [])
    model_el = next(el for el in elements if el.get("key") == "model")
    assert model_el == {
        "ui_type": "config",
        "type": "dropdown",
        "key": "model",
        "label": "Model",
        "icon": "cpu",
        "options": [],
        "placeholder": "Search models or enter a model ID",
        "custom_value": {
            "enabled": True,
            "option_label": "Use '{value}' as a custom model ID",
        },
        "rich_ui": {
            "kind": "dropdown",
            "label": "Model",
            "show_label": False,
            "options": [],
            "placeholder": "Search models or enter a model ID",
            "custom_value": {
                "enabled": True,
                "option_label": "Use '{value}' as a custom model ID",
            },
            "placements": ["composer"],
            "default_pinned": True,
        },
    }
    assert all(el.get("key") != "base_url" for el in elements)


def test_get_ui_elements_renders_rich_dropdown_when_models_present():
    provider = OpenAICompatibleProvider()
    elements = provider.get_ui_elements(
        {},
        [],
        [{"id": "m1", "name": "Model One"}, {"id": "m2"}],
    )
    model_el = next(el for el in elements if el.get("key") == "model")
    assert model_el.get("type") == "dropdown"
    assert model_el.get("options") == [
        {"value": "m1", "label": "Model One"},
        {"value": "m2", "label": "m2"},
    ]
    assert model_el["rich_ui"] == {
        "kind": "dropdown",
        "label": "Model",
        "show_label": False,
        "options": [
            {"value": "m1", "label": "Model One"},
            {"value": "m2", "label": "m2"},
        ],
        "placeholder": "Search models or enter a model ID",
        "custom_value": {
            "enabled": True,
            "option_label": "Use '{value}' as a custom model ID",
        },
        "placements": ["composer"],
        "default_pinned": True,
    }
    assert model_el["custom_value"] == {
        "enabled": True,
        "option_label": "Use '{value}' as a custom model ID",
    }


def test_get_ui_elements_renders_endpoint_dropdown_when_options_present():
    provider = OpenAICompatibleProvider()
    elements = provider.get_ui_elements(
        {
            "endpoint_options": {
                "General": "https://api.z.ai/api/paas/v4",
                "Coding": "https://api.z.ai/api/coding/paas/v4",
            }
        },
        [],
        [],
    )

    endpoint_el = next(el for el in elements if el.get("key") == "base_url")
    model_el = next(el for el in elements if el.get("key") == "model")

    assert endpoint_el == {
        "ui_type": "config",
        "type": "select",
        "key": "base_url",
        "label": "Endpoint",
        "options": [
            {"value": "https://api.z.ai/api/paas/v4", "label": "General"},
            {"value": "https://api.z.ai/api/coding/paas/v4", "label": "Coding"},
        ],
    }
    assert model_el.get("type") == "dropdown"
    assert model_el.get("options") == []
    assert model_el["rich_ui"]["custom_value"]["enabled"] is True


def test_get_ui_elements_skips_invalid_endpoint_options_entries():
    provider = OpenAICompatibleProvider()
    elements = provider.get_ui_elements(
        {
            "endpoint_options": {
                "General": "https://api.z.ai/api/paas/v4",
                "": "https://example.com/v1",
                "BadValue": 123,
            }
        },
        [],
        [],
    )

    endpoint_el = next(el for el in elements if el.get("key") == "base_url")
    assert endpoint_el.get("options") == [
        {"value": "https://api.z.ai/api/paas/v4", "label": "General"}
    ]


def test_get_tags_are_conservative_about_reasoning_support():
    provider = OpenAICompatibleProvider()
    assert provider.get_tags({}, []) == [
        "provider:openai_compatible",
        "supports_streaming",
        "supports_tools",
        "cost_tracking",
    ]
