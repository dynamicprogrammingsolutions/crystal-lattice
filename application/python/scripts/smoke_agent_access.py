from __future__ import annotations

import argparse
import contextlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


RUN_GATE = "RUN_CRYSTAL_LATTICE_OPENROUTER_ACCESS_E2E"
MODEL = "anthropic/claude-haiku-4.5"
CLI_WORKER = "cli-worker"
SDK_WORKER = "sdk-worker"
OUTER_AGENT = "access-orchestrator"
CLI_MARKER = "CLI_WORKER_RESULT_71A9"
SDK_MARKER = "SDK_WORKER_RESULT_C42E"
SECRET_NAME = "OPENROUTER_API_KEY"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run real model-mediated CLI and SDK access smoke."
    )
    parser.add_argument("archive", nargs="?", type=Path)
    parser.add_argument("--inside-runtime", action="store_true")
    parser.add_argument("--default-config-dir", type=Path)
    parser.add_argument("--workspace", type=Path)
    args = parser.parse_args()

    if args.inside_runtime:
        if args.default_config_dir is None or args.workspace is None:
            parser.error(
                "--inside-runtime requires --default-config-dir and --workspace"
            )
        run_inside_runtime(
            default_config_dir=args.default_config_dir.resolve(),
            workspace=args.workspace.resolve(),
        )
        return

    if os.environ.get(RUN_GATE) != "1":
        raise RuntimeError(f"{RUN_GATE} must be '1'")
    if not os.environ.get(SECRET_NAME):
        raise RuntimeError(f"{SECRET_NAME} is required")
    if args.archive is None:
        parser.error("archive is required")
    run_archive_smoke(args.archive.resolve())


