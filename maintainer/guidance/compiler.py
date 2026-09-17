from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib  # type: ignore[no-redef]


COMPILER_VERSION = "2"
SLOT_PATTERN = re.compile(
    rb"<!-- guidance-slot:([a-z0-9][a-z0-9-]*) -->"
)


@dataclass(frozen=True)
class CompilationResult:
    bundle_id: str
    target_id: str
    outputs: Mapping[str, bytes]
    lock: Mapping[str, Any]


class InputTracker:
    def __init__(self) -> None:
        self._paths: dict[tuple[str, Path], str] = {}

    def read_bytes(self, path: Path, *, role: str) -> bytes:
        resolved = path.resolve()
        value = resolved.read_bytes()
        self._paths[(role, resolved)] = _sha256(value)
        return value

    def read_toml(self, path: Path, *, role: str) -> dict[str, Any]:
        value = tomllib.loads(
            self.read_bytes(path, role=role).decode("utf-8")
        )
        if not isinstance(value, dict):
            raise ValueError(f"{path} must contain a TOML table")
        return value

    def records(
        self,
        *,
        bundle_root: Path,
        target_root: Path,
    ) -> tuple[dict[str, str], ...]:
        bundle_paths = [
            path for role, path in self._paths if role == "bundle"
        ]
        bundle_anchor = _common_parent(bundle_paths) or bundle_root
        values: list[dict[str, str]] = []
        for (role, path), digest in self._paths.items():
            anchor = bundle_anchor if role == "bundle" else target_root
            try:
                relative = path.relative_to(anchor)
            except ValueError:
                relative = Path(path.name)
            values.append(
                {
                    "role": role,
                    "path": relative.as_posix(),
                    "sha256": digest,
                }
            )
        return tuple(
            sorted(
                values,
                key=lambda item: (item["role"], item["path"]),
            )
        )

    def paths_for_role(self, role: str) -> tuple[Path, ...]:
        return tuple(
            path for item_role, path in self._paths if item_role == role
        )


