# 102 - Shell Engine Truncation

Short description: Add generic parametrized truncation support as a separate helper function.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/100-shell-tools.md`

Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/101-shell-engine-core.md`

## Requirements checklist

- [ ] Add `truncate_output()` helper function with parameters: `limit_type`, `limit_value`, `head_ratio`
- [ ] Implement `_truncate_chars()`, `_truncate_lines()`, `_truncate_tokens()`
- [ ] Use Codex's token approximation (`len(text) // 4`), NOT tiktoken
- [ ] Return truncation metadata in result dict
- [ ] Default `head_ratio=0.5` (Codex-style 50/50 split)
- [ ] Keep vendor-specific formatting OUT of shared engine

## Goal

Add generic truncation support that can be configured by vendor wrappers. The shared engine provides a `truncate_output()` helper that returns truncated output + metadata; vendors handle their own formatting.

## Design Principle

**The shared engine is generic and parametrized.** It does NOT contain vendor-specific logic like "Gemini truncation" or "Qwen truncation". Instead, it provides a helper function with parameters to control truncation behavior and returns metadata that vendor wrappers use for formatting.

## Codex Research Findings (IMPORTANT)

After examining the actual Codex CLI implementation (`/Users/ferenci84/Dev/Mine/codex/codex-rs/core/src/truncate.rs`):

1. **Codex does NOT use real tokenization!** It uses a simple heuristic:
   ```rust
   const APPROX_BYTES_PER_TOKEN: usize = 4;
   pub(crate) fn approx_token_count(text: &str) -> usize {
       len(text) / 4  // Essentially this
   }
   ```

2. **Default split is 50/50** (not head-only):
   ```rust
   fn split_budget(budget: usize) -> (usize, usize) {
       let left = budget / 2;
       (left, budget - left)
   }
   ```

3. **Output format when truncated:**
   ```
   Total output lines: {total_lines}
   
   {head}…{N} tokens truncated…{tail}
   ```

4. **Default limit:** `DEFAULT_MAX_OUTPUT_TOKENS = 10_000`

**Conclusion:** We should use the same approximation as Codex (`len(text) // 4`) instead of tiktoken. This matches how GPT-5.2/5.3/5.4 Codex models actually handle truncation.

## Interface (Separate Helper Function)

```python
def truncate_output(
    content: str,
    *,
    limit_type: Literal["chars"] | Literal["lines"] | Literal["tokens"],
    limit_value: int,
    head_ratio: float = 0.5,  # Default 50/50 split (Codex-style)
) -> tuple[str, dict[str, Any]]:
    """
    Truncate content and return (truncated_content, metadata).
    
    Truncation behavior:
    - limit_type="chars": truncate by character count
    - limit_type="lines": truncate by line count  
    - limit_type="tokens": truncate by token count (using Codex approximation: len//4)
    
    head_ratio controls distribution:
    - head_ratio=1.0: keep first N chars/lines/tokens (standard head truncation, Qwen-style)
    - head_ratio=0.5: keep first 50% + last 50% (Codex-style split, DEFAULT)
    - head_ratio=0.2: keep first 20% + last 80% (Gemini-style split)
    
    Returns:
        Tuple of (truncated_content, metadata_dict).
    """
```

## Return Metadata Structure

```python
{
    "truncated": bool,
    "total_chars": int,
    "total_lines": int,
    "total_tokens": int,           # Always computed (cheap approximation)
    "omitted_chars": int,
    "omitted_lines": int,
    "omitted_tokens": int,
    "head_kept": int,              # Units kept from beginning
    "tail_kept": int,              # Units kept from end
    "limit_type": str,             # The limit type used
    "limit_value": int,            # The limit value used
    "head_ratio": float,           # The head ratio used
}
```

## Internal Truncation Algorithm

