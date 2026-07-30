"""Refresh the checked-in Codex models snapshot used by OpenAI Responses."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_SRC = REPO_ROOT / "plugins" / "openai_responses" / "src"
plugin_src_str = str(PLUGIN_SRC)
if plugin_src_str not in sys.path:
    sys.path.insert(0, plugin_src_str)

from openai_responses_plugins.openai_responses_codex_models import (
    build_live_snapshot_payload,
    default_snapshot_path,
)


def refresh_snapshot(output_path: Path, *, timeout: float = 30.0) -> Path:
    payload = build_live_snapshot_payload(timeout=timeout)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh the checked-in Codex models snapshot for OpenAI Responses.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_snapshot_path(),
        help="Where to write the Codex models snapshot JSON.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Network timeout in seconds for GitHub requests.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = refresh_snapshot(args.output, timeout=args.timeout)
    print(f"Wrote Codex models snapshot to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())