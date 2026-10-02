from __future__ import annotations

from pathlib import Path

from .requirement_quality import root_guidance_source


SNAPSHOT_ROOT = (
    Path(__file__).resolve().parent
    / "guidance_variants"
    / "root-guidance"
)
SNAPSHOT_VARIANTS = ("baseline", "combined-v2")


def render_snapshots() -> tuple[Path, ...]:
    written: list[Path] = []
    for variant in SNAPSHOT_VARIANTS:
        output = SNAPSHOT_ROOT / variant / "AGENTS.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(
            root_guidance_source(variant, "root-only").read_bytes("AGENTS.md")
        )
        written.append(output)
    return tuple(written)


def main() -> None:
    for path in render_snapshots():
        print(path)


if __name__ == "__main__":
    main()