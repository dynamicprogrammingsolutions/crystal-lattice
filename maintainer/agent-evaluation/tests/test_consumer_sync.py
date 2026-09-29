from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
GUIDANCE_ROOT = REPOSITORY_ROOT / "maintainer" / "guidance"

PLATFORM_LAYOUT = {
    "maintainer/guidance/current/bundle.toml": (
        'format = 1\nid = "current"\n\n[sections]\n'
        'documentation = "sections/documentation.md"\n'
        'testing-strategy = "sections/testing-strategy.md"\n'
    ),
    "maintainer/guidance/current/sections/documentation.md": "# Documentation\n",
    "maintainer/guidance/current/sections/testing-strategy.md": "# Testing\n",
    "docs/development/documentation.md": "# Authoring guide\n",
}

CONSUMER_SYNC_TOML = """\
format = 1
consumer_id = "example-consumer"

[sync]
sections = ["documentation", "testing-strategy"]

[[sync.files]]
source = "docs/development/documentation.md"
destinations = ["docs/development/documentation.md"]

[[sync.roots]]
path = "../.."
"""


def _load_consumer_sync(tmp_path: Path):
    spec = importlib.util.spec_from_file_location(
        "consumer_sync_under_test", GUIDANCE_ROOT / "consumer_sync.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _build_platform(tmp_path: Path) -> Path:
    platform = tmp_path / "platform"
    for relative, content in PLATFORM_LAYOUT.items():
        target = platform / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    for name in ("compiler.py", "consumer_sync.py"):
        shutil.copyfile(GUIDANCE_ROOT / name, platform / "maintainer/guidance" / name)
    return platform


def _build_consumer(tmp_path: Path) -> Path:
    consumer = tmp_path / "consumer"
    guidance = consumer / "maintainer" / "guidance"
    guidance.mkdir(parents=True)
    (guidance / "sync.toml").write_text(CONSUMER_SYNC_TOML, encoding="utf-8")
    return consumer


def test_consumer_sync_vendored_layout_and_check(tmp_path, monkeypatch) -> None:
    platform = _build_platform(tmp_path)
    consumer = _build_consumer(tmp_path)
    module = _load_consumer_sync(tmp_path)
    guidance = consumer / "maintainer" / "guidance"
    monkeypatch.setattr(module, "GUIDANCE_ROOT", guidance)

    changed = module.synchronize(platform, check=False)

    assert changed is True
    assert (
        guidance / "current/sections/documentation.md"
    ).read_text(encoding="utf-8") == "# Documentation\n"
    assert (guidance / "compiler.py").read_bytes() == (
        platform / "maintainer/guidance/compiler.py"
    ).read_bytes()
    assert (guidance / "consumer_sync.py").read_bytes() == (
        platform / "maintainer/guidance/consumer_sync.py"
    ).read_bytes()
    manifest = (guidance / "current/bundle.toml").read_text(encoding="utf-8")
    assert 'id = "example-consumer"' in manifest
    assert 'documentation = "sections/documentation.md"' in manifest
    assert (
        consumer / "docs/development/documentation.md"
    ).read_text(encoding="utf-8") == "# Authoring guide\n"
    lock = json.loads((guidance / "sync-lock.json").read_text(encoding="utf-8"))
    assert lock["schema_version"] == 2
    assert {entry["source"] for entry in lock["files"]} == {
        "maintainer/guidance/compiler.py",
        "maintainer/guidance/consumer_sync.py",
        "maintainer/guidance/current/sections/documentation.md",
        "maintainer/guidance/current/sections/testing-strategy.md",
        "docs/development/documentation.md",
    }

    assert module.synchronize(platform, check=True) is False


def test_consumer_sync_check_reports_drift(tmp_path, monkeypatch) -> None:
    platform = _build_platform(tmp_path)
    consumer = _build_consumer(tmp_path)
    module = _load_consumer_sync(tmp_path)
    monkeypatch.setattr(module, "GUIDANCE_ROOT", consumer / "maintainer" / "guidance")
    module.synchronize(platform, check=False)

    drifted = consumer / "docs/development/documentation.md"
    drifted.write_text("# Changed\n", encoding="utf-8")

    with pytest.raises(ValueError, match="synced guidance differs"):
        module.synchronize(platform, check=True)


def test_consumer_sync_rejects_incomplete_config(tmp_path, monkeypatch) -> None:
    consumer = _build_consumer(tmp_path)
    module = _load_consumer_sync(tmp_path)
    monkeypatch.setattr(module, "GUIDANCE_ROOT", consumer / "maintainer" / "guidance")
    (consumer / "maintainer/guidance/sync.toml").write_text(
        'format = 1\nconsumer_id = "example-consumer"\n', encoding="utf-8"
    )

    with pytest.raises(module.ConsumerConfigError, match=r"\[sync\]"):
        module.synchronize(tmp_path, check=False)
