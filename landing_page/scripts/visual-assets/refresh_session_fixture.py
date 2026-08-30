from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


OPERATIONAL_INSTRUCTIONS = (
    "This is a read-only planning session. Inspect repository files only. "
    "Do not modify files, install dependencies, run builds, start servers, "
    "or launch simulators."
)
FORBIDDEN_COMMANDS = re.compile(
    r"(?i)(?:npm|pnpm|yarn|pip|uv|poetry)\s+(?:install|sync)"
    r"|(?:xcodebuild|gradle|gradlew|react-native|detox)\b"
    r"|(?:sed\s+-i|apply_patch|tee\s|cat\s+[^|]+\s*>|echo\s+[^|]+\s*>)"
)
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
DROP_KEYS = {
    "access_token",
    "account_id",
    "api_key",
    "authorization",
    "cookie",
    "credentials",
    "encrypted_content",
    "headers",
    "native_messages",
    "native_messages_integrity",
    "raw_response",
    "refresh_token",
    "request_id",
    "response_id",
}


def _run(command: list[str], *, cwd: Path, timeout: int) -> None:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"{' '.join(command)} failed: {detail}")


def _directory_bytes(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def checkout_repository(
    manifest: Mapping[str, Any], destination: Path
) -> dict[str, Any]:
    repository = manifest["repository"]
    started = time.monotonic()
    timeout = int(repository["max_checkout_seconds"])
    _run(["git", "init", "-q"], cwd=destination, timeout=timeout)
    _run(
        ["git", "remote", "add", "origin", str(repository["url"])],
        cwd=destination,
        timeout=timeout,
    )
    _run(
        ["git", "sparse-checkout", "init", "--cone"],
        cwd=destination,
        timeout=timeout,
    )
    _run(
        ["git", "sparse-checkout", "set", *repository["sparse_paths"]],
        cwd=destination,
        timeout=timeout,
    )
    _run(
        [
            "git",
            "fetch",
            "-q",
            "--depth=1",
            "--filter=blob:none",
            "origin",
            str(repository["revision"]),
        ],
        cwd=destination,
        timeout=timeout,
    )
    _run(
        ["git", "checkout", "-q", "--detach", "FETCH_HEAD"],
        cwd=destination,
        timeout=timeout,
    )
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=destination, text=True
    ).strip()
    if revision != repository["revision"]:
        raise RuntimeError(f"Checked out {revision}, expected {repository['revision']}")
    elapsed = time.monotonic() - started
    size = _directory_bytes(destination)
    if size > int(repository["max_checkout_bytes"]):
        raise RuntimeError(f"Checkout exceeds byte budget: {size}")
    if elapsed > timeout:
        raise RuntimeError(f"Checkout exceeds time budget: {elapsed:.2f}s")
    return {"bytes": size, "seconds": round(elapsed, 3), "revision": revision}


def _prepare_config(
    source_path: Path,
    destination: Path,
    *,
    credentials_path: Path,
    agent_id: str,
) -> None:
    config = json.loads(source_path.read_text(encoding="utf-8"))
    agents = config.get("agents") or {}
    if agent_id not in agents:
        raise RuntimeError(f"Unknown configured agent: {agent_id}")
    destination.write_text(json.dumps(config, indent=2), encoding="utf-8")
    if not credentials_path.is_file():
        raise RuntimeError("ChatGPT credentials are missing")


