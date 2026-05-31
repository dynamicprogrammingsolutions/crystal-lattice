from __future__ import annotations

import json
import os
import platform
import shutil
import socket
import subprocess
import tarfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

import pytest


pytestmark = [pytest.mark.integration, pytest.mark.ollama]


ROOT = Path(__file__).resolve().parents[3]
OLLAMA_MODEL = os.getenv("BUNDLE_E2E_OLLAMA_MODEL", "qwen3:0.6b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def test_installed_bundle_default_config_ollama_tool_call_e2e(
    tmp_path: Path,
) -> None:
    if os.environ.get("RUN_CRYSTAL_BUNDLE_OLLAMA_E2E") != "1":
        pytest.skip("RUN_CRYSTAL_BUNDLE_OLLAMA_E2E != '1'")

    archive_raw = os.environ.get("CRYSTAL_LATTICE_BUNDLE_ARCHIVE")
    if not archive_raw:
        pytest.skip("CRYSTAL_LATTICE_BUNDLE_ARCHIVE not set")
    archive_path = Path(archive_raw).expanduser().resolve()
    if not archive_path.is_file():
        pytest.skip(f"CRYSTAL_LATTICE_BUNDLE_ARCHIVE is not a file: {archive_path}")
    if not _archive_matches_current_platform(archive_path):
        pytest.skip(f"Bundle archive does not match current platform: {archive_path.name}")

    _ensure_ollama_model()

    bundle_dir = _extract_bundle_archive(archive_path, tmp_path / "bundle")
    executable = bundle_dir / ("crystal-lattice.exe" if os.name == "nt" else "crystal-lattice")
    assert executable.is_file()

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _assert_default_config_starts(executable, tmp_path / "default-config-workspace")

    config_path = _write_ollama_tool_config(tmp_path / "ollama_tool_config.json", workspace)
    fixture_file = workspace / "bundle-e2e.txt"
    fixture_file.write_text("BUNDLE_TOOL_SENTINEL_01216\n", encoding="utf-8")

    port = _reserve_port()
    env = {
        **os.environ,
        "OPENROUTER_API_KEY": os.environ.get("OPENROUTER_API_KEY", "test-openrouter-key"),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", "test-openai-key"),
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", "test-gemini-key"),
        "TAVILY_API_KEY": os.environ.get("TAVILY_API_KEY", "test-tavily-key"),
        "FIREWORKS_API_KEY": os.environ.get("FIREWORKS_API_KEY", "test-fireworks-key"),
        "ZAI_API_KEY": os.environ.get("ZAI_API_KEY", "test-zai-key"),
        "OLLAMA_HOST": OLLAMA_HOST,
    }
    server = subprocess.Popen(
        [
            str(executable),
            "--config",
            str(config_path),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=str(workspace),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        base_url = f"http://127.0.0.1:{port}"
        _wait_for_server(base_url, server)
        created = _json_request(
            "POST",
            f"{base_url}/sessions",
                {
                    "agent_id": "default",
                    "system_message": (
                        "You are a careful assistant. Always use the read_file tool "
                        "when asked about file contents; do not answer without using "
                        "the tool."
                    ),
                },
        )
        session_id = created["session"]["session_id"]
        sent = _json_request(
            "POST",
            f"{base_url}/sessions/{session_id}/send_message",
            {
                "message": {
                    "role": "user",
                    "content": (
                        "Use the read_file tool to read this file and then "
                        f"reply with its exact contents: {fixture_file}"
                    ),
                },
                "config_overrides": {
                    "model": OLLAMA_MODEL,
                    "base_url": f"{OLLAMA_HOST}/v1",
                    "allowed_paths": [str(workspace)],
                    "max_file_size": 1024 * 1024,
                    "timeout": 180,
                },
            },
        )
        request_id = sent["request_id"]
        events = _wait_for_request_events(base_url, request_id, timeout_seconds=240)
        messages_payload = _json_request(
            "GET",
            f"{base_url}/sessions/{session_id}/messages",
            None,
            timeout=10,
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=20)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=20)

    assert any(event.get("type") == "tool_results" for event in events), events
    messages = [
        item.get("message") or {}
        for item in (messages_payload.get("messages") or [])
        if isinstance(item, dict)
    ]
    assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]
    assert assistant_messages
    assert "BUNDLE_TOOL_SENTINEL_01216" in (
        assistant_messages[-1].get("content") or ""
    )


