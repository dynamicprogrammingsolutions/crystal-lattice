from datetime import datetime
from pathlib import Path


def _resolve_cwd() -> Path:
    raw_cwd = globals().get("cwd")
    try:
        return Path(str(raw_cwd)).resolve()
    except Exception:
        return Path.cwd().resolve()


def _format_directory_listing(root: Path, limit: int = 200) -> str:
    try:
        entries = sorted(root.iterdir(), key=lambda path: path.name.lower())
    except Exception as exc:
        return f"<failed to list directory: {exc}>"

    lines: list[str] = []
    for entry in entries[:limit]:
        suffix = "/" if entry.is_dir() else ""
        lines.append(f"{entry.name}{suffix}")

    omitted = len(entries) - len(lines)
    if omitted > 0:
        lines.append(f"... ({omitted} more entries omitted)")

    return "\n".join(lines) if lines else "<empty directory>"


_cwd = _resolve_cwd()
_listing = _format_directory_listing(_cwd)

# Get previous metadata from globals (provided by SystemMessageFeature)
_previous_metadata = globals().get("PREVIOUS_METADATA", {})

# Check if we already have a timestamp stored from previous request
_current_time = _previous_metadata.get("current_time")

# If no stored timestamp, generate one and mark for storage
if not _current_time:
    _current_time = datetime.now().astimezone().isoformat()
    # Set METADATA_UPDATES to persist this value for next request
    METADATA_UPDATES = {"current_time": _current_time}

SYSTEM_MESSAGE_VALUE = f"""# Working Environment

## Date and Time

The current date and time in ISO format is `{_current_time}`. This is a reference for web research, timestamps, and other time-sensitive work. If you need the exact current time, use a shell command.

## Working Directory

The current working directory is `{_cwd}`. Treat it as the project root unless the user says otherwise. File operations are relative to this directory unless a tool explicitly requires absolute paths.

The directory listing of the current working directory is:

```text
{_listing}
```

Use this as your basic understanding of the project structure."""