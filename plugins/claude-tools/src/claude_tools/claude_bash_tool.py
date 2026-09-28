# Copyright 2026 Dynamic Programming Solutions Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import asyncio
import concurrent.futures
import os
import re
import shlex
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_core.tool_result_payloads import (
    FORMAT_ANTHROPIC_MESSAGES,
    make_provider_native_tool_result,
)
from agent_core.types import ToolPlugin
from tool_compat_shared.background_processes import (
    DEFAULT_BACKGROUND_OWNERSHIP_MODE,
    DEFAULT_BACKGROUND_SHUTDOWN_POLICY,
    ensure_background_process_registry,
)
from tool_compat_shared.shell_engine import (
    ShellInfo,
    detect_shell,
    run_shell_command,
)

from .interop import claude_tool_interop_contribution


BASH_DESCRIPTION = (
    "Executes a given bash command and returns its output.\n\n"
    "The working directory persists between commands, but shell state does not. The shell environment is initialized from the user's profile (bash or zsh).\n\n"
    "IMPORTANT: Avoid using this tool to run `find`, `grep`, `cat`, `head`, `tail`, `sed`, `awk`, or `echo` commands, unless explicitly instructed or after you have verified that a dedicated tool cannot accomplish your task. Instead, use the appropriate dedicated tool as this will provide a much better experience for the user:\n\n"
    " - File search: Use Glob (NOT find or ls)\n"
    " - Content search: Use Grep (NOT grep or rg)\n"
    " - Read files: Use Read (NOT cat/head/tail)\n"
    " - Edit files: Use Edit (NOT sed/awk)\n"
    " - Write files: Use Write (NOT echo >/cat <<EOF)\n"
    " - Communication: Output text directly (NOT echo/printf)\n"
    "While the Bash tool can do similar things, it’s better to use the built-in tools as they provide a better user experience and make it easier to review tool calls and give permission.\n\n"
    "# Instructions\n"
    " - If your command will create new directories or files, first use this tool to run `ls` to verify the parent directory exists and is the correct location.\n"
    ' - Always quote file paths that contain spaces with double quotes in your command (e.g., cd "path with spaces/file.txt")\n'
    " - Try to maintain your current working directory throughout the session by using absolute paths and avoiding usage of `cd`. You may use `cd` if the User explicitly requests it. In particular, never prepend `cd <current-directory>` to a `git` command — `git` already operates on the current working tree, and the compound triggers a permission prompt.\n"
    " - You may specify an optional timeout in milliseconds (up to 600000ms / 10 minutes). By default, your command will timeout after 120000ms (2 minutes).\n"
    " - You can use the `run_in_background` parameter to run the command in the background. Only use this if you don't need the result immediately and are OK being notified when the command completes later. You do not need to check the output right away - you'll be notified when it finishes. You do not need to use '&' at the end of the command when using this parameter.\n"
    " - When issuing multiple commands:\n"
    '  - If the commands are independent and can run in parallel, make multiple Bash tool calls in a single message. Example: if you need to run "git status" and "git diff", send a single message with two Bash tool calls in parallel.\n'
    "  - If the commands depend on each other and must run sequentially, use a single Bash call with '&&' to chain them together.\n"
    "  - Use ';' only when you need to run commands sequentially but don't care if earlier commands fail.\n"
    "  - DO NOT use newlines to separate commands (newlines are ok in quoted strings).\n"
    " - For git commands:\n"
    "  - Prefer to create a new commit rather than amending an existing commit.\n"
    "  - Before running destructive operations (e.g., git reset --hard, git push --force, git checkout --), consider whether there is a safer alternative that achieves the same goal. Only use destructive operations when they are truly the best approach.\n"
    "  - Never skip hooks (--no-verify) or bypass signing (--no-gpg-sign, -c commit.gpgsign=false) unless the user has explicitly asked for it. If a hook fails, investigate and fix the underlying issue.\n"
    " - Avoid unnecessary `sleep` commands:\n"
    "  - Do not sleep between commands that can run immediately — just run them.\n"
    "  - If your command is long running and you would like to be notified when it finishes — use `run_in_background`. No sleep needed.\n"
    "  - Do not retry failing commands in a sleep loop — diagnose the root cause.\n"
    "  - If waiting for a background task you started with `run_in_background`, you will be notified when it completes — do not poll.\n"
    "  - If you must poll an external process, use a check command (e.g. `gh run view`) rather than sleeping first.\n"
    "  - If you must sleep, keep the duration short to avoid blocking the user.\n\n\n"
    "# Committing changes with git\n\n"
    "Only create commits when requested by the user. If unclear, ask first. When the user asks you to create a new git commit, follow these steps carefully:\n\n"
    "You can call multiple tools in a single response. When multiple independent pieces of information are requested and all commands are likely to succeed, run multiple tool calls in parallel for optimal performance. The numbered steps below indicate which commands should be batched in parallel.\n\n"
    "Git Safety Protocol:\n"
    " - NEVER update the git config\n"
    " - NEVER run destructive git commands (push --force, reset --hard, checkout ., restore ., clean -f, branch -D) unless the user explicitly requests these actions. Taking unauthorized destructive actions is unhelpful and can result in lost work, so it's best to ONLY run these commands when given direct instructions \n"
    " - NEVER skip hooks (--no-verify, --no-gpg-sign, etc) unless the user explicitly requests it\n"
    " - NEVER run force push to main/master, warn the user if they request it\n"
    " - CRITICAL: Always create NEW commits rather than amending, unless the user explicitly requests a git amend. When a pre-commit hook fails, the commit did NOT happen — so --amend would modify the PREVIOUS commit, which may result in destroying work or losing previous changes. Instead, after hook failure, fix the issue, re-stage, and create a NEW commit\n"
    ' - When staging files, prefer adding specific files by name rather than using "git add -A" or "git add .", which can accidentally include sensitive files (.env, credentials) or large binaries\n'
    " - NEVER commit changes unless the user explicitly asks you to. It is VERY IMPORTANT to only commit when explicitly asked, otherwise the user will feel that you are being too proactive\n\n"
    "1. Run the following bash commands in parallel, each using the Bash tool:\n"
    "  - Run a git status command to see all untracked files. IMPORTANT: Never use the -uall flag as it can cause memory issues on large repos.\n"
    "  - Run a git diff command to see both staged and unstaged changes that will be committed.\n"
    "  - Run a git log command to see recent commit messages, so that you can follow this repository's commit message style.\n"
    "2. Analyze all staged changes (both previously staged and newly added) and draft a commit message:\n"
    '  - Summarize the nature of the changes (eg. new feature, enhancement to an existing feature, bug fix, refactoring, test, docs, etc.). Ensure the message accurately reflects the changes and their purpose (i.e. "add" means a wholly new feature, "update" means an enhancement to an existing feature, "fix" means a bug fix, etc.).\n'
    "  - Do not commit files that likely contain secrets (.env, credentials.json, etc). Warn the user if they specifically request to commit those files\n"
    '  - Draft a concise (1-2 sentences) commit message that focuses on the "why" rather than the "what"\n'
    "  - Ensure it accurately reflects the changes and their purpose\n"
    "3. Run the following commands in parallel:\n"
    "   - Add relevant untracked files to the staging area.\n"
    "   - Create the commit with a message ending with:\n"
    "   Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>\n"
    "   - Run git status after the commit completes to verify success.\n"
    "   Note: git status depends on the commit completing, so run it sequentially after the commit.\n"
    "4. If the commit fails due to pre-commit hook: fix the issue and create a NEW commit\n\n"
    "Important notes:\n"
    " - NEVER run additional commands to read or explore code, besides git bash commands\n"
    " - NEVER use the TodoWrite or Agent tools\n"
    " - DO NOT push to the remote repository unless the user explicitly asks you to do so\n"
    " - IMPORTANT: Never use git commands with the -i flag (like git rebase -i or git add -i) since they require interactive input which is not supported.\n"
    " - IMPORTANT: Do not use --no-edit with git rebase commands, as the --no-edit flag is not a valid option for git rebase.\n"
    " - If there are no changes to commit (i.e., no untracked files and no modifications), do not create an empty commit\n"
    " - In order to ensure good formatting, ALWAYS pass the commit message via a HEREDOC, a la this example:\n"
    "<example>\n"
    "git commit -m \"$(cat <<'EOF'\n"
    "   Commit message here.\n\n"
    "   Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>\n"
    "   EOF\n"
    '   )"\n'
    "</example>\n\n"
    "# Creating pull requests\n"
    "Use the gh command via the Bash tool for ALL GitHub-related tasks including working with issues, pull requests, checks, and releases. If given a Github URL use the gh command to get the information needed.\n\n"
    "IMPORTANT: When the user asks you to create a pull request, follow these steps carefully:\n\n"
    "1. Run the following bash commands in parallel using the Bash tool, in order to understand the current state of the branch since it diverged from the main branch:\n"
    "   - Run a git status command to see all untracked files (never use -uall flag)\n"
    "   - Run a git diff command to see both staged and unstaged changes that will be committed\n"
    "   - Check if the current branch tracks a remote branch and is up to date with the remote, so you know if you need to push to the remote\n"
    "   - Run a git log command and `git diff [base-branch]...HEAD` to understand the full commit history for the current branch (from the time it diverged from the base branch)\n"
    "2. Analyze all changes that will be included in the pull request, making sure to look at all relevant commits (NOT just the latest commit, but ALL commits that will be included in the pull request!!!), and draft a pull request title and summary:\n"
    "   - Keep the PR title short (under 70 characters)\n"
    "   - Use the description/body for details, not the title\n"
    "3. Run the following commands in parallel:\n"
    "   - Create new branch if needed\n"
    "   - Push to remote with -u flag if needed\n"
    "   - Create PR using gh pr create with the format below. Use a HEREDOC to pass the body to ensure correct formatting.\n"
    "<example>\n"
    'gh pr create --title "the pr title" --body "$(cat <<\'EOF\'\n'
    "## Summary\n"
    "<1-3 bullet points>\n\n"
    "## Test plan\n"
    "[Bulleted markdown checklist of TODOs for testing the pull request...]\n\n"
    "🤖 Generated with [Claude Code](https://claude.com/claude-code)\n"
    "EOF\n"
    ')"\n'
    "</example>\n\n"
    "Important:\n"
    " - DO NOT use the TodoWrite or Agent tools\n"
    " - Return the PR URL when you're done, so the user can see it\n\n"
    "# Other common operations\n"
    " - View comments on a Github PR: gh api repos/foo/bar/pulls/123/comments"
)

