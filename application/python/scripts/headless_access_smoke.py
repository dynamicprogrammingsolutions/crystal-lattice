from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Mapping, Sequence

from boot_smoke import build_isolated_cli_environment


ACCESS_AGENT_ID = "headless-access-smoke"
ACCESS_PROVIDER_ID = "headless_access_deterministic"
ACCESS_MIXIN_ID = "headless_access_smoke_system"
ACCESS_TEMPLATE = "{{CRYSTAL_LATTICE_ACCESS}}\n\n{{CRYSTAL_LATTICE_CLI_ACCESS}}"
TOOL_MESSAGE_EXCLUDE_JSONPATH = "$.messages[?(@.message.role == 'tool')]"


def assert_headless_access(
    command: Sequence[str | os.PathLike[str]],
    *,
    python: Path,
    config_path: Path,
    workspace: Path,
    home_dir: Path,
    base_env: Mapping[str, str] | None = None,
) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    home_dir.mkdir(parents=True, exist_ok=True)
    smoke_config = prepare_headless_access_config(config_path)
    env, _placeholder_names = build_isolated_cli_environment(
        smoke_config,
        home_dir=home_dir,
        base_env=base_env,
    )

    cli_sessions = workspace / "CLI sessions with spaces"
    cli_result = _run_json(
        [
            *(str(part) for part in command),
            "--config",
            str(smoke_config),
            "--sessions-dir",
            str(cli_sessions),
            "run",
            "--agent",
            ACCESS_AGENT_ID,
            "--prompt",
            "CLI_ACCESS_SMOKE",
            "--format",
            "json",
            "--no-progress",
        ],
        cwd=workspace,
        env=env,
    )
    _assert_access_result(
        cli_result,
        marker="CLI_ACCESS_SMOKE",
        python=python,
        config_path=smoke_config,
        session_root=cli_sessions,
    )
    cli_session_id = _result_session_id(cli_result)
    listed_session_ids = _run_text(
        [
            *(str(part) for part in command),
            "--config",
            str(smoke_config),
            "--sessions-dir",
            str(cli_sessions),
            "sessions",
            "--filter",
            "modified_after=1970-01-01T00:00:00Z",
            "--include",
            "$.sessions[*].session_id",
            "--format",
            "text",
        ],
        cwd=workspace,
        env=env,
    ).splitlines()
    if listed_session_ids != [cli_session_id]:
        raise RuntimeError(
            "Installed sessions command did not emit exactly the persisted "
            f"session ID: {listed_session_ids!r}"
        )
    projected_messages = _run_json(
        [
            *(str(part) for part in command),
            "--config",
            str(smoke_config),
            "--sessions-dir",
            str(cli_sessions),
            "messages",
            "--session",
            cli_session_id,
            "--include",
            "$.messages[*].index",
            "--include",
            "$.messages[*].message.role",
            "--include",
            "$.messages[*].message.content",
            "--exclude",
            TOOL_MESSAGE_EXCLUDE_JSONPATH,
            "--format",
            "json",
        ],
        cwd=workspace,
        env=env,
    )
    if "CLI_ACCESS_SMOKE" not in json.dumps(projected_messages):
        raise RuntimeError(
            "Installed messages command omitted the deterministic marker: "
            f"{projected_messages!r}"
        )

    sdk_sessions = workspace / "SDK sessions with spaces"
    sdk_script = workspace / "run SDK access smoke.py"
    sdk_script.write_text(
        "\n".join(
            [
                "import contextlib",
                "import json",
                "import sys",
                "",
                "with contextlib.redirect_stdout(sys.stderr):",
                "    from agent_terminal_app import open_runtime",
                "",
                "    with open_runtime(config_path=sys.argv[1], session_root=sys.argv[2]) as runtime:",
                "        result = runtime.run(",
                "            'SDK_ACCESS_SMOKE',",
                "            agent_id='headless-access-smoke',",
                "        )",
                "        sessions = runtime.list_sessions(",
                "            filter_values={'modified_after': '1970-01-01T00:00:00Z'},",
                "            include=['$.sessions[*].session_id'],",
                "        )",
                "        assert sessions == {'sessions': [{'session_id': result.session_id}]}",
                "        messages = runtime.list_messages(",
                "            result.session_id,",
                "            include=[",
                "                '$.messages[*].index',",
                "                '$.messages[*].message.role',",
                "                '$.messages[*].message.content',",
                "            ],",
                f"            exclude=[{TOOL_MESSAGE_EXCLUDE_JSONPATH!r}],",
                "        )",
                "        assert 'SDK_ACCESS_SMOKE' in json.dumps(messages)",
                "print(json.dumps(result.to_dict(), sort_keys=True))",
                "",
            ]
        ),
        encoding="utf-8",
    )
    sdk_result = _run_json(
        [
            str(python),
            str(sdk_script),
            str(smoke_config),
            str(sdk_sessions),
        ],
        cwd=workspace,
        env=env,
    )
    _assert_access_result(
        sdk_result,
        marker="SDK_ACCESS_SMOKE",
        python=python,
        config_path=smoke_config,
        session_root=sdk_sessions,
    )