def _assert_default_config_starts(executable: Path, workspace: Path) -> None:
    workspace.mkdir()
    port = _reserve_port()
    env = {
        **os.environ,
        "OPENROUTER_API_KEY": os.environ.get("OPENROUTER_API_KEY", "test-openrouter-key"),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", "test-openai-key"),
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", "test-gemini-key"),
        "TAVILY_API_KEY": os.environ.get("TAVILY_API_KEY", "test-tavily-key"),
        "FIREWORKS_API_KEY": os.environ.get("FIREWORKS_API_KEY", "test-fireworks-key"),
        "ZAI_API_KEY": os.environ.get("ZAI_API_KEY", "test-zai-key"),
    }
    server = subprocess.Popen(
        [
            str(executable),
            "--config-local",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=str(workspace),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        base_url = f"http://127.0.0.1:{port}"
        _wait_for_server(base_url, server)
        payload = _json_request("GET", f"{base_url}/agents", None)
        agents = payload.get("agents") or []
        assert "ollama" in agents
        assert "cloud-script-author" in agents
    finally:
        server.terminate()
        try:
            server.wait(timeout=20)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=20)


def _write_ollama_tool_config(path: Path, workspace: Path) -> Path:
    config = {
        "providers": {
            "ollama_tools": {
                "provider": "openai_compatible",
                "model": OLLAMA_MODEL,
                "base_url": f"{OLLAMA_HOST}/v1",
                "timeout": 180,
                "allowed_paths": [str(workspace)],
                "max_file_size": 1024 * 1024,
            }
        },
        "plugins": [
            "plugins.openai_provider.OpenAICompatibleProvider",
            "plugins.openai_tools_extension.OpenAIToolsExtension",
            "plugins.ollama_thinking_extension.OllamaThinkingExtension",
            "plugins.file_reader_tool.FileReaderTool",
        ],
        "agents": {
            "default": {
                "provider": "ollama_tools",
            }
        },
    }
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def _archive_matches_current_platform(path: Path) -> bool:
    name = path.name.lower()
    system = platform.system().lower()
    machine = platform.machine().lower()
    expected_platform = "darwin" if system == "darwin" else "windows" if system == "windows" else "linux"
    expected_arch = "arm64" if machine in {"arm64", "aarch64"} else "amd64"
    return f"-{expected_platform}-{expected_arch}" in name


def _ensure_ollama_model() -> None:
    if shutil.which("ollama") is None:
        pytest.skip("ollama is not installed")
    _run(["ollama", "ps"], cwd=ROOT, skip_on_failure="ollama is not running")
    _run(["ollama", "pull", OLLAMA_MODEL], cwd=ROOT, timeout=1200)


def _extract_bundle_archive(archive_path: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True)
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(target_dir)
    else:
        with tarfile.open(archive_path, "r:gz") as archive:
            archive.extractall(target_dir)
    directories = [path for path in target_dir.iterdir() if path.is_dir()]
    assert len(directories) == 1, directories
    return directories[0]


def _reserve_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(base_url: str, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 120
    last_error = ""
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout is not None else ""
            raise AssertionError(f"server exited early\n{output}")
        try:
            _json_request("GET", f"{base_url}/api/hello", None, timeout=2)
            return
        except Exception as exc:
            last_error = str(exc)
            time.sleep(0.5)
    raise AssertionError(f"server did not become ready: {last_error}")


def _wait_for_request_events(
    base_url: str,
    request_id: str,
    *,
    timeout_seconds: int,
) -> list[dict[str, Any]]:
    deadline = time.monotonic() + timeout_seconds
    collected: list[dict[str, Any]] = []
    while time.monotonic() < deadline:
        payload = _json_request(
            "GET",
            f"{base_url}/events?request_id={request_id}&limit=200",
            None,
            timeout=10,
        )
        collected = payload.get("events") or []
        if any(event.get("type") == "request_completed" for event in collected):
            return collected
        if any(event.get("type") == "error" for event in collected):
            raise AssertionError(f"request failed: {collected}")
        time.sleep(1)
    raise AssertionError(f"timed out waiting for request {request_id}: {collected}")


def _json_request(
    method: str,
    url: str,
    payload: dict[str, Any] | None,
    *,
    timeout: int = 30,
) -> Any:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AssertionError(f"HTTP {exc.code} from {url}: {detail}") from exc
    return json.loads(body) if body else None


def _run(
    command: list[str],
    *,
    cwd: Path,
    timeout: int = 120,
    skip_on_failure: str | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    if result.returncode != 0:
        if skip_on_failure is not None:
            pytest.skip(f"{skip_on_failure}\n{result.stdout}")
        raise AssertionError(
            f"Command failed with exit code {result.returncode}: {' '.join(command)}\n"
            f"{result.stdout}"
        )
    return result