def compile_guidance(
    *,
    bundle: str | Path,
    target: str | Path,
    base_directory: Path | None = None,
    repository_root: Path | None = None,
    ref: str | None = None,
) -> CompilationResult:
    if ref is not None:
        raise ValueError(
            "compile a checked-out worktree for the desired revision; "
            "--ref is not supported across independent source repositories"
        )
    base = (
        repository_root.resolve()
        if repository_root is not None
        else (base_directory or Path.cwd()).resolve()
    )
    bundle_dir = _absolute_path(bundle, base)
    target_dir = _absolute_path(target, base)
    tracker = InputTracker()
    bundle_id, bundle_sections = _load_bundle(
        tracker,
        bundle_dir,
    )
    target_id, outputs, slots = _load_target(
        tracker,
        target_dir,
    )

    resolved_sections: dict[str, bytes] = {}
    for slot_name, source in slots.items():
        kind = source.get("source")
        if kind == "bundle":
            section_name = _required_text(
                source,
                "section",
                f"slot {slot_name}",
            )
            try:
                section_path = bundle_sections[section_name]
            except KeyError as error:
                raise ValueError(
                    f"slot {slot_name} references unknown bundle section "
                    f"{section_name}"
                ) from error
            resolved_sections[slot_name] = tracker.read_bytes(
                section_path,
                role="bundle",
            )
        elif kind == "target":
            relative = _required_text(
                source,
                "path",
                f"slot {slot_name}",
            )
            resolved_sections[slot_name] = tracker.read_bytes(
                _safe_child(target_dir, relative),
                role="target",
            )
        else:
            raise ValueError(
                f"slot {slot_name} source must be 'bundle' or 'target'"
            )

    compiled: dict[str, bytes] = {}
    used: dict[str, int] = {name: 0 for name in slots}
    for output_path, template_path in outputs.items():
        template = tracker.read_bytes(
            _safe_child(target_dir, template_path),
            role="target",
        )
        found = [
            match.group(1).decode("ascii")
            for match in SLOT_PATTERN.finditer(template)
        ]
        duplicates = sorted(
            name for name in set(found) if found.count(name) != 1
        )
        if duplicates:
            raise ValueError(
                f"{output_path} has duplicate slots: {duplicates!r}"
            )
        unknown = sorted(set(found).difference(slots))
        if unknown:
            raise ValueError(
                f"{output_path} has unknown slots: {unknown!r}"
            )

        def replace(match: re.Match[bytes]) -> bytes:
            name = match.group(1).decode("ascii")
            used[name] += 1
            return resolved_sections[name]

        compiled[output_path] = SLOT_PATTERN.sub(replace, template)

    unused = sorted(name for name, count in used.items() if count == 0)
    multiply_used = sorted(name for name, count in used.items() if count > 1)
    if unused:
        raise ValueError(f"target declares unused slots: {unused!r}")
    if multiply_used:
        raise ValueError(
            f"target uses slots more than once: {multiply_used!r}"
        )

    inputs = tracker.records(
        bundle_root=bundle_dir,
        target_root=target_dir,
    )
    output_records = [
        {"path": path, "sha256": _sha256(content)}
        for path, content in sorted(compiled.items())
    ]
    portable_identity = {
        "compiler_version": COMPILER_VERSION,
        "bundle_id": bundle_id,
        "target_id": target_id,
        "inputs": list(inputs),
        "outputs": output_records,
    }
    compilation_hash = _sha256(
        json.dumps(
            portable_identity,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    lock = {
        "schema_version": 1,
        "compiler_version": COMPILER_VERSION,
        "bundle": {
            "id": bundle_id,
            "path": str(bundle_dir),
            "git": _git_metadata(
                bundle_dir,
                tracker.paths_for_role("bundle"),
            ),
        },
        "target": {
            "id": target_id,
            "path": str(target_dir),
            "git": _git_metadata(
                target_dir,
                tracker.paths_for_role("target"),
            ),
        },
        "inputs": list(inputs),
        "outputs": output_records,
        "compilation_sha256": compilation_hash,
    }
    return CompilationResult(
        bundle_id=bundle_id,
        target_id=target_id,
        outputs=compiled,
        lock=lock,
    )


def write_compilation(
    result: CompilationResult,
    *,
    destination: Path,
    lock_path: Path | None = None,
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for relative, content in result.outputs.items():
        output = destination / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(content)
    if lock_path is not None:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text(
            json.dumps(result.lock, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def check_compilation(
    result: CompilationResult,
    *,
    destination: Path,
) -> tuple[str, ...]:
    mismatches: list[str] = []
    for relative, expected in result.outputs.items():
        output = destination / relative
        if not output.is_file() or output.read_bytes() != expected:
            mismatches.append(relative)
    return tuple(mismatches)


def _load_bundle(
    tracker: InputTracker,
    bundle_dir: Path,
) -> tuple[str, dict[str, Path]]:
    manifest_path = _bundle_manifest(bundle_dir)
    manifest = tracker.read_toml(manifest_path, role="bundle")
    if manifest.get("format") != 1:
        raise ValueError(f"{manifest_path} must use format = 1")
    bundle_id = _required_text(manifest, "id", str(manifest_path))
    sections: dict[str, Path] = {}
    extends = manifest.get("extends")
    if extends is not None:
        if not isinstance(extends, str) or not extends.strip():
            raise ValueError(f"{manifest_path} has invalid extends")
        _, sections = _load_bundle(
            tracker,
            (bundle_dir / extends).resolve(),
        )
    for table_name in ("sections", "overrides"):
        values = manifest.get(table_name, {})
        if not isinstance(values, dict):
            raise ValueError(f"{manifest_path} {table_name} must be a table")
        for name, relative in values.items():
            if not isinstance(name, str) or not isinstance(relative, str):
                raise ValueError(
                    f"{manifest_path} {table_name} entries must be strings"
                )
            sections[name] = _safe_child(bundle_dir, relative)
    if not sections:
        raise ValueError(f"{manifest_path} defines no sections")
    return bundle_id, sections


def _bundle_manifest(bundle_dir: Path) -> Path:
    for name in ("bundle.toml", "candidate.toml"):
        path = bundle_dir / name
        if path.is_file():
            return path
    raise FileNotFoundError(
        f"{bundle_dir} has no bundle.toml or candidate.toml"
    )


def _load_target(
    tracker: InputTracker,
    target_dir: Path,
) -> tuple[str, dict[str, str], dict[str, dict[str, str]]]:
    manifest_path = target_dir / "target.toml"
    manifest = tracker.read_toml(manifest_path, role="target")
    if manifest.get("format") != 1:
        raise ValueError(f"{manifest_path} must use format = 1")
    target_id = _required_text(manifest, "id", str(manifest_path))
    outputs = manifest.get("outputs")
    if not isinstance(outputs, dict) or not outputs:
        raise ValueError(f"{manifest_path} outputs must be a non-empty table")
    output_values: dict[str, str] = {}
    for path, template in outputs.items():
        if not isinstance(path, str) or not isinstance(template, str):
            raise ValueError(f"{manifest_path} output entries must be strings")
        output_values[_relative_output(path)] = template
    slots = manifest.get("slots")
    if not isinstance(slots, dict) or not slots:
        raise ValueError(f"{manifest_path} slots must be a non-empty table")
    slot_values: dict[str, dict[str, str]] = {}
    for name, source in slots.items():
        if not isinstance(name, str) or not isinstance(source, dict):
            raise ValueError(f"{manifest_path} has an invalid slot {name!r}")
        slot_values[name] = {
            str(key): str(value)
            for key, value in source.items()
        }
    return target_id, output_values, slot_values


def _required_text(
    value: Mapping[str, Any],
    key: str,
    owner: str,
) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise ValueError(f"{owner} requires non-empty {key}")
    return item


def _absolute_path(value: str | Path, base: Path) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def _safe_child(parent: Path, relative: str) -> Path:
    child = (parent / relative).resolve()
    try:
        child.relative_to(parent.resolve())
    except ValueError as error:
        raise ValueError(
            f"{relative!r} escapes source directory {parent}"
        ) from error
    return child


def _relative_output(value: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"invalid output path: {value}")
    return path.as_posix()


def _common_parent(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return Path(os.path.commonpath([str(path.parent) for path in paths]))


def _git_metadata(
    directory: Path,
    input_paths: tuple[Path, ...],
) -> dict[str, Any] | None:
    try:
        root = Path(
            _git(directory, "rev-parse", "--show-toplevel").strip()
        )
        revision = _git(root, "rev-parse", "HEAD").strip()
    except subprocess.CalledProcessError:
        return None
    relative_inputs: list[str] = []
    for path in input_paths:
        try:
            relative_inputs.append(path.relative_to(root).as_posix())
        except ValueError:
            continue
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", *relative_inputs],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return {
        "revision": revision,
        "dirty": bool(status.strip()),
    }


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _git(directory: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=directory,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile agent guidance.")
    parser.add_argument("command", choices=("compile", "check", "write"))
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--lock", type=Path)
    args = parser.parse_args()

    result = compile_guidance(
        bundle=args.bundle,
        target=args.target,
    )
    if args.command == "compile":
        if args.destination is None:
            parser.error("compile requires --destination")
        write_compilation(
            result,
            destination=args.destination,
            lock_path=args.lock,
        )
    elif args.command == "write":
        if args.destination is None:
            parser.error("write requires --destination")
        write_compilation(
            result,
            destination=args.destination,
            lock_path=args.lock,
        )
    else:
        if args.destination is None:
            parser.error("check requires --destination")
        mismatches = check_compilation(
            result,
            destination=args.destination,
        )
        if mismatches:
            parser.error(
                "compiled guidance differs: " + ", ".join(mismatches)
            )
    print(json.dumps(result.lock, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()