BASH_DESCRIPTION = (
    BASH_DESCRIPTION.replace(
        "\n - NEVER update the git config", "\n- NEVER update the git config"
    )
    .replace(
        "\n - NEVER run destructive git commands",
        "\n- NEVER run destructive git commands",
    )
    .replace("\n - NEVER skip hooks", "\n- NEVER skip hooks")
    .replace(
        "\n - NEVER run force push to main/master, warn the user if they request it",
        "\n- NEVER run force push to main/master, warn the user if they request it",
    )
    .replace(
        "\n - CRITICAL: Always create NEW commits rather than amending, unless the user explicitly requests a git amend. When a pre-commit hook fails, the commit did NOT happen — so --amend would modify the PREVIOUS commit, which may result in destroying work or losing previous changes. Instead, after hook failure, fix the issue, re-stage, and create a NEW commit",
        "\n- CRITICAL: Always create NEW commits rather than amending, unless the user explicitly requests a git amend. When a pre-commit hook fails, the commit did NOT happen — so --amend would modify the PREVIOUS commit, which may result in destroying work or losing previous changes. Instead, after hook failure, fix the issue, re-stage, and create a NEW commit",
    )
    .replace(
        '\n - When staging files, prefer adding specific files by name rather than using "git add -A" or "git add .", which can accidentally include sensitive files (.env, credentials) or large binaries',
        '\n- When staging files, prefer adding specific files by name rather than using "git add -A" or "git add .", which can accidentally include sensitive files (.env, credentials) or large binaries',
    )
    .replace(
        "\n - NEVER commit changes unless the user explicitly asks you to. It is VERY IMPORTANT to only commit when explicitly asked, otherwise the user will feel that you are being too proactive",
        "\n- NEVER commit changes unless the user explicitly asks you to. It is VERY IMPORTANT to only commit when explicitly asked, otherwise the user will feel that you are being too proactive",
    )
    .replace(
        "\n - NEVER run additional commands to read or explore code, besides git bash commands",
        "\n- NEVER run additional commands to read or explore code, besides git bash commands",
    )
    .replace(
        "\n - NEVER use the TodoWrite or Agent tools",
        "\n- NEVER use the TodoWrite or Agent tools",
        1,
    )
    .replace(
        "\n - DO NOT push to the remote repository unless the user explicitly asks you to do so",
        "\n- DO NOT push to the remote repository unless the user explicitly asks you to do so",
    )
    .replace(
        "\n - IMPORTANT: Never use git commands with the -i flag (like git rebase -i or git add -i) since they require interactive input which is not supported.",
        "\n- IMPORTANT: Never use git commands with the -i flag (like git rebase -i or git add -i) since they require interactive input which is not supported.",
    )
    .replace(
        "\n - IMPORTANT: Do not use --no-edit with git rebase commands, as the --no-edit flag is not a valid option for git rebase.",
        "\n- IMPORTANT: Do not use --no-edit with git rebase commands, as the --no-edit flag is not a valid option for git rebase.",
    )
    .replace(
        "\n - If there are no changes to commit (i.e., no untracked files and no modifications), do not create an empty commit",
        "\n- If there are no changes to commit (i.e., no untracked files and no modifications), do not create an empty commit",
    )
    .replace(
        "\n - In order to ensure good formatting, ALWAYS pass the commit message via a HEREDOC, a la this example:",
        "\n- In order to ensure good formatting, ALWAYS pass the commit message via a HEREDOC, a la this example:",
    )
    .replace(
        "\n - DO NOT use the TodoWrite or Agent tools",
        "\n- DO NOT use the TodoWrite or Agent tools",
    )
    .replace(
        "\n - Return the PR URL when you're done, so the user can see it",
        "\n- Return the PR URL when you're done, so the user can see it",
    )
    .replace(
        "\n - View comments on a Github PR: gh api repos/foo/bar/pulls/123/comments",
        "\n- View comments on a Github PR: gh api repos/foo/bar/pulls/123/comments",
    )
)