def prepare_headless_access_config(config_path: Path) -> Path:
    destination = config_path.parent / "headless access config"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(
        config_path.parent,
        destination,
        ignore=shutil.ignore_patterns(
            ".plugin_cache",
            "auth",
            "__pycache__",
            "*.pyc",
            "headless access config",
        ),
    )
    destination_config = destination / config_path.name
    source_config = json.loads(destination_config.read_text(encoding="utf-8"))
    access_mixin = source_config["mixins"]["crystal_lattice_access"]
    smoke_mixin = {
        **access_mixin,
        "system_message": {
            **access_mixin["system_message"],
            "template": ACCESS_TEMPLATE,
        },
    }
    config = {
        "plugin_cache_dir": str(
            (config_path.parent / ".plugin_cache" / "plugins").resolve()
        ),
        "mixins": {
            "crystal_lattice_access": access_mixin,
            ACCESS_MIXIN_ID: smoke_mixin,
        },
        "providers": {
            ACCESS_PROVIDER_ID: {
                "provider": "deterministic_stream",
                "model": "headless-access-smoke",
                "stream_chunk_count": 1,
            }
        },
        "plugins": [
            "path:${env:BUILTIN_PLUGINS}/feature-system-message",
            "path:${env:BUILTIN_PLUGINS}/session-timestamp-meta-app",
            "plugins.deterministic_stream_provider.DeterministicStreamProvider",
        ],
        "agents": {
            ACCESS_AGENT_ID: {
                "mixin_refs": [ACCESS_MIXIN_ID],
                "provider": ACCESS_PROVIDER_ID,
                "include_crystal_lattice_access": True,
            }
        },
    }
    destination_config.write_text(
        json.dumps(config, indent=2) + "\n",
        encoding="utf-8",
    )
    (destination / ".env").write_text("", encoding="utf-8")
    return destination_config


def _run_json(
    command: list[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
) -> dict:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        env=dict(env),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=300,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Headless access command failed ({result.returncode}): "
            f"{subprocess.list2cmdline(command)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Headless access command did not return one JSON document:\n"
            f"{result.stdout}\nstderr:\n{result.stderr}"
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Headless access result must be an object: {payload!r}")
    return payload


def _run_text(
    command: list[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
) -> str:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        env=dict(env),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=300,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Headless access command failed ({result.returncode}): "
            f"{subprocess.list2cmdline(command)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result.stdout


def _result_session_id(result: dict) -> str:
    session_id = result.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        raise RuntimeError(f"Headless access result lacks session_id: {result!r}")
    return session_id


def _assert_access_result(
    result: dict,
    *,
    marker: str,
    python: Path,
    config_path: Path,
    session_root: Path,
) -> None:
    if result.get("status") != "succeeded":
        raise RuntimeError(f"Headless access request failed: {result!r}")
    output = result.get("output_text")
    if not isinstance(output, str):
        raise RuntimeError(f"Headless access output is not text: {result!r}")
    python_value = str(python.resolve())
    expected_argv = json.dumps(
        [
            python_value,
            "-m",
            "agent_terminal_app",
            "--config",
            str(config_path.resolve()),
            "--sessions-dir",
            str(session_root.resolve()),
        ]
    )
    expected = (
        marker,
        "# Crystal Lattice Access (CLI and Python SDK)",
        str(config_path.resolve()),
        str(session_root.resolve()),
        python_value,
        f"Programmatic CLI argv: `{expected_argv}`",
        "from agent_terminal_app import open_runtime",
        "https://docs.crystallattice.dev/",
    )
    missing = [value for value in expected if value not in output]
    if missing:
        raise RuntimeError(
            f"Headless access output is missing values {missing!r}:\n{output}"
        )
    if "# Crystal Lattice Access (CLI only)" in output:
        raise RuntimeError("Bundled/source smoke unexpectedly compiled CLI-only access")
    docs_match = re.search(r"Local documentation: `([^`]+)`", output)
    if docs_match is None or not Path(docs_match.group(1)).is_dir():
        raise RuntimeError(
            f"Headless access output lacks a readable local docs path:\n{output}"
        )
    session_id = _result_session_id(result)
    if not list(session_root.rglob(f"{session_id}.json")):
        raise RuntimeError(
            f"Headless access session was not persisted under {session_root}: {session_id}"
        )
