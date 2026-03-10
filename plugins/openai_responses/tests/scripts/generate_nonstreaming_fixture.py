from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a real OpenAI Responses non-streaming fixture for tests."
    )
    parser.add_argument("--model", default="gpt-5-mini")
    parser.add_argument(
        "--output",
        default=str(
            Path(__file__).resolve().parents[1]
            / "fixtures"
            / "openai_responses_gpt5mini_nonstreaming.json"
        ),
    )
    parser.add_argument(
        "--prompt",
        default="Reply with a single short sentence that includes the word fixture.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[4]
    load_dotenv(repo_root / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required (env or .env)")

    base_url = os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"

    client = OpenAI(api_key=api_key, base_url=base_url)

    response = client.responses.create(
        model=args.model,
        input=[
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": args.prompt}],
            }
        ],
        stream=False,
    )

    payload = response.model_dump(mode="python")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote fixture to {output_path}")
    print(f"response_id={payload.get('id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
