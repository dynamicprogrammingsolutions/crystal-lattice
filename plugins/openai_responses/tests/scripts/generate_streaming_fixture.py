from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from openai import OpenAI


def _event_to_dict(event: Any) -> Dict[str, Any]:
    if isinstance(event, dict):
        return event
    if hasattr(event, "model_dump"):
        payload = event.model_dump(mode="python")
        if isinstance(payload, dict):
            return payload
    raise RuntimeError(f"unsupported stream event payload: {type(event).__name__}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a real OpenAI Responses streaming fixture for tests."
    )
    parser.add_argument("--model", default="gpt-5-mini")
    parser.add_argument(
        "--output",
        default=str(
            Path(__file__).resolve().parents[1]
            / "fixtures"
            / "openai_responses_gpt5mini_streaming_events.json"
        ),
    )
    parser.add_argument(
        "--prompt",
        default="Reply with exactly STREAM_OK",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[4]
    load_dotenv(repo_root / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required (env or .env)")

    base_url = os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    client = OpenAI(api_key=api_key, base_url=base_url)

    stream = client.responses.create(
        model=args.model,
        input=[
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": args.prompt}],
            }
        ],
        stream=True,
    )

    events: list[Dict[str, Any]] = []
    with stream as event_stream:
        for event in event_stream:
            events.append(_event_to_dict(event))

    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "event_count": len(events),
        "events": events,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    event_types = [e.get("type") for e in events if isinstance(e, dict)]
    print(f"Wrote fixture to {output_path}")
    print(f"event_count={len(events)}")
    print(f"event_types={event_types}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())