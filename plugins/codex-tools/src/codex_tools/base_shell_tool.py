"""Base class for Codex shell tools with shared formatting and truncation logic.

Both `shell` (array-based) and `shell_command` (string-based) tools share
the same output formatting and truncation behavior, implemented here.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List

from agent_core.types import ToolPlugin
from tool_compat_shared.shell_engine import (
    ShellInfo,
    detect_shell,
    run_shell_command,
    truncate_output,
)

DEFAULT_MAX_OUTPUT_TOKENS = 10_000  # From Codex models.json truncation_policy


class BaseCodexShellTool(ToolPlugin):
    """Base class for Codex shell tools with shared formatting logic.
    
    Provides:
    - Codex-style output formatting (exit code, wall time, truncation info)
    - Token-based truncation with 50/50 head/tail split
    - 10K token default limit
    
    Subclasses implement:
    - get_tool_schemas(): Return tool-specific schema
    - execute_tool(): Parse args and call _execute_command()
    - stream_tool(): Streaming implementation
    """
    
    version: str = "1.0.0"
    
    def _build_result(
        self,
        result: Dict[str, Any],
        truncated_output: str,
        trunc_meta: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build result dict with Codex-style formatting.
        
        Output format (no truncation):
            Exit code: 0
            Wall time: 1.5 seconds
            Output:
            <combined output>
        
        Output format (with truncation):
            Exit code: 0
            Wall time: 1.5 seconds
            Total output lines: 5000
            
            <head>…<N> tokens truncated…<tail>
        
        Args:
            result: Raw result from run_shell_command()
            truncated_output: Output after truncation (may include truncation marker)
            trunc_meta: Truncation metadata dict
            
        Returns:
            Formatted result dict with 'success', 'output', and metadata
        """
        lines: List[str] = []
        
        # Exit code
        exit_code = result.get("exit_code")
        if exit_code is not None:
            lines.append(f"Exit code: {exit_code}")
        else:
            lines.append("Exit code: none")
        
        # Duration (wall time)
        duration = result.get("duration_seconds", 0)
        lines.append(f"Wall time: {duration:.1f} seconds")
        
        # Truncation header (only when truncated)
        if trunc_meta.get("truncated"):
            lines.append(f"Total output lines: {trunc_meta['total_lines']}")
            lines.append("")  # Blank line before output
        
        # Output (already contains truncation marker if truncated)
        lines.append(truncated_output)
        
        output_text = "\n".join(lines)
        
        # Success determination
        # Non-zero exit code = tool error
        # Timeout = tool error
        success = exit_code == 0 and not result.get("timed_out", False)
        
        return {
            "success": success,
            "output": output_text,
            "exit_code": exit_code,
            "timed_out": result.get("timed_out", False),
            "truncated": trunc_meta.get("truncated", False),
            "duration_seconds": duration,
        }
    
    def _apply_truncation(
        self,
        output: str,
        max_output_tokens: int | None = None,
    ) -> tuple[str, Dict[str, Any]]:
        """Apply Codex-style truncation (50/50 split, token approximation).
        
        Uses simple len(text) // 4 approximation for token count,
        matching Codex CLI behavior (no tiktoken needed).
        
        Args:
            output: Raw output string to potentially truncate
            max_output_tokens: Token limit (default: 10,000)
            
        Returns:
            Tuple of (truncated_output, metadata_dict)
        """
        limit = max_output_tokens or DEFAULT_MAX_OUTPUT_TOKENS
        return truncate_output(
            output,
            limit_type="tokens",
            limit_value=limit,
            head_ratio=0.5,  # Codex uses 50/50 split
        )
    
    def _insert_truncation_marker(
        self,
        output: str,
        trunc_meta: Dict[str, Any],
    ) -> str:
        """Insert Codex-style truncation marker into output.
        
        Format: <head>…<N> tokens truncated…<tail>
        
        The marker uses Unicode ellipsis (…) and is embedded in the output
        between head and tail sections.
        
        Args:
            output: Truncated output (head + tail concatenated)
            trunc_meta: Truncation metadata with head_kept, tail_kept, omitted_tokens
            
        Returns:
            Output with truncation marker inserted between head and tail
        """
        if not trunc_meta.get("truncated"):
            return output
        
        head_kept = trunc_meta.get("head_kept", 0)
        tail_kept = trunc_meta.get("tail_kept", 0)
        omitted_tokens = trunc_meta.get("omitted_tokens", 0)
        
        if tail_kept == 0:
            # No tail, just return head
            return output
        
        # Split output into head and tail
        head = output[:head_kept]
        tail = output[-tail_kept:] if tail_kept > 0 else ""
        
        # Insert marker
        marker = f"…{omitted_tokens} tokens truncated…"
        return head + marker + tail
    
    def format_tool_result(
        self,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> str:
        """Format result for LLM consumption.
        
        Returns the formatted output string.
        """
        return result.get("output", "")
    
    def format_tool_call_preview(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> str:
        """Generate a preview for tool call display.
        
        Shows the command being executed.
        """
        command = arguments.get("command", "")
        if isinstance(command, str):
            cmd = command.strip()
            return cmd.splitlines()[0] if "\n" in cmd else cmd
        elif isinstance(command, list) and command:
            # Show first few elements of array command
            preview_parts = command[:3]
            preview = " ".join(preview_parts)
            if len(command) > 3:
                preview += " ..."
            return preview
        return ""
    
    def to_display_format(
        self,
        text: str,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Format result for display.
        
        Adds command and workdir header to output.
        """
        command = result.get("command")
        workdir = result.get("workdir")
        
        lines: List[str] = []
        
        if workdir:
            lines.append(f"Workdir: {workdir}")
        
        if command:
            if isinstance(command, list):
                cmd_str = " ".join(command)
            else:
                cmd_str = command
            lines.append(f"Command: {cmd_str}")
        
        if lines:
            lines.append("Output:")
            header = "\n".join(lines)
            content = f"{header}\n{text}" if text else header
        else:
            content = text
        
        return {"type": "text", "content": content}


__all__ = [
    "BaseCodexShellTool",
    "DEFAULT_MAX_OUTPUT_TOKENS",
]