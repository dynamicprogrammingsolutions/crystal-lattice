from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from agent_eval.result_packages import (
    AVAILABILITY_STATES,
    CollectedFile,
    GeneratedView,
    PackageRecords,
    apply_replacements,
    availability,
    check_result_package,
    collect_result_package,
    estimate_run_cost,
    render_json_text,
    render_result_package,
    restore_replacements,
    sha256_text,
)

REPORT_CONFIG = """\
[cost]
currency = "USD"

[cost.prices."gpt-test"]
input_per_1m = 1.0
cached_input_per_1m = 0.1
cache_write_per_1m = 1.25
output_per_1m = 6.0

[cost.price_provenance]
source = "unit-test price page"
fetched_at = "2026-07-18"
"""


def _usage(
    *,
    input_tokens: int | None = 1000,
    cached: int | None = 200,
    cache_write: int | None = 100,
    output: int | None = 50,
    state: str = "captured",
) -> dict[str, object]:
    return {
        "availability": availability(state),
        "input_tokens": input_tokens,
        "cached_input_tokens": cached,
        "cached_input_estimated": True,
        "cache_write_tokens": cache_write,
        "output_tokens": output,
        "reasoning_tokens": 10,
        "provider_reported_cost": 0.001145,
    }


def _runs() -> list[dict[str, object]]:
    return [
        {
            "run_id": "run-gpt-1",
            "label": "GPT subject run",
            "provider": "gpt",
            "model": "gpt-test",
            "reasoning_effort": "high",
            "usage": _usage(),
        },
        {
            "run_id": "run-glm-1",
            "label": "GLM subject run",
            "provider": "glm",
            "model": "glm-test",
            "reasoning_effort": "max",
            "usage": {
                "availability": availability(
                    "unavailable", detail="provider saved no usage metadata"
                )
            },
        },
    ]


def _files() -> list[CollectedFile]:
    return [
        CollectedFile(
            relative_path="cases/case-a/cell.json",
            content=render_json_text({"scenario": "case-a", "secret_token": "x"}),
            provenance={"source": "synthetic"},
        ),
        CollectedFile(
            relative_path="shared/system-messages/gpt.md",
            content="# Compiled message\n",
            provenance={"source": "synthetic"},
        ),
    ]


def _suite_views(records: PackageRecords) -> list[GeneratedView]:
    cell = records.collected_json("cases/case-a/cell.json")
    return [
        GeneratedView(
            relative_path="index.md",
            content=f"# Package index\n\nScenario: {cell['scenario']}\n",
        )
    ]


def _collect(package_dir: Path, *, replace: bool = False) -> Path:
    collect_result_package(
        package_dir,
        identity={
            "name": "unit-package",
            "label": "Unit package",
            "dataset_id": "unit-1",
        },
        runs=_runs(),
        files=_files(),
        report_config_text=REPORT_CONFIG,
        generator_version="unit-test-v1",
        replace=replace,
    )
    return package_dir


def test_collect_writes_records_and_manifest(tmp_path: Path) -> None:
    package_dir = _collect(tmp_path / "package")

    manifest = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["generator_version"] == "unit-test-v1"
    assert manifest["identity"]["dataset_id"] == "unit-1"
    assert manifest["files"]["generated"] == {}
    collected = manifest["files"]["collected"]
    assert set(collected) == {
        "cases/case-a/cell.json",
        "shared/system-messages/gpt.md",
    }
    content = (package_dir / "cases/case-a/cell.json").read_text(encoding="utf-8")
    assert collected["cases/case-a/cell.json"]["sha256"] == sha256_text(content)
    assert manifest["report_config"]["sha256"] == sha256_text(
        (package_dir / "report-config.toml").read_text(encoding="utf-8")
    )
    assert [run["run_id"] for run in manifest["runs"]] == ["run-gpt-1", "run-glm-1"]


def test_collect_redacts_sensitive_record_values(tmp_path: Path) -> None:
    _collect(tmp_path / "package")

    cell = json.loads(
        (tmp_path / "package" / "cases/case-a/cell.json").read_text(encoding="utf-8")
    )

    assert cell["secret_token"] == "<redacted>"
    assert cell["scenario"] == "case-a"


def test_collect_rejects_invalid_run_inventory(tmp_path: Path) -> None:
    duplicate = _runs()
    duplicate.append(dict(duplicate[0]))
    with pytest.raises(ValueError, match="duplicate run_id"):
        _collect_runs(tmp_path / "package", duplicate)
    bad_state = _runs()
    bad_state[0]["usage"] = {"availability": {"state": "guessed"}}
    with pytest.raises(ValueError, match="invalid usage availability state"):
        _collect_runs(tmp_path / "package", bad_state)


def _collect_runs(package_dir: Path, runs: list[dict[str, object]]) -> None:
    collect_result_package(
        package_dir,
        identity={"name": "unit-package"},
        runs=runs,
        files=_files(),
        report_config_text=REPORT_CONFIG,
        generator_version="unit-test-v1",
    )