def run_archive_smoke(archive: Path) -> None:
    from smoke_runtime_archive import (
        extract_archive,
        find_package_dir,
        python_path,
        validate_package,
    )

    if not archive.is_file():
        raise RuntimeError(f"Archive does not exist: {archive}")
    with tempfile.TemporaryDirectory(prefix="crystal-agent-access-smoke-") as tmp:
        temp_dir = Path(tmp)
        extract_dir = temp_dir / "runtime extraction with spaces"
        extract_archive(archive, extract_dir)
        package_dir = find_package_dir(extract_dir)
        validate_package(package_dir)

        env = dict(os.environ)
        for name in (
            "CONFIG_DIR",
            "CRYSTAL_RUNTIME_LAYOUT",
            "PYTHONHOME",
            "PYTHONPATH",
            "VIRTUAL_ENV",
        ):
            env.pop(name, None)
        result = subprocess.run(
            [
                str(python_path(package_dir)),
                str(Path(__file__).resolve()),
                "--inside-runtime",
                "--default-config-dir",
                str(
                    package_dir
                    / "application"
                    / "python"
                    / "agent_terminal_app"
                    / "default_config"
                ),
                "--workspace",
                str(temp_dir / "external project with spaces"),
            ],
            cwd=str(temp_dir),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=900,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Real agent access smoke failed ({result.returncode})\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        payload = json.loads(result.stdout)
        if payload.get("status") != "succeeded":
            raise RuntimeError(f"Real agent access result failed: {payload!r}")
        print(json.dumps(payload, sort_keys=True))


def run_inside_runtime(*, default_config_dir: Path, workspace: Path) -> None:
    from agent_terminal_app.local_runtime import open_runtime

    workspace.mkdir(parents=True)
    config_dir = workspace.parent / f"{workspace.name} Crystal config"
    sessions = workspace.parent / f"{workspace.name} Shared sessions"
    config_path = write_real_access_config(
        default_config_dir=default_config_dir,
        config_dir=config_dir,
        workspace=workspace,
    )
    os.chdir(workspace)

    secret = os.environ.get(SECRET_NAME)
    if not secret:
        raise RuntimeError(f"{SECRET_NAME} is required inside packaged runtime")

    with contextlib.redirect_stdout(sys.stderr):
        with open_runtime(config_path=config_path, session_root=sessions) as runtime:
            removed = os.environ.pop(SECRET_NAME, None)
            if removed != secret or SECRET_NAME in os.environ:
                raise RuntimeError(
                    "Provider credential was not removed before tool use"
                )

            cli_result = runtime.run(
                (
                    "Use the CLI method from your Crystal Lattice access guidance "
                    "to ask the agent with ID `cli-worker` to return its assigned "
                    "result, then report that result."
                ),
                agent_id=OUTER_AGENT,
                overrides={"include_crystal_lattice_access": True},
                timeout=360,
            )
            sdk_result = runtime.run(
                (
                    "Use the Python SDK method from your Crystal Lattice access "
                    "guidance to ask the agent with ID `sdk-worker` to return its "
                    "assigned result, then report that result."
                ),
                agent_id=OUTER_AGENT,
                overrides={"include_crystal_lattice_access": True},
                timeout=360,
            )
            summaries = runtime.application.list_session_summaries()
            records = [
                runtime.application.load_session_record(summary["session_id"])
                for summary in summaries
            ]

    _assert_method_result(
        result=cli_result,
        records=records,
        worker_id=CLI_WORKER,
        marker=CLI_MARKER,
        method_evidence=('"name": "Bash"', "agent_terminal_app", "run", CLI_WORKER),
        secret=secret,
    )
    _assert_method_result(
        result=sdk_result,
        records=records,
        worker_id=SDK_WORKER,
        marker=SDK_MARKER,
        method_evidence=('"name": "Bash"', "open_runtime", SDK_WORKER),
        secret=secret,
    )
    if secret in config_path.read_text(encoding="utf-8"):
        raise RuntimeError("Provider credential was written into child configuration")

    print(
        json.dumps(
            {
                "status": "succeeded",
                "model": MODEL,
                "cli_session_id": cli_result.session_id,
                "sdk_session_id": sdk_result.session_id,
                "worker_session_count": sum(
                    1
                    for record in records
                    if record is not None
                    and record.metadata.get("agent_id") in {CLI_WORKER, SDK_WORKER}
                ),
            },
            sort_keys=True,
        )
    )


def write_real_access_config(
    *,
    default_config_dir: Path,
    config_dir: Path,
    workspace: Path,
) -> Path:
    shutil.copytree(
        default_config_dir,
        config_dir,
        ignore=shutil.ignore_patterns(".plugin_cache", "auth", "__pycache__", "*.pyc"),
    )
    source = json.loads((config_dir / "config.json").read_text(encoding="utf-8"))
    access_mixin = source["mixins"]["crystal_lattice_access"]
    outer_system_mixin = {
        **access_mixin,
        "system_message": {
            **access_mixin["system_message"],
            "template": "{{CRYSTAL_LATTICE_ACCESS}}\n\n{{CRYSTAL_LATTICE_CLI_ACCESS}}",
        },
    }
    disabled_outer_tools = [
        "claude_compaction",
        "claude_read_tool",
        "claude_task_stop_tool",
        "claude_edit_tool",
        "claude_glob_tool",
        "claude_grep_tool",
        "claude_web_fetch_tool",
        "claude_web_search_tool",
        "claude_mcp_tool",
    ]
    disabled_worker_tools = [
        *disabled_outer_tools,
        "claude_write_tool",
        "claude_bash_tool",
    ]
    config: dict[str, Any] = {
        "plugin_cache_dir": str(config_dir / ".plugin_cache" / "plugins"),
        "mixins": {
            "crystal_lattice_access": access_mixin,
            "outer_access_system": outer_system_mixin,
        },
        "providers": {
            "outer": {
                "provider": "openrouter",
                "api_key": "${env:OPENROUTER_API_KEY}",
                "base_url": "https://openrouter.ai/api/v1",
                "model": MODEL,
                "timeout": 300,
                "allowed_paths": [str(workspace), str(config_dir)],
                "working_directory": str(workspace),
                "enable_reasoning": False,
            },
            "worker": {
                "provider": "deterministic_stream",
                "model": "deterministic-worker",
                "stream_chunk_count": 1,
            },
        },
        "plugins": [
            "path:${env:BUILTIN_PLUGINS}/openrouter",
            "path:${env:BUILTIN_PLUGINS}/feature-system-message",
            "path:${env:BUILTIN_PLUGINS}/claude-tools",
            "plugins.deterministic_stream_provider.DeterministicStreamProvider",
        ],
        "agents": {
            OUTER_AGENT: {
                "mixin_refs": ["outer_access_system"],
                "provider": "outer",
                "plugins": ["path:${env:BUILTIN_PLUGINS}/claude-tools"],
                "disabled_plugins": disabled_outer_tools,
            },
            CLI_WORKER: {
                "provider": "worker",
                "system_message_enabled": True,
                "system_message": {"template": CLI_MARKER},
                "disabled_plugins": disabled_worker_tools,
            },
            SDK_WORKER: {
                "provider": "worker",
                "system_message_enabled": True,
                "system_message": {"template": SDK_MARKER},
                "disabled_plugins": disabled_worker_tools,
            },
        },
    }
    config_path = config_dir / "config.json"
    config_path.write_text(
        json.dumps(config, indent=2) + "\n",
        encoding="utf-8",
    )
    (config_dir / ".env").write_text("", encoding="utf-8")
    return config_path


def _assert_method_result(
    *,
    result: Any,
    records: list[Any],
    worker_id: str,
    marker: str,
    method_evidence: tuple[str, ...],
    secret: str,
) -> None:
    if result.status != "succeeded":
        raise RuntimeError(f"Outer {worker_id} request failed: {result.to_dict()!r}")
    if marker not in result.output_text:
        raise RuntimeError(
            f"Outer {worker_id} result did not report worker marker: "
            f"{result.output_text!r}"
        )

    workers = [
        record
        for record in records
        if record is not None and record.metadata.get("agent_id") == worker_id
    ]
    if not workers:
        raise RuntimeError(f"No separately persisted {worker_id!r} session exists")
    worker_text = _record_text(workers[-1])
    if marker not in worker_text or workers[-1].messages[-1].role != "assistant":
        raise RuntimeError(f"Worker {worker_id!r} did not complete with {marker!r}")

    outer = next(
        (
            record
            for record in records
            if record is not None and record.session_id == result.session_id
        ),
        None,
    )
    if outer is None:
        raise RuntimeError(f"Outer session is missing: {result.session_id}")
    tool_calls = [
        call
        for message in outer.messages
        for call in (message.metadata or {}).get("tool_calls", [])
        if isinstance(call, dict)
    ]
    serialized_tool_calls = json.dumps(tool_calls, sort_keys=True, default=str)
    missing_evidence = [
        value for value in method_evidence if value not in serialized_tool_calls
    ]
    if missing_evidence:
        raise RuntimeError(
            f"Outer {worker_id} tool calls lack method evidence "
            f"{missing_evidence!r}:\n{serialized_tool_calls}"
        )

    serialized_outer = "\n".join(
        (
            _record_text(outer),
            *(
                json.dumps(message.metadata or {}, sort_keys=True, default=str)
                for message in outer.messages
            ),
        )
    )
    if secret in serialized_outer or secret in worker_text:
        raise RuntimeError("Provider credential leaked into model or child history")


def _record_text(record: Any) -> str:
    return "\n".join(
        message.content
        for message in record.messages
        if isinstance(message.content, str)
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