BASH_SCHEMA: Dict[str, Any] = {
    "name": "Bash",
    "description": BASH_DESCRIPTION,
    "input_schema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "command": {
                "description": "The command to execute",
                "type": "string",
            },
            "dangerouslyDisableSandbox": {
                "description": "Set this to true to dangerously override sandbox mode and run commands without sandboxing.",
                "type": "boolean",
            },
            "description": {
                "description": 'Clear, concise description of what this command does in active voice. Never use words like "complex" or "risk" in the description - just describe what it does.\n\nFor simple commands (git, npm, standard CLI tools), keep it brief (5-10 words):\n- ls → "List files in current directory"\n- git status → "Show working tree status"\n- npm install → "Install package dependencies"\n\nFor commands that are harder to parse at a glance (piped commands, obscure flags, etc.), add enough context to clarify what it does:\n- find . -name "*.tmp" -exec rm {} \\; → "Find and delete all .tmp files recursively"\n- git reset --hard origin/main → "Discard all local changes and match remote main"\n- curl -s url | jq \'.data[]\' → "Fetch JSON from URL and extract data array elements"',
                "type": "string",
            },
            "run_in_background": {
                "description": "Set to true to run this command in the background. Use Read to read the output later.",
                "type": "boolean",
            },
            "timeout": {
                "description": "Optional timeout in milliseconds (max 600000)",
                "type": "number",
            },
        },
        "required": ["command"],
        "type": "object",
    },
}

