# 080 — Shell `apply_patch` interception hardening

Short description: Lower-priority Codex parity follow-up to make shell-surfaced `apply_patch` behavior safer and more Codex-like when the model emits patch edits through shell tools instead of the dedicated `apply_patch` tool.

**STATUS: PENDING**

## Requirements checklist

- [ ] Decide whether shell `apply_patch` should be broadened for safe interception or explicitly rejected when the dedicated `apply_patch` tool is enabled.
- [ ] Cover shell-script forms that currently bypass interception, especially prefixed and suffixed scripts.
- [ ] Ensure the model gets a clear, non-hanging failure mode when it emits shell `apply_patch` in an unsupported form.
- [ ] Add regression tests for the currently missed shell-script shapes.

Parent Task: `tasks/20260225-codex-tools-parity/000-main.md`
Depends On: `tasks/20260225-codex-tools-parity/013-apply-patch-true-parity.md`

## Why this follow-up exists

Investigation on 2026-04-04 found that `intercept_apply_patch` is enabled in the default config, but the shell interceptor only catches a narrow subset of shell forms:

- `application/python/agent_terminal_app/default_config/config.json:595-602`
- `application/python/agent_terminal_app/default_config/.plugin_cache/plugins/codex-tools@60017b8be6285556c9d71bd1a707bc9016b012ece2144c4f9fd1d03280488a81/codex_tools/base_shell_tool.py:40-66`
- `application/python/agent_terminal_app/default_config/.plugin_cache/plugins/codex-tools@60017b8be6285556c9d71bd1a707bc9016b012ece2144c4f9fd1d03280488a81/codex_tools/apply_patch_runtime.py:101-105`
- `application/python/agent_terminal_app/default_config/.plugin_cache/plugins/codex-tools@60017b8be6285556c9d71bd1a707bc9016b012ece2144c4f9fd1d03280488a81/codex_tools/apply_patch_runtime.py:814-829`

Confirmed misses:

- `echo before` followed by `apply_patch <<'PATCH' ...`
- `apply_patch <<'PATCH' ...` followed by another shell command
- bare `apply_patch` reading stdin

Those forms can fall through to the real PATH `apply_patch` helper, which is unsafe in our current shell runtime.

## Desired outcome

When the dedicated `apply_patch` tool exists, shell `apply_patch` should never degrade into a hanging external helper. It should either:

- be intercepted and routed safely to the internal patch runtime, or
- be rejected immediately with a clear error telling the model to use the real `apply_patch` tool.

## Testing expectations

- Pure heredoc shell patch form.
- Prefixed shell patch form.
- Suffixed shell patch form.
- Bare `apply_patch` with no stdin payload.
- A session using the dedicated `apply_patch` tool should remain unaffected.