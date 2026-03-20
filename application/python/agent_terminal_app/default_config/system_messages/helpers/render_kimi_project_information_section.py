from pathlib import Path


def _resolve_cwd() -> Path:
    raw_cwd = globals().get("cwd")
    try:
        return Path(str(raw_cwd)).resolve()
    except Exception:
        return Path.cwd().resolve()


def _load_agents_text(root: Path) -> str:
    path = root / "AGENTS.md"
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


_cwd = _resolve_cwd()
_agents_path = _cwd / "AGENTS.md"
_agents_text = _load_agents_text(_cwd)

if _agents_text:
    _agents_block = f"""The project-level `{_agents_path}`:

````````
{_agents_text}
````````

If the root `AGENTS.md` is not enough, check `README.md` files and nested `AGENTS.md` files for more specific guidance.

If you modify files, styles, structures, configurations, or workflows mentioned in `AGENTS.md`, update the corresponding `AGENTS.md` files to keep them accurate."""
else:
    _agents_block = f"""No project-level `AGENTS.md` was found at `{_agents_path}`.

Check `README.md` files and nested `AGENTS.md` files when you need more local guidance for part of the codebase."""

SYSTEM_MESSAGE_VALUE = f"""# Project Information

Markdown files named `AGENTS.md` usually contain project background, structure, coding styles, build steps, testing expectations, and other agent-specific guidance.

{_agents_block}"""