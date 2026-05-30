from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from agent_core.utils import get_logger
from agent_terminal_app.runtime_layout import RuntimeLayout

from .cloud_agent_profiles import DEFAULT_RUNTIME_IMAGE


_log = get_logger("cloud_agent_validation")

RUNTIME_DIGEST_LABEL = "org.crystal-lattice.cloud-runtime.digest"
_DIGEST_IGNORE_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    ".crystal",
    ".plugin_cache",
    ".venv",
    "artifacts",
    "build",
    "dist",
    "htmlcov",
    "node_modules",
    "site",
}
_DIGEST_IGNORE_SUFFIXES = {".pyc", ".pyo", ".log"}
_SOURCE_RUNTIME_DIGEST_PATHS = (
    Path("core") / "python" / "agent_core",
    Path("core") / "python" / "agent_app",
    Path("core") / "python" / "plugins",
    Path("core") / "python" / "sitecustomize.py",
    Path("application") / "python" / "agent_terminal_app",
    Path("plugins"),
    Path("cloud-orchestrator") / "runtime" / "python" / "Dockerfile",
    Path("cloud-orchestrator") / "runtime" / "python" / "runtime.py",
)


@dataclass(frozen=True)
class RuntimeImageBuildSpec:
    context_dir: Path
    dockerfile: Path

    def resolved(self) -> "RuntimeImageBuildSpec":
        return RuntimeImageBuildSpec(
            context_dir=self.context_dir.expanduser().resolve(),
            dockerfile=self.dockerfile.expanduser().resolve(),
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


def resolve_runtime_build_spec(
    runtime_layout: RuntimeLayout,
    *,
    build_context: Path | None = None,
    dockerfile: Path | None = None,
) -> RuntimeImageBuildSpec | None:
    context = build_context or runtime_layout.cloud_runtime_build_context
    dockerfile_path = dockerfile or runtime_layout.cloud_runtime_dockerfile
    if context is None and dockerfile_path is None:
        return None
    if context is None or dockerfile_path is None:
        raise RuntimeError(
            "Cloud runtime image build metadata must include both a build "
            "context and a Dockerfile."
        )
    spec = RuntimeImageBuildSpec(
        context_dir=context, dockerfile=dockerfile_path
    ).resolved()
    if not spec.context_dir.is_dir():
        raise RuntimeError(
            f"Cloud runtime image build context does not exist: {spec.context_dir}"
        )
    if not spec.dockerfile.is_file():
        raise RuntimeError(
            f"Cloud runtime image Dockerfile does not exist: {spec.dockerfile}"
        )
    return spec


def ensure_local_runtime_image(
    runtime_image: str,
    *,
    runtime_layout: RuntimeLayout,
    build_context: Path | None = None,
    dockerfile: Path | None = None,
    logger=None,
) -> dict[str, str]:
    active_logger = logger or _log
    inspect_payload = inspect_runtime_image(
        runtime_image,
        logger=active_logger,
    )
    explicit_build_metadata = build_context is not None or dockerfile is not None
    if runtime_image != DEFAULT_RUNTIME_IMAGE and not explicit_build_metadata:
        if inspect_payload is not None:
            return {"runtime_image": runtime_image, "source": "existing_custom"}
        raise RuntimeError(
            "Configured runtime image "
            f"`{runtime_image}` is not available locally. Pull or build that image "
            "before running `validate-cloud`, or provide explicit runtime build metadata."
        )

    build_spec = resolve_runtime_build_spec(
        runtime_layout,
        build_context=build_context,
        dockerfile=dockerfile,
    )

    if build_spec is None:
        if inspect_payload is not None:
            return {"runtime_image": runtime_image, "source": "existing"}
        raise RuntimeError(
            "Configured runtime image "
            f"`{runtime_image}` is not available locally. Pull or build that image "
            "before running `validate-cloud`, or provide explicit runtime build metadata."
        )

    digest = runtime_build_digest(build_spec)
    existing_digest = runtime_image_digest_label(inspect_payload)
    if inspect_payload is not None and existing_digest == digest:
        return {
            "runtime_image": runtime_image,
            "source": "existing",
            "build_context": str(build_spec.context_dir),
            "dockerfile": str(build_spec.dockerfile),
            "digest": digest,
        }
    if (
        inspect_payload is not None
        and runtime_image != DEFAULT_RUNTIME_IMAGE
        and not explicit_build_metadata
    ):
        return {
            "runtime_image": runtime_image,
            "source": "existing_custom",
            "build_context": str(build_spec.context_dir),
            "dockerfile": str(build_spec.dockerfile),
            "digest": digest,
            "existing_digest": existing_digest or "",
        }

    digest_tag = runtime_digest_tag(runtime_image, digest)
    active_logger.info(
        "cloud_validation_runtime_image_building",
        runtime_image=runtime_image,
        digest_tag=digest_tag,
        existing_digest=existing_digest,
        expected_digest=digest,
        build_context=str(build_spec.context_dir),
        dockerfile=str(build_spec.dockerfile),
    )
    build_result = run_command(
        [
            "docker",
            "build",
            "-t",
            runtime_image,
            "-t",
            digest_tag,
            "--label",
            f"{RUNTIME_DIGEST_LABEL}={digest}",
            "-f",
            str(build_spec.dockerfile),
            str(build_spec.context_dir),
        ],
        cwd=build_spec.context_dir,
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
        "digest_tag": digest_tag,
        "source": "built",
        "build_context": str(build_spec.context_dir),
        "dockerfile": str(build_spec.dockerfile),
        "digest": digest,
        "existing_digest": existing_digest or "",
    }


def inspect_runtime_image(runtime_image: str, *, logger=None) -> dict | None:
    result = run_command(
        ["docker", "image", "inspect", runtime_image],
        cwd=Path.cwd(),
        logger=logger or _log,
        event_name="cloud_validation_runtime_image_inspect",
    )
    if result.returncode != 0:
        return None
    try:
        parsed = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return {}
    if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
        return parsed[0]
    return {}


def runtime_image_digest_label(inspect_payload: dict | None) -> str | None:
    if not isinstance(inspect_payload, dict):
        return None
    config = inspect_payload.get("Config")
    labels = config.get("Labels") if isinstance(config, dict) else None
    if not isinstance(labels, dict):
        return None
    raw = labels.get(RUNTIME_DIGEST_LABEL)
    return raw if isinstance(raw, str) and raw else None


def runtime_build_digest(build_spec: RuntimeImageBuildSpec) -> str:
    spec = build_spec.resolved()
    digest = hashlib.sha256()
    digest.update(b"crystal-cloud-runtime-v1\n")
    for path in iter_runtime_build_files(spec):
        relative = _digest_relative_path(spec, path)
        digest.update(relative.as_posix().encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def iter_runtime_build_files(build_spec: RuntimeImageBuildSpec) -> list[Path]:
    spec = build_spec.resolved()
    files: set[Path] = set()
    if spec.dockerfile.is_file():
        files.add(spec.dockerfile)

    source_paths = [spec.context_dir / path for path in _SOURCE_RUNTIME_DIGEST_PATHS]
    if all(path.exists() for path in source_paths):
        roots = source_paths
    else:
        roots = [spec.context_dir]

    for candidate in roots:
        if candidate.is_file():
            files.add(candidate.resolve())
            continue
        if not candidate.is_dir():
            continue
        files.update(_iter_digest_files_under(candidate))
    return sorted(files, key=lambda path: _digest_relative_path(spec, path).as_posix())


def _iter_digest_files_under(root_dir: Path) -> list[Path]:
    files: list[Path] = []
    for root, dirs, names in os.walk(root_dir):
        root_path = Path(root)
        dirs[:] = [
            name
            for name in sorted(dirs)
            if name not in _DIGEST_IGNORE_DIRS and not name.endswith(".egg-info")
        ]
        for name in sorted(names):
            path = root_path / name
            if path.suffix in _DIGEST_IGNORE_SUFFIXES:
                continue
            if name in {".coverage", ".DS_Store"}:
                continue
            if path.is_file():
                files.append(path.resolve())
    return files


def _digest_relative_path(build_spec: RuntimeImageBuildSpec, path: Path) -> Path:
    try:
        return path.resolve().relative_to(build_spec.context_dir)
    except ValueError:
        return Path("__dockerfile__") / path.name


def runtime_digest_tag(runtime_image: str, digest: str) -> str:
    short = digest[:16]
    last_segment = runtime_image.rsplit("/", 1)[-1]
    if ":" in last_segment:
        base = runtime_image.rsplit(":", 1)[0]
    else:
        base = runtime_image
    return f"{base}:sha-{short}"


__all__ = [
    "DEFAULT_RUNTIME_IMAGE",
    "ensure_local_runtime_image",
    "inspect_runtime_image",
    "iter_runtime_build_files",
    "reserve_local_port",
    "resolve_runtime_build_spec",
    "runtime_build_digest",
    "runtime_digest_tag",
    "runtime_image_digest_label",
    "run_command",
]
