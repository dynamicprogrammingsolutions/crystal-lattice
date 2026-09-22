"""Durable, regenerable result packages for completed evaluations.

A result package preserves one completed evaluation as compact committed
records plus deterministically regenerated human and machine views:

- *collection* reads suite-selected records and environment-owned review
  projections and writes the committed source records, the report
  configuration, and a manifest;
- *rendering* reads only the committed package and regenerates every view,
  so layout and presentation can change without rerunning models or keeping
  temporary raw run directories;
- *checking* verifies manifest hashes and byte-for-byte regeneration.

The module defines structural contracts only: package identity, run
references, availability states, redaction, path-normalization bookkeeping,
and one configured usage/cost presentation. Suite and environment records
remain opaque named values. It does not define sessions, messages, requests,
tools, providers, tasks, assessments, or scores, and it does not participate
in :class:`agent_eval.AgentEval` runs.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]

from .services import jsonable

MANIFEST_PATH = "manifest.json"
REPORT_CONFIG_PATH = "report-config.toml"
MANIFEST_SCHEMA_VERSION = 1

CAPTURED = "captured"
RECONSTRUCTED = "reconstructed"
UNAVAILABLE = "unavailable"
AVAILABILITY_STATES = (CAPTURED, RECONSTRUCTED, UNAVAILABLE)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def availability(
    state: str,
    *,
    detail: str | None = None,
    verified: bool | None = None,
) -> dict[str, Any]:
    """Build one availability record."""

    if state not in AVAILABILITY_STATES:
        raise ValueError(f"unknown availability state: {state!r}")
    value: dict[str, Any] = {"state": state}
    if detail is not None:
        value["detail"] = detail
    if state == RECONSTRUCTED and verified is not None:
        value["verified"] = bool(verified)
    return value


def render_json_text(value: object) -> str:
    """Render deterministic, redacted JSON text for a committed record."""

    return (
        json.dumps(
            jsonable(value),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    )


def apply_replacements(text: str, replacements: Mapping[str, str]) -> str:
    """Apply an original-to-placeholder mapping in the given order."""

    for original in sorted(replacements, key=len, reverse=True):
        text = text.replace(original, replacements[original])
    return text


def restore_replacements(text: str, replacements: Mapping[str, str]) -> str:
    """Reverse :func:`apply_replacements` using the same mapping."""

    inverse = {placeholder: original for original, placeholder in replacements.items()}
    for placeholder in sorted(inverse, key=len, reverse=True):
        text = text.replace(placeholder, inverse[placeholder])
    return text


@dataclass(frozen=True)
class CollectedFile:
    """One committed source record supplied by a package owner."""

    relative_path: str
    content: str
    provenance: Mapping[str, object] | None = None


@dataclass(frozen=True)
class GeneratedView:
    """One regenerable view produced from committed records."""

    relative_path: str
    content: str


ViewBuilder = Callable[["PackageRecords"], "Sequence[GeneratedView]"]


def collect_result_package(
    package_dir: Path,
    *,
    identity: Mapping[str, object],
    runs: Sequence[Mapping[str, object]],
    files: Iterable[CollectedFile],
    report_config_text: str,
    generator_version: str,
    replace: bool = False,
) -> Path:
    """Write the committed source records and manifest of one package.

    The caller (normally a suite adapter) supplies the package identity, the
    run inventory, the committed records, and the report configuration text.
    Collection never invokes a model and never reads a raw run directory;
    those reads belong to the caller.
    """

    package_dir = Path(package_dir)
    if package_dir.exists() and any(package_dir.iterdir()):
        if not replace:
            raise ValueError(
                f"package directory is not empty: {package_dir} "
                "(pass replace=True to re-collect)"
            )
        shutil.rmtree(package_dir)
    collected = _validate_runs(runs)
    files = list(files)
    seen: set[str] = set()
    for item in files:
        _check_relative_path(item.relative_path)
        if item.relative_path in seen:
            raise ValueError(f"duplicate collected file: {item.relative_path}")
        seen.add(item.relative_path)
        if item.relative_path in (MANIFEST_PATH, REPORT_CONFIG_PATH):
            raise ValueError(
                f"collected file collides with package registry: {item.relative_path}"
            )
    if not report_config_text.endswith("\n"):
        report_config_text += "\n"

    package_dir.mkdir(parents=True, exist_ok=True)
    registry: dict[str, dict[str, object]] = {}
    for item in sorted(files, key=lambda value: value.relative_path):
        path = package_dir / item.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(item.content, encoding="utf-8")
        registry[item.relative_path] = {
            "sha256": sha256_text(item.content),
            "bytes": len(item.content.encode("utf-8")),
            "provenance": jsonable(item.provenance) if item.provenance else None,
        }
    config_path = package_dir / REPORT_CONFIG_PATH
    config_path.write_text(report_config_text, encoding="utf-8")
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "generator_version": generator_version,
        "identity": jsonable(identity),
        "report_config": {
            "path": REPORT_CONFIG_PATH,
            "sha256": sha256_text(report_config_text),
        },
        "runs": collected,
        "files": {
            "collected": registry,
            "generated": {},
        },
    }
    _write_manifest(package_dir, manifest)
    return package_dir


class PackageRecords:
    """Read-only access to one committed package."""

    def __init__(self, package_dir: Path) -> None:
        self.package_dir = Path(package_dir)
        manifest_path = self.package_dir / MANIFEST_PATH
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError(f"invalid manifest: {manifest_path}")
        if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported manifest schema version: "
                f"{manifest.get('schema_version')!r}"
            )
        self.manifest: dict[str, Any] = manifest
        config_text = (
            self.package_dir / str(manifest.get("report_config", {}).get("path"))
        ).read_text(encoding="utf-8")
        self.report_config_text = config_text
        self.report_config: dict[str, Any] = tomllib.loads(config_text)

    @property
    def identity(self) -> Mapping[str, Any]:
        return self.manifest.get("identity", {})

    @property
    def runs(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(self.manifest.get("runs", ()))

    @property
    def collected_paths(self) -> tuple[str, ...]:
        return tuple(self.manifest.get("files", {}).get("collected", {}))

    def collected_text(self, relative_path: str) -> str:
        return (self.package_dir / relative_path).read_text(encoding="utf-8")

    def collected_json(self, relative_path: str) -> Any:
        return json.loads(self.collected_text(relative_path))


def render_result_package(
    package_dir: Path,
    *,
    view_builders: Iterable[ViewBuilder] = (),
) -> list[Path]:
    """Regenerate every view from committed records and update the manifest."""

    records = PackageRecords(package_dir)
    views = list(build_cost_views(records))
    for builder in view_builders:
        views.extend(builder(records))
    seen: set[str] = set()
    for view in views:
        _check_relative_path(view.relative_path)
        if view.relative_path in seen:
            raise ValueError(f"duplicate generated view: {view.relative_path}")
        seen.add(view.relative_path)
    written: list[Path] = []
    for view in sorted(views, key=lambda value: value.relative_path):
        path = records.package_dir / view.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(view.content, encoding="utf-8")
        written.append(path)
    for relative_path in records.manifest.get("files", {}).get("generated", {}):
        if relative_path not in seen:
            stale = records.package_dir / relative_path
            if stale.exists():
                stale.unlink()
    generated: dict[str, dict[str, object]] = {}
    for view in views:
        generated[view.relative_path] = {
            "sha256": sha256_text(view.content),
            "bytes": len(view.content.encode("utf-8")),
        }
    records.manifest["files"]["generated"] = dict(
        sorted(generated.items())
    )
    _write_manifest(records.package_dir, records.manifest)
    return written


def check_result_package(
    package_dir: Path,
    *,
    view_builders: Iterable[ViewBuilder] = (),
) -> list[str]:
    """Verify hashes and byte-for-byte regeneration; return problems."""

    problems: list[str] = []
    try:
        records = PackageRecords(package_dir)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [f"package does not load: {error}"]
    manifest = records.manifest
    files = manifest.get("files", {})

    config_entry = manifest.get("report_config", {})
    config_path = package_dir / str(config_entry.get("path"))
    if not config_path.exists():
        problems.append(f"missing report config: {config_path}")
    elif sha256_text(config_path.read_text(encoding="utf-8")) != config_entry.get(
        "sha256"
    ):
        problems.append(f"report config hash mismatch: {config_path}")

    for relative_path, entry in sorted(files.get("collected", {}).items()):
        path = package_dir / relative_path
        if not path.exists():
            problems.append(f"missing collected file: {relative_path}")
            continue
        if sha256_text(path.read_text(encoding="utf-8")) != entry.get("sha256"):
            problems.append(f"collected file hash mismatch: {relative_path}")

    expected_views: dict[str, GeneratedView] = {}
    try:
        for view in (
            *build_cost_views(records),
            *(view for builder in view_builders for view in builder(records)),
        ):
            expected_views[view.relative_path] = view
    except Exception as error:  # noqa: BLE001 - report, do not crash the check
        problems.append(f"view generation failed: {error}")
        expected_views = {}

    for relative_path, entry in sorted(files.get("generated", {}).items()):
        path = package_dir / relative_path
        if not path.exists():
            problems.append(f"missing generated file: {relative_path}")
            continue
        actual = path.read_text(encoding="utf-8")
        if sha256_text(actual) != entry.get("sha256"):
            problems.append(f"generated file hash mismatch: {relative_path}")
        view = expected_views.get(relative_path)
        if view is None:
            problems.append(f"generated file is no longer produced: {relative_path}")
        elif view.content != actual:
            problems.append(f"generated file is not reproducible: {relative_path}")

    for relative_path in sorted(expected_views):
        if relative_path not in files.get("generated", {}):
            problems.append(f"generated view is not registered: {relative_path}")
        elif not (package_dir / relative_path).exists():
            problems.append(f"generated view is missing on disk: {relative_path}")

    for path in sorted(package_dir.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        relative = path.relative_to(package_dir).as_posix()
        if relative in (MANIFEST_PATH, str(config_entry.get("path"))):
            continue
        if relative not in files.get("collected", {}) and relative not in files.get(
            "generated", {}
        ):
            problems.append(f"unregistered file: {relative}")
    return problems


def build_cost_views(records: PackageRecords) -> tuple[GeneratedView, ...]:
    """Build the generic per-run usage and estimated-cost views."""

    cost_config = records.report_config.get("cost", {})
    currency = str(cost_config.get("currency", "USD"))
    prices = cost_config.get("prices", {})
    if not isinstance(prices, Mapping):
        prices = {}
    provenance = cost_config.get("price_provenance", {})

    rows: list[dict[str, Any]] = []
    for run in records.runs:
        usage = run.get("usage")
        model = run.get("model")
        model_prices = prices.get(str(model)) if model is not None else None
        rows.append(_cost_row(run, usage, model_prices, currency))
    csv_lines = [_cost_csv_header()]
    for row in rows:
        csv_lines.append(_cost_csv_row(row))
    md_lines = [
        "# Usage and estimated cost",
        "",
        "One row per run. Estimated cost uses only the price table pinned by",
        f"this package's report configuration ({currency}). Missing usage or",
        "pricing stays visibly incomplete and is never treated as zero.",
        "",
        "| Run | Provider | Model | Effort | Input | Cached input |"
        " Cache write | Output | Reasoning | Estimated cost |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        md_lines.append(
            "| {run_id} | {provider} | {model} | {effort} | {input} |"
            " {cached} | {cache_write} | {output} | {reasoning} | {cost} |".format(
                run_id=f"`{row['run_id']}`",
                provider=row["provider"] or "—",
                model=row["model"] or "—",
                effort=row["reasoning_effort"] or "—",
                input=_format_count(row["input_tokens"]),
                cached=_format_count(row["cached_input_tokens"]),
                cache_write=_format_count(row["cache_write_tokens"]),
                output=_format_count(row["output_tokens"]),
                reasoning=_format_count(row["reasoning_tokens"]),
                cost=row["cost_cell"],
            )
        )
    priced = [row for row in rows if row["cost"] is not None]
    md_lines.extend(
        [
            "",
            f"Estimated cost is available for {len(priced)} of {len(rows)} runs.",
        ]
    )
    if priced:
        total = sum(row["cost"] for row in priced)
        md_lines.append(
            f"The total across priced runs is {total:.7f} {currency} and covers"
            " only those runs."
        )
    else:
        md_lines.append("No run has a complete priced estimate.")
    unavailable = [
        row for row in rows if row["usage_state"] == UNAVAILABLE or row["cost"] is None
    ]
    if unavailable:
        md_lines.extend(
            [
                "",
                "## Incomplete rows",
                "",
            ]
        )
        for row in unavailable:
            reason = row["cost_detail"] or row["usage_detail"] or "unknown"
            md_lines.append(f"- `{row['run_id']}`: {reason}")
    if provenance:
        md_lines.extend(["", "## Price provenance", ""])
        if isinstance(provenance, Mapping):
            for key in sorted(provenance):
                md_lines.append(f"- {key}: {provenance[key]}")
    return (
        GeneratedView(relative_path="costs.csv", content="\n".join(csv_lines) + "\n"),
        GeneratedView(relative_path="costs.md", content="\n".join(md_lines) + "\n"),
    )


def estimate_run_cost(
    usage: Mapping[str, Any] | None,
    prices: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Estimate one run's cost from available usage and one pinned price table.

    The calculation splits reported input tokens into mutually exclusive
    ordinary, cached-read, and cache-write buckets so no token is priced
    twice, mirroring the provider plugin's published estimation formula.
    """

    if not isinstance(usage, Mapping):
        return _cost_unavailable("usage record missing")
    state = (usage.get("availability") or {}).get("state")
    if state == UNAVAILABLE:
        detail = (usage.get("availability") or {}).get("detail")
        return _cost_unavailable(detail or "usage unavailable")
    if state not in AVAILABILITY_STATES:
        return _cost_unavailable(f"invalid usage availability state: {state!r}")
    input_total = usage.get("input_tokens")
    output_total = usage.get("output_tokens")
    if not isinstance(input_total, int) or not isinstance(output_total, int):
        return _cost_unavailable("input or output token counts are unavailable")
    cached_read = usage.get("cached_input_tokens")
    cache_write = usage.get("cache_write_tokens")
    cached_read = cached_read if isinstance(cached_read, int) else 0
    cache_write = cache_write if isinstance(cache_write, int) else 0
    input_total = max(0, input_total)
    output_total = max(0, output_total)
    if cached_read + cache_write > input_total:
        if cached_read >= cache_write:
            cached_read = max(0, input_total - cache_write)
        else:
            cache_write = max(0, input_total - cached_read)
        ordinary_input = 0
    else:
        ordinary_input = input_total - cached_read - cache_write
    if not isinstance(prices, Mapping):
        return _cost_unavailable("price not pinned for this model")
    input_price = prices.get("input_per_1m")
    output_price = prices.get("output_per_1m")
    if not isinstance(input_price, (int, float)) or not isinstance(
        output_price, (int, float)
    ):
        return _cost_unavailable("price table is missing input or output rates")
    cached_price = prices.get("cached_input_per_1m")
    if cached_read > 0 and not isinstance(cached_price, (int, float)):
        return _cost_unavailable("price table is missing the cached-input rate")
    cache_write_price = prices.get("cache_write_per_1m")
    if cache_write > 0 and not isinstance(cache_write_price, (int, float)):
        cache_write_price = input_price
    estimated = (
        ordinary_input * float(input_price)
        + cached_read * (float(cached_price) if cached_price is not None else 0.0)
        + cache_write * float(cache_write_price)
        + output_total * float(output_price)
    ) / 1_000_000.0
    return {
        "cost": estimated,
        "basis": "pinned-price-table",
        "detail": None,
        "buckets": {
            "ordinary_input_tokens": ordinary_input,
            "cached_read_tokens": cached_read,
            "cache_write_tokens": cache_write,
            "output_tokens": output_total,
        },
    }


