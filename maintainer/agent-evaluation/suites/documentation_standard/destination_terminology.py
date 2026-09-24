from __future__ import annotations

import hashlib
import os
from typing import Any

from maintainer.guidance import CompilationResult, compile_guidance

from .support import CURRENT_GUIDANCE_PATHS, GuidanceSource, REPOSITORY_ROOT


CURRENT_VARIANT = "current"
CANDIDATE_BUNDLES = {
    "abstract-specific": (
        "maintainer/guidance/candidates/" "destination-terminology-abstract-specific"
    ),
    "explicit-contexts-specific": (
        "maintainer/guidance/candidates/"
        "destination-terminology-explicit-contexts-specific"
    ),
}
CURRENT_BUNDLE = "maintainer/guidance/current"
CRYSTAL_TARGET = "maintainer/guidance/targets/crystal-lattice"
GUIDE_TARGET = (
    "maintainer/agent-evaluation/suites/documentation_standard/fixtures/"
    "destination_terminology/guidance"
)


def selected_destination_terminology_variant() -> str:
    value = os.getenv(
        "AGENT_EVAL_DESTINATION_TERMINOLOGY_VARIANT",
        CURRENT_VARIANT,
    ).strip()
    if value == CURRENT_VARIANT or value in CANDIDATE_BUNDLES:
        return value
    allowed = ", ".join((CURRENT_VARIANT, *CANDIDATE_BUNDLES))
    raise ValueError(
        "AGENT_EVAL_DESTINATION_TERMINOLOGY_VARIANT must be one of: " f"{allowed}"
    )


def destination_terminology_guidance_source(
    variant: str | None = None,
) -> GuidanceSource:
    selected = variant or selected_destination_terminology_variant()
    bundle = (
        CURRENT_BUNDLE if selected == CURRENT_VARIANT else CANDIDATE_BUNDLES[selected]
    )
    root = _compile(bundle, CRYSTAL_TARGET)
    overrides: list[tuple[str, bytes]] = [
        ("AGENTS.md", root.outputs["AGENTS.md"]),
    ]
    provenance: dict[str, Any] = {
        "variant": selected,
        "root_compilation": root.lock,
    }

    if selected == CURRENT_VARIANT:
        guide_path = REPOSITORY_ROOT / "docs/development/documentation.md"
        guide = guide_path.read_bytes()
        provenance["guide_source"] = {
            "path": "docs/development/documentation.md",
            "sha256": hashlib.sha256(guide).hexdigest(),
        }
    else:
        guide_compilation = _compile(bundle, GUIDE_TARGET)
        guide = guide_compilation.outputs["docs/development/documentation.md"]
        provenance["guide_compilation"] = guide_compilation.lock
    overrides.append(("docs/development/documentation.md", guide))

    return GuidanceSource(
        name=f"destination-terminology-{selected}",
        paths=CURRENT_GUIDANCE_PATHS,
        content_overrides=tuple(overrides),
        provenance=provenance,
    )


def _compile(bundle: str, target: str) -> CompilationResult:
    return compile_guidance(
        bundle=bundle,
        target=target,
        repository_root=REPOSITORY_ROOT,
    )
