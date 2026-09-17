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
    if env.get("CRYSTAL_RUN_CHATGPT_LOGIN_E2E") != "1":
        run(["npm", "run", "detox:test:embedded-chatgpt-login:ios"], env)
        print(
            "ChatGPT login Detox was collected but not run; set "
            "CRYSTAL_RUN_CHATGPT_LOGIN_E2E=1 to enable the manual flow."
        )
        return 0

    env.update(
        {
            "CRYSTAL_EMBEDDED_MATRIX_AUTH_MODE": "auto",
            "CRYSTAL_EMBEDDED_MATRIX_SKIP_PROVIDER_REQUEST": "1",
        }
    )
    run(
        [
            sys.executable,
            "scripts/run_embedded_provider_detox_matrix.py",
            "--row",
            "openai",
            "--skip-build",
        ],
        env,
    )
    run(["npm", "run", "detox:test:embedded-chatgpt-login:ios"], env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())