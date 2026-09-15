from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "agents" / "TASKS-v7.md"
BUNDLED = (
    ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "default_config"
    / "TASKS_v7.md"
)


def synchronize(
    canonical: Path = CANONICAL,
    bundled: Path = BUNDLED,
    *,
    check: bool = False,
) -> bool:
    expected = canonical.read_bytes()
    actual = bundled.read_bytes() if bundled.exists() else None
    if actual == expected:
        return False
    if check:
        raise ValueError(
            f"{bundled} differs from canonical task guidance {canonical}; "
            "run scripts/sync_tasks_v7.py"
        )
    bundled.parent.mkdir(parents=True, exist_ok=True)
    bundled.write_bytes(expected)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Synchronize bundled TASKS_v7.md from agents/TASKS-v7.md.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report drift without modifying the bundled file.",
    )
    args = parser.parse_args()

    try:
        changed = synchronize(check=args.check)
    except ValueError as error:
        parser.exit(1, f"{error}\n")
    if args.check:
        print("TASKS-v7 guidance is synchronized.")
    elif changed:
        print(f"Updated {BUNDLED.relative_to(ROOT)}")
    else:
        print("TASKS-v7 guidance is already synchronized.")


if __name__ == "__main__":
    main()