# Segments of the upstream ``BASH_DESCRIPTION`` that vary with the cwd
# persistence and permissive-cd-guidance config options. The constants must
# match the upstream text exactly; tests assert their presence so upstream
# description changes are caught.
_UPSTREAM_OPENING = (
    "The working directory persists between commands, but shell state does not. "
    "The shell environment is initialized from the user's profile (bash or zsh).\n\n"
)
_NO_PERSISTENCE_OPENING = (
    "The working directory does not persist between commands; each command "
    "starts in the configured working directory. Shell state does not persist "
    "either. The shell environment is initialized from the user's profile "
    "(bash or zsh).\n\n"
)
_UPSTREAM_CD_GUIDANCE = (
    " - Try to maintain your current working directory throughout the session "
    "by using absolute paths and avoiding usage of `cd`. You may use `cd` if "
    "the User explicitly requests it. In particular, never prepend "
    "`cd <current-directory>` to a `git` command — `git` already operates on "
    "the current working tree, and the compound triggers a permission prompt.\n"
)
_UPSTREAM_CD_GUIDANCE_NO_PERSISTENCE = (
    " - Try to maintain your current working directory throughout the session "
    "by using absolute paths and avoiding usage of `cd`. You may use `cd` if "
    "the User explicitly requests it. When you do use `cd`, chain it with the "
    "command in a single Bash call (`cd dir && cmd`) because the working "
    "directory does not persist between commands. In particular, never "
    "prepend `cd <current-directory>` to a `git` command — `git` already "
    "operates on the current working tree, and the compound triggers a "
    "permission prompt.\n"
)
_PERMISSIVE_CD_GUIDANCE_PERSISTENT = (
    " - You may use `cd` when a command must run from a specific directory. "
    "The working directory persists between commands, so `cd` alone is "
    "sufficient; you don't need to chain `cd dir && cmd` for one-off "
    "directory changes. Avoid prepending `cd <current-directory>` to a `git` "
    "command — `git` already operates on the current working tree, and the "
    "compound triggers a permission prompt.\n"
)
_PERMISSIVE_CD_GUIDANCE_NON_PERSISTENT = (
    " - You may use `cd` when a command must run from a specific directory. "
    "The working directory does not persist between commands, so chain "
    "`cd dir && cmd` in a single Bash call when you need to run from a "
    "specific directory. Avoid prepending `cd <current-directory>` to a `git` "
    "command — `git` already operates on the current working tree, and the "
    "compound triggers a permission prompt.\n"
)


