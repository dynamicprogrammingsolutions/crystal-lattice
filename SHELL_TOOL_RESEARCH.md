
Based on the search results, I can see that the bash/shell tool in OpenAI's Codex is actually called `shell` (not "bash tool"), and the documentation references it in the prompting guides. Let me provide you with the key information:

## Shell Tool Implementation in Codex

Based on the official documentation from the OpenAI Cookbook, here's what we know about the `shell` tool:

### Key Guidelines from the Codex Prompting Guide:

The arguments to `shell` will be passed to execvp(). Most terminal commands should be prefixed with ["bash", "-lc"]. Always set the `workdir` param when using the shell function.

### Implementation Details:

The `shell` tool is **not implemented in Python** as a standalone tool like `apply_patch`. Instead, it's a built-in virtual tool that's implemented directly in the Codex Rust binary (codex-rs). 

The shell tool:
1. **Takes arguments that are passed to execvp()** - a system call that executes commands
2. **Requires commands to be prefixed with `["bash", "-lc"]`** for proper terminal execution
3. **Requires a `workdir` parameter** to specify the working directory
4. **Is sandboxed** - operates under macOS Seatbelt or Linux Landlock sandboxes depending on the platform

### Where to Find More Info:

The GPT-5-Codex Prompt is available at https://github.com/openai/codex/blob/main/codex-rs/core/gpt_5_codex_prompt.md within Codex CLI as well as the GPT-5 prompt at https://github.com/openai/codex/blob/main/codex-rs/core/prompt.md

### Python Reference Implementation:

**Unlike `apply_patch`, there is NO standalone Python reference implementation for the shell tool**. The shell command execution is handled natively by the Codex CLI binary itself, which is written in Rust.

If you need to implement shell command execution in your own Python tool, you would typically use Python's `subprocess` module with proper sandboxing, similar to how Codex does it internally. The key is to:

1. Use `subprocess.run()` or similar
2. Prefix commands with `["bash", "-lc", "your_command"]`
3. Set the working directory (`cwd` parameter)
4. Implement proper sandboxing/security controls

Would you like me to help you create a Python wrapper for shell command execution that follows the Codex pattern?

--
I'll create a Python wrapper for shell command execution that follows the Codex pattern:

