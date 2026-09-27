from __future__ import annotations

import json
from pathlib import Path

from agent_app.config import (
    load_resolved_config,
    resolve_config_includes,
    resolve_config_mixins,
)


def _write(tmp_path: Path, name: str, payload) -> Path:
    target = tmp_path / name
    content = json.dumps(payload) if not isinstance(payload, str) else payload
    target.write_text(content, encoding="utf-8")
    return target


def test_include_merges_file_content_into_provider_and_consumes_key(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path,
        "rates.json",
        {"models": {"glm-5.2": {"input": 1.4, "completion": 4.4}}},
    )
    config = {
        "providers": {
            "ollama": {
                "provider": "reference_openai_compatible",
                "token_rates": {"$include": str(tmp_path / "rates.json")},
            }
        }
    }

    resolved, errors = resolve_config_includes(config, config_dir=tmp_path)

    assert errors == []
    rates = resolved["providers"]["ollama"]["token_rates"]
    assert rates == {"models": {"glm-5.2": {"input": 1.4, "completion": 4.4}}}
    assert "$include" not in rates


def test_include_at_root_level(tmp_path: Path) -> None:
    _write(tmp_path, "shared.json", {"timeout": 90, "tls_verify": False})
    config = {
        "$include": str(tmp_path / "shared.json"),
        "providers": {"ollama": {"provider": "reference_openai_compatible"}},
    }

    resolved, errors = resolve_config_includes(config, config_dir=tmp_path)

    assert errors == []
    assert resolved["timeout"] == 90
    assert resolved["tls_verify"] is False
    assert resolved["providers"]["ollama"]["provider"] == (
        "reference_openai_compatible"
    )
    assert "$include" not in resolved


def test_local_keys_override_included_content(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "rates.json",
        {
            "input": 1.0,
            "models": {"glm-5.2": {"input": 1.4, "completion": 4.4}},
        },
    )
    config = {
        "token_rates": {
            "$include": str(tmp_path / "rates.json"),
            "input": 2.0,
        }
    }

    resolved, errors = resolve_config_includes(config, config_dir=tmp_path)

    assert errors == []
    assert resolved["token_rates"]["input"] == 2.0
    assert resolved["token_rates"]["models"]["glm-5.2"]["input"] == 1.4


def test_nested_include_resolves_relative_to_including_file(tmp_path: Path) -> None:
    subdir = tmp_path / "pricing"
    subdir.mkdir()
    _write(
        subdir,
        "models.json",
        {"models": {"glm-5.2": {"input": 1.4, "completion": 4.4}}},
    )
    _write(subdir, "wrapper.json", {"$include": "models.json", "cached": 0.26})
    config = {
        "token_rates": {"$include": "pricing/wrapper.json"},
    }

    resolved, errors = resolve_config_includes(config, config_dir=tmp_path)

    assert errors == []
    rates = resolved["token_rates"]
    assert rates["cached"] == 0.26
    assert rates["models"]["glm-5.2"]["input"] == 1.4
    assert "$include" not in rates


def test_include_path_supports_env_placeholder_via_pipeline(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "rates.json",
        {"models": {"glm-5.2": {"input": 1.4, "completion": 4.4}}},
    )
    config = {
        "token_rates": {"$include": "${env:RATES_FILE}"},
    }
    config_file = _write(tmp_path, "config.json", config)

    resolved, errors, _env = load_resolved_config(
        config_file, env={"RATES_FILE": str(tmp_path / "rates.json")}
    )

    assert errors == []
    assert resolved["token_rates"]["models"]["glm-5.2"]["input"] == 1.4


def test_missing_include_reports_structured_error_and_keeps_local_keys(
    tmp_path: Path,
) -> None:
    config = {
        "token_rates": {
            "$include": str(tmp_path / "absent.json"),
            "input": 1.0,
        }
    }

    resolved, errors = resolve_config_includes(config, config_dir=tmp_path)

    assert [error["type"] for error in errors] == ["include_missing"]
    assert errors[0]["path"] == "token_rates.$include"
    assert resolved["token_rates"] == {"input": 1.0}


def test_unparsable_include_reports_structured_error(tmp_path: Path) -> None:
    _write(tmp_path, "broken.json", "{not json")
    config = {"token_rates": {"$include": str(tmp_path / "broken.json")}}

    resolved, errors = resolve_config_includes(config, config_dir=tmp_path)

    assert [error["type"] for error in errors] == ["include_invalid"]
    assert resolved["token_rates"] == {}


def test_non_object_include_reports_structured_error(tmp_path: Path) -> None:
    _write(tmp_path, "list.json", [1, 2, 3])
    config = {"token_rates": {"$include": str(tmp_path / "list.json")}}

    resolved, errors = resolve_config_includes(config, config_dir=tmp_path)

    assert [error["type"] for error in errors] == ["include_invalid"]
    assert "must contain a JSON object" in errors[0]["detail"]