def test_collect_rejects_unsafe_and_registry_paths(tmp_path: Path) -> None:
    for relative_path, match in (
        ("../outside.json", "unsafe package path"),
        ("/abs.json", "unsafe package path"),
        ("a/../b.json", "unsafe package path"),
        ("manifest.json", "collides with package registry"),
        ("report-config.toml", "collides with package registry"),
    ):
        with pytest.raises(ValueError, match=match):
            collect_result_package(
                tmp_path / "package",
                identity={"name": "x"},
                runs=_runs(),
                files=[CollectedFile(relative_path=relative_path, content="x")],
                report_config_text=REPORT_CONFIG,
                generator_version="v",
            )


def test_collect_requires_replace_for_existing_package(tmp_path: Path) -> None:
    package_dir = _collect(tmp_path / "package")
    with pytest.raises(ValueError, match="not empty"):
        _collect(package_dir)
    collect_result_package(
        package_dir,
        identity={"name": "unit-package"},
        runs=_runs(),
        files=_files(),
        report_config_text=REPORT_CONFIG,
        generator_version="unit-test-v1",
        replace=True,
    )
    assert (package_dir / "manifest.json").exists()


def test_render_regenerates_views_deterministically(tmp_path: Path) -> None:
    package_dir = _collect(tmp_path / "package")

    render_result_package(package_dir, view_builders=[_suite_views])
    first = {
        path.relative_to(package_dir).as_posix()
        for path in package_dir.rglob("*")
        if path.is_file()
    }
    contents = {
        relative: (package_dir / relative).read_text(encoding="utf-8")
        for relative in first
    }
    render_result_package(package_dir, view_builders=[_suite_views])
    second = {
        path.relative_to(package_dir).as_posix()
        for path in package_dir.rglob("*")
        if path.is_file()
    }
    assert first == second
    for relative in first:
        assert contents[relative] == (package_dir / relative).read_text(
            encoding="utf-8"
        )

    manifest = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
    assert set(manifest["files"]["generated"]) == {
        "costs.csv",
        "costs.md",
        "index.md",
    }


def test_render_removes_stale_generated_views(tmp_path: Path) -> None:
    package_dir = _collect(tmp_path / "package")
    render_result_package(package_dir, view_builders=[_suite_views])
    assert (package_dir / "index.md").exists()

    render_result_package(package_dir, view_builders=[])

    assert not (package_dir / "index.md").exists()
    manifest = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
    assert set(manifest["files"]["generated"]) == {"costs.csv", "costs.md"}


def test_cost_views_present_usage_and_unknowns(tmp_path: Path) -> None:
    package_dir = _collect(tmp_path / "package")
    render_result_package(package_dir)

    csv_text = (package_dir / "costs.csv").read_text(encoding="utf-8")
    lines = csv_text.strip().splitlines()
    assert lines[0].startswith("run_id,label,provider,model,reasoning_effort")
    gpt_row = lines[1].split(",")
    glm_row = lines[2].split(",")
    assert gpt_row[0] == "run-gpt-1"
    assert gpt_row[5] == "1000"
    assert gpt_row[13] == "0.0011450"
    assert glm_row[0] == "run-glm-1"
    assert glm_row[5] == ""
    assert glm_row[13] == ""
    assert glm_row[11] == "unavailable"

    md_text = (package_dir / "costs.md").read_text(encoding="utf-8")
    assert "One row per run." in md_text
    assert "`run-gpt-1`" in md_text
    assert "Estimated cost is available for 1 of 2 runs." in md_text
    assert "provider saved no usage metadata" in md_text
    assert "unit-test price page" in md_text


def test_check_passes_and_detects_drift(tmp_path: Path) -> None:
    package_dir = _collect(tmp_path / "package")
    render_result_package(package_dir, view_builders=[_suite_views])
    assert check_result_package(package_dir, view_builders=[_suite_views]) == []

    collected = package_dir / "cases/case-a/cell.json"
    collected.write_text("tampered\n", encoding="utf-8")
    problems = check_result_package(package_dir, view_builders=[_suite_views])
    assert any("collected file hash mismatch" in problem for problem in problems)

    _collect(package_dir, replace=True)
    render_result_package(package_dir, view_builders=[_suite_views])
    generated = package_dir / "index.md"
    generated.write_text("tampered view\n", encoding="utf-8")
    problems = check_result_package(package_dir, view_builders=[_suite_views])
    assert any("not reproducible" in problem for problem in problems)

    _collect(package_dir, replace=True)
    render_result_package(package_dir, view_builders=[_suite_views])
    (package_dir / "stray.txt").write_text("stray\n", encoding="utf-8")
    problems = check_result_package(package_dir, view_builders=[_suite_views])
    assert any("unregistered file" in problem for problem in problems)

    _collect(package_dir, replace=True)
    render_result_package(package_dir, view_builders=[_suite_views])
    (package_dir / "costs.csv").unlink()
    problems = check_result_package(package_dir, view_builders=[_suite_views])
    assert any("missing generated file" in problem for problem in problems)


