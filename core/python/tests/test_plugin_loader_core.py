"""Unit tests for core-level plugin loader interfaces and helpers.

These tests avoid any network or subprocess work and validate only
pure computation and dotted-path importing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import types

import pytest

from agent_core.plugin.loader import (
    DottedPathSource,
    get_plugin_id,
    validate_plugin_for_kind,
)


def test_get_plugin_id_prefers_name_attribute() -> None:
    class WithName:
        name = "custom_name"

    class WithoutName:
        pass

    assert get_plugin_id(WithName) == "custom_name"
    assert get_plugin_id(WithoutName) == "WithoutName"


def test_validate_plugin_for_kind_matches_and_mismatches() -> None:
    # Use existing dummy classes from tests package for realistic duck typing
    from tests.dummy_provider import DummyProvider
    from tests.dummy_tool import DummyCalculator
    from tests.dummy_feature import DummyFeature
    from tests.dummy_extension import DummyExtension

    assert validate_plugin_for_kind(DummyProvider, "providers") is None
    assert validate_plugin_for_kind(DummyCalculator, "tools") is None
    assert validate_plugin_for_kind(DummyFeature, "features") is None
    assert validate_plugin_for_kind(DummyExtension, "extensions") is None

    err = validate_plugin_for_kind(DummyProvider, "tools")
    assert isinstance(err, dict) and err.get("type") == "plugin_type_mismatch"


def test_dotted_path_source_supports_and_loads_valid_class() -> None:
    src = DottedPathSource()
    # Known in-repo plugin class
    path = "plugins.openai_provider.OpenAICompatibleProvider"
    assert src.supports(path) is True
    result = src.load(path, cache_dir=Path("."), policy={})
    assert result.error is None
    assert result.cls is not None
    assert getattr(result.cls, "__name__", "") == "OpenAICompatibleProvider"


def test_dotted_path_source_rejects_non_dotted_or_prefixed_specs() -> None:
    src = DottedPathSource()
    assert src.supports("git+https://example.com/repo.git#v1::module.Class") is False
    assert src.supports("path:/tmp/pkg::module.Class") is False
    assert src.supports("file:/tmp/file.py::module.Class") is False
    assert src.supports("not_a_dotted_path") is False


def test_dotted_path_source_returns_error_on_import_failure() -> None:
    src = DottedPathSource()
    bad = "no.such.module.Class"
    assert src.supports(bad) is True
    result = src.load(bad, cache_dir=Path("."), policy={})
    assert result.cls is None
    assert isinstance(result.error, dict)
    assert result.error.get("type") in {"plugin_import_error", "plugin_path_invalid"}