def _cost_unavailable(detail: str) -> dict[str, Any]:
    return {"cost": None, "basis": None, "detail": detail, "buckets": None}


def _cost_row(
    run: Mapping[str, Any],
    usage: Mapping[str, Any] | None,
    model_prices: Any,
    currency: str,
) -> dict[str, Any]:
    usage_state = UNAVAILABLE
    usage_detail: str | None = None
    if isinstance(usage, Mapping):
        record = usage.get("availability") or {}
        usage_state = str(record.get("state", UNAVAILABLE))
        usage_detail = record.get("detail")
    estimate = estimate_run_cost(usage, model_prices)
    cost = estimate["cost"]
    if cost is None:
        cost_cell = "unknown"
    else:
        cost_cell = f"{cost:.7f} {currency}"
    return {
        "run_id": run.get("run_id"),
        "label": run.get("label"),
        "provider": run.get("provider"),
        "model": run.get("model"),
        "reasoning_effort": run.get("reasoning_effort"),
        "input_tokens": usage.get("input_tokens") if isinstance(usage, Mapping) else None,
        "cached_input_tokens": (
            usage.get("cached_input_tokens") if isinstance(usage, Mapping) else None
        ),
        "cached_input_estimated": (
            bool(usage.get("cached_input_estimated"))
            if isinstance(usage, Mapping)
            else None
        ),
        "cache_write_tokens": (
            usage.get("cache_write_tokens") if isinstance(usage, Mapping) else None
        ),
        "output_tokens": usage.get("output_tokens") if isinstance(usage, Mapping) else None,
        "reasoning_tokens": (
            usage.get("reasoning_tokens") if isinstance(usage, Mapping) else None
        ),
        "usage_state": usage_state,
        "usage_detail": usage_detail,
        "cost": cost,
        "cost_basis": estimate["basis"],
        "cost_detail": estimate["detail"],
        "cost_cell": cost_cell,
    }


