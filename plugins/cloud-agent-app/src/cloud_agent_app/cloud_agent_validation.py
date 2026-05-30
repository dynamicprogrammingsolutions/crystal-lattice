from __future__ import annotations

import socket
import subprocess
import time
from pathlib import Path

from agent_core.utils import get_logger
from agent_terminal_app.runtime_layout import RuntimeLayout

from .cloud_agent_profiles import DEFAULT_RUNTIME_IMAGE


_log = get_logger("cloud_agent_validation")

_RUNTIME_DOCKERFILE_RELATIVE = Path("cloud-orchestrator") / "runtime" / "python" / "Dockerfile"
_REQUIRED_RUNTIME_ROOT_PATHS = (
    Path("core") / "python",
    Path("application") / "python",
    Path("plugins"),
    _RUNTIME_DOCKERFILE_RELATIVE,
)


def reserve_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def run_command(
    command: list[str],
    *,
    cwd: Path,
    logger=None,
    event_name: str = "cloud_validation_command",
) -> subprocess.CompletedProcess[str]:
    active_logger = logger or _log
    active_logger.info(
        f"{event_name}_start",
        command=command,
        cwd=str(cwd),
    )
    started_at = time.monotonic()
    result = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    duration = round(time.monotonic() - started_at, 3)
    active_logger.info(
        f"{event_name}_complete",
        command=command,
        cwd=str(cwd),
        returncode=result.returncode,
        duration_seconds=duration,
        output_preview=(result.stdout or "")[:1200],
    )
    return result


def find_runtime_build_root(runtime_layout: RuntimeLayout) -> Path | None:
    candidates: list[Path] = []
    builtin_plugins = runtime_layout.builtin_plugins.resolve()
    candidates.append(builtin_plugins.parent)
    manifest_dir = runtime_layout.manifest_dir.resolve()
    candidates.extend(manifest_dir.parents)

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if _is_runtime_build_root(resolved):
            return resolved
    return None


def ensure_local_runtime_image(
    runtime_image: str,
    *,
    runtime_layout: RuntimeLayout,
    logger=None,
) -> dict[str, str]:
    active_logger = logger or _log
    inspect_result = run_command(
        ["docker", "image", "inspect", runtime_image],
        cwd=Path.cwd(),
        logger=active_logger,
        event_name="cloud_validation_runtime_image_inspect",
    )
    if inspect_result.returncode == 0:
        return {"runtime_image": runtime_image, "source": "existing"}

    if runtime_image != DEFAULT_RUNTIME_IMAGE:
        raise RuntimeError(
            "Configured runtime image "
            f"`{runtime_image}` is not available locally. Pull or build that image "
            "before running `validate-cloud`."
        )

    build_root = find_runtime_build_root(runtime_layout)
    if build_root is None:
        raise RuntimeError(
            "Configured runtime image "
            f"`{runtime_image}` is not available locally, and no canonical "
            "cloud runtime source tree was found for building it."
        )

    dockerfile = (build_root / _RUNTIME_DOCKERFILE_RELATIVE).resolve()
    active_logger.info(
        "cloud_validation_runtime_image_building",
        runtime_image=runtime_image,
        build_root=str(build_root),
        dockerfile=str(dockerfile),
    )
    build_result = run_command(
        [
            "docker",
            "build",
            "-t",
            runtime_image,
            "-f",
            str(dockerfile),
            str(build_root),
        ],
        cwd=build_root,
        logger=active_logger,
        event_name="cloud_validation_runtime_image_build",
    )
    if build_result.returncode != 0:
        raise RuntimeError(
            "Failed to build configured runtime image "
            f"`{runtime_image}` locally.\n{build_result.stdout or ''}".rstrip()
        )
    return {
        "runtime_image": runtime_image,
        "source": "built",
        "build_root": str(build_root),
    }


def _is_runtime_build_root(root: Path) -> bool:
    return all((root / path).exists() for path in _REQUIRED_RUNTIME_ROOT_PATHS)


__all__ = [
    "DEFAULT_RUNTIME_IMAGE",
    "ensure_local_runtime_image",
    "find_runtime_build_root",
    "reserve_local_port",
    "run_command",
]