def run_application_session(
    *,
    repository_root: Path,
    config_path: Path,
    config_dir: Path,
    session_root: Path,
    workspace: Path,
    agent_id: str,
    prompt: str,
    follow_up_prompt: str | None = None,
    seed_messages: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    import agent_app

    dev_root = Path(agent_app.__file__).resolve().parents[3]
    for relative in (
        "plugins/feature-system-message/src",
        "plugins/feature-request-options/src",
    ):
        value = str(dev_root / relative)
        if value not in sys.path:
            sys.path.insert(0, value)
    from agent_terminal_app.terminal_app import TerminalApplication

    credentials_path = config_dir / "auth" / "chatgpt-auth.json"
    app = TerminalApplication(
        config_path=config_path,
        session_root=session_root,
        env_overrides={
            "CONFIG_DIR": str(config_dir),
            "WORKING_DIR": str(workspace),
            "SESSION_RUNTIME_DIR": str(session_root.parent),
            "CHATGPT_CREDENTIALS": str(credentials_path),
            "CRYSTAL_PLUGIN_PYTHON": sys.executable,
            "PIP_NO_INDEX": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        },
    )
    try:
        app.start_new_session(agent_id)
        for key, value in {
            "auth_mode": "chatgpt",
            "chatgpt_credentials_path": str(credentials_path),
            "allowed_paths": [str(workspace)],
            "working_directory": str(workspace),
        }.items():
            app.update_override(key, value)
        if seed_messages:
            for item in seed_messages:
                message = item.get("message") if isinstance(item, Mapping) else None
                if not isinstance(message, Mapping):
                    continue
                role = message.get("role")
                content = message.get("content")
                metadata = message.get("metadata")
                if role not in {"user", "assistant", "tool"} or not isinstance(
                    content, str
                ):
                    continue
                app.add_message(
                    app.session_id,
                    role=role,
                    content=content,
                    metadata=dict(metadata) if isinstance(metadata, Mapping) else None,
                )
            request_prompts = [follow_up_prompt] if follow_up_prompt else []
        else:
            request_prompts = [prompt]
            if isinstance(follow_up_prompt, str) and follow_up_prompt:
                request_prompts.append(follow_up_prompt)
        final_session: Any = None
        last_final_messages: list[dict[str, Any]] = []
        for request_prompt in request_prompts:
            app.add_message(app.session_id, role="user", content=request_prompt)
            final_session, final_messages, _request_id = app.send_request(stream=True)
            last_final_messages = []
            for message in final_messages:
                if isinstance(message, dict):
                    last_final_messages.append(message)
                    continue
                to_dict = getattr(message, "to_dict", None)
                if callable(to_dict):
                    converted = to_dict()
                    if isinstance(converted, dict):
                        last_final_messages.append(converted)

        session = app.session.to_dict()
        messages = list(session.get("messages") or [])
        if not follow_up_prompt and not any(
            message.get("role") == "assistant" for message in messages
        ):
            assistant_candidate = next(
                (
                    message
                    for message in reversed(last_final_messages)
                    if message.get("role") == "assistant"
                ),
                None,
            )
            metadata = session.get("metadata")
            native_messages = (
                metadata.get("native_messages") if isinstance(metadata, dict) else None
            )
            if assistant_candidate is None and isinstance(native_messages, list):
                assistant_candidate = next(
                    (
                        message
                        for message in reversed(native_messages)
                        if isinstance(message, dict)
                        and message.get("role") == "assistant"
                    ),
                    None,
                )
            if isinstance(assistant_candidate, dict):
                content = assistant_candidate.get("content")
                if isinstance(content, str) and content:
                    messages.append(
                        {
                            "role": "assistant",
                            "content": content,
                            "metadata": {},
                        }
                    )
        session["messages"] = messages
        return session
    finally:
        app.close()


def _sanitize(value: Any, *, workspace: Path, home: Path) -> Any:
    if isinstance(value, dict):
        return {
            key: _sanitize(item, workspace=workspace, home=home)
            for key, item in value.items()
            if key.lower() not in DROP_KEYS
        }
    if isinstance(value, list):
        return [_sanitize(item, workspace=workspace, home=home) for item in value]
    if isinstance(value, str):
        sanitized = value.replace(str(workspace), "/workspace/starlette").replace(
            str(home), "~"
        )
        sanitized = sanitized.replace(home.name, "<user>")
        return EMAIL.sub("<redacted-email>", sanitized)
    return value


def _tool_commands(value: Any) -> list[str]:
    if isinstance(value, dict):
        commands = []
        for key, child in value.items():
            if key == "command" and isinstance(child, str):
                commands.append(child)
            else:
                commands.extend(_tool_commands(child))
        return commands
    if isinstance(value, list):
        return [item for child in value for item in _tool_commands(child)]
    return []


def build_candidate(
    raw_session: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any],
    prompt: str,
    follow_up_prompt: str | None = None,
    seed_fixture: Mapping[str, Any] | None = None,
    workspace: Path,
) -> tuple[dict[str, Any], int]:
    for text in _tool_commands(raw_session):
        if FORBIDDEN_COMMANDS.search(text):
            raise RuntimeError(f"Forbidden tool activity detected: {text[:160]}")
    visible = []
    tool_activity = 0
    for raw_message in raw_session.get("messages") or []:
        if not isinstance(raw_message, dict):
            continue
        role = raw_message.get("role")
        if role == "system":
            continue
        if role not in {"user", "assistant", "tool"}:
            continue
        message = _sanitize(raw_message, workspace=workspace, home=Path.home())
        content = message.get("content")
        if role == "tool" and isinstance(content, str):
            if content.startswith("Error:"):
                continue
            if "checkout: moving from" in content:
                continue
            if len(content) > 3000:
                message["content"] = (
                    content[:3000].rstrip()
                    + "\n\n[Tool output truncated in the reviewed website fixture.]"
                )
        if role == "tool":
            tool_activity += 1
        if role == "assistant" and "tool_calls" in json.dumps(message):
            tool_activity += 1
        visible.append({"index": len(visible), "message": message})
    roles = {item["message"].get("role") for item in visible}
    if not {"user", "assistant"}.issubset(roles):
        raise RuntimeError("Generated session must contain user and assistant messages")
    if tool_activity < 1:
        raise RuntimeError(
            "Generated session must contain repository-inspection tool activity"
        )
    follow_up_user_position: int | None = None
    if isinstance(follow_up_prompt, str) and follow_up_prompt:
        user_positions = [
            index
            for index, item in enumerate(visible)
            if item["message"].get("role") == "user"
        ]
        if len(user_positions) < 2:
            raise RuntimeError("Generated session is missing the follow-up user turn")
        follow_up_user_position = user_positions[-1]
        follow_up_user = visible[follow_up_user_position]["message"]
        if str(follow_up_user.get("content") or "").strip() != follow_up_prompt.strip():
            raise RuntimeError("Generated session follow-up prompt does not match")
        follow_up_segment = visible[follow_up_user_position + 1 :]
        if (
            len(follow_up_segment) != 1
            or follow_up_segment[0]["message"].get("role") != "assistant"
        ):
            shape = [
                {
                    "role": item["message"].get("role"),
                    "has_content": bool(
                        str(item["message"].get("content") or "").strip()
                    ),
                    "has_tool_calls": "tool_calls" in json.dumps(item["message"]),
                }
                for item in follow_up_segment
            ]
            raise RuntimeError(
                "Generated follow-up must finish with one assistant response "
                f"and no tool activity; observed {shape}"
            )
        follow_up_assistant = follow_up_segment[0]["message"]
        if not str(follow_up_assistant.get("content") or "").strip():
            raise RuntimeError("Generated follow-up assistant response is empty")
        metadata = follow_up_assistant.get("metadata")
        reasoning = metadata.get("reasoning") if isinstance(metadata, dict) else None
        if reasoning in (None, "", [], {}):
            raise RuntimeError(
                "Generated follow-up assistant response has no reasoning metadata"
            )
    if seed_fixture is not None:
        seed_items = seed_fixture.get("messages")
        if not isinstance(seed_items, list) or not seed_items:
            raise RuntimeError("Reviewed seed fixture has no messages")
        if follow_up_user_position is None:
            raise RuntimeError("Reviewed seed extension requires a follow-up turn")
        runtime_seed_items = [
            item
            for item in seed_items
            if not (
                isinstance(item, dict)
                and isinstance(item.get("message"), dict)
                and item["message"].get("role") == "assistant"
                and not str(item["message"].get("content") or "").strip()
                and "tool_calls" in json.dumps(item["message"])
            )
        ]
        raw_prefix = visible[:follow_up_user_position]
        if len(raw_prefix) != len(runtime_seed_items):
            raise RuntimeError(
                "Runtime seed prefix length changed: "
                f"reviewed={len(runtime_seed_items)} "
                f"roles={[item.get('message', {}).get('role') for item in runtime_seed_items if isinstance(item, dict)]}; "
                f"runtime={len(raw_prefix)} "
                f"roles={[item.get('message', {}).get('role') for item in raw_prefix]}"
            )
        for expected, actual in zip(runtime_seed_items, raw_prefix):
            expected_message = (
                expected.get("message") if isinstance(expected, dict) else None
            )
            actual_message = actual.get("message")
            if not isinstance(expected_message, dict) or not isinstance(
                actual_message, dict
            ):
                raise RuntimeError("Reviewed seed prefix contains an invalid message")
            if expected_message.get("role") != actual_message.get(
                "role"
            ) or expected_message.get("content") != actual_message.get("content"):
                raise RuntimeError("Runtime seed prefix content changed")
        follow_up_items = visible[follow_up_user_position:]
        visible = [copy.deepcopy(item) for item in seed_items]
        for item in follow_up_items:
            visible.append(
                {
                    "index": len(visible),
                    "message": item["message"],
                }
            )
    presentation = manifest["presentation"]
    session_metadata: dict[str, Any] = {}
    agent_id = manifest.get("agent_id")
    if isinstance(agent_id, str) and agent_id:
        session_metadata["agent_id"] = agent_id
    candidate = {
        "schema_version": 1,
        "fixture_id": manifest["fixture_id"],
        "session": {
            "session_id": presentation["session_id"],
            "modified": 1,
            "preview": prompt.splitlines()[0],
            "metadata": session_metadata,
            "presentation": {
                "title": presentation["title"],
                "subtitle": presentation["subtitle"],
                "meta": f"{len(visible)} messages",
            },
        },
        "messages": visible,
    }
    return candidate, tool_activity


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--provenance", required=True)
    parser.add_argument("--seed-fixture")
    return parser.parse_args()


