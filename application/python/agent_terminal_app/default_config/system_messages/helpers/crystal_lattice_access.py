import json
import os
import shlex
import subprocess


CONFIG = globals().get("CONFIG", {})


def include_crystal_lattice_access() -> bool:
    return bool(CONFIG.get("include_crystal_lattice_access", False))


def get_ui_elements() -> list[dict]:
    return [
        {
            "ui_type": "config",
            "type": "checkbox",
            "key": "include_crystal_lattice_access",
            "label": "Include Crystal Lattice Access Guidance",
            "default": include_crystal_lattice_access(),
        }
    ]


def _cli_argv() -> list[str]:
    raw = os.environ.get("CRYSTAL_LATTICE_CLI_ARGV_JSON", "")
    try:
        value = json.loads(raw)
    except Exception:
        return []
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        return []
    return value


def _shell_command(argv: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(argv)
    return shlex.join(argv)


def _command(base: list[str], *arguments: str) -> str:
    return _shell_command([*base, *arguments])


def get_value() -> str:
    base = _cli_argv()
    docs_path = os.environ.get("CRYSTAL_LATTICE_DOCS", "")
    docs_url = os.environ.get("CRYSTAL_LATTICE_DOCS_URL", "")
    python = os.environ.get("CRYSTAL_LATTICE_PYTHON", "")
    api_module = os.environ.get("CRYSTAL_LATTICE_PYTHON_API_MODULE", "")
    config_path = os.environ.get("CRYSTAL_LATTICE_CONFIG", "")
    session_root = os.environ.get("CRYSTAL_LATTICE_SESSIONS", "")

    lines = [
        "# Crystal Lattice Access",
        "",
        "You can delegate a bounded task to another configured Crystal Lattice "
        "agent by creating a distinct persisted session.",
    ]

    if base:
        lines.extend(
            [
                "",
                "Use these commands exactly as the base invocation is shown; it "
                "already selects this runtime's config and session store:",
                "Replace angle-bracket placeholders with the selected agent, "
                "session, and task values.",
                "",
                f"- List configured agents: `{_command(base, 'agents', '--format', 'json')}`",
                "- Start a delegated task in a new session: "
                f"`{_command(base, 'run', '--agent', '<agent-id>', '--prompt', '<task>', '--format', 'json')}`",
                "- Continue only after that run completes: "
                f"`{_command(base, 'run', '--session', '<session-id>', '--prompt', '<follow-up>', '--format', 'json')}`",
                "- Inspect bounded history: "
                f"`{_command(base, 'history', '--session', '<session-id>', '--start', '-50', '--format', 'json')}`",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "The runtime did not publish a usable CLI invocation. Do not "
                "guess an executable or configuration path.",
            ]
        )

    if config_path:
        lines.append(f"- Active config: `{config_path}`")
    if session_root:
        lines.append(f"- Shared session root: `{session_root}`")

    if python and api_module:
        lines.extend(
            [
                "",
                f"Python interpreter: `{python}`",
                f"Python API import: `from {api_module} import open_runtime`",
                "Pass the active config and session root above when opening the "
                "runtime from another project.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "This runtime does not expose a general Python interpreter or "
                "importable Python API. Use the CLI invocation above.",
            ]
        )

    if docs_path:
        lines.extend(["", f"Local documentation: `{docs_path}`"])
    if docs_url:
        lines.append(f"Public documentation: {docs_url}")

    lines.extend(
        [
            "",
            "These commands run ordinary synchronous requests in persisted "
            "sessions. They do not provide parent-child session metadata, "
            "mid-run input, detached lifetime, or persistent subagent recovery.",
        ]
    )
    return "\n".join(lines)
