# 120 - Shell Engine Truncation

Short description: Add generic parametrized truncation support to the shared shell engine.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/101-shell-engine-core.md`

## Requirements checklist

- [ ] Add truncation parameters to `run_shell_command()`: `limit_type`, `limit_value`, `head_ratio`
- [ ] Implement `_truncate_chars()`, `_truncate_lines()`, `_truncate_tokens()`
- [ ] Add `tiktoken` as required dependency in `pyproject.toml`
- [ ] Return truncation metadata in result dict
- [ ] Keep vendor-specific formatting OUT of shared engine

## Goal

Add generic truncation support that can be configured by vendor wrappers. The shared engine returns raw truncated output + metadata; vendors handle their own formatting.

## Design Principle

**The shared engine is generic and parametrized.** It does NOT contain vendor-specific logic like "Gemini truncation" or "Qwen truncation". Instead, it provides parameters to control truncation behavior and returns metadata that vendor wrappers use for formatting.

## Interface Extension (for approval)

```python
async def run_shell_command(
    command: str,
    *,
    workdir: str | None = None,
    timeout_seconds: float | None = None,
    env: dict[str, str] | None = None,
    shell_path: str | None = None,
    
    # Truncation control (NEW)
    limit_type: Literal["chars"] | Literal["lines"] | Literal["tokens"] | None = None,
    limit_value: int | None = None,
    head_ratio: float = 1.0,  # 1.0 = all from beginning, 0.2 = 20% head + 80% tail
) -> dict[str, Any]:
    """
    Execute a shell command with optional truncation.
    
    Truncation behavior:
    - limit_type="chars": truncate by character count
    - limit_type="lines": truncate by line count  
    - limit_type="tokens": truncate by token count (using tiktoken)
    
    head_ratio controls distribution:
    - head_ratio=1.0: keep first N chars/lines/tokens (standard head truncation)
    - head_ratio=0.2: keep first 20% + last 80% (Gemini-style split)
    
    If limit_type is None, no truncation is applied.
    """
```

## Return Data Structure (Extended)

```python
{
    # Core output (from Chunk 1)
    "exit_code": int | None,
    "output": str,           # The (possibly truncated) output
    "stdout": str,           # Separate stdout
    "stderr": str,           # Separate stderr
    "duration_seconds": float,
    "timed_out": bool,
    
    # Truncation metadata (NEW)
    "truncated": bool,
    "total_lines": int,
    "total_chars": int,
    "total_tokens": int | None,   # Only computed if limit_type="tokens"
    "omitted_lines": int,
    "omitted_chars": int,
    "omitted_tokens": int | None,
    "head_kept": int,         # How many units kept from beginning
    "tail_kept": int,         # How many units kept from end
}
```

## Internal Truncation Algorithm

```python
import tiktoken

_encoding = tiktoken.get_encoding("cl100k_base")

def _apply_truncation(
    content: str,
    limit_type: str,
    limit_value: int,
    head_ratio: float,
) -> tuple[str, dict]:
    """Apply truncation and return (truncated_content, metadata)."""
    
    # Calculate totals
    total_chars = len(content)
    total_lines = len(content.splitlines())
    
    # Check if truncation needed
    if limit_type == "tokens":
        total_tokens = len(_encoding.encode(content))
        if total_tokens <= limit_value:
            return content, _build_metadata(truncated=False, total_tokens=total_tokens, ...)
    elif limit_type == "lines":
        if total_lines <= limit_value:
            return content, _build_metadata(truncated=False, ...)
    else:  # chars
        if total_chars <= limit_value:
            return content, _build_metadata(truncated=False, ...)
    
    # Apply truncation based on limit_type
    if limit_type == "tokens":
        return _truncate_tokens(content, limit_value, head_ratio)
    elif limit_type == "lines":
        return _truncate_lines(content, limit_value, head_ratio)
    else:
        return _truncate_chars(content, limit_value, head_ratio)


def _truncate_chars(content: str, max_chars: int, head_ratio: float) -> tuple[str, dict]:
    head_chars = int(max_chars * head_ratio)
    tail_chars = max_chars - head_chars
    
    if head_ratio >= 1.0:
        # All from beginning
        return content[:max_chars], {
            "truncated": True,
            "head_kept": max_chars,
            "tail_kept": 0,
            "omitted_chars": len(content) - max_chars,
        }
    
    # Split: head + tail
    head = content[:head_chars]
    tail = content[-tail_chars:] if tail_chars > 0 else ""
    truncated = head + tail
    return truncated, {
        "truncated": True,
        "head_kept": head_chars,
        "tail_kept": tail_chars,
        "omitted_chars": len(content) - max_chars,
    }


