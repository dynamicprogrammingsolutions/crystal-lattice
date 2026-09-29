from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MOBILE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "test"))

from repo_test_env import load_repo_root_env  # noqa: E402


def run(command: list[str], env: dict[str, str]) -> None:
    subprocess.run(command, cwd=MOBILE_ROOT, env=env, check=True)


def main() -> int:
    load_repo_root_env()
    env = os.environ.copy()
    run(["npm", "run", "detox:test:embedded-chatgpt-login:ios"], env)
    if env.get("CRYSTAL_RUN_CHATGPT_LOGIN_E2E") != "1":
        print(
            "ChatGPT login start passed; the human authorization/tool request "
            "was collected but not run. Set CRYSTAL_RUN_CHATGPT_LOGIN_E2E=1 "
            "to enable the manual flow."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())