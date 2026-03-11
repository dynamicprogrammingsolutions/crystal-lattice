"""Refresh the checked-in OpenAI pricing snapshot from official model docs."""

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


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_SRC = REPO_ROOT / "plugins" / "openai_responses" / "src"
plugin_src_str = str(PLUGIN_SRC)
if plugin_src_str not in sys.path:
    sys.path.insert(0, plugin_src_str)

from openai_responses_plugins.openai_responses_pricing import (
    DEFAULT_MODEL_DOC_SLUGS,
    build_snapshot_payload,
    default_snapshot_path,
    extract_pricing_from_model_doc_html,
)


DOC_BASE_URL = "https://developers.openai.com/api/docs/models"
USER_AGENT = "openai-responses-pricing-refresh/1.0"


def _fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def refresh_snapshot(models: Sequence[str], output_path: Path) -> Path:
    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    model_entries = []

    for model in models:
        source_url = f"{DOC_BASE_URL}/{model}"
        try:
            html = _fetch_text(source_url)
            model_entries.append(
                extract_pricing_from_model_doc_html(
                    html=html,
                    model=model,
                    source_url=source_url,
                )
            )
        except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError) as exc:
            raise RuntimeError(f"failed to refresh pricing for {model} from {source_url}: {exc}") from exc

    payload = build_snapshot_payload(fetched_at=fetched_at, model_entries=model_entries)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
        "models",
        nargs="*",
        default=list(DEFAULT_MODEL_DOC_SLUGS),
        help="Model doc slugs to refresh, e.g. gpt-5-mini gpt-4.1-mini.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = refresh_snapshot(models=args.models, output_path=args.output)
    print(f"Wrote pricing snapshot to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())