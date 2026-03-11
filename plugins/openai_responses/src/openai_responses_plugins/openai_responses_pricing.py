"""Pricing snapshot loading and estimation helpers for OpenAI Responses.

The refresh script writes a checked-in pricing snapshot sourced from official
OpenAI model documentation pages. Runtime code reads only the saved snapshot so
estimated-cost behavior is deterministic and does not depend on live network
access.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from html import unescape
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


DEFAULT_MODEL_DOC_SLUGS = (
    "gpt-5",
    "gpt-5-mini",
    "gpt-5-nano",
    "gpt-5.1",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "gpt-4o",
    "gpt-4o-mini",
)

_DEFAULT_SNAPSHOT_RELATIVE = "data/openai_model_pricing.json"
_SNAPSHOT_SUFFIX_RE = re.compile(r"^(?P<base>.+)-\d{4}-\d{2}-\d{2}$")
_PRICING_VALUE_RE = re.compile(
    r"<div>\s*(Input|Cached input|Output)\s*</div>"
    r"\s*<div[^>]*>\s*\$(\d+(?:\.\d+)?)\s*</div>",
    re.IGNORECASE,
)


def default_snapshot_path() -> Path:
    return Path(__file__).resolve().parent / _DEFAULT_SNAPSHOT_RELATIVE


@lru_cache(maxsize=1)
def load_pricing_snapshot(path: str | None = None) -> Dict[str, Any]:
    snapshot_path = Path(path) if path else default_snapshot_path()
    with snapshot_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise RuntimeError("invalid OpenAI pricing snapshot payload")
    models = data.get("models")
    if not isinstance(models, dict):
        raise RuntimeError("OpenAI pricing snapshot missing models mapping")
    return data


def clear_pricing_snapshot_cache() -> None:
    load_pricing_snapshot.cache_clear()


def normalize_model_name(model: str) -> str:
    if not isinstance(model, str):
        return ""
    value = model.strip()
    if not value:
        return ""
    match = _SNAPSHOT_SUFFIX_RE.match(value)
    if match:
        return match.group("base")
    return value


def resolve_pricing_entry(
    model: str,
    snapshot: Dict[str, Any] | None = None,
    snapshot_path: str | None = None,
) -> Optional[Dict[str, Any]]:
    if not isinstance(model, str) or not model.strip():
        return None
    data = snapshot or load_pricing_snapshot(snapshot_path)
    models = data.get("models")
    if not isinstance(models, dict):
        return None

    direct = models.get(model)
    if isinstance(direct, dict):
        return direct

    normalized = normalize_model_name(model)
    resolved = models.get(normalized)
    if isinstance(resolved, dict):
        return resolved

    return None


def _pricing_block(entry: Dict[str, Any]) -> Optional[Dict[str, float]]:
    pricing = entry.get("pricing")
    if not isinstance(pricing, dict):
        return None

    required = ("input_per_1m", "cached_input_per_1m", "output_per_1m")
    out: Dict[str, float] = {}
    for key in required:
        raw = pricing.get(key)
        if not isinstance(raw, (int, float)):
            return None
        out[key] = float(raw)
    return out


def estimate_usage_cost(
    usage: Dict[str, Any],
    model: str,
    snapshot: Dict[str, Any] | None = None,
    snapshot_path: str | None = None,
) -> Optional[float]:
    if not isinstance(usage, dict) or not usage:
        return None

    entry = resolve_pricing_entry(model, snapshot=snapshot, snapshot_path=snapshot_path)
    if not isinstance(entry, dict):
        return None

    pricing = _pricing_block(entry)
    if pricing is None:
        return None

    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    if not isinstance(input_tokens, (int, float)) or not isinstance(output_tokens, (int, float)):
        return None

    cached_tokens = 0
    details = usage.get("input_tokens_details")
    if isinstance(details, dict):
        raw_cached = details.get("cached_tokens")
        if isinstance(raw_cached, (int, float)):
            cached_tokens = max(0, int(raw_cached))

    input_total = max(0, int(input_tokens))
    output_total = max(0, int(output_tokens))
    cached_total = min(input_total, cached_tokens)
    uncached_total = input_total - cached_total

    estimated = (
        uncached_total * pricing["input_per_1m"]
        + cached_total * pricing["cached_input_per_1m"]
        + output_total * pricing["output_per_1m"]
    ) / 1_000_000.0

    return float(estimated)


def extract_pricing_from_model_doc_html(
    html: str,
    model: str,
    source_url: str,
) -> Dict[str, Any]:
    if not isinstance(html, str) or not html.strip():
        raise ValueError("model doc html must be a non-empty string")

    compact = re.sub(r"\s+", " ", unescape(html))
    pricing_anchor = compact.find("Text tokens")
    if pricing_anchor < 0:
        raise RuntimeError(f"pricing section not found for {model}")

    section_end = len(compact)
    for marker in ("Quick comparison", "Modalities", "Endpoints"):
        idx = compact.find(marker, pricing_anchor)
        if idx >= 0:
            section_end = min(section_end, idx)
    section = compact[pricing_anchor:section_end]

    matches = _PRICING_VALUE_RE.findall(section)
    prices: Dict[str, float] = {}
    for label, value in matches:
        label_key = label.strip().lower().replace(" ", "_")
        prices[label_key] = float(value)

    missing = [key for key in ("input", "cached_input", "output") if key not in prices]
    if missing:
        raise RuntimeError(f"missing pricing fields for {model}: {', '.join(missing)}")

    return {
        "model": model,
        "source_url": source_url,
        "pricing": {
            "input_per_1m": prices["input"],
            "cached_input_per_1m": prices["cached_input"],
            "output_per_1m": prices["output"],
        },
    }


def build_snapshot_payload(
    fetched_at: str,
    model_entries: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    models: Dict[str, Dict[str, Any]] = {}
    for entry in model_entries:
        if not isinstance(entry, dict):
            continue
        model = entry.get("model")
        if not isinstance(model, str) or not model:
            continue
        models[model] = entry

    return {
        "version": 1,
        "fetched_at": fetched_at,
        "source_base_url": "https://developers.openai.com/api/docs/models",
        "models": dict(sorted(models.items())),
    }