def test_non_string_include_value_reports_structured_error(tmp_path: Path) -> None:
    config = {"token_rates": {"$include": ["rates.json"]}}

    resolved, errors = resolve_config_includes(config, config_dir=tmp_path)

    assert [error["type"] for error in errors] == ["include_invalid"]
    assert resolved["token_rates"] == {}


def test_include_cycle_reports_structured_error(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "self.json",
        {"$include": "self.json", "input": 1.0},
    )
    config = {"token_rates": {"$include": str(tmp_path / "self.json")}}

    resolved, errors = resolve_config_includes(config, config_dir=tmp_path)

    assert [error["type"] for error in errors] == ["include_cycle"]
    # The outer include still lands its non-cyclic local content.
    assert resolved["token_rates"]["input"] == 1.0


def test_include_depth_is_bounded(tmp_path: Path) -> None:
    # A chain of distinct files (no cycle) still stops at the depth bound.
    chain_length = 8
    for index in range(chain_length):
        if index == chain_length - 1:
            payload: dict[str, object] = {"input": 1.0}
        else:
            payload = {"$include": f"link-{index + 1}.json"}
        _write(tmp_path, f"link-{index}.json", payload)

    resolved, errors = resolve_config_includes(
        {"token_rates": {"$include": str(tmp_path / "link-0.json")}},
        config_dir=tmp_path,
        max_depth=4,
    )

    types = [error["type"] for error in errors]
    assert "include_depth_exceeded" in types
    assert "include_cycle" not in types
    assert isinstance(resolved["token_rates"], dict)


def test_included_file_merge_directive_governs_merge(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "rates.json",
        {
            "$merge": "deep",
            "models": {
                "glm-5.2": {"input": 1.4, "completion": 4.4},
                "glm-5.3-flash": {"input": 0.15, "completion": 0.5},
            },
        },
    )
    config = {
        "token_rates": {
            "$include": str(tmp_path / "rates.json"),
            "models": {"glm-5.2": {"input": 99.0}},
        }
    }

    resolved, errors = resolve_config_includes(config, config_dir=tmp_path)

    assert errors == []
    models = resolved["token_rates"]["models"]
    # Deep merge: the local glm-5.2 override merges into (not replaces) the
    # included mapping, keeping the included completion rate.
    assert models["glm-5.2"] == {"input": 99.0, "completion": 4.4}
    assert models["glm-5.3-flash"] == {"input": 0.15, "completion": 0.5}


def test_node_merge_directive_is_preserved_after_include(tmp_path: Path) -> None:
    _write(tmp_path, "shared.json", {"timeout": 90})
    config = {
        "$include": str(tmp_path / "shared.json"),
        "$merge": "deep",
        "providers": {},
    }

    resolved, errors = resolve_config_includes(config, config_dir=tmp_path)

    assert errors == []
    assert resolved["$merge"] == "deep"
    assert resolved["timeout"] == 90


def test_included_content_can_carry_mixin_refs_for_later_resolution(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path,
        "provider.json",
        {"provider": "reference_openai_compatible", "mixin_refs": ["shared"]},
    )
    config = {
        "mixins": {"shared": {"timeout": 45}},
        "providers": {
            "ollama": {"$include": str(tmp_path / "provider.json")},
        },
    }

    include_resolved, include_errors = resolve_config_includes(
        config, config_dir=tmp_path
    )
    assert include_errors == []
    assert include_resolved["providers"]["ollama"]["mixin_refs"] == ["shared"]

    mixin_resolved, mixin_errors = resolve_config_mixins(include_resolved)
    assert mixin_errors == []
    ollama = mixin_resolved["providers"]["ollama"]
    assert ollama["timeout"] == 45
    assert "mixin_refs" not in ollama
    assert "$include" not in ollama


def test_home_relative_include_path_expands(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    crystal_dir = tmp_path / ".crystal"
    crystal_dir.mkdir()
    _write(
        crystal_dir,
        "rates.json",
        {"models": {"glm-5.2": {"input": 1.4, "completion": 4.4}}},
    )
    config = {"token_rates": {"$include": "~/.crystal/rates.json"}}

    resolved, errors = resolve_config_includes(config, config_dir=tmp_path)

    assert errors == []
    assert resolved["token_rates"]["models"]["glm-5.2"]["input"] == 1.4


def test_mixin_policy_default_merge_governs_includes(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "rates.json",
        {"models": {"glm-5.2": {"input": 1.4, "completion": 4.4}}},
    )
    config = {
        "mixin_policy": {"default_merge": "deep"},
        "token_rates": {
            "$include": str(tmp_path / "rates.json"),
            "models": {"glm-5.2": {"input": 99.0}},
        },
    }

    resolved, errors = resolve_config_includes(config, config_dir=tmp_path)

    assert errors == []
    assert resolved["token_rates"]["models"]["glm-5.2"] == {
        "input": 99.0,
        "completion": 4.4,
    }
