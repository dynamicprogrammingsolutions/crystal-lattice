"""Smoke tests: the package manifest is valid and its plugins load.

The runtime loads this package through a ``path:`` plugin source, so the
``agent_plugin.json`` manifest is the loading contract: every entry must
import and its declared kind must match the class's protocol.
"""

from __future__ import annotations

import importlib
from pathlib import Path

from agent_app.app_plugins import ApplicationPlugin
from agent_app.plugin_sources.descriptor import read_descriptor
from agent_core.types import FeaturePlugin

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def test_manifest_entries_import_with_declared_kinds() -> None:
    descriptor, error = read_descriptor(PACKAGE_ROOT)
    assert descriptor is not None, error
    assert error is None
    assert descriptor.entries, "expected at least one plugin entry"

    for entry in descriptor.entries:
        kind = descriptor.kinds.get(entry)
        assert kind, f"entry {entry!r} has no declared kind"
        module_path, class_name = entry.rsplit(".", 1)
        cls = getattr(importlib.import_module(module_path), class_name)
        # The plugin protocols are runtime_checkable Protocols with
        # non-method members, so kind checks use explicit subclass
        # membership rather than isinstance.
        if kind == "features":
            assert FeaturePlugin in cls.__mro__, entry
        elif kind == "application":
            assert ApplicationPlugin in cls.__mro__, entry


def test_tracking_feature_shape() -> None:
    from duration_tracking_plugins.duration_tracking_extension import (
        DurationTrackingExtension,
    )

    assert FeaturePlugin in DurationTrackingExtension.__mro__
    feature = DurationTrackingExtension()
    assert feature.name == "duration_tracking"
    assert feature.priority == 210
    schema = feature.get_config_schema()
    assert set(schema) == {
        "track_durations",
        "duration_tracking_db_path",
        "show_duration_status_total",
        "duration_breakdown",
        "duration_primary",
        "duration_additional_fields",
        "duration_statistics",
        "track_duration_tracking_summary_csv",
        "duration_tracking_summary_csv_path",
    }
    breakdown = schema["duration_breakdown"]
    assert breakdown["options"] == ["none", "totals", "averages"]
    assert breakdown["default"] == "none"
    assert schema["duration_primary"]["options"] == [
        "hidden",
        "llm",
        "llm_tools",
    ]
    assert schema["duration_additional_fields"]["options"] == [
        "none",
        "tools",
        "human",
        "tools_human",
    ]
    assert schema["duration_statistics"]["options"] == [
        "none",
        "counts",
        "counts_averages",
    ]