def _bash_description_for_options(
    *,
    cwd_persistence: bool,
    permissive_cd_guidance: bool,
) -> str:
    """Build the Bash tool description for the cwd config options.

    With both options at their defaults (persistence on, upstream guidance)
    the result is the unmodified upstream ``BASH_DESCRIPTION``.
    """
    description = BASH_DESCRIPTION
    if not cwd_persistence:
        description = description.replace(_UPSTREAM_OPENING, _NO_PERSISTENCE_OPENING)
        cd_guidance = (
            _PERMISSIVE_CD_GUIDANCE_NON_PERSISTENT
            if permissive_cd_guidance
            else _UPSTREAM_CD_GUIDANCE_NO_PERSISTENCE
        )
    elif permissive_cd_guidance:
        cd_guidance = _PERMISSIVE_CD_GUIDANCE_PERSISTENT
    else:
        return description
    return description.replace(_UPSTREAM_CD_GUIDANCE, cd_guidance)


DEFAULT_TIMEOUT_MS = 120_000
MAX_TIMEOUT_MS = 600_000
SENTINEL_STATUS = "__CLAUDE_BASH_STATUS__:"
SENTINEL_CWD = "__CLAUDE_BASH_CWD__:"
SENTINEL_RE = re.compile(
    rf"\n{re.escape(SENTINEL_STATUS)}(?P<status>-?\d+)\n{re.escape(SENTINEL_CWD)}(?P<cwd>[^\n]*)\n?$",
    re.S,
)


def _detect_login_shell() -> ShellInfo:
    shell = detect_shell()
    if shell.name in {"bash", "zsh"}:
        return ShellInfo(name=shell.name, path=shell.path, args=("-lc",))
    return shell


def _run_async(awaitable: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(asyncio.run, awaitable)
        return future.result()


def _tool_result_block(
    tool_use_id: str,
    content: str,
    *,
    is_error: bool,
) -> Dict[str, Any]:
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": content,
        "is_error": is_error,
        "cache_control": {"type": "ephemeral"},
    }


def _wrap_foreground_command(command: str) -> str:
    quoted = shlex.quote(command)
    return (
        'ORIG_PWD="$PWD"; '
        f"eval {quoted}; "
        'STATUS=$?; FINAL_PWD="$PWD"; '
        f'printf "\\n{SENTINEL_STATUS}%s\\n{SENTINEL_CWD}%s\\n" "$STATUS" "$FINAL_PWD"; '
        "exit 0"
    )


def _parse_wrapped_output(output: str, *, working_directory: str) -> dict[str, Any]:
    match = SENTINEL_RE.search(output)
    if match is None:
        return {
            "exit_code": 0,
            "output": output.rstrip("\n"),
            "cwd": working_directory,
        }
    content = output[: match.start()]
    if content.endswith("\n"):
        content = content[:-1]
    cwd_raw = match.group("cwd")
    cwd = cwd_raw if isinstance(cwd_raw, str) and cwd_raw else working_directory
    return {
        "exit_code": int(match.group("status")),
        "output": content,
        "cwd": cwd,
    }


