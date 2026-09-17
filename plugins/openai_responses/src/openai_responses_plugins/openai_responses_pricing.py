"""Pricing snapshot loading and estimation helpers for OpenAI Responses.

The refresh script writes a checked-in pricing snapshot sourced from the
OpenAI pricing page. Runtime code reads only the saved snapshot so
estimated-cost behavior is deterministic and does not depend on live network
access.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from html import unescape
from importlib import resources
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

DEFAULT_PRICING_PAGE_URLS = (
    "https://developers.openai.com/api/docs/pricing?latest-pricing=standard",
    "https://developers.openai.com/api/docs/pricing?latest-pricing=flex",
)

_DEFAULT_SNAPSHOT_RELATIVE = "data/openai_model_pricing.json"
_SNAPSHOT_SUFFIX_RE = re.compile(r"^(?P<base>.+)-\d{4}-\d{2}-\d{2}$")
_TEXT_TOKEN_TABLE_RE = re.compile(
    r'component-export="TextTokenPricingTables".*?props="(.*?)" ssr',
    re.DOTALL,
)
_TIER_RE = re.compile(r'"tier":\[\d+,"([^"]+)"\]')
# Each row starts with the model name followed by one or more price cells.
# Legacy rows have three prices (input, cached input, output); GPT-5.6+ rows
# have four prices (input, cached input, cache writes, output). Capture the
# full price-cell list and interpret by position downstream so the parser
# supports both row shapes without losing older model entries.
_ROW_RE = re.compile(r'\[\[0,"([^"]+)"\]((?:,\[0,(?:[^\]]+)\])+)\]')
_PRICE_CELL_RE = re.compile(r"\[0,([^\]]+)\]")
_CONTEXT_SUFFIX_RE = re.compile(r"\s+\([^)]*context length[^)]*\)$", re.IGNORECASE)


def default_snapshot_path() -> Path:
    return Path(__file__).resolve().parent / _DEFAULT_SNAPSHOT_RELATIVE


@lru_cache(maxsize=1)
def load_pricing_snapshot(path: str | None = None) -> Dict[str, Any]:
    resource = (
        Path(path)
        if path
        else resources.files(__package__).joinpath(_DEFAULT_SNAPSHOT_RELATIVE)
    )
    with resource.open("r", encoding="utf-8") as handle:
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


def normalize_service_tier(service_tier: str | None) -> str:
    if not isinstance(service_tier, str):
        return ""
    return service_tier.strip().lower()


def normalize_pricing_table_model_name(model: str) -> str:
    normalized = normalize_model_name(model)
    if not normalized:
        return ""
    return _CONTEXT_SUFFIX_RE.sub("", normalized).strip()


def resolve_pricing_entry(
    model: str,
    snapshot: Dict[str, Any] | None = None,
    snapshot_path: str | None = None,
    manual_entries: Dict[str, Any] | None = None,
) -> Optional[Dict[str, Any]]:
    if not isinstance(model, str) or not model.strip():
        return None
    data = snapshot or load_pricing_snapshot(snapshot_path)
    models = data.get("models")
    if not isinstance(models, dict):
        models = {}

    direct = models.get(model)
    if isinstance(direct, dict):
        return direct

    normalized = normalize_model_name(model)
    resolved = models.get(normalized)
    if isinstance(resolved, dict):
        return resolved

    if isinstance(manual_entries, dict):
        direct_manual = manual_entries.get(model)
        if isinstance(direct_manual, dict):
            return direct_manual
        normalized_manual = manual_entries.get(normalized)
        if isinstance(normalized_manual, dict):
            return normalized_manual

    return None


def _coerce_price(raw: Any) -> Optional[float]:
    if isinstance(raw, (int, float)):
        return float(raw)
    if not isinstance(raw, str):
        return None

    value = raw.strip().strip('"')
    if not value or value in {"-", "/"}:
        return None
    if value == "null":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _pricing_block_from_mapping(pricing: Any) -> Optional[Dict[str, Optional[float]]]:
    if not isinstance(pricing, dict):
        return None

    input_price = pricing.get("input_per_1m")
    output_price = pricing.get("output_per_1m")
    if not isinstance(input_price, (int, float)) or not isinstance(
        output_price, (int, float)
    ):
        return None

    cached_price = pricing.get("cached_input_per_1m")
    cached_value: Optional[float] = None
    if isinstance(cached_price, (int, float)):
        cached_value = float(cached_price)

    cache_write_price = pricing.get("cache_write_per_1m")
    cache_write_value: Optional[float] = None
    if isinstance(cache_write_price, (int, float)):
        cache_write_value = float(cache_write_price)

    return {
        "input_per_1m": float(input_price),
        "cached_input_per_1m": cached_value,
        "cache_write_per_1m": cache_write_value,
        "output_per_1m": float(output_price),
    }


def _pricing_block(
    entry: Dict[str, Any], service_tier: str | None = None
) -> Optional[Dict[str, Optional[float]]]:
    normalized_tier = normalize_service_tier(service_tier)
    service_tiers = entry.get("service_tiers") if isinstance(entry, dict) else None
    if isinstance(service_tiers, dict) and normalized_tier:
        tier_pricing = _pricing_block_from_mapping(service_tiers.get(normalized_tier))
        if tier_pricing is not None:
            return tier_pricing

        if normalized_tier in {"default", "auto", "standard"}:
            standard_pricing = _pricing_block_from_mapping(
                service_tiers.get("standard")
            )
            if standard_pricing is not None:
                return standard_pricing
            return _pricing_block_from_mapping(entry.get("pricing"))

        return None

    if normalized_tier and normalized_tier not in {"default", "auto", "standard"}:
        return None

    pricing = entry.get("pricing")
    if isinstance(pricing, dict):
        return _pricing_block_from_mapping(pricing)

    if isinstance(service_tiers, dict):
        return _pricing_block_from_mapping(service_tiers.get("standard"))
    return None


def estimate_usage_cost(
    usage: Dict[str, Any],
    model: str,
    service_tier: str | None = None,
    snapshot: Dict[str, Any] | None = None,
    snapshot_path: str | None = None,
    manual_entries: Dict[str, Any] | None = None,
) -> Optional[float]:
    if not isinstance(usage, dict) or not usage:
        return None

    entry = resolve_pricing_entry(
        model,
        snapshot=snapshot,
        snapshot_path=snapshot_path,
        manual_entries=manual_entries,
    )
    if not isinstance(entry, dict):
        return None

    pricing = _pricing_block(entry, service_tier=service_tier)
    if pricing is None:
        return None

    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    if not isinstance(input_tokens, (int, float)) or not isinstance(
        output_tokens, (int, float)
    ):
        return None

    cached_read_tokens = 0
    cache_write_tokens = 0
    details = usage.get("input_tokens_details")
    if isinstance(details, dict):
        raw_cached = details.get("cached_tokens")
        if isinstance(raw_cached, (int, float)):
            cached_read_tokens = max(0, int(raw_cached))
        raw_cache_write = details.get("cache_write_tokens")
        if isinstance(raw_cache_write, (int, float)):
            cache_write_tokens = max(0, int(raw_cache_write))

    input_total = max(0, int(input_tokens))
    output_total = max(0, int(output_tokens))

    # Split input into three mutually exclusive buckets so the same token is
    # never charged twice. If the reported detail counters are inconsistent
    # (their sum exceeds input_total), reduce the larger counter to fit and
    # clamp ordinary_input_tokens to zero. This keeps cost estimation
    # deterministic and non-negative without rejecting the whole payload.
    if cached_read_tokens + cache_write_tokens > input_total:
        if cached_read_tokens >= cache_write_tokens:
            cached_read_tokens = max(0, input_total - cache_write_tokens)
        else:
            cache_write_tokens = max(0, input_total - cached_read_tokens)
        ordinary_input_tokens = 0
    else:
        ordinary_input_tokens = input_total - cached_read_tokens - cache_write_tokens

    cached_price = pricing.get("cached_input_per_1m")
    if cached_read_tokens > 0 and cached_price is None:
        return None

    cache_write_price = pricing.get("cache_write_per_1m")
    if cache_write_tokens > 0 and cache_write_price is None:
        # Fall back to the ordinary input rate when the provider reports
        # billable cache writes but the published pricing block does not
        # include a separate cache-write column. This keeps older models
        # estimable instead of returning None and hiding the model entirely.
        cache_write_price = pricing["input_per_1m"]

    estimated = (
        ordinary_input_tokens * pricing["input_per_1m"]
        + cached_read_tokens * (cached_price if cached_price is not None else 0.0)
        + cache_write_tokens
        * (cache_write_price if cache_write_price is not None else 0.0)
        + output_total * pricing["output_per_1m"]
    ) / 1_000_000.0

    return float(estimated)


def extract_visible_text_token_tier_pricing_from_page_html(
    html: str,
    source_url: str,
) -> Dict[str, Dict[str, Any]]:
    if not isinstance(html, str) or not html.strip():
        raise ValueError("pricing page html must be a non-empty string")

    model_entries: Dict[str, Dict[str, Any]] = {}

    for match in _TEXT_TOKEN_TABLE_RE.finditer(html):
        props = unescape(match.group(1))
        tier_match = _TIER_RE.search(props)
        if not tier_match:
            continue
        tier = normalize_service_tier(tier_match.group(1))
        if not tier:
            continue

        for raw_model, raw_price_cells in _ROW_RE.findall(props):
            model = normalize_pricing_table_model_name(raw_model)
            if not model:
                continue

            price_cells = _PRICE_CELL_RE.findall(raw_price_cells)
            if len(price_cells) < 3:
                continue

            input_price = _coerce_price(price_cells[0])
            output_price = _coerce_price(price_cells[-1])
            if input_price is None or output_price is None:
                continue

            tier_pricing: Dict[str, Any] = {
                "input_per_1m": input_price,
                "output_per_1m": output_price,
            }

            if len(price_cells) == 3:
                # Legacy row: input, cached input, output.
                cached_input_price = _coerce_price(price_cells[1])
                if cached_input_price is not None:
                    tier_pricing["cached_input_per_1m"] = cached_input_price
            else:
                # New row: input, cached input, cache writes, output.
                # Any extra middle cells beyond the first two and the last are
                # ignored; the OpenAI table currently has exactly four price
                # columns for GPT-5.6+ rows.
                cached_input_price = _coerce_price(price_cells[1])
                if cached_input_price is not None:
                    tier_pricing["cached_input_per_1m"] = cached_input_price
                cache_write_price = _coerce_price(price_cells[2])
                if cache_write_price is not None:
                    tier_pricing["cache_write_per_1m"] = cache_write_price

            entry = model_entries.setdefault(
                model,
                {
                    "model": model,
                    "source_url": source_url,
                    "service_tiers": {},
                },
            )
            service_tiers = entry.setdefault("service_tiers", {})
            service_tiers[tier] = tier_pricing

    if not model_entries:
        raise RuntimeError(
            f"no visible text-token pricing tables found in {source_url}"
        )

    return model_entries


def merge_pricing_entry(
    existing: Dict[str, Any] | None, incoming: Dict[str, Any]
) -> Dict[str, Any]:
    existing_entry = existing if isinstance(existing, dict) else {}
    incoming_entry = incoming if isinstance(incoming, dict) else {}

    merged: Dict[str, Any] = {**existing_entry, **incoming_entry}

    existing_tiers = (
        existing_entry.get("service_tiers")
        if isinstance(existing_entry, dict)
        else None
    )
    incoming_tiers = (
        incoming_entry.get("service_tiers")
        if isinstance(incoming_entry, dict)
        else None
    )
    merged_tiers: Dict[str, Any] = {}
    if isinstance(existing_tiers, dict):
        merged_tiers.update(existing_tiers)
    if isinstance(incoming_tiers, dict):
        merged_tiers.update(incoming_tiers)
    if merged_tiers:
        merged["service_tiers"] = merged_tiers

    if not isinstance(merged.get("pricing"), dict):
        standard_pricing = _pricing_block_from_mapping(merged_tiers.get("standard"))
        if standard_pricing is not None:
            merged["pricing"] = standard_pricing

    return merged


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
        "version": 2,
        "fetched_at": fetched_at,
        "source_base_url": "https://developers.openai.com/api/docs/pricing",
        "models": dict(sorted(models.items())),
    }
