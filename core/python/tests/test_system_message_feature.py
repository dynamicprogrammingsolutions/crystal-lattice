"""Tests for SystemMessageFeature (system message feature plugin)."""

from __future__ import annotations

from typing import Dict, Any, List

from plugins.system_message_feature import SystemMessageFeature


def _simple_native(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Helper to build a naive provider-native list from core messages."""

    return [{"role": m["role"], "content": m.get("content", "")} for m in messages]


def test_normalize_string_system_message() -> None:
    config = {
        "system_message_enabled": True,
        "system_message": "Hello {{NAME}}",
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)

    assert cfg["enabled"] is True
    assert cfg["template"] == "Hello {{NAME}}"
    assert cfg["variables"] == {}


def test_normalize_object_system_message_with_text_variable() -> None:
    config = {
        "system_message": {
            "template": "Hello {{NAME}}",
            "variables": {"NAME": "Core User"},
        }
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)

    assert cfg["enabled"] is True
    assert cfg["template"] == "Hello {{NAME}}"
    assert cfg["variables"]["NAME"] == {"kind": "text", "value": "Core User"}


def test_resolve_variables_files_and_code(tmp_path) -> None:
    file1 = tmp_path / "a.txt"
    file2 = tmp_path / "b.txt"
    file1.write_text("ALPHA", encoding="utf-8")
    file2.write_text("BETA", encoding="utf-8")

    code_file = tmp_path / "code_val.py"
    code_file.write_text("SYSTEM_MESSAGE_VALUE = 'FROM-CODE'\n", encoding="utf-8")

    specs = {
        "TEXT": {"kind": "text", "value": "plain"},
        "FILES": {"kind": "files", "files": [str(file1), str(file2)]},
        "CODE": {"kind": "code", "path": str(code_file)},
    }

    resolved = SystemMessageFeature._resolve_variables(specs)

    assert resolved["TEXT"] == "plain"
    assert resolved["FILES"] == "ALPHA\n\nBETA"
    assert resolved["CODE"] == "FROM-CODE"


def test_system_message_permanent_template_injected_when_missing() -> None:
    feature = SystemMessageFeature()

    config = {
        "system_message_enabled": True,
        "system_message": {
            "template": "You are a helper for {{PROJECT}}.",
            "variables": {"PROJECT": "AI Agent Platform"},
        },
    }

    state: Dict[str, Any] = {}
    state = feature.init(config, state)

    messages = [{"role": "user", "content": "Hi"}]
    native = _simple_native(messages)

    new_native = feature.to_native_messages(messages, native)

    # New permanent system message is prepended, but still contains the
    # template (variables are not rendered at this stage).
    assert len(new_native) == 2
    assert new_native[0]["role"] == "system"
    assert new_native[0]["content"] == "You are a helper for {{PROJECT}}."
    # Original user message preserved
    assert new_native[1]["role"] == "user"
    assert new_native[1]["content"] == "Hi"
    # Core history remains unmodified
    assert messages[0]["content"] == "Hi"


def test_no_permanent_system_message_when_user_system_present() -> None:
    feature = SystemMessageFeature()

    config = {
        "system_message_enabled": True,
        "system_message": {"template": "Hello {{NAME}}"},
    }

    state: Dict[str, Any] = {}
    state = feature.init(config, state)

    messages = [
        {"role": "system", "content": "User system {{NAME}}"},
        {"role": "user", "content": "Hi"},
    ]
    native = _simple_native(messages)

    new_native = feature.to_native_messages(messages, native)

    # Existing system message is preserved, no additional permanent system
    # is inserted.
    assert new_native == native


def test_system_message_files_variable_loaded_relative_to_cwd(tmp_path, monkeypatch) -> None:
    feature = SystemMessageFeature()

    # Create the file in a temporary directory and use a relative path.
    file_path = tmp_path / "context.txt"
    file_path.write_text("File-based context", encoding="utf-8")

    # Make the temporary directory the current working directory so that
    # the relative path is resolved against it.
    monkeypatch.chdir(tmp_path)

    config = {
        "system_message_enabled": True,
        "system_message": {
            "template": "Context: {{CTX}}",
            "variables": {"CTX": {"files": ["context.txt"]}},
        },
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)
    resolved = SystemMessageFeature._resolve_variables(cfg["variables"])

    assert resolved["CTX"] == "File-based context"


def test_text_variable_object_form() -> None:
    feature = SystemMessageFeature()

    config = {
        "system_message_enabled": True,
        "system_message": {
            "template": "Hello {{NAME}}",
            "variables": {"NAME": {"text": "Tester"}},
        },
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)
    resolved = SystemMessageFeature._resolve_variables(cfg["variables"])

    assert resolved["NAME"] == "Tester"


def test_code_variable_uses_python_file(tmp_path) -> None:
    feature = SystemMessageFeature()

    code_file = tmp_path / "code_val.py"
    code_file.write_text("""\nSYSTEM_MESSAGE_VALUE = 'FROM-CODE-FEATURE'\n""", encoding="utf-8")

    config = {
        "system_message_enabled": True,
        "system_message": {
            "template": "Code: {{VAL}}",
            "variables": {"VAL": {"code": str(code_file)}},
        },
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)
    resolved = SystemMessageFeature._resolve_variables(cfg["variables"])

    assert resolved["VAL"] == "FROM-CODE-FEATURE"


def test_system_message_dynamic_variables_change_between_configs() -> None:
    feature = SystemMessageFeature()

    # First config
    config1 = {
        "system_message_enabled": True,
        "system_message": {
            "template": "IGNORED",
            "variables": {"VAL": "one"},
        },
    }
    cfg1 = SystemMessageFeature._extract_plugin_config(config1)
    resolved1 = SystemMessageFeature._resolve_variables(cfg1["variables"])
    assert resolved1["VAL"] == "one"

    # Second config with updated value
    config2 = {
        "system_message_enabled": True,
        "system_message": {
            "template": "IGNORED",
            "variables": {"VAL": "two"},
        },
    }
    cfg2 = SystemMessageFeature._extract_plugin_config(config2)
    resolved2 = SystemMessageFeature._resolve_variables(cfg2["variables"])
    assert resolved2["VAL"] == "two"


def test_system_message_disabled_no_changes() -> None:
    feature = SystemMessageFeature()

    config = {"system_message_enabled": False, "system_message": "X"}
    state: Dict[str, Any] = {}
    state = feature.init(config, state)

    messages = [{"role": "user", "content": "Hi"}]
    native = _simple_native(messages)

    new_native = feature.to_native_messages(messages, native)

    # Feature disabled -> native messages unchanged
    assert new_native == native