def test_check_detects_view_registered_but_unregistered_on_disk(
    tmp_path: Path,
) -> None:
    package_dir = _collect(tmp_path / "package")
    render_result_package(package_dir, view_builders=[_suite_views])

    problems = check_result_package(package_dir, view_builders=[])

    assert any("is no longer produced" in problem for problem in problems)


def test_package_works_from_a_clean_checkout(tmp_path: Path) -> None:
    package_dir = _collect(tmp_path / "package")
    render_result_package(package_dir, view_builders=[_suite_views])

    checkout = tmp_path / "checkout"
    shutil.copytree(package_dir, checkout)

    assert check_result_package(checkout, view_builders=[_suite_views]) == []
    records = PackageRecords(checkout)
    assert records.identity["name"] == "unit-package"
    assert records.report_config["cost"]["currency"] == "USD"
    assert records.collected_json("cases/case-a/cell.json")["scenario"] == "case-a"


def test_estimate_run_cost_uses_pinned_price_buckets() -> None:
    prices = {
        "input_per_1m": 1.0,
        "cached_input_per_1m": 0.1,
        "cache_write_per_1m": 1.25,
        "output_per_1m": 6.0,
    }
    estimate = estimate_run_cost(_usage(), prices)
    assert estimate["cost"] == pytest.approx(0.001145)
    assert estimate["basis"] == "pinned-price-table"
    assert estimate["buckets"] == {
        "ordinary_input_tokens": 700,
        "cached_read_tokens": 200,
        "cache_write_tokens": 100,
        "output_tokens": 50,
    }


def test_estimate_run_cost_clamps_inconsistent_detail_counters() -> None:
    prices = {
        "input_per_1m": 1.0,
        "cached_input_per_1m": 0.1,
        "cache_write_per_1m": 1.25,
        "output_per_1m": 6.0,
    }
    estimate = estimate_run_cost(
        _usage(input_tokens=100, cached=80, cache_write=50, output=10),
        prices,
    )
    assert estimate["buckets"] == {
        "ordinary_input_tokens": 0,
        "cached_read_tokens": 50,
        "cache_write_tokens": 50,
        "output_tokens": 10,
    }
    assert estimate["cost"] == pytest.approx(
        (50 * 0.1 + 50 * 1.25 + 10 * 6.0) / 1_000_000
    )


def test_estimate_run_cost_falls_back_to_input_rate_for_cache_writes() -> None:
    estimate = estimate_run_cost(
        _usage(input_tokens=100, cached=0, cache_write=40, output=0),
        {"input_per_1m": 2.0, "output_per_1m": 6.0},
    )
    assert estimate["cost"] == pytest.approx((60 * 2.0 + 40 * 2.0) / 1_000_000)


def test_estimate_run_cost_reports_missing_information() -> None:
    prices = {"input_per_1m": 1.0, "output_per_1m": 6.0}
    unavailable_usage = estimate_run_cost(
        {"availability": availability("unavailable", detail="no metadata")}, prices
    )
    assert unavailable_usage["cost"] is None
    assert unavailable_usage["detail"] == "no metadata"
    missing_price = estimate_run_cost(_usage(), None)
    assert missing_price["cost"] is None
    assert "price not pinned" in str(missing_price["detail"])
    missing_counts = estimate_run_cost(
        {"availability": availability("captured"), "input_tokens": None},
        prices,
    )
    assert missing_counts["cost"] is None
    assert "token counts are unavailable" in missing_counts["detail"]
    missing_cached_rate = estimate_run_cost(
        _usage(cached=10), {"input_per_1m": 1.0, "output_per_1m": 6.0}
    )
    assert "cached-input rate" in missing_cached_rate["detail"]


def test_availability_validates_states() -> None:
    assert availability("captured") == {"state": "captured"}
    assert availability("reconstructed", verified=True) == {
        "state": "reconstructed",
        "verified": True,
    }
    assert availability("inherited", detail="from the parent run") == {
        "state": "inherited",
        "detail": "from the parent run",
    }
    assert availability("unavailable", detail="gone") == {
        "state": "unavailable",
        "detail": "gone",
    }
    with pytest.raises(ValueError, match="unknown availability state"):
        availability("guessed")
    assert AVAILABILITY_STATES == (
        "captured",
        "reconstructed",
        "inherited",
        "unavailable",
    )


def test_path_replacements_round_trip() -> None:
    original = "/Users/me/work/run-1/workspace and /Users/me/work elsewhere"
    replacements = {"/Users/me/work": "<root>"}
    normalized = apply_replacements(original, replacements)
    assert "/Users/me" not in normalized
    assert restore_replacements(normalized, replacements) == original
    assert sha256_text(restore_replacements(normalized, replacements)) == sha256_text(
        original
    )
