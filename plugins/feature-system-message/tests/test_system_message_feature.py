"""Tests for SystemMessageFeature (system message feature plugin)."""

from __future__ import annotations

import subprocess
from typing import Dict, Any, List

from feature_system_message.system_message_feature import SystemMessageFeature


def _simple_native(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Helper to build a naive provider-native list from core messages."""

    return [{"role": m["role"], "content": m.get("content", "")} for m in messages]


def _write_runtime_code(tmp_path, body: str | None = None):
    runtime_file = tmp_path / "runtime.py"
    runtime_file.write_text(
        body
        or (
            "import subprocess\n"
            "from pathlib import Path\n\n"
            "cwd = str(Path.cwd().resolve())\n\n"
            "def git_root(path=None):\n"
            "    target = Path(path or cwd)\n"
            "    if target.is_file():\n"
            "        target = target.parent\n"
            '    proc = subprocess.run(["git", "-C", str(target), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)\n'
            "    if proc.returncode != 0:\n"
            "        return None\n"
            "    return proc.stdout.strip() or None\n\n"
            "def is_git_repo(path=None):\n"
            "    return git_root(path) is not None\n"
        ),
        encoding="utf-8",
    )
    return runtime_file


def test_normalize_string_system_message() -> None:
    config = {
        "system_message_enabled": True,
        "system_message": "Hello {{NAME}}",
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)

    assert cfg["enabled"] is True
    assert cfg["as_instructions"] is False
    assert cfg["template"] == "Hello {{NAME}}"
    assert cfg["variables"] == {}


def test_normalize_system_message_as_instructions_flag() -> None:
    config = {
        "system_message_enabled": True,
        "system_message_as_instructions": True,
        "system_message": "Hello {{NAME}}",
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)

    assert cfg["enabled"] is True
    assert cfg["as_instructions"] is True
    assert cfg["template"] == "Hello {{NAME}}"


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


def test_normalize_object_system_message_with_runtime_code(tmp_path) -> None:
    runtime_file = _write_runtime_code(tmp_path)

    config = {
        "system_message": {
            "template": "Hello {{NAME}}",
            "runtime_code": str(runtime_file),
            "variables": {"NAME": "Core User"},
        }
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)

    assert cfg["runtime_code"] == str(runtime_file)


def test_normalize_variable_value_with_runtime_code(tmp_path) -> None:
    runtime_file = _write_runtime_code(tmp_path)

    config = {
        "system_message": {
            "template": "{{NAME}}",
            "variables": {
                "NAME": {
                    "inline_code": "greeting()",
                    "runtime_code": str(runtime_file),
                }
            },
        }
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)

    assert cfg["variables"]["NAME"]["runtime_code"] == str(runtime_file)


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

    resolved, _metadata_updates = SystemMessageFeature._resolve_variables(specs)

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

    # Structural insertion now happens during initialize_request and
    # returns updated native_messages along with state.
    new_native, new_state = feature.initialize_request(native, state)

    # New permanent system message is prepended, but still contains the
    # template (variables are not rendered in native history).
    assert len(new_native) == 2
    assert new_native[0]["role"] == "system"
    assert new_native[0]["content"] == "You are a helper for {{PROJECT}}."
    assert new_native[0]["_metadata"]["compiled_content"] == (
        "You are a helper for AI Agent Platform."
    )
    # Original user message preserved
    assert new_native[1]["role"] == "user"
    assert new_native[1]["content"] == "Hi"
    # Core history remains unmodified
    assert messages[0]["content"] == "Hi"
    # State should include a request override with rendered messages.
    request = new_state.get("request") or {}
    override = request.get("messages") or []
    assert override and override[0]["role"] == "system"


def test_system_message_can_compile_into_request_instructions() -> None:
    feature = SystemMessageFeature()

    config = {
        "system_message_enabled": True,
        "system_message_as_instructions": True,
        "system_message": {
            "template": "You are a helper for {{PROJECT}}.",
            "variables": {"PROJECT": "AI Agent Platform"},
        },
    }

    state: Dict[str, Any] = {"request": {"payload": {"model": "gpt-5"}}}
    state = feature.init(config, state)

    native = _simple_native([{"role": "user", "content": "Hi"}])

    new_native, new_state = feature.initialize_request(native, state)

    assert new_native == native
    request = new_state.get("request") or {}
    assert request.get("instructions") == "You are a helper for AI Agent Platform."
    assert "messages" not in request


def test_state_system_message_variables_override_config_values() -> None:
    feature = SystemMessageFeature()

    config = {
        "system_message_enabled": True,
        "system_message": {
            "template": "Hello {{NAME}}",
            "variables": {"NAME": "Config User"},
        },
    }

    state: Dict[str, Any] = {"system_message_variables": {"NAME": "State User"}}
    state = feature.init(config, state)

    native = _simple_native([{"role": "user", "content": "Hi"}])
    _new_native, new_state = feature.initialize_request(native, state)

    request = new_state.get("request") or {}
    override = request.get("messages") or []
    assert override[0]["content"] == "Hello State User"


def test_existing_request_messages_are_preserved_when_rendering_system_message() -> None:
    feature = SystemMessageFeature()

    config = {
        "system_message_enabled": True,
        "system_message": {
            "template": "Hello {{NAME}}",
            "variables": {"NAME": "Alice"},
        },
    }

    state: Dict[str, Any] = {
        "request": {
            "messages": [
                {"role": "user", "content": "Original"},
                {"role": "user", "content": "<skill>\n<name>demo</name>\n</skill>"},
            ]
        }
    }
    state = feature.init(config, state)

    native = _simple_native([{"role": "user", "content": "Hi"}])
    _new_native, new_state = feature.initialize_request(native, state)

    request = new_state.get("request") or {}
    override = request.get("messages") or []
    assert override[0]["role"] == "system"
    assert override[0]["content"] == "Hello Alice"
    assert override[1]["content"] == "Original"
    assert override[2]["content"] == "<skill>\n<name>demo</name>\n</skill>"


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

    new_native, _ = feature.initialize_request(native, state)

    # Existing system message is preserved, no additional permanent
    # system is inserted.
    assert len(new_native) == len(native)
    assert [message["role"] for message in new_native] == ["system", "user"]
    assert new_native[0]["content"] == "User system {{NAME}}"


def test_compiled_content_is_stamped_and_logged_once(capsys) -> None:
    feature = SystemMessageFeature()

    config = {
        "system_message_enabled": True,
        "system_message": {
            "template": "Hello {{NAME}}",
            "variables": {"NAME": "Alice"},
        },
    }

    state: Dict[str, Any] = {}
    state = feature.init(config, state)

    native = _simple_native([{"role": "user", "content": "Hi"}])

    new_native, new_state = feature.initialize_request(native, state)
    assert new_native[0]["content"] == "Hello {{NAME}}"
    assert new_native[0]["_metadata"]["compiled_content"] == "Hello Alice"
    assert new_native[0]["_metadata"]["system_message_compiled_logged"] is True

    first_output = capsys.readouterr().out
    assert "[system_message compiled]" in first_output
    assert "Hello Alice" in first_output

    newer_native, _newer_state = feature.initialize_request(new_native, new_state)
    assert newer_native[0]["_metadata"]["compiled_content"] == "Hello Alice"
    assert capsys.readouterr().out == ""


def test_system_message_files_variable_loaded_relative_to_cwd(
    tmp_path, monkeypatch
) -> None:
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
    resolved, _metadata_updates = SystemMessageFeature._resolve_variables(cfg["variables"])

    assert resolved["CTX"] == "File-based context"


def test_text_variable_object_form() -> None:
    config = {
        "system_message_enabled": True,
        "system_message": {
            "template": "Hello {{NAME}}",
            "variables": {"NAME": {"text": "Tester"}},
        },
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)
    resolved, _metadata_updates = SystemMessageFeature._resolve_variables(cfg["variables"])

    assert resolved["NAME"] == "Tester"


def test_code_variable_uses_python_file(tmp_path) -> None:
    code_file = tmp_path / "code_val.py"
    code_file.write_text(
        """\nSYSTEM_MESSAGE_VALUE = 'FROM-CODE-FEATURE'\n""", encoding="utf-8"
    )

    config = {
        "system_message_enabled": True,
        "system_message": {
            "template": "Code: {{VAL}}",
            "variables": {"VAL": {"code": str(code_file)}},
        },
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)
    resolved, _metadata_updates = SystemMessageFeature._resolve_variables(cfg["variables"])

    assert resolved["VAL"] == "FROM-CODE-FEATURE"


def test_inline_code_expression_variable(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runtime_file = _write_runtime_code(tmp_path)
    runtime_context = SystemMessageFeature._load_runtime_context(str(runtime_file))

    config = {
        "system_message": {
            "template": "{{VAL}}",
            "runtime_code": str(runtime_file),
            "variables": {
                "VAL": {"inline_code": "f'Current working directory: {cwd}'"},
            },
        }
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)
    resolved, _metadata_updates = SystemMessageFeature._resolve_variables(
        cfg["variables"],
        runtime_context=runtime_context,
    )

    assert resolved["VAL"] == f"Current working directory: {tmp_path.resolve()}"


def test_runtime_code_can_read_config_in_inline_code(tmp_path) -> None:
    runtime_file = tmp_path / "runtime.py"
    runtime_file.write_text(
        "selected_model = CONFIG.get('model')\n",
        encoding="utf-8",
    )

    config = {
        "model": "openai/gpt-5.4",
        "system_message": {
            "template": "{{VAL}}",
            "runtime_code": str(runtime_file),
            "variables": {
                "VAL": {"inline_code": "selected_model"},
            },
        },
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)
    runtime_context = SystemMessageFeature._load_runtime_context(
        str(runtime_file),
        base_context=SystemMessageFeature._build_base_runtime_context(config=config),
    )
    resolved, _metadata_updates = SystemMessageFeature._resolve_variables(
        cfg["variables"],
        runtime_context=runtime_context,
    )

    assert resolved["VAL"] == "openai/gpt-5.4"


def test_inline_code_has_no_default_helper_context_without_runtime_code() -> None:
    config = {
        "system_message": {
            "template": "{{VAL}}",
            "variables": {
                "VAL": {"inline_code": "f'Current working directory: {cwd}'"},
            },
        }
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)
    resolved, _metadata_updates = SystemMessageFeature._resolve_variables(cfg["variables"])

    assert resolved["VAL"] == ""


def test_inline_code_block_uses_value_variable() -> None:
    config = {
        "system_message": {
            "template": "{{VAL}}",
            "variables": {
                "VAL": {
                    "inline_code": (
                        "if True:\n"
                        "    VALUE = 'Rendered from block'\n"
                        "else:\n"
                        "    VALUE = ''\n"
                    )
                },
            },
        }
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)
    resolved, _metadata_updates = SystemMessageFeature._resolve_variables(cfg["variables"])

    assert resolved["VAL"] == "Rendered from block"


def test_condition_inline_code_on_text_variable() -> None:
    config = {
        "system_message": {
            "template": "Hello{{VAL}}",
            "variables": {
                "VAL": {
                    "text": " world",
                    "condition": {"inline_code": "False"},
                },
            },
        }
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)
    resolved, _metadata_updates = SystemMessageFeature._resolve_variables(cfg["variables"])

    assert resolved["VAL"] == ""
    assert SystemMessageFeature._render_template(cfg["template"], resolved) == "Hello"


def test_condition_inline_code_on_files_variable_skips_file_reads(monkeypatch) -> None:
    def _fail_read(paths: List[str]) -> str:
        raise AssertionError(f"_read_files should not be called: {paths}")

    monkeypatch.setattr(SystemMessageFeature, "_read_files", staticmethod(_fail_read))

    config = {
        "system_message": {
            "template": "{{VAL}}",
            "variables": {
                "VAL": {
                    "files": ["should-not-be-read.md"],
                    "condition": {"inline_code": "False"},
                },
            },
        }
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)
    resolved, _metadata_updates = SystemMessageFeature._resolve_variables(cfg["variables"])

    assert resolved["VAL"] == ""


def test_condition_code_uses_external_helper_file(tmp_path) -> None:
    condition_file = tmp_path / "condition.py"
    condition_file.write_text("SYSTEM_MESSAGE_VALUE = True\n", encoding="utf-8")

    config = {
        "system_message": {
            "template": "{{VAL}}",
            "variables": {
                "VAL": {
                    "text": "from text",
                    "condition": {"code": str(condition_file)},
                },
            },
        }
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)
    resolved, _metadata_updates = SystemMessageFeature._resolve_variables(cfg["variables"])

    assert resolved["VAL"] == "from text"


def test_helper_runtime_available_to_inline_code_in_git_repo(
    tmp_path, monkeypatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init"], cwd=repo, check=True, capture_output=True, text=True
    )
    monkeypatch.chdir(repo)
    runtime_context = SystemMessageFeature._load_runtime_context(
        str(_write_runtime_code(tmp_path))
    )

    assert SystemMessageFeature._execute_inline_code(
        "cwd", runtime_context=runtime_context
    ) == str(repo.resolve())
    assert (
        SystemMessageFeature._execute_inline_code_raw(
            "is_git_repo()",
            runtime_context=runtime_context,
        )
        is True
    )
    assert SystemMessageFeature._execute_inline_code(
        "git_root()",
        runtime_context=runtime_context,
    ) == str(repo.resolve())


def test_helper_runtime_available_to_file_backed_code(tmp_path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init"], cwd=repo, check=True, capture_output=True, text=True
    )
    monkeypatch.chdir(repo)
    runtime_file = _write_runtime_code(tmp_path)
    runtime_context = SystemMessageFeature._load_runtime_context(str(runtime_file))

    code_file = tmp_path / "code_val.py"
    code_file.write_text(
        "SYSTEM_MESSAGE_VALUE = f'{cwd}|{is_git_repo()}|{git_root()}'\n",
        encoding="utf-8",
    )

    config = {
        "system_message": {
            "template": "{{VAL}}",
            "variables": {"VAL": {"code": str(code_file)}},
        }
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)
    resolved, _metadata_updates = SystemMessageFeature._resolve_variables(
        cfg["variables"],
        runtime_context=runtime_context,
    )

    assert resolved["VAL"] == f"{repo.resolve()}|True|{repo.resolve()}"


def test_file_backed_code_can_read_config_without_custom_runtime_file(tmp_path) -> None:
    code_file = tmp_path / "code_val.py"
    code_file.write_text("SYSTEM_MESSAGE_VALUE = CONFIG['model']\n", encoding="utf-8")

    config = {
        "model": "openai/gpt-5.2",
        "system_message": {
            "template": "{{VAL}}",
            "variables": {"VAL": {"code": str(code_file)}},
        },
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)
    runtime_context = SystemMessageFeature._load_runtime_context(
        None,
        base_context=SystemMessageFeature._build_base_runtime_context(config=config),
    )
    resolved, _metadata_updates = SystemMessageFeature._resolve_variables(
        cfg["variables"],
        runtime_context=runtime_context,
    )

    assert resolved["VAL"] == "openai/gpt-5.2"


def test_runtime_code_zero_arg_get_ui_elements_uses_runtime_globals(tmp_path) -> None:
    runtime_file = tmp_path / "runtime.py"
    runtime_file.write_text(
        "def get_ui_elements():\n"
        "    return [{\n"
        "        'ui_type': 'config',\n"
        "        'type': 'select',\n"
        "        'key': 'codex_personality',\n"
        "        'label': f\"{CONFIG.get('model')}|{','.join(TAGS)}|{MODELS[0]['id']}\",\n"
        "        'options': ['default', 'friendly', 'pragmatic'],\n"
        "    }]\n",
        encoding="utf-8",
    )

    feature = SystemMessageFeature()
    elements = feature.get_ui_elements(
        config={
            "model": "openai/gpt-5.4",
            "system_message": {"runtime_code": str(runtime_file)},
        },
        tags=["supports_tools"],
        models=[{"id": "openai/gpt-5.4"}],
    )

    assert len(elements) == 1
    assert elements[0]["key"] == "codex_personality"
    assert elements[0]["type"] == "select"
    assert elements[0]["label"] == "openai/gpt-5.4|supports_tools|openai/gpt-5.4"


def test_variable_runtime_code_augments_request_context(tmp_path) -> None:
    runtime_file = _write_runtime_code(
        tmp_path,
        body=(
            "def greeting():\n"
            "    return f\"hello from {CONFIG['model']}\"\n"
        ),
    )

    config = {
        "model": "moonshotai/kimi-k2.5",
        "system_message": {
            "template": "{{VAL}}",
            "variables": {
                "VAL": {
                    "inline_code": "greeting()",
                    "runtime_code": str(runtime_file),
                }
            },
        },
    }

    cfg = SystemMessageFeature._extract_plugin_config(config)
    runtime_context = SystemMessageFeature._load_runtime_context(
        None,
        base_context=SystemMessageFeature._build_base_runtime_context(config=config),
    )
    resolved, _metadata_updates = SystemMessageFeature._resolve_variables(
        cfg["variables"],
        runtime_context=runtime_context,
    )

    assert resolved["VAL"] == "hello from moonshotai/kimi-k2.5"


def test_variable_runtime_code_contributes_ui_schema(tmp_path) -> None:
    runtime_file = _write_runtime_code(
        tmp_path,
        body=(
            "def get_ui_elements():\n"
            "    return [{\n"
            "        'ui_type': 'config',\n"
            "        'type': 'checkbox',\n"
            "        'key': 'include_tasks',\n"
            "        'label': f\"Include tasks for {CONFIG['model']}\",\n"
            "        'default': False,\n"
            "    }]\n"
        ),
    )

    feature = SystemMessageFeature()
    elements = feature.get_ui_elements(
        config={
            "model": "openai/gpt-5.4",
            "system_message": {
                "template": "{{TASKS}}",
                "variables": {
                    "TASKS": {
                        "text": "ignored",
                        "runtime_code": str(runtime_file),
                    }
                },
            },
        },
        tags=[],
        models=[{"id": "openai/gpt-5.4"}],
    )

    assert len(elements) == 1
    assert elements[0]["key"] == "include_tasks"
    assert elements[0]["type"] == "checkbox"
    assert elements[0]["default"] is False


def test_system_message_dynamic_variables_change_between_configs() -> None:
    # First config
    config1 = {
        "system_message_enabled": True,
        "system_message": {
            "template": "IGNORED",
            "variables": {"VAL": "one"},
        },
    }
    cfg1 = SystemMessageFeature._extract_plugin_config(config1)
    resolved1, _metadata_updates1 = SystemMessageFeature._resolve_variables(cfg1["variables"])
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
    resolved2, _metadata_updates2 = SystemMessageFeature._resolve_variables(cfg2["variables"])
    assert resolved2["VAL"] == "two"


def test_system_message_disabled_no_changes() -> None:
    feature = SystemMessageFeature()

    config = {"system_message_enabled": False, "system_message": "X"}
    state: Dict[str, Any] = {}
    state = feature.init(config, state)

    messages = [{"role": "user", "content": "Hi"}]
    native = _simple_native(messages)

    new_native, new_state = feature.initialize_request(native, state)

    # Feature disabled -> native messages and state unchanged
    assert new_native == native
    assert new_state == state