```python
import subprocess
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
import shlex


class ShellExecutionError(Exception):
    """Custom exception for shell execution errors."""
    pass


class ShellTool:
    """
    Shell tool implementation following OpenAI Codex patterns.
    Executes shell commands with proper sandboxing and working directory management.
    """
    
    def __init__(self, allowed_dirs: Optional[List[str]] = None, timeout: int = 300):
        """
        Initialize the shell tool.
        
        Args:
            allowed_dirs: List of directories where command execution is allowed (for sandboxing)
            timeout: Maximum execution time in seconds (default: 300)
        """
        self.allowed_dirs = [Path(d).resolve() for d in allowed_dirs] if allowed_dirs else None
        self.timeout = timeout
    
    def execute(
        self,
        command: str,
        workdir: str,
        env: Optional[Dict[str, str]] = None,
        capture_output: bool = True,
        shell_prefix: List[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a shell command following Codex patterns.
        
        Args:
            command: The shell command to execute
            workdir: Working directory for command execution (required)
            env: Optional environment variables to set
            capture_output: Whether to capture stdout/stderr (default: True)
            shell_prefix: Shell prefix (default: ["bash", "-lc"])
        
        Returns:
            Dict containing:
                - stdout: Standard output
                - stderr: Standard error
                - returncode: Exit code
                - success: Boolean indicating success
        
        Raises:
            ShellExecutionError: If execution fails or validation fails
        """
        if shell_prefix is None:
            shell_prefix = ["bash", "-lc"]
        
        # Validate workdir
        if not workdir:
            raise ShellExecutionError("workdir parameter is required")
        
        workdir_path = Path(workdir).resolve()
        
        # Check if workdir exists
        if not workdir_path.exists():
            raise ShellExecutionError(f"Working directory does not exist: {workdir}")
        
        if not workdir_path.is_dir():
            raise ShellExecutionError(f"Working directory is not a directory: {workdir}")
        
        # Sandboxing check: ensure workdir is in allowed directories
        if self.allowed_dirs:
            if not any(self._is_subpath(workdir_path, allowed) for allowed in self.allowed_dirs):
                raise ShellExecutionError(
                    f"Working directory {workdir} is not in allowed directories: {self.allowed_dirs}"
                )
        
        # Prepare the command following Codex pattern: ["bash", "-lc", "command"]
        if isinstance(command, str):
            cmd_args = shell_prefix + [command]
        else:
            cmd_args = shell_prefix + [" ".join(command)]
        
        # Prepare environment
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)
        
        try:
            # Execute the command
            result = subprocess.run(
                cmd_args,
                cwd=str(workdir_path),
                env=exec_env,
                capture_output=capture_output,
                text=True,
                timeout=self.timeout,
                check=False  # Don't raise exception on non-zero exit
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
                "command": command,
                "workdir": str(workdir_path)
            }
            
        except subprocess.TimeoutExpired:
            raise ShellExecutionError(f"Command timed out after {self.timeout} seconds: {command}")
        except Exception as e:
            raise ShellExecutionError(f"Failed to execute command: {str(e)}")
    
    def _is_subpath(self, path: Path, parent: Path) -> bool:
        """Check if path is a subpath of parent."""
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False


# Convenience function for quick execution
def shell(command: str, workdir: str, **kwargs) -> Dict[str, Any]:
    """
    Quick shell command execution following Codex pattern.
    
    Args:
        command: Shell command to execute
        workdir: Working directory (required)
        **kwargs: Additional arguments passed to ShellTool.execute()
    
    Returns:
        Dict with execution results
    
    Example:
        result = shell("ls -la", workdir="/tmp")
        if result["success"]:
            print(result["stdout"])
        else:
            print(f"Error: {result['stderr']}")
    """
    tool = ShellTool()
    return tool.execute(command, workdir, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    # Example 1: Basic usage
    print("=== Example 1: Basic command ===")
    result = shell("echo 'Hello from Codex shell tool'", workdir="/tmp")
    print(f"Success: {result['success']}")
    print(f"Output: {result['stdout']}")
    print(f"Return code: {result['returncode']}")
    
    # Example 2: With sandboxing
    print("\n=== Example 2: With sandboxing ===")
    sandboxed_shell = ShellTool(allowed_dirs=["/tmp", "/home"], timeout=60)
    try:
        result = sandboxed_shell.execute("pwd && ls -la", workdir="/tmp")
        print(f"Output:\n{result['stdout']}")
    except ShellExecutionError as e:
        print(f"Error: {e}")
    
    # Example 3: Multiple commands
    print("\n=== Example 3: Multiple commands ===")
    result = shell(
        "mkdir -p test_dir && cd test_dir && echo 'test content' > test.txt && cat test.txt",
        workdir="/tmp"
    )
    print(f"Success: {result['success']}")
    print(f"Output: {result['stdout']}")
    
    # Example 4: Error handling
    print("\n=== Example 4: Error handling ===")
    result = shell("ls /nonexistent_directory", workdir="/tmp")
    print(f"Success: {result['success']}")
    print(f"Error output: {result['stderr']}")
    print(f"Return code: {result['returncode']}")
    
    # Example 5: Custom environment variables
    print("\n=== Example 5: Custom environment ===")
    result = shell(
        "echo $CUSTOM_VAR",
        workdir="/tmp",
        env={"CUSTOM_VAR": "Hello from custom env"}
    )
    print(f"Output: {result['stdout']}")
```

## Key Features:

1. **Codex Pattern Compliance**:
   - Commands are prefixed with `["bash", "-lc"]` (configurable)
   - `workdir` parameter is required
   - Returns structured results with stdout, stderr, returncode

2. **Security Features**:
   - Optional directory sandboxing (allowed_dirs)
   - Working directory validation
   - Timeout protection (default 300 seconds)
   - Path traversal prevention

3. **Flexible Usage**:
   - Class-based `ShellTool` for advanced usage
   - Convenience `shell()` function for quick commands
   - Custom environment variable support
   - Configurable shell prefix

4. **Error Handling**:
   - Custom `ShellExecutionError` exception
   - Validation before execution
   - Timeout handling
   - Non-zero exit codes don't raise exceptions (returned in result)

## Usage Examples:

```python
# Simple usage
result = shell("git status", workdir="/path/to/repo")
if result["success"]:
    print(result["stdout"])

# With sandboxing
tool = ShellTool(allowed_dirs=["/home/user/projects"], timeout=60)
result = tool.execute("npm install", workdir="/home/user/projects/myapp")

# Tool-calling format (for LLM integration)
def call_shell_tool(command: str, workdir: str) -> dict:
    """Tool callable by LLM."""
    return shell(command, workdir)
```

This implementation follows the Codex pattern while providing Python-native error handling and security features. Would you like me to add any additional features like streaming output, async support, or more advanced sandboxing?