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


def test_get_ui_elements_renders_text_when_no_models():
    provider = OpenAICompatibleProvider()
    elements = provider.get_ui_elements({}, [], [])
    model_el = next(el for el in elements if el.get("key") == "model")
    assert model_el.get("type") == "text"
    assert "options" not in model_el
    assert all(el.get("key") != "base_url" for el in elements)


def test_get_ui_elements_renders_select_when_models_present():
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
    assert model_el.get("type") == "text"


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
    ]
