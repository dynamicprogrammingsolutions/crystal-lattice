#!/usr/bin/env python3
"""Validate and generate the compact website compatibility projection."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import re
from pathlib import Path
from typing import Any, Mapping


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE / "website-compatibility-selection.json"
FEATURE_CATALOG = HERE / "feature-catalog.json"
APPLICATION_FEATURES = HERE / "application-feature-compatibility.csv"
PROVIDER_MATRIX = HERE / "provider-support-matrix.json"
OUTPUT_JSON = HERE / "website-compatibility-data.json"
OUTPUT_MARKDOWN = HERE / "website-compatibility-data.md"

PUBLIC_STATUSES = {
    "available",
    "conditional",
    "optional",
    "planned",
    "unavailable",
    "not_applicable",
    "not_verified",
}

SIMPLE_PROVIDER_STATUS_MAP = {
    "supported": {"available", "conditional"},
    "conditional": {"conditional"},
    "planned": {"planned"},
    "unsupported": {"unavailable"},
    "not_applicable": {"not_applicable"},
    "unknown": {"not_verified"},
}

APPLICATION_STATUS_MAP = {
    "current": "available",
    "partial": "conditional",
    "optional": "optional",
    "experimental": "conditional",
    "planned": "planned",
    "unsupported": "unavailable",
    "not_applicable": "not_applicable",
    "unknown": "not_verified",
}

INTERNAL_KEYS = {
    "source_plugins",
    "source_claim_ids",
    "source_feature_ids",
    "source_entries",
    "planning_source",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _application_feature_rows() -> dict[str, dict[str, str]]:
    with APPLICATION_FEATURES.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        source_path = str(row.get("source_path") or "")
        plugin_id = (
            source_path.removeprefix("plugins/")
            if source_path.startswith("plugins/")
            else str(row["row_id"]).removeprefix("feature:")
        )
        result[plugin_id] = row
    return result


def _descriptor_entries(package_id: str) -> set[str]:
    path = ROOT / "plugins" / package_id / "agent_plugin.json"
    if not path.is_file():
        raise ValueError(f"{package_id}: missing agent_plugin.json")
    payload = _load_json(path)
    return {str(value) for value in payload.get("entries") or []}


def _unique(values: list[str], context: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{context}: duplicate ids")


def _validate_status(status: str, context: str) -> None:
    if status not in PUBLIC_STATUSES:
        raise ValueError(f"{context}: unknown display status {status!r}")


def _validate_features(
    source: Mapping[str, Any],
    *,
    feature_catalog: Mapping[str, Any],
    application_rows: Mapping[str, Mapping[str, str]],
) -> None:
    selection = source["feature_selection"]
    selected = [str(value) for value in selection["plugin_ids"]]
    _unique(selected, "feature plugin selection")
    catalog_rows = {
        str(row["plugin_id"]): row for row in feature_catalog["rows"]
    }
    excluded_groups = selection.get("excluded_overlaps") or {}
    excluded = [
        str(plugin_id)
        for values in excluded_groups.values()
        for plugin_id in values
    ]
    _unique(excluded, "feature overlap exclusions")
    overlap = set(selected) & set(excluded)
    if overlap:
        raise ValueError(
            f"feature selection appears in both selected and excluded sets: "
            f"{sorted(overlap)}"
        )
    missing_catalog = set(selected) - set(catalog_rows)
    if missing_catalog:
        raise ValueError(
            f"feature selection has unknown catalog plugins: "
            f"{sorted(missing_catalog)}"
        )
    missing_application = set(selected) - set(application_rows)
    if missing_application:
        raise ValueError(
            f"feature selection has unknown application rows: "
            f"{sorted(missing_application)}"
        )
    classified = set(selected) | set(excluded)
    if classified != set(application_rows):
        raise ValueError(
            "feature selection must classify every application-feature row; "
            f"missing={sorted(set(application_rows) - classified)}, "
            f"extra={sorted(classified - set(application_rows))}"
        )
    for plugin_id in selected:
        catalog_row = catalog_rows[plugin_id]
        expected_path = f"plugins/{plugin_id}"
        if catalog_row.get("source_path") != expected_path:
            raise ValueError(
                f"feature:{plugin_id}: expected source path {expected_path!r}, "
                f"got {catalog_row.get('source_path')!r}"
            )
        capability_state = str(
            application_rows[plugin_id].get("capability_state") or "unknown"
        )
        status = APPLICATION_STATUS_MAP.get(capability_state)
        if status is None:
            raise ValueError(
                f"feature:{plugin_id}: unknown capability state "
                f"{capability_state!r}"
            )
        _validate_status(status, f"feature:{plugin_id}")


def _public_features(
    source: Mapping[str, Any],
    feature_catalog: Mapping[str, Any],
    application_rows: Mapping[str, Mapping[str, str]],
) -> dict[str, Any]:
    selection = source["feature_selection"]
    catalog_rows = {
        str(row["plugin_id"]): row for row in feature_catalog["rows"]
    }
    rows = []
    for plugin_id in selection["plugin_ids"]:
        catalog_row = catalog_rows[plugin_id]
        application_row = application_rows[plugin_id]
        capability_state = str(
            application_row.get("capability_state") or "unknown"
        )
        rows.append(
            {
                "feature_id": plugin_id,
                "plugin_id": plugin_id,
                "plugin_path": catalog_row["source_path"],
                "status": APPLICATION_STATUS_MAP[capability_state],
                "capability_state": capability_state,
                "lifecycle_status": catalog_row["lifecycle_status"],
                "default_selected": bool(catalog_row["default_selected"]),
                "description": catalog_row["description"],
                "limitations": application_row.get("limitations") or "",
            }
        )
    return {
        "title": selection["title"],
        "description": selection["description"],
        "rows": rows,
        "represented_elsewhere": copy.deepcopy(
            selection.get("excluded_overlaps") or {}
        ),
    }


def _provider_lookup(provider_matrix: Mapping[str, Any]) -> tuple[
    set[str],
    dict[str, dict[str, str]],
]:
    feature_ids = {
        str(feature["feature_id"]) for feature in provider_matrix["features"]
    }
    lookup: dict[str, dict[str, str]] = {}
    for provider in provider_matrix["providers"]:
        lookup[provider["provider_id"]] = {
            cell["feature_id"]: cell["status"] for cell in provider["cells"]
        }
    return feature_ids, lookup


def _validate_providers(
    source: Mapping[str, Any],
    provider_matrix: Mapping[str, Any],
) -> None:
    selection = source["provider_selection"]
    columns = selection["columns"]
    rows = selection["rows"]
    column_ids = [column["column_id"] for column in columns]
    _unique(column_ids, "provider columns")
    _unique([row["provider_id"] for row in rows], "provider rows")
    feature_ids, provider_lookup = _provider_lookup(provider_matrix)
    column_source_ids: dict[str, list[str]] = {}
    for column in columns:
        source_ids = [str(value) for value in column["source_feature_ids"]]
        missing = set(source_ids) - feature_ids
        if missing:
            raise ValueError(
                f"provider column {column['column_id']}: unknown source features "
                f"{sorted(missing)}"
            )
        column_source_ids[column["column_id"]] = source_ids

    for row in rows:
        provider_id = row["provider_id"]
        if provider_id not in provider_lookup:
            raise ValueError(f"provider:{provider_id}: unknown provider")
        cells = row["cells"]
        if set(cells) != set(column_ids):
            raise ValueError(
                f"provider:{provider_id}: cells must exactly match selected columns"
            )
        for column_id, cell in cells.items():
            context = f"provider:{provider_id}:{column_id}"
            display_status = str(cell["status"])
            _validate_status(display_status, context)
            source_ids = column_source_ids[column_id]
            if len(source_ids) != 1:
                continue
            detailed_status = provider_lookup[provider_id][source_ids[0]]
            allowed = SIMPLE_PROVIDER_STATUS_MAP[detailed_status]
            if display_status not in allowed:
                raise ValueError(
                    f"{context}: {display_status!r} is inconsistent with "
                    f"detailed status {detailed_status!r}"
                )


def _validate_model_tools(source: Mapping[str, Any]) -> None:
    families = source["model_tool_selection"]["families"]
    _unique([family["family_id"] for family in families], "model families")
    for family in families:
        package_id = family["package_id"]
        entries = _descriptor_entries(package_id)
        tools = family["tools"]
        _unique(
            [tool["tool_id"] for tool in tools],
            f"model family {family['family_id']}",
        )
        for tool in tools:
            context = f"model:{family['family_id']}:{tool['tool_id']}"
            status = str(tool["status"])
            _validate_status(status, context)
            source_entries = tool.get("source_entries") or []
            planning_source = tool.get("planning_source")
            if status == "planned":
                if source_entries:
                    raise ValueError(f"{context}: planned row has source entries")
                if not isinstance(planning_source, str):
                    raise ValueError(f"{context}: planned row has no planning source")
                if not (ROOT / planning_source).is_file():
                    raise ValueError(
                        f"{context}: missing planning source {planning_source}"
                    )
                continue
            if planning_source:
                raise ValueError(f"{context}: current row has a planning source")
            if not source_entries:
                raise ValueError(f"{context}: current row has no descriptor entry")
            missing = set(source_entries) - entries
            if missing:
                raise ValueError(
                    f"{context}: descriptor entries not found {sorted(missing)}"
                )


def _strip_internal(value: Any) -> Any:
    if isinstance(value, list):
        return [_strip_internal(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _strip_internal(item)
            for key, item in value.items()
            if key not in INTERNAL_KEYS
        }
    return value


def _public_payload(
    source: Mapping[str, Any],
    feature_catalog: Mapping[str, Any],
    application_rows: Mapping[str, Mapping[str, str]],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "review_state": source["review_state"],
        "maturity": source["maturity"],
        "revision_policy": source["revision_policy"],
        "status_labels": source["display_statuses"],
        "identity_note": (
            "Compatibility profiles and tool bundles are Crystal Lattice "
            "implementations, not official upstream applications or sessions."
        ),
        "features": _public_features(
            source,
            feature_catalog,
            application_rows,
        ),
        "providers": _strip_internal(source["provider_selection"]),
        "model_family_tools": _strip_internal(source["model_tool_selection"]),
    }


def _escape(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace(
        "\n", " "
    )


def _status_label(payload: Mapping[str, Any], status: str) -> str:
    return str(payload["status_labels"][status])


def _markdown(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Website Compatibility Data",
        "",
        f"Review state: `{payload['review_state']}`",
        f"Maturity: `{payload['maturity']}`",
        "",
        payload["identity_note"],
        "",
        payload["revision_policy"],
        "",
        f"## {payload['features']['title']}",
        "",
        payload["features"]["description"],
        "",
        "| Plugin | Path | Status | Description | Limitations |",
        "|---|---|---|---|---|",
    ]
    for row in payload["features"]["rows"]:
        lines.append(
            "| `{}` | `{}` | {} | {} | {} |".format(
                _escape(row["plugin_id"]),
                _escape(row["plugin_path"]),
                _escape(_status_label(payload, row["status"])),
                _escape(row["description"]),
                _escape(row["limitations"]),
            )
        )
    lines.extend(["", "### Represented in the other matrices", ""])
    for group, plugin_ids in payload["features"][
        "represented_elsewhere"
    ].items():
        label = str(group).replace("_", " ").title()
        lines.append(
            f"- **{_escape(label)}:** "
            + ", ".join(f"`{_escape(plugin_id)}`" for plugin_id in plugin_ids)
        )

    providers = payload["providers"]
    lines.extend(
        [
            "",
            f"## {providers['title']}",
            "",
            providers["description"],
            "",
        ]
    )
    header = ["Provider", *[column["label"] for column in providers["columns"]]]
    lines.append("| " + " | ".join(_escape(value) for value in header) + " |")
    lines.append("|" + "|".join("---" for _ in header) + "|")
    for row in providers["rows"]:
        cells = []
        for column in providers["columns"]:
            cell = row["cells"][column["column_id"]]
            cells.append(cell["label"])
        provider_label = f"{row['label']}<br><small>{row['access']}</small>"
        lines.append(
            "| "
            + " | ".join(
                [_escape(provider_label), *[_escape(value) for value in cells]]
            )
            + " |"
        )

    model_tools = payload["model_family_tools"]
    lines.extend(
        [
            "",
            f"## {model_tools['title']}",
            "",
            model_tools["description"],
            "",
        ]
    )
    for family in model_tools["families"]:
        lines.extend(
            [
                f"### {_escape(family['label'])}",
                "",
                "| Tool | Status | Description |",
                "|---|---|---|",
            ]
        )
        for tool in family["tools"]:
            lines.append(
                "| {} | {} | {} |".format(
                    _escape(tool["name"]),
                    _escape(_status_label(payload, tool["status"])),
                    _escape(tool["description"]),
                )
            )
        lines.append("")
    return "\n".join(lines)


def _outputs() -> dict[Path, str]:
    source = _load_json(SOURCE)
    feature_catalog = _load_json(FEATURE_CATALOG)
    application_rows = _application_feature_rows()
    provider_matrix = _load_json(PROVIDER_MATRIX)
    _validate_features(
        source,
        feature_catalog=feature_catalog,
        application_rows=application_rows,
    )
    _validate_providers(source, provider_matrix)
    _validate_model_tools(source)
    payload = _public_payload(source, feature_catalog, application_rows)
    return {
        OUTPUT_JSON: json.dumps(payload, indent=2) + "\n",
        OUTPUT_MARKDOWN: _markdown(payload),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = _outputs()
    if args.check:
        errors = []
        for path, expected in outputs.items():
            if not path.is_file():
                errors.append(f"{path.name}: missing")
                continue
            actual = path.read_text(encoding="utf-8")
            if actual != expected:
                errors.append(f"{path.name}: generated content differs")
            if re.search(r"\b020\b", actual):
                errors.append(
                    f"{path.name}: numeric task identifier leaked into public data"
                )
            if "tasks/" in actual:
                errors.append(
                    f"{path.name}: internal task path leaked into public data"
                )
        if errors:
            print("\n".join(errors))
            return 1
        print("website compatibility data check passed")
        return 0
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    print("wrote " + ", ".join(path.name for path in outputs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())