def _cwd_for_storage(end_cwd: str, configured_wd: str) -> str:
    """Compute the cwd for storage, relative to ``configured_wd`` when inside the tree.

    Returns:
        - ``"."`` when ``end_cwd`` is the configured working directory
        - a relative path (e.g. ``"subdir"``, ``"subdir/nested"``) when inside the tree
        - an absolute path when outside the tree (best effort; not portable)
    """
    try:
        resolved_end = Path(end_cwd).resolve()
        resolved_cfg = Path(configured_wd).resolve()
    except Exception:
        return end_cwd
    try:
        rel = resolved_end.relative_to(resolved_cfg)
        rel_str = str(rel)
        return rel_str if rel_str else "."
    except ValueError:
        # Outside the tree → store absolute path
        return str(resolved_end)


def _resolve_stored_cwd(stored: Any, configured_wd: str) -> str:
    """Resolve a stored cwd against the configured working directory.

    Falls back to the configured working directory when the stored value is
    missing, empty, or resolves to a nonexistent path.
    """
    if not isinstance(stored, str) or not stored or stored == ".":
        return str(Path(configured_wd).resolve())
    if os.path.isabs(stored):
        candidate = str(Path(stored).resolve())
    else:
        candidate = str((Path(configured_wd) / stored).resolve())
    if not Path(candidate).exists():
        return str(Path(configured_wd).resolve())
    return candidate


def _apply_cwd_lines(
    message: str,
    *,
    start_cwd: str,
    end_cwd: str,
    cwd_persistence: bool,
) -> str:
    """Wrap a bash result message with cwd visibility lines for the model.

    The initial cwd always appears as the first line. The end cwd is noted as
    the last line only when the command changed it and the change persists.
    """
    parts = [f"[cwd: {start_cwd}]", message]
    if cwd_persistence and end_cwd != start_cwd:
        parts.append(f"[cwd: {end_cwd}]")
    return "\n".join(parts)


def _last_bash_end_cwd_from_context(
    context: Optional[Dict[str, Any]],
) -> Optional[str]:
    """Scan session messages for the most recent bash tool-result ``end_cwd``."""
    if not isinstance(context, dict):
        return None
    session = context.get("session")
    if not isinstance(session, dict):
        return None
    messages = session.get("messages")
    if not isinstance(messages, list):
        return None
    for message in reversed(messages):
        if not isinstance(message, dict):
            continue
        if message.get("role") != "tool":
            continue
        metadata = message.get("metadata")
        if not isinstance(metadata, dict):
            continue
        if metadata.get("tool_name") != "Bash":
            continue
        if metadata.get("tool_plugin") != "claude_bash_tool":
            continue
        bash_meta = metadata.get("bash")
        if not isinstance(bash_meta, dict):
            continue
        end_cwd = bash_meta.get("end_cwd")
        if isinstance(end_cwd, str) and end_cwd:
            return end_cwd
    return None


def _runtime_state_root_from_context(
    context: Optional[Dict[str, Any]],
    *,
    working_directory: str,
) -> Path:
    if isinstance(context, dict):
        root = context.get("runtime_state_root")
        if isinstance(root, (str, os.PathLike)):
            return Path(root).expanduser().resolve()
    return (Path(working_directory).resolve() / ".crystal" / "runtime").resolve()


def _tool_runtime_from_context(context: Optional[Dict[str, Any]]) -> Any | None:
    if isinstance(context, dict):
        return context.get("tool_runtime") or context.get("runtime_store")
    return None


def _session_id_from_context(context: Optional[Dict[str, Any]]) -> str | None:
    if not isinstance(context, dict):
        return None
    value = context.get("session_id")
    return value if isinstance(value, str) and value else None


def _agent_id_from_context(context: Optional[Dict[str, Any]]) -> str | None:
    if not isinstance(context, dict):
        return None
    session = context.get("session")
    if not isinstance(session, dict):
        return None
    metadata = session.get("metadata")
    if not isinstance(metadata, dict):
        return None
    value = metadata.get("agent_id")
    return value if isinstance(value, str) and value else None


