"""Refresh the checked-in OpenAI pricing snapshot from official pricing pages."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_SRC = REPO_ROOT / "plugins" / "openai_responses" / "src"
plugin_src_str = str(PLUGIN_SRC)
if plugin_src_str not in sys.path:
    sys.path.insert(0, plugin_src_str)

from openai_responses_plugins.openai_responses_pricing import (
    DEFAULT_PRICING_PAGE_URLS,
    build_snapshot_payload,
    default_snapshot_path,
    extract_visible_text_token_tier_pricing_from_page_html,
    merge_pricing_entry,
)


USER_AGENT = "openai-responses-pricing-refresh/1.0"


def _fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def refresh_snapshot(urls: Sequence[str], output_path: Path) -> Path:
    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    model_entries: dict[str, dict] = {}

    for source_url in urls:
        try:
            html = _fetch_text(source_url)
            parsed_entries = extract_visible_text_token_tier_pricing_from_page_html(
                html=html,
                source_url=source_url,
            )
            for model, entry in parsed_entries.items():
                model_entries[model] = merge_pricing_entry(
                    model_entries.get(model), entry
                )
        except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError) as exc:
            raise RuntimeError(
                f"failed to refresh pricing from {source_url}: {exc}"
            ) from exc

    existing_entries = []
    if output_path.exists():
        existing_payload = json.loads(output_path.read_text(encoding="utf-8"))
        existing_models = existing_payload.get("models")
        if isinstance(existing_models, dict):
            existing_entries = [
                entry for entry in existing_models.values() if isinstance(entry, dict)
            ]

    merged_entries_by_model: dict[str, dict] = {}
    for entry in existing_entries:
        model = entry.get("model")
        if isinstance(model, str) and model:
            # Route retained entries through merge_pricing_entry (with an
            # empty incoming entry) so tier keys are normalized (obsolete
            # ``priority`` renamed to ``fast``) even for models the pricing
            # page no longer lists.
            merged_entries_by_model[model] = merge_pricing_entry(entry, {})

    for model, entry in model_entries.items():
        merged_entries_by_model[model] = merge_pricing_entry(
            merged_entries_by_model.get(model), entry
        )

    payload = build_snapshot_payload(
        fetched_at=fetched_at,
        model_entries=merged_entries_by_model.values(),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh the checked-in OpenAI model pricing snapshot.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_snapshot_path(),
        help="Where to write the pricing snapshot JSON.",
    )
    parser.add_argument(
        "--url",
        dest="urls",
        action="append",
        default=list(DEFAULT_PRICING_PAGE_URLS),
        help=(
            "Pricing page URL to scrape. May be provided multiple times; defaults scrape "
            "the OpenAI pricing page variants used for visible tier rows."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = refresh_snapshot(urls=args.urls, output_path=args.output)
    print(f"Wrote pricing snapshot to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