_COST_COLUMNS = (
    "run_id",
    "label",
    "provider",
    "model",
    "reasoning_effort",
    "input_tokens",
    "cached_input_tokens",
    "cached_input_estimated",
    "cache_write_tokens",
    "output_tokens",
    "reasoning_tokens",
    "usage_state",
    "usage_detail",
    "estimated_cost",
    "cost_basis",
    "cost_detail",
)


def _cost_csv_header() -> str:
    return ",".join(_COST_COLUMNS)


def _cost_csv_row(row: Mapping[str, Any]) -> str:
    values: list[str] = []
    for column in _COST_COLUMNS:
        if column == "estimated_cost":
            value = row["cost"]
            values.append("" if value is None else f"{value:.7f}")
            continue
        raw = row.get(column)
        if raw is None:
            values.append("")
        else:
            text = str(raw)
            if any(character in text for character in (",", '"', "\n")):
                text = '"' + text.replace('"', '""') + '"'
            values.append(text)
    return ",".join(values)


def _format_count(value: Any) -> str:
    return "unknown" if value is None else f"{value}"


def _validate_runs(runs: Sequence[Mapping[str, object]]) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for run in runs:
        run_id = run.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            raise ValueError("every run requires a non-empty string run_id")
        if run_id in seen:
            raise ValueError(f"duplicate run_id: {run_id}")
        seen.add(run_id)
        value = jsonable(run)
        usage = value.get("usage")
        if isinstance(usage, Mapping):
            state = (usage.get("availability") or {}).get("state")
            if state not in AVAILABILITY_STATES:
                raise ValueError(f"invalid usage availability state: {state!r}")
        collected.append(value)
    return collected


def _check_relative_path(relative_path: str) -> None:
    if not relative_path or relative_path.startswith("/") or ".." in Path(
        relative_path
    ).parts:
        raise ValueError(f"unsafe package path: {relative_path}")
    if re.search(r"[\x00-\x1f]", relative_path):
        raise ValueError(f"unsafe package path: {relative_path}")


def _write_manifest(package_dir: Path, manifest: Mapping[str, Any]) -> None:
    path = package_dir / MANIFEST_PATH
    path.write_text(render_json_text(manifest), encoding="utf-8")