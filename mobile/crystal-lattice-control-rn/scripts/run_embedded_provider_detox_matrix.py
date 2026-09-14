from __future__ import annotations

import argparse
import os
import secrets
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


REPO_ROOT = Path(__file__).resolve().parents[3]
MOBILE_ROOT = Path(__file__).resolve().parents[1]
TEST_SUPPORT = REPO_ROOT / "test"
sys.path.insert(0, str(TEST_SUPPORT))

from repo_test_env import load_repo_root_env  # noqa: E402


@dataclass(frozen=True)
class MatrixRow:
    name: str
    profile: str
    agent: str
    base_url: str
    api_key: str
    model: str


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required for the selected matrix row")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--row", action="append", default=[])
    parser.add_argument("--skip-build", action="store_true")
    return parser.parse_args()


def ollama_available(base_url: str) -> bool:
    import urllib.request

    try:
        with urllib.request.urlopen(f"{base_url.rstrip('/')}/models", timeout=2):
            return True
    except Exception:
        return False


def matrix_rows(requested: set[str]) -> Iterator[MatrixRow]:
    def wanted(name: str) -> bool:
        return not requested or name in requested

    ollama_base_url = os.environ.get(
        "OLLAMA_OPENAI_BASE_URL",
        "http://127.0.0.1:11434/v1",
    )
    if wanted("ollama") and ollama_available(ollama_base_url):
        yield MatrixRow(
            name="ollama",
            profile="reviewer",
            agent="reviewer-claude",
            base_url=ollama_base_url,
            api_key="ollama-local",
            model=os.environ.get("OLLAMA_OPENAI_MODEL", "qwen3.5:0.8b"),
        )
    if wanted("openai"):
        yield MatrixRow(
            name="openai",
            profile="openai",
            agent="openai-codex",
            base_url=os.environ.get(
                "OPENAI_BASE_URL",
                "https://api.openai.com/v1",
            ),
            api_key=required_env("OPENAI_API_KEY"),
            model=os.environ.get("OPENAI_RESPONSES_MODEL", "gpt-5.6-luna"),
        )
    if wanted("openrouter"):
        yield MatrixRow(
            name="openrouter",
            profile="openrouter",
            agent="openrouter-claude",
            base_url=os.environ.get(
                "OPENROUTER_BASE_URL",
                "https://openrouter.ai/api/v1",
            ),
            api_key=required_env("OPENROUTER_API_KEY"),
            model=os.environ.get(
                "OPENROUTER_EMBEDDED_MODEL",
                "anthropic/claude-haiku-4.5",
            ),
        )
    if wanted("anthropic"):
        yield MatrixRow(
            name="anthropic",
            profile="anthropic",
            agent="anthropic-claude",
            base_url=os.environ.get(
                "ANTHROPIC_BASE_URL",
                "https://api.anthropic.com",
            ),
            api_key=required_env("ANTHROPIC_API_KEY"),
            model=os.environ.get(
                "ANTHROPIC_EMBEDDED_MODEL",
                "claude-haiku-4-5-20251001",
            ),
        )
    reviewer_url = os.environ.get("REVIEWER_PROXY_URL")
    reviewer_key = os.environ.get("REVIEWER_PROXY_API_KEY")
    if wanted("reviewer") and reviewer_url and reviewer_key:
        yield MatrixRow(
            name="reviewer",
            profile="reviewer",
            agent="reviewer-claude",
            base_url=reviewer_url,
            api_key=reviewer_key,
            model=os.environ.get("REVIEWER_PROXY_MODEL", "gpt-5.6-luna"),
        )


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=MOBILE_ROOT, env=env, check=True)


def main() -> int:
    args = parse_args()
    load_repo_root_env()
    requested = set(args.row)
    rows = list(matrix_rows(requested))
    if not rows:
        raise SystemExit("No provider matrix rows were selected")

    if not args.skip_build:
        run(["npm", "run", "detox:build:ios"])

    for row in rows:
        env = os.environ.copy()
        env.update(
            {
                "CRYSTAL_EMBEDDED_MATRIX_PROFILE": row.profile,
                "CRYSTAL_EMBEDDED_MATRIX_AGENT": row.agent,
                "CRYSTAL_EMBEDDED_MATRIX_BASE_URL": row.base_url,
                "CRYSTAL_EMBEDDED_MATRIX_API_KEY": row.api_key,
                "CRYSTAL_EMBEDDED_MATRIX_MODEL": row.model,
                "CRYSTAL_EMBEDDED_MATRIX_AUTH_MODE": os.environ.get(
                    "CRYSTAL_EMBEDDED_MATRIX_AUTH_MODE",
                    "api",
                ),
                "CRYSTAL_EMBEDDED_MATRIX_RUN_ID": secrets.token_hex(8),
                "CRYSTAL_EMBEDDED_MATRIX_SKIP_PROVIDER_REQUEST": (
                    os.environ.get("CRYSTAL_EMBEDDED_MATRIX_SKIP_PROVIDER_REQUEST")
                    or ("1" if row.name == "ollama" else "0")
                ),
            }
        )
        print(f"Running embedded provider Detox row: {row.name}")
        run(
            [
                "npm",
                "run",
                "detox:test:embedded-provider-matrix:ios",
            ],
            env=env,
        )
        if row.name == "ollama":
            ollama_env = env.copy()
            ollama_env.update(
                {
                    "CRYSTAL_EMBEDDED_PROXY_URL": row.base_url,
                    "CRYSTAL_EMBEDDED_PROXY_API_KEY": row.api_key,
                    "CRYSTAL_EMBEDDED_MODEL": row.model,
                }
            )
            run(
                [
                    "npm",
                    "run",
                    "detox:test:embedded-python-ollama:ios",
                ],
                env=ollama_env,
            )
        time.sleep(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())