```python
APPROX_BYTES_PER_TOKEN = 4

def approx_token_count(text: str) -> int:
    """Approximate token count using Codex's heuristic: len(text) // 4."""
    return len(text) // APPROX_BYTES_PER_TOKEN

def truncate_output(
    content: str,
    *,
    limit_type: Literal["chars"] | Literal["lines"] | Literal["tokens"],
    limit_value: int,
    head_ratio: float = 0.5,
) -> tuple[str, dict[str, Any]]:
    """Truncate content and return (truncated_content, metadata)."""
    
    # Calculate totals (always cheap)
    total_chars = len(content)
    total_lines = len(content.splitlines())
    total_tokens = approx_token_count(content)
    
    # Check if truncation needed
    needs_truncation = {
        "chars": total_chars > limit_value,
        "lines": total_lines > limit_value,
        "tokens": total_tokens > limit_value,
    }[limit_type]
    
    if not needs_truncation:
        return content, _build_metadata(
            truncated=False,
            total_chars=total_chars,
            total_lines=total_lines,
            total_tokens=total_tokens,
            ...
        )
    
    # Apply truncation based on limit_type
    if limit_type == "tokens":
        return _truncate_tokens(content, limit_value, head_ratio, total_chars, total_lines, total_tokens)
    elif limit_type == "lines":
        return _truncate_lines(content, limit_value, head_ratio, total_chars, total_lines, total_tokens)
    else:
        return _truncate_chars(content, limit_value, head_ratio, total_chars, total_lines, total_tokens)


def _truncate_chars(content: str, max_chars: int, head_ratio: float, ...) -> tuple[str, dict]:
    head_chars = int(max_chars * head_ratio)
    tail_chars = max_chars - head_chars
    
    if head_ratio >= 1.0:
        # All from beginning (Qwen-style)
        return content[:max_chars], {
            "truncated": True,
            "head_kept": max_chars,
            "tail_kept": 0,
            "omitted_chars": len(content) - max_chars,
            ...
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
        ...
    }


def _truncate_lines(content: str, max_lines: int, head_ratio: float, ...) -> tuple[str, dict]:
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
            ...
        }
    
    head = "".join(lines[:head_lines])
    tail = "".join(lines[-tail_lines:]) if tail_lines > 0 else ""
    truncated = head + tail
    return truncated, {
        "truncated": True,
        "head_kept": head_lines,
        "tail_kept": tail_lines,
        "omitted_lines": len(lines) - max_lines,
        ...
    }


def _truncate_tokens(content: str, max_tokens: int, head_ratio: float, ...) -> tuple[str, dict]:
    """Token-aware truncation using Codex's approximation (len//4)."""
    total_tokens = approx_token_count(content)
    
    if total_tokens <= max_tokens:
        return content, {"truncated": False, "total_tokens": total_tokens, ...}
    
    # Convert token budget to char budget
    max_chars = max_tokens * APPROX_BYTES_PER_TOKEN
    
    # Delegate to char truncation with same head_ratio
    # This is exactly how Codex does it
    return _truncate_chars(content, max_chars, head_ratio, ...)
```

## Vendor Wrapper Usage Examples

**Gemini wrapper:**
```python
from tool_compat_shared import run_shell_command, truncate_output

result = await run_shell_command(command)

output, meta = truncate_output(
    result["output"],
    limit_type="chars",
    limit_value=40_000,
    head_ratio=0.2,  # 20% head, 80% tail
)

if meta["truncated"]:
    # Vendor-specific: save to temp file, format message
    filepath = save_full_output(result["output"], ...)
    formatted = (
        f"Output too large. Showing first {meta['head_kept']:,} "
        f"and last {meta['tail_kept']:,} characters. "
        f"For full output see: {filepath}\n"
        f"{output}\n"
        f"... [{meta['omitted_chars']:,} characters omitted] ..."
    )
```

**Qwen wrapper:**
```python
from tool_compat_shared import run_shell_command, truncate_output

result = await run_shell_command(command)

output, meta = truncate_output(
    result["output"],
    limit_type="lines",
    limit_value=1_000,
    head_ratio=1.0,  # All from beginning
)

if meta["truncated"]:
    formatted = f"{output}\n[{meta['omitted_lines']} lines truncated] ..."
```

**Codex V2 wrapper (matches actual Codex behavior):**
```python
from tool_compat_shared import run_shell_command, truncate_output

result = await run_shell_command(command)

output, meta = truncate_output(
    result["output"],
    limit_type="tokens",
    limit_value=10_000,  # Codex default
    head_ratio=0.5,  # 50/50 split (Codex-style)
)

if meta["truncated"]:
    # Codex format:
    formatted = (
        f"Total output lines: {meta['total_lines']}\n\n"
        f"{output}\n"
    )
    # Note: Codex includes truncation marker IN the output: "…N tokens truncated…"
```

## Dependencies

**No new dependencies needed!** Token approximation uses simple arithmetic (`len(text) // 4`), matching Codex CLI's implementation.

## Tests

- `test_approx_token_count()`: Verify `len(text) // 4` matches Codex heuristic
- `test_no_truncation_when_under_limit()`: output < limit → truncated=False, output unchanged
- `test_truncate_chars_head_only()`: head_ratio=1.0 → all from beginning
- `test_truncate_chars_50_50_split()`: head_ratio=0.5 → 50/50 split
- `test_truncate_chars_20_80_split()`: head_ratio=0.2 → Gemini-style
- `test_truncate_lines_preserves_line_breaks()`: Verify line breaks preserved
- `test_truncate_tokens_uses_approximation()`: Token truncation delegates to chars
- `test_metadata_complete()`: Verify all metadata fields returned
- `test_utf8_content()`: Verify UTF-8 boundaries respected

## Deliverables

1. Updated `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`
   - `approx_token_count()` helper using Codex heuristic
   - `truncate_output()` public function
   - Internal `_truncate_chars()`, `_truncate_lines()`, `_truncate_tokens()`
2. Updated `plugins/tool-compat-shared/src/tool_compat_shared/__init__.py`
   - Export `truncate_output`, `approx_token_count`
3. Updated `plugins/tool-compat-shared/tests/test_shell_engine.py`
   - Truncation tests in `TestTruncateOutput` class

## Notes for completing agent

- Token approximation is always computed (cheap: `len(text) // 4`)
- UTF-8 boundary handling: use char indices, not byte indices
- Default `head_ratio=0.5` matches Codex's 50/50 split
- Codex format includes truncation marker IN the output text: `…N tokens truncated…`

## Completion notes

(To be filled during implementation)