class ClaudeBashTool(ToolPlugin):
    name = "claude_bash_tool"
    version = "0.1.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        working_directory = str(config.get("working_directory") or os.getcwd())
        return {
            "config": config,
            "working_directory": str(Path(working_directory).resolve()),
            "timeout_ms": int(config.get("shell_timeout_ms") or DEFAULT_TIMEOUT_MS),
            "max_timeout_ms": int(config.get("shell_max_timeout_ms") or MAX_TIMEOUT_MS),
            "cwd_persistence": bool(config.get("bash_cwd_persistence", True)),
            "include_cwd_in_result": bool(
                config.get("bash_include_cwd_in_result", False)
            ),
            "permissive_cd_guidance": bool(
                config.get("bash_permissive_cd_guidance", False)
            ),
            "background_ownership_mode": str(
                config.get("background_process_ownership_mode")
                or DEFAULT_BACKGROUND_OWNERSHIP_MODE
            ),
            "background_shutdown_policy": str(
                config.get("background_process_shutdown_policy")
                or DEFAULT_BACKGROUND_SHUTDOWN_POLICY
            ),
        }

    def get_tool_interop_contribution(self, state: Dict[str, Any]):
        return claude_tool_interop_contribution()

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        description = _bash_description_for_options(
            cwd_persistence=bool(state.get("cwd_persistence", True)),
            permissive_cd_guidance=bool(state.get("permissive_cd_guidance", False)),
        )
        return [{**BASH_SCHEMA, "description": description}]

    def can_handle_tool_call(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        **_: Any,
    ) -> Optional[bool]:
        return tool_name == "Bash"

    def _result(
        self,
        *,
        tool_use_id: str,
        message: str,
        success: bool,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        data = {
            "success": success,
            "anthropic_content": [
                _tool_result_block(tool_use_id, message, is_error=not success)
            ],
            "text": message,
        }
        if extra:
            data.update(extra)
        return data

    def _format_success_output(self, output: str) -> str:
        cleaned = output.rstrip("\n")
        if not cleaned:
            return "(Bash completed with no output)"
        return cleaned

    def _format_failure_output(self, *, exit_code: int, output: str) -> str:
        payload = f"Exit code {exit_code}"
        cleaned = output.rstrip("\n")
        if cleaned:
            payload = f"{payload}\n{cleaned}"
        return payload

    def _execute_foreground(
        self,
        command: str,
        *,
        timeout_ms: int,
        working_directory: str,
        cancellation: Any | None = None,
    ) -> Dict[str, Any]:
        shell = _detect_login_shell()
        wrapped = _wrap_foreground_command(command)
        result = _run_async(
            run_shell_command(
                wrapped,
                workdir=working_directory,
                timeout_seconds=timeout_ms / 1000.0,
                shell=shell,
                cancellation=cancellation,
            )
        )
        if result.get("timed_out") or result.get("cancelled"):
            return {
                "exit_code": 143,
                "output": str(result.get("output") or "").rstrip("\n"),
                "success": False,
                "cwd": working_directory,
                "cancelled": bool(result.get("cancelled")),
            }
        parsed = _parse_wrapped_output(
            str(result.get("output") or ""),
            working_directory=working_directory,
        )
        exit_code = int(parsed["exit_code"])
        return {
            "exit_code": exit_code,
            "output": str(parsed["output"]),
            "success": exit_code == 0,
            "cwd": str(parsed.get("cwd") or working_directory),
        }

    def execute_tool(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        tool_call: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        cancellation: Any | None = None,
        **_: Any,
    ) -> Dict[str, Any]:
        if tool_name != "Bash":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        if not isinstance(payload, dict):
            return {"success": False, "error": "Bash input must be an object"}

        command = payload.get("command")
        if not isinstance(command, str) or not command.strip():
            return {"success": False, "error": "command must be a non-empty string"}

        tool_use_id = "call_Bash"
        if isinstance(tool_call, dict):
            raw_id = tool_call.get("id")
            if isinstance(raw_id, str) and raw_id:
                tool_use_id = raw_id

        default_timeout_ms = int(state.get("timeout_ms") or DEFAULT_TIMEOUT_MS)
        max_timeout_ms = int(state.get("max_timeout_ms") or MAX_TIMEOUT_MS)
        timeout_raw = payload.get("timeout")
        if isinstance(timeout_raw, (int, float)):
            timeout_ms = max(1, min(int(timeout_raw), max_timeout_ms))
        else:
            timeout_ms = min(default_timeout_ms, max_timeout_ms)

        working_directory = str(state.get("working_directory") or os.getcwd())
        cwd_persistence = bool(state.get("cwd_persistence", True))
        include_cwd = bool(state.get("include_cwd_in_result", False))
        if bool(payload.get("run_in_background")):
            registry = ensure_background_process_registry(
                runtime_state_root=_runtime_state_root_from_context(
                    context,
                    working_directory=working_directory,
                ),
                tool_runtime=_tool_runtime_from_context(context),
            )
            background = registry.start_background_command(
                command.strip(),
                working_directory=working_directory,
                shell=_detect_login_shell(),
                ownership_mode=str(
                    state.get("background_ownership_mode")
                    or DEFAULT_BACKGROUND_OWNERSHIP_MODE
                ),
                shutdown_policy=str(
                    state.get("background_shutdown_policy")
                    or DEFAULT_BACKGROUND_SHUTDOWN_POLICY
                ),
                agent_id=_agent_id_from_context(context),
                session_id=_session_id_from_context(context),
                request_id=(
                    context.get("request_id")
                    if isinstance(context, dict)
                    and isinstance(context.get("request_id"), str)
                    else None
                ),
            )
            if background.status == "running":
                output_path = str(background.output_path)
                background_id = background.process_id
                message = (
                    f"Command running in background with ID: {background_id}. "
                    f"Output is being written to: {output_path}"
                )
                if include_cwd:
                    message = _apply_cwd_lines(
                        message,
                        start_cwd=working_directory,
                        end_cwd=working_directory,
                        cwd_persistence=False,
                    )
                return self._result(
                    tool_use_id=tool_use_id,
                    message=message,
                    success=True,
                    extra={
                        "background": True,
                        "background_id": background_id,
                        "output_path": output_path,
                        "pid": int(background.pid),
                    },
                )
            output = (
                background.output_path.read_text(encoding="utf-8", errors="replace")
                if background.output_path.exists()
                else ""
            )
            if background.status == "succeeded":
                message = self._format_success_output(output)
                if include_cwd:
                    message = _apply_cwd_lines(
                        message,
                        start_cwd=working_directory,
                        end_cwd=working_directory,
                        cwd_persistence=False,
                    )
                return self._result(
                    tool_use_id=tool_use_id,
                    message=message,
                    success=True,
                )
            message = self._format_failure_output(
                exit_code=int(background.exit_code or 0),
                output=output,
            )
            if include_cwd:
                message = _apply_cwd_lines(
                    message,
                    start_cwd=working_directory,
                    end_cwd=working_directory,
                    cwd_persistence=False,
                )
            return self._result(
                tool_use_id=tool_use_id,
                message=message,
                success=False,
            )

        # Resolve the working directory from the most recent bash tool-result
        # ``end_cwd`` in the session, falling back to the configured working
        # directory. This makes ``cd`` persist between commands the way the
        # upstream Claude Code Bash tool description says it does. When cwd
        # persistence is disabled, every command starts in the configured
        # working directory and no ``end_cwd`` metadata is emitted.
        if cwd_persistence:
            stored_cwd = _last_bash_end_cwd_from_context(context)
            if stored_cwd is not None:
                resolved = _resolve_stored_cwd(stored_cwd, working_directory)
            else:
                resolved = str(Path(working_directory).resolve())
        else:
            resolved = str(Path(working_directory).resolve())

        foreground = self._execute_foreground(
            command.strip(),
            timeout_ms=timeout_ms,
            working_directory=resolved,
            cancellation=cancellation,
        )
        exit_code = int(foreground["exit_code"])
        output = str(foreground["output"] or "")
        end_cwd = str(foreground.get("cwd") or resolved)
        if foreground["success"]:
            message = self._format_success_output(output)
        else:
            message = self._format_failure_output(exit_code=exit_code, output=output)
        if include_cwd:
            message = _apply_cwd_lines(
                message,
                start_cwd=resolved,
                end_cwd=end_cwd,
                cwd_persistence=cwd_persistence,
            )
        extra: Dict[str, Any] = {}
        if cwd_persistence:
            stored = _cwd_for_storage(end_cwd, working_directory)
            extra["metadata"] = {"bash": {"end_cwd": stored}}
        if foreground.get("cancelled"):
            extra["cancelled"] = True
        return self._result(
            tool_use_id=tool_use_id,
            message=message,
            success=bool(foreground["success"]),
            extra=extra or None,
        )

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> Any:
        content = result.get("anthropic_content")
        if isinstance(content, list) and all(
            isinstance(item, dict) for item in content
        ):
            return make_provider_native_tool_result(
                format=FORMAT_ANTHROPIC_MESSAGES,
                content=content,
                text=str(result.get("text") or ""),
            )
        if result.get("success"):
            return str(result.get("text") or "")
        return f"Error: {result.get('text') or result.get('error') or ''}"

    def to_display_format(
        self,
        text: str,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "type": "text",
            "content": text,
            "single_line": "Bash command",
        }


__all__ = ["ClaudeBashTool", "BASH_SCHEMA"]
