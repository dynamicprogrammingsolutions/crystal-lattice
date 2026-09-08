from __future__ import annotations

from template_python_provider.provider import TemplateProvider


def test_provider_name_and_version_are_nonempty() -> None:
    provider = TemplateProvider()
    assert isinstance(provider.name, str) and provider.name
    assert isinstance(provider.version, str) and provider.version


def test_config_schema_has_common_fields() -> None:
    schema = TemplateProvider().get_config_schema()

    assert schema.get("model", {}).get("required") is True
    assert schema.get("timeout", {}).get("default") == 60
    assert "debug_stream" in schema


def test_tags_include_streaming_capability() -> None:
    provider = TemplateProvider()
    tags = provider.get_tags({"model": "m"}, models=[{"id": "m"}])
    assert "supports_streaming" in tags


def test_model_ui_uses_the_portable_rich_dropdown() -> None:
    provider = TemplateProvider()

    elements = provider.get_ui_elements(
        {"model": "m"},
        tags=[],
        models=[{"id": "m", "name": "Model M"}],
    )

    model = elements[0]
    assert model["type"] == "dropdown"
    assert model["icon"] == "cpu"
    assert model["options"] == [{"value": "m", "label": "Model M"}]
    assert model["custom_value"]["enabled"] is True
    assert model["rich_ui"]["kind"] == "dropdown"
    assert model["rich_ui"]["show_label"] is False
    assert model["rich_ui"]["options"] == model["options"]
    assert model["rich_ui"]["placements"] == ["composer"]
    assert "icon" not in model["rich_ui"]


def test_default_message_conversion_shapes() -> None:
    provider = TemplateProvider()

    core_messages = [
        {"role": "system", "content": "You are helpful.", "metadata": {"x": 1}},
        {"role": "user", "content": "Hello", "metadata": {}},
        {"role": "assistant", "content": "Hi", "metadata": {"y": 2}},
    ]
    native = provider.to_native_messages(core_messages, state={})

    assert native == [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
    ]

    rebuilt = provider.from_native_messages(native, state={})
    assert rebuilt == [
        {"role": "system", "content": "You are helpful.", "metadata": {}},
        {"role": "user", "content": "Hello", "metadata": {}},
        {"role": "assistant", "content": "Hi", "metadata": {}},
    ]


def test_init_and_initialize_request_reset_partial_state() -> None:
    provider = TemplateProvider()
    state = provider.init({"model": "m", "debug_stream": True})
    assert state.get("accumulator") is None
    assert state.get("debug_stream") is True

    native_messages = [{"role": "user", "content": "hi"}]
    native_after, new_state = provider.initialize_request(native_messages, state)

    assert native_after == native_messages
    assert new_state.get("accumulator") is None