def _truncate_lines(content: str, max_lines: int, head_ratio: float) -> tuple[str, dict]:
    lines = content.splitlines(keepends=True)
    head_lines = int(max_lines * head_ratio)
    tail_lines = max_lines - head_lines
    
    if head_ratio >= 1.0:
        truncated = "".join(lines[:max_lines])
        return truncated, {
            "truncated": True,
            "head_kept": max_lines,
            "tail_kept": 0,
            "omitted_lines": len(lines) - max_lines,
        }
    
    head = "".join(lines[:head_lines])
    tail = "".join(lines[-tail_lines:]) if tail_lines > 0 else ""
    truncated = head + tail
    return truncated, {
        "truncated": True,
        "head_kept": head_lines,
        "tail_kept": tail_lines,
        "omitted_lines": len(lines) - max_lines,
    }


def _truncate_tokens(content: str, max_tokens: int, head_ratio: float) -> tuple[str, dict]:
    """Token-aware truncation using tiktoken."""
    tokens = _encoding.encode(content)
    total_tokens = len(tokens)
    
    if total_tokens <= max_tokens:
        return content, {"truncated": False, "total_tokens": total_tokens}
    
    head_tokens = int(max_tokens * head_ratio)
    tail_tokens = max_tokens - head_tokens
    
    if head_ratio >= 1.0:
        truncated = _encoding.decode(tokens[:max_tokens])
        return truncated, {
            "truncated": True,
            "head_kept": max_tokens,
            "tail_kept": 0,
            "omitted_tokens": total_tokens - max_tokens,
            "total_tokens": total_tokens,
        }
    
    head = _encoding.decode(tokens[:head_tokens])
    tail = _encoding.decode(tokens[-tail_tokens:]) if tail_tokens > 0 else ""
    truncated = head + tail
    return truncated, {
        "truncated": True,
        "head_kept": head_tokens,
        "tail_kept": tail_tokens,
        "omitted_tokens": total_tokens - max_tokens,
        "total_tokens": total_tokens,
    }
```

## Vendor Wrapper Usage Examples

**Gemini wrapper:**
```python
result = await run_shell_command(
    command,
    limit_type="chars",
    limit_value=40_000,
    head_ratio=0.2,  # 20% head, 80% tail
)

if result["truncated"]:
    # Vendor-specific: save to temp file, format message
    filepath = save_full_output(result["output"], ...)
    formatted = (
        f"Output too large. Showing first {result['head_kept']:,} "
        f"and last {result['tail_kept']:,} characters. "
        f"For full output see: {filepath}\n"
        f"{result['output']}\n"
        f"... [{result['omitted_chars']:,} characters omitted] ..."
    )
```

**Qwen wrapper:**
```python
result = await run_shell_command(
    command,
    limit_type="lines",
    limit_value=1_000,
    head_ratio=1.0,  # All from beginning
)

if result["truncated"]:
    formatted = f"{result['output']}\n[{result['omitted_lines']} lines truncated] ..."
```

**Codex V2 wrapper:**
```python
result = await run_shell_command(
    command,
    limit_type="tokens",
    limit_value=8_000,
    head_ratio=1.0,
)

if result["truncated"]:
    formatted = (
        f"Total output lines: {result['total_lines']}\n"
        f"{result['output']}\n"
        f"... truncated, {result['omitted_tokens']} more tokens"
    )
```

## Dependency

`tiktoken` is a **required dependency** of `tool-compat-shared`:

```toml
# plugins/tool-compat-shared/pyproject.toml
[project]
dependencies = [
    "tiktoken",
]
```

## Tests

- Truncation by chars: output > 1000 chars, limit 100 → truncated=True, head_kept=100
- Truncation by lines: 100 lines, limit 50 → truncated=True, omitted_lines=50
- Truncation by tokens: verify tiktoken encoding works correctly
- head_ratio=0.2: verify 20/80 split (head=200, tail=800 for limit=1000)
- head_ratio=1.0: verify all from beginning
- No truncation: output < limit → truncated=False, output unchanged

## Deliverables

1. Updated `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`
   - Truncation parameters in `run_shell_command()`
   - Internal `_apply_truncation()`, `_truncate_chars()`, `_truncate_lines()`, `_truncate_tokens()`
2. Updated `plugins/tool-compat-shared/pyproject.toml`
   - Add `tiktoken` dependency
3. Updated `plugins/tool-compat-shared/tests/test_shell_engine.py`
   - Truncation tests

## Notes for completing agent

- Finalize the exact metadata fields returned - vendor wrappers depend on these
- Consider whether `total_tokens` should always be computed (expensive) or only when `limit_type="tokens"`
- Verify tiktoken encoding matches Codex CLI expectations

## Completion notes

(To be filled during implementation)