def _plugin_cache_path(config_path: Path, config_dir: Path) -> Path:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    raw = config.get("plugin_cache_dir") or config_dir / "cache" / "plugins"
    return Path(raw).expanduser().resolve()


def _cache_state(cache_path: Path) -> dict[str, tuple[int, int]]:
    if not cache_path.is_dir():
        return {}
    return {
        child.name: (child.stat().st_mtime_ns, child.stat().st_size)
        for child in cache_path.iterdir()
    }


def main() -> int:
    args = _parse_args()
    repository_root = Path(args.repository_root).resolve()
    manifest_path = Path(args.manifest).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    prompt_path = manifest_path.parent / manifest["prompt_file"]
    prompt = prompt_path.read_text(encoding="utf-8").strip()
    follow_up_prompt_file = manifest.get("follow_up_prompt_file")
    follow_up_prompt = (
        (manifest_path.parent / follow_up_prompt_file)
        .read_text(encoding="utf-8")
        .strip()
        if isinstance(follow_up_prompt_file, str) and follow_up_prompt_file
        else None
    )
    seed_fixture_path = Path(args.seed_fixture).resolve() if args.seed_fixture else None
    seed_fixture = (
        json.loads(seed_fixture_path.read_text(encoding="utf-8"))
        if seed_fixture_path is not None
        else None
    )
    all_seed_messages = (
        seed_fixture.get("messages") if isinstance(seed_fixture, dict) else None
    )
    seed_message_count = manifest.get("seed_message_count")
    seed_messages = (
        all_seed_messages[:seed_message_count]
        if isinstance(all_seed_messages, list)
        and isinstance(seed_message_count, int)
        and seed_message_count > 0
        else all_seed_messages
    )
    effective_seed_fixture = (
        {
            **seed_fixture,
            "messages": seed_messages,
        }
        if isinstance(seed_fixture, dict) and isinstance(seed_messages, list)
        else seed_fixture
    )
    if seed_fixture is not None and not follow_up_prompt:
        raise RuntimeError("Reviewed seed extension requires a follow-up prompt")
    config_dir = Path(args.config_dir).expanduser().resolve()
    source_config = Path(args.config).expanduser().resolve()
    candidate_path = Path(args.candidate).resolve()
    provenance_path = Path(args.provenance).resolve()
    with tempfile.TemporaryDirectory(prefix="crystal-website-session-") as raw_temp:
        temp_root = Path(raw_temp)
        workspace = temp_root / "starlette"
        workspace.mkdir()
        checkout = checkout_repository(manifest, workspace)
        runtime_root = temp_root / "runtime"
        runtime_root.mkdir()
        runtime_config = temp_root / "config.json"
        credentials_path = config_dir / "auth" / "chatgpt-auth.json"
        _prepare_config(
            source_config,
            runtime_config,
            credentials_path=credentials_path,
            agent_id=args.agent,
        )
        raw_session = run_application_session(
            repository_root=repository_root,
            config_path=runtime_config,
            config_dir=config_dir,
            session_root=runtime_root / "sessions",
            workspace=workspace,
            agent_id=args.agent,
            prompt=prompt,
            follow_up_prompt=follow_up_prompt,
            seed_messages=seed_messages if isinstance(seed_messages, list) else None,
        )
        candidate, tool_activity = build_candidate(
            raw_session,
            manifest=manifest,
            prompt=prompt,
            follow_up_prompt=follow_up_prompt,
            seed_fixture=effective_seed_fixture,
            workspace=workspace,
        )
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(json.dumps(candidate, indent=2), encoding="utf-8")
    provenance = {
        "schema_version": 1,
        "fixture_id": manifest["fixture_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "agent": args.agent,
        "repository": manifest["repository"]["url"],
        "revision": checkout["revision"],
        "checkout_bytes": checkout["bytes"],
        "checkout_seconds": checkout["seconds"],
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "follow_up_prompt_sha256": (
            hashlib.sha256(follow_up_prompt.encode()).hexdigest()
            if follow_up_prompt
            else None
        ),
        "seed_fixture_sha256": (
            hashlib.sha256(seed_fixture_path.read_bytes()).hexdigest()
            if seed_fixture_path is not None
            else None
        ),
        "config_sha256": hashlib.sha256(source_config.read_bytes()).hexdigest(),
        "tool_activity": tool_activity,
        "python": sys.executable,
        "candidate_sha256": hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
    }
    provenance_path.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
